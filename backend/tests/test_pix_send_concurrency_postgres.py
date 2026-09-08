"""
M1 — cobertura permanente de regressão para concorrência REAL (PostgreSQL)
do fluxo de idempotência de POST /api/v1/pix/send.

Este arquivo é a promoção, para CI, da prova local descartável executada
manualmente contra PostgreSQL 16.12 nesta auditoria (raw compatibility
bridge + scoped key de M1.1, guard obrigatório de M1.2b, e a proteção de
saldo via `with_for_update()`). SQLite (usado no restante da suíte, ex.:
test_pix_send_idempotency_scope.py) não oferece um modelo de concorrência
representativo do PostgreSQL de produção para este tipo de teste —
`with_for_update()` é, inclusive, silenciosamente um no-op sob o dialeto
SQLite. Este arquivo existe especificamente para fechar essa lacuna.

Importa e executa o `send_pix()` REAL de `app.services.pix_service` — a
lógica de negócio nunca é reimplementada aqui. Toda a sincronização
determinística de concorrência é feita por fora, via eventos oficiais do
SQLAlchemy (`before_flush`/`after_flush`, `after_cursor_execute`),
anexados apenas à Session/Connection específica de T1 em cada prova —
nunca ao Engine globalmente — e sempre removidos em `finally`.

GUARD FAIL-CLOSED: este arquivo só lê `PIX_CONCURRENCY_TEST_DATABASE_URL`
— nunca `DATABASE_URL` (a variável real usada por produção/Alembic/app).
Se a variável estiver ausente, todos os testes deste arquivo são pulados
(`pytest.skip`). Se estiver presente mas não corresponder exatamente ao
banco de teste efêmero esperado (scheme=postgresql[+psycopg2],
host=localhost/127.0.0.1, database=auratest_ci, user=auratest), o teste
falha imediatamente (`pytest.fail`) ANTES de qualquer `create_engine`/
`drop_all`/`create_all` — nunca há risco de rodar contra um banco real.

Cada worker (T1 e T2) segue exatamente o lifecycle real de
`app.database.get_db()`:

    db = SessionLocal()
    try:
        return send_pix(db, ...)
    finally:
        db.close()

sem nenhum `rollback()` artificial adicionado — `Session.close()` já
reverte implicitamente qualquer transação pendente, por especificação do
SQLAlchemy, exatamente como a aplicação real se comporta.
"""
import concurrent.futures
import json
import os
import threading
import time
from decimal import Decimal
from urllib.parse import urlparse

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.idempotency import IdempotencyKey
from app.models.pix_ledger import PixLedger
from app.models.transaction import Transaction
from app.models.user_main import User
from app.services.pix_service import (
    _get_user_balance,
    _idem_hash,
    _pix_send_scoped_key,
    _round_money,
    send_pix,
)

TIMEOUT = 15  # segundos, conservador, para toda espera/join/future.result

_ENV_VAR = "PIX_CONCURRENCY_TEST_DATABASE_URL"
_ALLOWED_SCHEMES = {"postgresql", "postgresql+psycopg2"}
_ALLOWED_HOSTS = {"localhost", "127.0.0.1"}
_ALLOWED_DATABASE = "auratest_ci"
_ALLOWED_USER = "auratest"


def _require_test_database_url() -> str:
    """Guard fail-closed. NUNCA lê DATABASE_URL — só a variável exclusiva
    deste arquivo. Ausência => skip (sem infraestrutura local). Presença
    fora do allowlist exato => fail imediato, antes de qualquer conexão
    útil ou operação destrutiva contra qualquer banco."""
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
    """Isolamento total entre provas: schema recriado do zero a cada
    função de teste, sobre o mesmo database já validado pelo guard."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


# ----------------------------------------------------------------------
# Helpers de fixture (nunca reimplementam a lógica de send_pix — apenas
# preparam dados e leem o estado real do banco através dos mecanismos
# reais do projeto, como _get_user_balance).
# ----------------------------------------------------------------------
def _create_user(session_factory, user_id, email):
    """Cria a linha real em `users` exigida pela FK real
    transactions.user_id (PostgreSQL a enforça)."""
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


def _balance_of(session_factory, user_id):
    db = session_factory()
    try:
        return _get_user_balance(db, user_id)
    finally:
        db.close()


def _counts(session_factory):
    db = session_factory()
    try:
        return {
            "IdempotencyKey": db.query(IdempotencyKey).count(),
            "Transaction": db.query(Transaction).count(),
            "PixLedger": db.query(PixLedger).count(),
        }
    finally:
        db.close()


def _expected_hash(*, user_id, valor, chave_pix, descricao):
    return _idem_hash(
        user_id=user_id,
        valor=_round_money(Decimal(valor)),
        chave_pix=chave_pix,
        descricao=descricao,
    )


def _worker(session_factory, **kwargs):
    """Lifecycle idêntico ao real app.database.get_db(): sem nenhum
    rollback() artificial — Session.close() já reverte implicitamente
    qualquer transação pendente, exatamente como a aplicação real."""
    db = session_factory()
    try:
        return send_pix(db, **kwargs)
    finally:
        db.close()


# ----------------------------------------------------------------------
# Instrumentação de sincronização determinística (eventos oficiais do
# SQLAlchemy, nunca modificam send_pix()). Escopo sempre limitado à
# Session/Connection específica de T1 — nunca ao Engine. detach() é
# idempotente para nunca vazar entre testes mesmo sob chamada dupla.
# ----------------------------------------------------------------------
class FlushPauseHook:
    """Pausa T1 logo após o PRIMEIRO flush real da raw IdempotencyKey
    alvo ter sido efetivamente enviado ao PostgreSQL (after_flush),
    nunca antes disso."""

    def __init__(self, session, target_raw_key):
        self.session = session
        self.target_raw_key = target_raw_key
        self.paused_event = threading.Event()
        self.release_event = threading.Event()
        self.fired = False
        self._matched_this_flush = False
        self._attached = False

    def before_flush(self, session, flush_context, instances):
        self._matched_this_flush = any(
            isinstance(obj, IdempotencyKey) and obj.key == self.target_raw_key
            for obj in session.new
        )

    def after_flush(self, session, flush_context):
        if self._matched_this_flush and not self.fired:
            self.fired = True
            self._matched_this_flush = False
            self.paused_event.set()
            released = self.release_event.wait(timeout=TIMEOUT)
            if not released:
                raise TimeoutError(
                    f"T1 nao foi liberada a tempo (flush hook, "
                    f"key={self.target_raw_key!r})"
                )

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


class ForUpdatePauseHook:
    """Pausa T1 somente depois que after_cursor_execute confirma que o
    SQL contendo FOR UPDATE foi REALMENTE executado no PostgreSQL (lock
    já concedido pelo servidor, não apenas construído pelo SQLAlchemy)."""

    def __init__(self, connection):
        self.connection = connection
        self.lock_acquired_event = threading.Event()
        self.release_event = threading.Event()
        self.captured_sql = None
        self.fired = False
        self._attached = False

    def after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        if not self.fired and "FOR UPDATE" in statement.upper():
            self.fired = True
            self.captured_sql = statement
            self.lock_acquired_event.set()
            released = self.release_event.wait(timeout=TIMEOUT)
            if not released:
                raise TimeoutError("T1 nao foi liberada a tempo (for update hook)")

    def attach(self):
        if not self._attached:
            event.listen(self.connection, "after_cursor_execute", self.after_cursor_execute)
            self._attached = True

    def detach(self):
        if self._attached:
            event.remove(self.connection, "after_cursor_execute", self.after_cursor_execute)
            self._attached = False


# ======================================================================
# PROVA A — mesmo user + mesma raw key + mesmo payload (replay)
# ======================================================================
def test_prova_a_replay_concorrente(engine, session_factory, clean_schema):
    _create_user(session_factory, 101, "user101@concurrency.test")
    _fund(session_factory, 101, Decimal("100"))

    RAW_KEY = "concurrency-A-key"

    db1 = session_factory()
    hook = FlushPauseHook(db1, RAW_KEY)
    hook.attach()

    result_holder = {}

    def run_t1():
        try:
            result_holder["t1"] = send_pix(
                db1, user_id=101, valor=Decimal("10"), chave_pix="dest@a",
                descricao="PIX", idempotency_key=RAW_KEY,
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
                _worker, session_factory, user_id=101, valor=Decimal("10"),
                chave_pix="dest@a", descricao="PIX", idempotency_key=RAW_KEY,
            )
            time.sleep(2)
            assert not fut.done(), "T2 deveria estar contida enquanto T1 segurava a raw key"

            hook.release_event.set()
            t1_thread.join(timeout=TIMEOUT)
            assert not t1_thread.is_alive(), "T1 nao terminou a tempo apos liberacao"

            t2_result = fut.result(timeout=TIMEOUT)
    finally:
        hook.detach()
        if t1_thread.is_alive():
            t1_thread.join(timeout=TIMEOUT)

    assert "t1_error" not in result_holder, f"T1 falhou inesperadamente: {result_holder.get('t1_error')!r}"
    t1_tx = result_holder["t1"]

    # Contrato exato: T2 recebe o replay do payload concluído por T1.
    assert isinstance(t2_result, dict)
    assert t2_result["status"] == "success"
    assert t2_result["id"] == t1_tx.id

    counts = _counts(session_factory)
    assert counts["Transaction"] == 1
    assert counts["PixLedger"] == 2  # crédito inicial + único débito
    assert counts["IdempotencyKey"] == 2  # raw + scoped, ambas de T1

    assert _balance_of(session_factory, 101) == Decimal("90.00")

    verify_db = session_factory()
    try:
        raw_row = verify_db.query(IdempotencyKey).filter_by(key=RAW_KEY).one()
        scoped_row = verify_db.query(IdempotencyKey).filter_by(
            key=_pix_send_scoped_key(101, RAW_KEY)
        ).one()
        assert json.loads(raw_row.response_json)["id"] == t1_tx.id
        assert json.loads(scoped_row.response_json)["id"] == t1_tx.id
    finally:
        verify_db.close()


# ======================================================================
# PROVA B — mesmo user + mesma raw key + payload DIFERENTE (conflito)
# ======================================================================
def test_prova_b_conflito_concorrente(engine, session_factory, clean_schema):
    _create_user(session_factory, 102, "user102@concurrency.test")
    _fund(session_factory, 102, Decimal("100"))

    RAW_KEY = "concurrency-B-key"

    db1 = session_factory()
    hook = FlushPauseHook(db1, RAW_KEY)
    hook.attach()

    result_holder = {}

    def run_t1():
        try:
            result_holder["t1"] = send_pix(
                db1, user_id=102, valor=Decimal("10"), chave_pix="dest@a",
                descricao="PIX", idempotency_key=RAW_KEY,
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
            # Payload DIFERENTE: valor 20 em vez de 10, mesma raw key.
            fut = ex.submit(
                _worker, session_factory, user_id=102, valor=Decimal("20"),
                chave_pix="dest@a", descricao="PIX", idempotency_key=RAW_KEY,
            )
            time.sleep(2)
            assert not fut.done(), "T2 deveria estar contida enquanto T1 segurava a raw key"

            hook.release_event.set()
            t1_thread.join(timeout=TIMEOUT)
            assert not t1_thread.is_alive(), "T1 nao terminou a tempo apos liberacao"

            t2_result = fut.result(timeout=TIMEOUT)
    finally:
        hook.detach()
        if t1_thread.is_alive():
            t1_thread.join(timeout=TIMEOUT)

    assert "t1_error" not in result_holder, f"T1 falhou inesperadamente: {result_holder.get('t1_error')!r}"
    t1_tx = result_holder["t1"]

    # Contrato exato atual de conflito — não aceitar genericamente.
    assert t2_result == {
        "status": "conflict",
        "error": "Idempotency-Key reuse com payload diferente",
        "code": "IDEMPOTENCY_KEY_REUSE_DIFFERENT_PAYLOAD",
    }

    counts = _counts(session_factory)
    assert counts["Transaction"] == 1
    assert counts["PixLedger"] == 2  # crédito inicial + único débito (só T1)
    assert counts["IdempotencyKey"] == 2  # raw + scoped, ambas de T1

    assert _balance_of(session_factory, 102) == Decimal("90.00")

    verify_db = session_factory()
    try:
        expected_hash_t1 = _expected_hash(
            user_id=102, valor=Decimal("10"), chave_pix="dest@a", descricao="PIX"
        )
        raw_row = verify_db.query(IdempotencyKey).filter_by(key=RAW_KEY).one()
        scoped_row = verify_db.query(IdempotencyKey).filter_by(
            key=_pix_send_scoped_key(102, RAW_KEY)
        ).one()
        # request_hash persistido corresponde à operação vencedora (T1),
        # nunca ao payload perdedor de T2.
        assert raw_row.request_hash == expected_hash_t1
        assert scoped_row.request_hash == expected_hash_t1
        assert json.loads(raw_row.response_json)["id"] == t1_tx.id
    finally:
        verify_db.close()


# ======================================================================
# PROVA C — users diferentes + mesma raw key (cross-user)
# ======================================================================
def test_prova_c_cross_user_raw_bridge(engine, session_factory, clean_schema):
    _create_user(session_factory, 201, "user201@concurrency.test")
    _create_user(session_factory, 202, "user202@concurrency.test")
    _fund(session_factory, 201, Decimal("100"))
    _fund(session_factory, 202, Decimal("100"))

    RAW_KEY = "concurrency-C-key"

    db1 = session_factory()
    hook = FlushPauseHook(db1, RAW_KEY)
    hook.attach()

    result_holder = {}

    def run_t1():
        try:
            result_holder["t1"] = send_pix(
                db1, user_id=201, valor=Decimal("10"), chave_pix="dest@a",
                descricao="PIX", idempotency_key=RAW_KEY,
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
        assert paused, "T1 (user 201) nunca pausou"

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(
                _worker, session_factory, user_id=202, valor=Decimal("15"),
                chave_pix="dest@b", descricao="PIX", idempotency_key=RAW_KEY,
            )
            time.sleep(2)
            assert not fut.done(), "T2 (user 202) deveria sofrer contencao na mesma raw key"

            hook.release_event.set()
            t1_thread.join(timeout=TIMEOUT)
            assert not t1_thread.is_alive(), "T1 nao terminou a tempo apos liberacao"

            t2_tx = fut.result(timeout=TIMEOUT)
    finally:
        hook.detach()
        if t1_thread.is_alive():
            t1_thread.join(timeout=TIMEOUT)

    assert "t1_error" not in result_holder, f"T1 falhou inesperadamente: {result_holder.get('t1_error')!r}"
    t1_tx = result_holder["t1"]

    assert t1_tx.user_id == 201
    assert t2_tx.user_id == 202
    assert t1_tx.id != t2_tx.id  # nenhuma falsa colisão cross-user

    counts = _counts(session_factory)
    assert counts["Transaction"] == 2
    assert counts["PixLedger"] == 4  # 2 créditos iniciais + 2 débitos
    assert counts["IdempotencyKey"] == 3  # 1 raw compartilhada + 2 scoped

    assert _balance_of(session_factory, 201) == Decimal("90.00")
    assert _balance_of(session_factory, 202) == Decimal("85.00")

    verify_db = session_factory()
    try:
        raw_row = verify_db.query(IdempotencyKey).filter_by(key=RAW_KEY).one()
        assert json.loads(raw_row.response_json)["id"] == t1_tx.id

        scoped_row_b = verify_db.query(IdempotencyKey).filter_by(
            key=_pix_send_scoped_key(202, RAW_KEY)
        ).one()
        assert json.loads(scoped_row_b.response_json)["id"] == t2_tx.id

        # Nenhuma falsa colisão cross-user: a Transaction de B pertence
        # de fato a B no banco, não a A.
        tx_b_row = verify_db.query(Transaction).filter_by(id=t2_tx.id).one()
        assert tx_b_row.user_id == 202
    finally:
        verify_db.close()


# ======================================================================
# PROVA D — FOR UPDATE / saldo (a prova mais importante)
# ======================================================================
def test_prova_d_for_update_saldo(engine, session_factory, clean_schema):
    _create_user(session_factory, 301, "user301@concurrency.test")
    _fund(session_factory, 301, Decimal("100"))

    db1 = session_factory()
    conn1 = db1.connection()  # força a Session a associar uma Connection real
    hook = ForUpdatePauseHook(conn1)
    hook.attach()

    result_holder = {}

    def run_t1():
        try:
            result_holder["t1"] = send_pix(
                db1, user_id=301, valor=Decimal("60"), chave_pix="dest@a",
                descricao="PIX", idempotency_key="concurrency-D-key-1",
            )
        except Exception as exc:  # noqa: BLE001
            result_holder["t1_error"] = exc
        finally:
            hook.detach()
            db1.close()

    t1_thread = threading.Thread(target=run_t1)
    t1_thread.start()

    t2_error = None
    try:
        lock_acquired = hook.lock_acquired_event.wait(timeout=TIMEOUT)
        assert lock_acquired, "T1 nunca adquiriu o FOR UPDATE real"
        assert hook.captured_sql is not None
        assert "FOR UPDATE" in hook.captured_sql.upper()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            fut = ex.submit(
                _worker, session_factory, user_id=301, valor=Decimal("60"),
                chave_pix="dest@b", descricao="PIX", idempotency_key="concurrency-D-key-2",
            )
            time.sleep(2)
            assert not fut.done(), "T2 deveria estar bloqueada enquanto T1 segurava o FOR UPDATE"

            hook.release_event.set()
            t1_thread.join(timeout=TIMEOUT)
            assert not t1_thread.is_alive(), "T1 nao terminou a tempo apos liberacao"

            try:
                fut.result(timeout=TIMEOUT)
            except ValueError as exc:
                t2_error = exc
    finally:
        hook.detach()
        if t1_thread.is_alive():
            t1_thread.join(timeout=TIMEOUT)

    assert "t1_error" not in result_holder, f"T1 falhou inesperadamente: {result_holder.get('t1_error')!r}"
    t1_tx = result_holder["t1"]
    assert t1_tx.user_id == 301

    assert t2_error is not None, "T2 deveria ter levantado ValueError('Saldo insuficiente')"
    assert str(t2_error) == "Saldo insuficiente"

    counts = _counts(session_factory)
    assert counts["Transaction"] == 1  # somente o débito de T1 persiste
    assert counts["PixLedger"] == 2  # crédito inicial + único débito

    saldo = _balance_of(session_factory, 301)
    assert saldo == Decimal("40.00")
    assert saldo != Decimal("-20.00")

    verify_db = session_factory()
    try:
        raw_k1 = verify_db.query(IdempotencyKey).filter_by(key="concurrency-D-key-1").one()
        scoped_k1 = verify_db.query(IdempotencyKey).filter_by(
            key=_pix_send_scoped_key(301, "concurrency-D-key-1")
        ).one()
        assert json.loads(raw_k1.response_json)["id"] == t1_tx.id
        assert json.loads(scoped_k1.response_json)["id"] == t1_tx.id

        # ASSERT CORRIGIDO (revisão conjunta pré-implementação): K2 (raw e
        # scoped) foram flushadas antes da checagem de saldo falhar, mas
        # NUNCA commitadas. O `finally: db.close()` do worker de T2
        # reverte implicitamente essa transação pendente, exatamente
        # como o lifecycle real de app.database.get_db() se comporta —
        # portanto nenhuma linha de K2 deve existir no banco.
        raw_k2 = verify_db.query(IdempotencyKey).filter_by(key="concurrency-D-key-2").first()
        assert raw_k2 is None, "raw K2 nao deveria persistir apos rollback implicito do close()"

        scoped_k2 = verify_db.query(IdempotencyKey).filter_by(
            key=_pix_send_scoped_key(301, "concurrency-D-key-2")
        ).first()
        assert scoped_k2 is None, "scoped K2 nao deveria persistir apos rollback implicito do close()"

        assert counts["IdempotencyKey"] == 2  # só raw+scoped de K1
    finally:
        verify_db.close()
