"""
M2 — cobertura de regressão para concorrência REAL (PostgreSQL) da
autoridade server-side de intent de PIX
(app/services/pix_send_intent_service.py).

Mesmo padrão e mesmas garantias de test_pix_send_concurrency_postgres.py:
SQLite não oferece um modelo de concorrência representativo do PostgreSQL
de produção para este tipo de prova (bloqueio real de linha sob
transação concorrente) — este arquivo existe especificamente para isso.

GUARD FAIL-CLOSED: idêntico ao arquivo irmão — só lê
`PIX_CONCURRENCY_TEST_DATABASE_URL`, nunca `DATABASE_URL`; ausência =>
skip; presença fora do allowlist exato => fail imediato, antes de
qualquer drop_all/create_all/conexão útil.

Cada worker segue o lifecycle real de `app.database.get_db()`
(`try: ... finally: db.close()`), sem rollback() artificial.

PROVA A — duas reservas iniciais simultâneas para o mesmo
(user_id, fingerprint): devem produzir UMA única linha e a MESMA send_key
(K1), nunca K1 e K2 distintos.

PROVA B — duas renovações (force_new=true) simultâneas após a intent já
estar acknowledged: devem produzir UMA única nova geração e a MESMA K2,
nunca K2 e K3.
"""
import concurrent.futures
import os
import threading
import time
from decimal import Decimal
from urllib.parse import urlparse

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.pix_ledger import PixLedger
from app.models.pix_send_intent import PixSendIntent
from app.models.user_main import User
from app.services.pix_send_intent_service import (
    acknowledge_pix_send_intent,
    reserve_pix_send_intent,
)
from app.services.pix_service import send_pix

TIMEOUT = 15

_ENV_VAR = "PIX_CONCURRENCY_TEST_DATABASE_URL"
_ALLOWED_SCHEMES = {"postgresql", "postgresql+psycopg2"}
_ALLOWED_HOSTS = {"localhost", "127.0.0.1"}
_ALLOWED_DATABASE = "auratest_ci"
_ALLOWED_USER = "auratest"


def _require_test_database_url() -> str:
    raw = os.environ.get(_ENV_VAR)
    if not raw:
        pytest.skip(
            f"{_ENV_VAR} não definida — teste de concorrência PostgreSQL "
            "pulado (sem serviço de banco disponível para esta execução)."
        )

    parsed = urlparse(raw)
    ok = (
        parsed.scheme in _ALLOWED_SCHEMES
        and parsed.hostname in _ALLOWED_HOSTS
        and parsed.path.lstrip("/") == _ALLOWED_DATABASE
        and parsed.username == _ALLOWED_USER
    )
    if not ok:
        pytest.fail(
            f"{_ENV_VAR} não corresponde exatamente ao banco de teste "
            f"efêmero esperado (scheme∈{_ALLOWED_SCHEMES}, "
            f"host∈{_ALLOWED_HOSTS}, database={_ALLOWED_DATABASE!r}, "
            f"user={_ALLOWED_USER!r}). Abortando ANTES de qualquer "
            "drop_all/create_all/conexão útil."
        )
    return raw


@pytest.fixture(scope="session")
def database_url():
    return _require_test_database_url()


@pytest.fixture(scope="session")
def engine(database_url):
    eng = create_engine(database_url, pool_size=10, max_overflow=10)
    yield eng
    eng.dispose()


@pytest.fixture(scope="session")
def session_factory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture()
def clean_schema(engine):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def _create_user(session_factory, user_id, email):
    db = session_factory()
    try:
        db.add(User(id=user_id, email=email, hashed_password="x", role="customer"))
        db.commit()
    finally:
        db.close()


def _fund(session_factory, user_id, amount):
    db = session_factory()
    try:
        db.add(PixLedger(user_id=user_id, kind="credit", amount=Decimal(amount)))
        db.commit()
    finally:
        db.close()


def _intents_for(session_factory, user_id):
    db = session_factory()
    try:
        return db.query(PixSendIntent).filter_by(user_id=user_id).all()
    finally:
        db.close()


def _reserve_worker(session_factory, **kwargs):
    db = session_factory()
    try:
        return reserve_pix_send_intent(db, **kwargs)
    finally:
        db.close()


class FlushPauseHook:
    """Pausa T1 logo após o INSERT da PixSendIntent alvo ter sido
    efetivamente flushado (after_flush), antes do commit — mesmo padrão
    de test_pix_send_concurrency_postgres.py, adaptado ao modelo novo."""

    def __init__(self, session, target_user_id, target_fingerprint):
        self.session = session
        self.target_user_id = target_user_id
        self.target_fingerprint = target_fingerprint
        self.paused_event = threading.Event()
        self.release_event = threading.Event()
        self.fired = False
        self._matched_this_flush = False
        self._attached = False

    def before_flush(self, session, flush_context, instances):
        self._matched_this_flush = any(
            isinstance(obj, PixSendIntent)
            and obj.user_id == self.target_user_id
            and obj.fingerprint_hash == self.target_fingerprint
            for obj in session.new
        )

    def after_flush(self, session, flush_context):
        if self._matched_this_flush and not self.fired:
            self.fired = True
            self._matched_this_flush = False
            self.paused_event.set()
            released = self.release_event.wait(timeout=TIMEOUT)
            if not released:
                raise TimeoutError("T1 nao foi liberada a tempo (flush hook, reserva inicial)")

    def attach(self):
        if not self._attached:
            event.listen(self.session, "before_flush", self.before_flush)
            event.listen(self.session, "after_flush", self.after_flush)
            self._attached = True

    def detach(self):
        if self._attached:
            event.remove(self.session, "before_flush", self.before_flush)
            event.remove(self.session, "after_flush", self.after_flush)
            self._attached = False


class UpdatePauseHook:
    """Pausa T1 logo depois que o UPDATE de renovação (compare-and-swap
    via Query.update()) em pix_send_intents foi realmente executado no
    PostgreSQL (lock de linha já concedido), antes do commit.

    Anexado à Session (evento `after_bulk_update`), não a uma Connection
    crua: `reserve_pix_send_intent()` já fez um INSERT+rollback antes de
    chegar aqui (tentativa inicial que colide, esperada), o que devolve a
    Connection física ao pool — um hook em `after_cursor_execute` de uma
    Connection capturada antes desse rollback nunca veria a execução
    seguinte. O evento de Session sobrevive a esse ciclo porque está
    ligado ao objeto Session, não à Connection física do momento."""

    def __init__(self, session):
        self.session = session
        self.lock_acquired_event = threading.Event()
        self.release_event = threading.Event()
        self.fired = False
        self._attached = False

    def after_bulk_update(self, update_context):
        if not self.fired:
            self.fired = True
            self.lock_acquired_event.set()
            released = self.release_event.wait(timeout=TIMEOUT)
            if not released:
                raise TimeoutError("T1 nao foi liberada a tempo (update hook, renovacao)")

    def attach(self):
        if not self._attached:
            event.listen(self.session, "after_bulk_update", self.after_bulk_update)
            self._attached = True

    def detach(self):
        if self._attached:
            event.remove(self.session, "after_bulk_update", self.after_bulk_update)
            self._attached = False


# ======================================================================
# PROVA A — duas reservas iniciais simultâneas -> UMA única K1
# ======================================================================
def test_prova_a_reserva_inicial_concorrente(engine, session_factory, clean_schema):
    _create_user(session_factory, 401, "user401@concurrency.test")

    db1 = session_factory()
    fingerprint = None

    # Calcula o fingerprint esperado com a MESMA fórmula do service, sem
    # duplicar a lógica: chama reserve uma vez "a seco" apenas para
    # descobrir o fingerprint não é viável sem criar a linha, então
    # inspecionamos via reserve_pix_send_intent diretamente no hook —
    # o hook casa por (user_id, fingerprint_hash) do objeto pendente,
    # então não precisamos calcular fingerprint aqui: qualquer PixSendIntent
    # novo para user_id=401 nesta prova é, por definição, o alvo.
    class AnyFingerprintHook(FlushPauseHook):
        def before_flush(self, session, flush_context, instances):
            self._matched_this_flush = any(
                isinstance(obj, PixSendIntent) and obj.user_id == self.target_user_id
                for obj in session.new
            )

    hook = AnyFingerprintHook(db1, 401, None)
    hook.attach()

    result_holder = {}

    def run_t1():
        try:
            result_holder["t1"] = reserve_pix_send_intent(
                db1, user_id=401, valor=Decimal("10"), chave_pix="dest@a", descricao="PIX",
            )
        except Exception as exc:  # noqa: BLE001
            result_holder["t1_error"] = exc
        finally:
            hook.detach()
            db1.close()

    t1_thread = threading.Thread(target=run_t1)
    t1_thread.start()

    try:
        paused = hook.paused_event.wait(timeout=TIMEOUT)
        assert paused, "T1 nunca pausou -- hook do flush nao disparou"

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(
                _reserve_worker, session_factory,
                user_id=401, valor=Decimal("10"), chave_pix="dest@a", descricao="PIX",
            )
            time.sleep(2)
            assert not fut.done(), "T2 deveria estar contida enquanto T1 segurava a linha"

            hook.release_event.set()
            t1_thread.join(timeout=TIMEOUT)
            assert not t1_thread.is_alive(), "T1 nao terminou a tempo apos liberacao"

            t2_result = fut.result(timeout=TIMEOUT)
    finally:
        hook.detach()
        if t1_thread.is_alive():
            t1_thread.join(timeout=TIMEOUT)

    assert "t1_error" not in result_holder, f"T1 falhou inesperadamente: {result_holder.get('t1_error')!r}"
    t1_result = result_holder["t1"]

    assert t1_result["send_key"] == t2_result["send_key"], "T1 e T2 receberam send_keys DIFERENTES (K1 != K2)"
    assert t1_result["generation"] == t2_result["generation"] == 1

    rows = _intents_for(session_factory, 401)
    assert len(rows) == 1, f"esperada exatamente 1 linha, encontradas {len(rows)}"


# ======================================================================
# PROVA B — duas renovações force_new simultâneas após acknowledged ->
# UMA única nova geração/K2, nunca K2 e K3
# ======================================================================
def test_prova_b_renovacao_concorrente(engine, session_factory, clean_schema):
    _create_user(session_factory, 402, "user402@concurrency.test")
    _fund(session_factory, 402, Decimal("1000"))

    # Prepara uma intent já acknowledged (fora da região cronometrada).
    setup_db = session_factory()
    try:
        first = reserve_pix_send_intent(
            setup_db, user_id=402, valor=Decimal("10"), chave_pix="dest@a", descricao="PIX",
        )
        k1 = first["send_key"]
        send_pix(
            setup_db, user_id=402, valor=Decimal("10"), chave_pix="dest@a",
            descricao="PIX", idempotency_key=k1,
        )
        ack = acknowledge_pix_send_intent(setup_db, user_id=402, send_key=k1)
        assert ack["state"] == "acknowledged"
    finally:
        setup_db.close()

    db1 = session_factory()
    hook = UpdatePauseHook(db1)
    hook.attach()

    result_holder = {}

    def run_t1():
        try:
            result_holder["t1"] = reserve_pix_send_intent(
                db1, user_id=402, valor=Decimal("10"), chave_pix="dest@a",
                descricao="PIX", force_new=True,
            )
        except Exception as exc:  # noqa: BLE001
            result_holder["t1_error"] = exc
        finally:
            hook.detach()
            db1.close()

    t1_thread = threading.Thread(target=run_t1)
    t1_thread.start()

    try:
        lock_acquired = hook.lock_acquired_event.wait(timeout=TIMEOUT)
        assert lock_acquired, "T1 nunca executou o UPDATE de renovacao"

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(
                _reserve_worker, session_factory,
                user_id=402, valor=Decimal("10"), chave_pix="dest@a",
                descricao="PIX", force_new=True,
            )
            time.sleep(2)
            assert not fut.done(), "T2 deveria estar bloqueada pelo lock de linha do UPDATE de T1"

            hook.release_event.set()
            t1_thread.join(timeout=TIMEOUT)
            assert not t1_thread.is_alive(), "T1 nao terminou a tempo apos liberacao"

            t2_result = fut.result(timeout=TIMEOUT)
    finally:
        hook.detach()
        if t1_thread.is_alive():
            t1_thread.join(timeout=TIMEOUT)

    assert "t1_error" not in result_holder, f"T1 falhou inesperadamente: {result_holder.get('t1_error')!r}"
    t1_result = result_holder["t1"]

    # Contrato: nunca K2 e K3 -- as duas devem convergir na MESMA nova
    # send_key e na MESMA nova geração (2), nunca 2 e 3.
    assert t1_result["send_key"] == t2_result["send_key"], "T1 e T2 divergiram em K2 (uma delas criou K3)"
    assert t1_result["generation"] == t2_result["generation"] == 2
    assert t1_result["send_key"] != k1

    rows = _intents_for(session_factory, 402)
    assert len(rows) == 1
    assert rows[0].generation == 2
    assert rows[0].state == "pending"
