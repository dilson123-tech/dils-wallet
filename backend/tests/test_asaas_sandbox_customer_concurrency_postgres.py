"""
Provas de concorrência do lock de criação de customer Asaas Sandbox em
PostgreSQL REAL, local e efêmero (nunca o banco da aplicação).

- Cada thread usa sua própria Session (conexão independente do pool).
- Sincronização determinística: threading.Barrier/Event e consulta a
  pg_stat_activity para comprovar bloqueio real de linha — nenhuma prova
  depende de sleep "para dar tempo".
- Asaas é sempre um transporte fake em memória: nenhum HTTP real.

Guard fail-closed em camadas, TODO executado antes de qualquer
drop_all/create_all (host/porta locais sozinhos NÃO bastam):

1. URL (PIX_CONCURRENCY_TEST_DATABASE_URL): ausente => skip; scheme,
   host loopback, usuário auratest e banco auratest_ci exatos; query,
   fragment e params PROIBIDOS (libpq aceita ?host=/?service= que
   sobrescreveriam o destino); PGHOSTADDR/PGSERVICE no ambiente proibidos.
2. Fatos do SERVIDOR, numa única conexão: current_database/current_user
   exatos; não é réplica; o cluster só contém auratest_ci + bancos padrão
   (postgres/template0/template1) e só o role de login auratest, i.e. é
   uma instância DEDICADA e descartável; o schema public do banco só tem
   tabelas do próprio modelo (nenhuma tabela estranha como
   alembic_version, típica de banco de aplicação/migrado).
3. Destruição confinada: drop_all/create_all atuam SÓ no schema dedicado
   asaas_lock_pg_test (search_path fixo), criado pelo próprio guard e
   marcado por COMMENT; schema homônimo sem a marca => recusa.

Qualquer falha => pytest.fail, sem nenhuma operação destrutiva.
Compatível com o serviço postgres efêmero do CI
(.github/workflows/pix-concurrency-postgres.yml).
"""
import concurrent.futures
import json
import os
import threading
import time

os.environ.setdefault("SECRET_KEY", "asaas-sandbox-customer-pg-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.idempotency import IdempotencyKey
from app.partner.asaas_client import AsaasSandboxClient
from app.partner.asaas_config import ASAAS_SANDBOX_BASE_URL, AsaasSandboxConfig
from app.services.asaas_correlated_pix_payment_service import (
    asaas_sandbox_customer_external_reference,
)
from app.services.asaas_sandbox_customer_service import (
    ASAAS_SANDBOX_CUSTOMER_LIST_LIMIT,
    AsaasSandboxCustomerIndeterminateError,
    AsaasSandboxCustomerPendingError,
    _acquire_lock,
    _lock_json,
    _lock_key,
    _release_lock,
    ensure_asaas_sandbox_customer,
)

TIMEOUT = 15  # segundos, conservador, para toda espera/join/future.result

_ENV_VAR = "PIX_CONCURRENCY_TEST_DATABASE_URL"
_ALLOWED_SCHEMES = {"postgresql", "postgresql+psycopg2"}
_ALLOWED_HOSTS = {"localhost", "127.0.0.1"}
_ALLOWED_DATABASE = "auratest_ci"
_ALLOWED_USER = "auratest"
_FORBIDDEN_PG_ENV = ("PGHOSTADDR", "PGSERVICE", "PGSERVICEFILE")
_DEDICATED_CLUSTER_DATABASES = frozenset(
    {_ALLOWED_DATABASE, "postgres", "template0", "template1"}
)
_DEDICATED_LOGIN_ROLES = frozenset({_ALLOWED_USER})
_TEST_SCHEMA = "asaas_lock_pg_test"
_SCHEMA_MARKER = "aurea-disposable-test-schema:asaas-sandbox-customer-lock"

USER_ID = 4242

TEST_CONFIG = AsaasSandboxConfig(
    env="sandbox",
    base_url=ASAAS_SANDBOX_BASE_URL,
    api_key="pg-concurrency-api-key-must-never-leak",
    webhook_token="pg-concurrency-webhook-token-must-never-leak",
    real_money_enabled=False,
    wallet_mode="partner",
    wallet_partner_provider="asaas",
)


def _url_refusal(raw: str, environ=None):
    """Motivo de recusa da URL (str) ou None se aceitável. Função pura."""
    environ = os.environ if environ is None else environ
    for name in _FORBIDDEN_PG_ENV:
        if environ.get(name):
            return f"variável {name} definida pode desviar a conexão"
    try:
        url = make_url(raw)
    except Exception:
        return "URL inválida"
    if url.drivername not in _ALLOWED_SCHEMES:
        return "scheme não permitido"
    if url.host not in _ALLOWED_HOSTS:
        return "host não é loopback permitido"
    if url.username != _ALLOWED_USER:
        return "usuário diferente do esperado"
    if url.database != _ALLOWED_DATABASE:
        return "banco diferente do esperado"
    if url.query:
        return "parâmetros de query proibidos (podem sobrescrever host/banco)"
    if any(token in raw for token in ("?", "#", ";")):
        return "query/fragment/params proibidos na URL"
    return None


def _server_refusal(facts: dict):
    """Motivo de recusa a partir de fatos lidos do servidor, ou None.
    Função pura: exige prova positiva de instância dedicada/descartável."""
    if facts.get("current_database") != _ALLOWED_DATABASE:
        return "current_database() inesperado"
    if facts.get("current_user") != _ALLOWED_USER:
        return "current_user inesperado"
    if facts.get("in_recovery") is not False:
        return "servidor em recovery/réplica ou estado desconhecido"
    databases = facts.get("databases")
    if not isinstance(databases, (set, frozenset)) or not databases:
        return "lista de bancos do cluster desconhecida"
    if not databases <= _DEDICATED_CLUSTER_DATABASES:
        return "cluster contém outros bancos (não é instância dedicada)"
    roles = facts.get("login_roles")
    if not isinstance(roles, (set, frozenset)) or roles != _DEDICATED_LOGIN_ROLES:
        return "cluster tem outros roles de login (não é instância dedicada)"
    public_tables = facts.get("public_tables")
    if not isinstance(public_tables, (set, frozenset)):
        return "tabelas do schema public desconhecidas"
    if not public_tables <= set(Base.metadata.tables):
        return "schema public contém tabelas estranhas ao modelo"
    if facts.get("schema_exists") is True:
        if facts.get("schema_comment") != _SCHEMA_MARKER:
            return "schema de teste existe sem a marca de descartável"
    elif facts.get("schema_exists") is not False:
        return "existência do schema de teste desconhecida"
    return None


def _read_server_facts(conn) -> dict:
    def rows(sql, **params):
        return {r[0] for r in conn.execute(text(sql), params)}

    head = conn.execute(
        text("SELECT current_database(), current_user, pg_is_in_recovery()")
    ).one()
    comment = conn.execute(
        text(
            "SELECT obj_description(oid, 'pg_namespace') FROM pg_namespace "
            "WHERE nspname = :s"
        ),
        {"s": _TEST_SCHEMA},
    ).all()
    return {
        "current_database": head[0],
        "current_user": head[1],
        "in_recovery": head[2],
        "databases": frozenset(rows("SELECT datname FROM pg_database")),
        "login_roles": frozenset(
            rows("SELECT rolname FROM pg_roles WHERE rolcanlogin")
        ),
        "public_tables": frozenset(
            rows("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        ),
        "schema_exists": bool(comment),
        "schema_comment": comment[0][0] if comment else None,
    }


def _require_test_database_url() -> str:
    raw = os.environ.get(_ENV_VAR)
    if not raw:
        pytest.skip(
            f"{_ENV_VAR} não definida — teste de concorrência PostgreSQL "
            "pulado (sem serviço de banco disponível para esta execução)."
        )
    reason = _url_refusal(raw)
    if reason is not None:
        pytest.fail(
            f"{_ENV_VAR} recusada: {reason}. Esperado exatamente "
            f"scheme∈{_ALLOWED_SCHEMES}, host∈{_ALLOWED_HOSTS}, "
            f"database={_ALLOWED_DATABASE!r}, user={_ALLOWED_USER!r}, sem "
            "query. Abortando ANTES de qualquer drop_all/create_all."
        )
    return raw


def _prove_isolated_and_prepare_schema(raw: str) -> None:
    """Verifica o servidor (sem nada destrutivo) e só então cria o schema
    dedicado marcado. Falha => pytest.fail sem drop_all/create_all."""
    probe = create_engine(raw)
    try:
        with probe.connect() as conn:
            facts = _read_server_facts(conn)
            reason = _server_refusal(facts)
            if reason is not None:
                conn.rollback()
                pytest.fail(
                    f"Servidor PostgreSQL recusado: {reason}. Só uma instância "
                    "dedicada e descartável é aceita. Nada foi alterado."
                )
            if not facts["schema_exists"]:
                conn.execute(text(f'CREATE SCHEMA "{_TEST_SCHEMA}"'))
                conn.execute(
                    text(f"COMMENT ON SCHEMA \"{_TEST_SCHEMA}\" IS '{_SCHEMA_MARKER}'")
                )
            conn.commit()
    finally:
        probe.dispose()


@pytest.fixture(scope="session")
def database_url():
    raw = _require_test_database_url()
    _prove_isolated_and_prepare_schema(raw)
    return raw


@pytest.fixture(scope="session")
def engine(database_url):
    eng = create_engine(
        database_url,
        pool_size=12,
        max_overflow=12,
        connect_args={"options": f"-csearch_path={_TEST_SCHEMA}"},
    )
    yield eng
    eng.dispose()


@pytest.fixture()
def session_factory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture()
def clean_schema(engine):
    # Revalida, imediatamente antes de destruir, que a conexão aponta só
    # para o schema dedicado e marcado (nunca public).
    with engine.connect() as conn:
        current = conn.execute(text("SELECT current_schemas(false)")).scalar_one()
        marker = conn.execute(
            text("SELECT obj_description(to_regnamespace(:s), 'pg_namespace')"),
            {"s": _TEST_SCHEMA},
        ).scalar_one()
        conn.rollback()
    if list(current) != [_TEST_SCHEMA] or marker != _SCHEMA_MARKER:
        pytest.fail("search_path não confinado ao schema de teste marcado.")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _ref(user_id: int) -> str:
    return asaas_sandbox_customer_external_reference(user_id)


def _customer_id(user_id: int) -> str:
    return f"cus_pgsandbox{user_id}"


def _page(*items) -> tuple:
    return 200, {
        "data": list(items),
        "totalCount": len(items),
        "hasMore": False,
        "limit": ASAAS_SANDBOX_CUSTOMER_LIST_LIMIT,
        "offset": 0,
    }


def _item(user_id: int) -> dict:
    return {"id": _customer_id(user_id), "externalReference": _ref(user_id), "deleted": False}


class ThreadSafeFakeAsaas:
    """
    Asaas fake compartilhado entre threads. GET reflete o estado "remoto"
    (customer criado ou não); POST pode ser segurado por um Event para
    abrir uma janela determinística em que o dono ainda detém o lock.
    """

    def __init__(self, *, user_id: int, post_gate: threading.Event | None = None,
                 post_status: int = 200):
        self.user_id = user_id
        self.post_gate = post_gate
        self.post_status = post_status
        self.post_entered = threading.Event()
        self._mutex = threading.Lock()
        self.created = False
        self.get_calls = 0
        self.post_calls = 0

    def http_get(self, request):
        assert request.operation == "list_customers_by_external_reference"
        with self._mutex:
            self.get_calls += 1
            created = self.created
        return _page(_item(self.user_id)) if created else _page()

    def http_post(self, request):
        assert request.operation == "create_customer"
        with self._mutex:
            self.post_calls += 1
        self.post_entered.set()
        if self.post_gate is not None:
            assert self.post_gate.wait(TIMEOUT), "gate do POST não liberado"
        if self.post_status != 200:
            return self.post_status, {}
        with self._mutex:
            self.created = True
        return 200, {**request.json, "id": _customer_id(self.user_id), "deleted": False}


def _ensure_in_own_session(session_factory, fake, user_id=USER_ID):
    db = session_factory()
    try:
        return ensure_asaas_sandbox_customer(
            db,
            client=AsaasSandboxClient(TEST_CONFIG),
            user_id=user_id,
            http_get=fake.http_get,
            http_post=fake.http_post,
        )
    finally:
        db.close()


def _lock_row(session_factory, user_id=USER_ID):
    db = session_factory()
    try:
        row = (
            db.query(IdempotencyKey)
            .filter(IdempotencyKey.key == _lock_key(user_id))
            .one_or_none()
        )
        return None if row is None else row.response_json
    finally:
        db.close()


def _manual_recovery(session_factory, user_id=USER_ID):
    db = session_factory()
    try:
        db.query(IdempotencyKey).filter(
            IdempotencyKey.key == _lock_key(user_id)
        ).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()


def _outcome(fn):
    try:
        return ("ok", fn())
    except BaseException as exc:  # noqa: BLE001 - classificado pelo teste
        return ("err", type(exc).__name__)


def _run_concurrently(n, fn):
    barrier = threading.Barrier(n, timeout=TIMEOUT)

    def worker():
        barrier.wait()
        return _outcome(fn)

    with concurrent.futures.ThreadPoolExecutor(max_workers=n) as pool:
        futures = [pool.submit(worker) for _ in range(n)]
        return [f.result(timeout=TIMEOUT) for f in futures]


def _wait_until_blocked_on_lock(engine, expected: int):
    """Comprova via pg_stat_activity que `expected` backends estão
    realmente bloqueados aguardando lock (sem sleep arbitrário)."""
    deadline = time.monotonic() + TIMEOUT
    with engine.connect() as conn:
        while time.monotonic() < deadline:
            waiting = conn.execute(
                text(
                    "SELECT count(*) FROM pg_stat_activity "
                    "WHERE datname = current_database() "
                    "AND wait_event_type = 'Lock' "
                    "AND query ILIKE '%idempotency_keys%'"
                )
            ).scalar_one()
            conn.rollback()
            if waiting >= expected:
                return
            time.sleep(0.01)
    pytest.fail(f"esperava {expected} backend(s) bloqueado(s) em lock")


# ----------------------------------------------------------------------
# Aquisição
# ----------------------------------------------------------------------
def test_simultaneous_acquire_has_exactly_one_owner(clean_schema, session_factory):
    n = 10

    def acquire():
        db = session_factory()
        try:
            return _acquire_lock(db, user_id=USER_ID)
        finally:
            db.close()

    results = _run_concurrently(n, acquire)
    assert all(kind == "ok" for kind, _ in results), results
    owners = [value for _, value in results if value is not None]
    assert len(owners) == 1
    assert _lock_row(session_factory) == owners[0]


def test_competing_insert_blocks_until_owner_commits_then_fails(
    clean_schema, engine, session_factory
):
    owner = session_factory()
    try:
        owner_json = _lock_json(user_id=USER_ID, token="a" * 32)
        owner.add(IdempotencyKey(key=_lock_key(USER_ID), response_json=owner_json))
        owner.flush()  # linha inserida, transação ABERTA

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            def acquire():
                db = session_factory()
                try:
                    return _acquire_lock(db, user_id=USER_ID)
                finally:
                    db.close()

            future = pool.submit(acquire)
            _wait_until_blocked_on_lock(engine, expected=1)
            assert not future.done()
            owner.commit()
            assert future.result(timeout=TIMEOUT) is None
    finally:
        owner.close()
    assert _lock_row(session_factory) == owner_json


def test_competing_insert_acquires_if_owner_transaction_rolls_back(
    clean_schema, engine, session_factory
):
    owner = session_factory()
    try:
        owner.add(
            IdempotencyKey(
                key=_lock_key(USER_ID),
                response_json=_lock_json(user_id=USER_ID, token="b" * 32),
            )
        )
        owner.flush()
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            def acquire():
                db = session_factory()
                try:
                    return _acquire_lock(db, user_id=USER_ID)
                finally:
                    db.close()

            future = pool.submit(acquire)
            _wait_until_blocked_on_lock(engine, expected=1)
            owner.rollback()
            acquired = future.result(timeout=TIMEOUT)
    finally:
        owner.close()
    assert acquired is not None
    assert _lock_row(session_factory) == acquired


# ----------------------------------------------------------------------
# ensure concorrente: um único POST
# ----------------------------------------------------------------------
def test_simultaneous_ensure_issues_exactly_one_post(clean_schema, session_factory):
    n = 8
    gate = threading.Event()
    fake = ThreadSafeFakeAsaas(user_id=USER_ID, post_gate=gate)
    finished = []
    finished_mutex = threading.Lock()

    def attempt():
        try:
            return _ensure_in_own_session(session_factory, fake)
        finally:
            with finished_mutex:
                finished.append(1)
                # O dono só conclui o POST depois que TODOS os concorrentes
                # terminaram: janela máxima de corrida, determinística.
                if len(finished) == n - 1:
                    gate.set()

    results = _run_concurrently(n, attempt)

    assert fake.post_calls == 1
    oks = [value for kind, value in results if kind == "ok"]
    errors = [value for kind, value in results if kind == "err"]
    assert oks == [_customer_id(USER_ID)]
    assert errors == ["AsaasSandboxCustomerPendingError"] * (n - 1)
    # Dono liberou o PRÓPRIO lock ao comprovar o customer.
    assert _lock_row(session_factory) is None

    # Novas tentativas simultâneas: reutilizam, nenhum POST adicional.
    again = _run_concurrently(n, lambda: _ensure_in_own_session(session_factory, fake))
    assert again == [("ok", _customer_id(USER_ID))] * n
    assert fake.post_calls == 1
    assert _lock_row(session_factory) is None


def test_competitor_finding_customer_never_removes_active_lock(
    clean_schema, session_factory
):
    gate = threading.Event()
    fake = ThreadSafeFakeAsaas(user_id=USER_ID, post_gate=gate)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        owner_future = pool.submit(
            _outcome, lambda: _ensure_in_own_session(session_factory, fake)
        )
        assert fake.post_entered.wait(TIMEOUT)
        active = _lock_row(session_factory)
        assert active is not None

        # O customer passa a existir no Asaas enquanto o dono ainda está
        # dentro do POST; o concorrente (lock alheio) só lê e devolve.
        with fake._mutex:
            fake.created = True
        competitor = _ensure_in_own_session(session_factory, fake)
        assert competitor == _customer_id(USER_ID)
        assert _lock_row(session_factory) == active  # intacto

        gate.set()
        assert owner_future.result(timeout=TIMEOUT) == ("ok", _customer_id(USER_ID))

    assert fake.post_calls == 1
    assert _lock_row(session_factory) is None


# ----------------------------------------------------------------------
# Posse por token (ABA / dono antigo / não dono)
# ----------------------------------------------------------------------
def test_old_owner_never_releases_newer_lock_across_connections(
    clean_schema, session_factory
):
    old_db, new_db = session_factory(), session_factory()
    try:
        old = _acquire_lock(old_db, user_id=USER_ID)
        _manual_recovery(session_factory)  # operador, outra conexão
        new = _acquire_lock(new_db, user_id=USER_ID)
        assert old is not None and new is not None and old != new

        assert _release_lock(old_db, user_id=USER_ID, lock_json=old) is False
        assert _lock_row(session_factory) == new
        assert _release_lock(new_db, user_id=USER_ID, lock_json=new) is True
        assert _lock_row(session_factory) is None
    finally:
        old_db.close()
        new_db.close()


def test_stale_and_foreign_releases_racing_never_delete_active_lock(
    clean_schema, session_factory
):
    owner_db = session_factory()
    try:
        active = _acquire_lock(owner_db, user_id=USER_ID)
    finally:
        owner_db.close()
    stale_tokens = [
        _lock_json(user_id=USER_ID, token=f"{i:032x}") for i in range(10)
    ]
    tokens = iter(stale_tokens)
    tokens_mutex = threading.Lock()

    def release_stale():
        with tokens_mutex:
            lock_json = next(tokens)
        db = session_factory()
        try:
            return _release_lock(db, user_id=USER_ID, lock_json=lock_json)
        finally:
            db.close()

    results = _run_concurrently(len(stale_tokens), release_stale)
    assert results == [("ok", False)] * len(stale_tokens)
    assert _lock_row(session_factory) == active


def test_aba_release_racing_new_acquisition_keeps_new_lock(
    clean_schema, engine, session_factory
):
    """
    Dono antigo tenta liberar ENQUANTO o novo dono insere o lock (linha
    nova ainda não commitada). O DELETE condicionado ao token antigo não
    casa com a linha nova em nenhuma ordem de commit.
    """
    old_db = session_factory()
    try:
        old = _acquire_lock(old_db, user_id=USER_ID)
        _manual_recovery(session_factory)

        new_db = session_factory()
        try:
            new_json = _lock_json(user_id=USER_ID, token="c" * 32)
            new_db.add(IdempotencyKey(key=_lock_key(USER_ID), response_json=new_json))
            new_db.flush()  # nova linha, transação aberta

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                stale = pool.submit(
                    _release_lock, old_db, user_id=USER_ID, lock_json=old
                )
                assert stale.result(timeout=TIMEOUT) is False
                new_db.commit()
        finally:
            new_db.close()
    finally:
        old_db.close()
    assert _lock_row(session_factory) == new_json


# ----------------------------------------------------------------------
# Desfecho incerto + recuperação manual
# ----------------------------------------------------------------------
def test_indeterminate_blocks_concurrent_retries_until_manual_recovery(
    clean_schema, session_factory
):
    failing = ThreadSafeFakeAsaas(user_id=USER_ID, post_status=500)
    with pytest.raises(AsaasSandboxCustomerIndeterminateError):
        _ensure_in_own_session(session_factory, failing)
    kept = _lock_row(session_factory)
    assert kept is not None

    healthy = ThreadSafeFakeAsaas(user_id=USER_ID)
    n = 6
    blocked = _run_concurrently(n, lambda: _ensure_in_own_session(session_factory, healthy))
    assert blocked == [("err", AsaasSandboxCustomerPendingError.__name__)] * n
    assert healthy.post_calls == 0
    assert _lock_row(session_factory) == kept

    _manual_recovery(session_factory)

    gate = threading.Event()
    recovered = ThreadSafeFakeAsaas(user_id=USER_ID, post_gate=gate)
    finished = []
    finished_mutex = threading.Lock()

    def attempt():
        try:
            return _ensure_in_own_session(session_factory, recovered)
        finally:
            with finished_mutex:
                finished.append(1)
                if len(finished) == n - 1:
                    gate.set()

    results = _run_concurrently(n, attempt)
    assert recovered.post_calls == 1
    assert sorted(results) == sorted(
        [("ok", _customer_id(USER_ID))]
        + [("err", AsaasSandboxCustomerPendingError.__name__)] * (n - 1)
    )
    assert _lock_row(session_factory) is None


def test_lock_payload_is_v2_with_token_on_postgres(clean_schema, session_factory):
    db = session_factory()
    try:
        acquired = _acquire_lock(db, user_id=USER_ID)
    finally:
        db.close()
    payload = json.loads(_lock_row(session_factory))
    assert _lock_row(session_factory) == acquired
    assert payload["contract"] == "asaas_sandbox_customer_pending_lock_v2"
    assert payload["real_money_enabled"] is False
    assert payload["user_id"] == USER_ID
    assert len(payload["token"]) == 32


# ----------------------------------------------------------------------
# Guard de isolamento (AG-08.4.1 D): configurações inseguras são recusadas
# ANTES de qualquer drop_all. Testes puros — rodam sem PostgreSQL.
# ----------------------------------------------------------------------

_SAFE_URL = "postgresql+psycopg2://auratest:auratest@127.0.0.1:55432/auratest_ci"


def _safe_facts(**overrides):
    facts = {
        "current_database": "auratest_ci",
        "current_user": "auratest",
        "in_recovery": False,
        "databases": frozenset({"auratest_ci", "postgres", "template0", "template1"}),
        "login_roles": frozenset({"auratest"}),
        "public_tables": frozenset(),
        "schema_exists": False,
        "schema_comment": None,
    }
    facts.update(overrides)
    return facts


def test_guard_accepts_dedicated_disposable_configuration():
    assert _url_refusal(_SAFE_URL, environ={}) is None
    assert (
        _url_refusal(
            "postgresql+psycopg2://auratest:auratest@localhost:5432/auratest_ci",
            environ={},
        )
        is None
    )
    assert _server_refusal(_safe_facts()) is None
    assert (
        _server_refusal(
            _safe_facts(
                schema_exists=True,
                schema_comment=_SCHEMA_MARKER,
                public_tables=frozenset({"idempotency_keys", "users"}),
            )
        )
        is None
    )


@pytest.mark.parametrize(
    "raw, environ",
    [
        ("not a url", {}),
        ("mysql://auratest:auratest@127.0.0.1:55432/auratest_ci", {}),
        ("postgresql+psycopg2://auratest:auratest@db.example.com:5432/auratest_ci", {}),
        ("postgresql+psycopg2://auratest:auratest@10.0.0.5:5432/auratest_ci", {}),
        ("postgresql+psycopg2://postgres:x@127.0.0.1:55432/auratest_ci", {}),
        ("postgresql+psycopg2://auratest:auratest@127.0.0.1:55432/aurea_prod", {}),
        ("postgresql+psycopg2://auratest:auratest@127.0.0.1:55432/auratest_ci?host=prod.example.com", {}),
        ("postgresql+psycopg2://auratest:auratest@127.0.0.1:55432/auratest_ci?service=prod", {}),
        ("postgresql+psycopg2://auratest:auratest@127.0.0.1:55432/auratest_ci?options=-csearch_path%3Dpublic", {}),
        (_SAFE_URL, {"PGHOSTADDR": "10.0.0.5"}),
        (_SAFE_URL, {"PGSERVICE": "prod"}),
        (_SAFE_URL, {"PGSERVICEFILE": "/etc/pg_service.conf"}),
    ],
    ids=[
        "invalid", "scheme", "remote-host", "private-ip", "wrong-user",
        "foreign-db", "query-host-override", "query-service", "query-options",
        "env-pghostaddr", "env-pgservice", "env-pgservicefile",
    ],
)
def test_guard_refuses_unsafe_url(raw, environ):
    assert _url_refusal(raw, environ=environ) is not None


@pytest.mark.parametrize(
    "overrides",
    [
        {"current_database": "aurea_prod"},
        {"current_user": "postgres"},
        {"in_recovery": True},
        {"in_recovery": None},
        {"databases": frozenset({"auratest_ci", "postgres", "template0", "template1", "aurea"})},
        {"databases": None},
        {"login_roles": frozenset({"auratest", "postgres"})},
        {"login_roles": frozenset({"auratest", "app_user"})},
        {"login_roles": frozenset()},
        {"public_tables": frozenset({"alembic_version"})},
        {"public_tables": frozenset({"users", "customer_ledger_backup"})},
        {"public_tables": None},
        {"schema_exists": True, "schema_comment": None},
        {"schema_exists": True, "schema_comment": "something else"},
        {"schema_exists": None},
    ],
    ids=[
        "foreign-current-db", "superuser-session", "replica", "recovery-unknown",
        "shared-cluster-extra-db", "db-list-unknown", "extra-login-postgres",
        "extra-login-app", "no-login-roles", "migrated-app-db",
        "unknown-public-table", "public-tables-unknown", "unmarked-schema",
        "foreign-marker", "schema-state-unknown",
    ],
)
def test_guard_refuses_unproven_isolation(overrides):
    assert _server_refusal(_safe_facts(**overrides)) is not None


def test_guard_passes_against_real_isolated_server(engine):
    """Integração: o servidor real usado nesta execução satisfaz o guard,
    o schema dedicado tem a marca e é o único no search_path."""
    with engine.connect() as conn:
        facts = _read_server_facts(conn)
        schemas = conn.execute(text("SELECT current_schemas(false)")).scalar_one()
        conn.rollback()
    assert _server_refusal(facts) is None
    assert facts["schema_exists"] is True
    assert facts["schema_comment"] == _SCHEMA_MARKER
    assert list(schemas) == [_TEST_SCHEMA]
