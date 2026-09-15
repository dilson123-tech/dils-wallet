"""
Prova de regressão permanente, em PostgreSQL real efêmero, da correção
CAS (compare-and-swap) da rotação do refresh token opaco em
POST /api/v1/auth/refresh (backend/app/api/v1/routes/auth.py).

Este arquivo é a promoção, para o formato de teste permanente, da prova
local descartável executada manualmente contra PostgreSQL 16.12 real
durante a auditoria/diagnóstico da race (duas requisições concorrentes
usando o MESMO refresh token, ambas retornando HTTP 200, a última a
commitar sobrescrevendo silenciosamente token_hash e deixando um dos
dois clientes com um refresh_token que já nascia inválido -- lost
update). PostgreSQL usa READ COMMITTED por padrão (sem
isolation_level customizado em app/database.py), onde leitores nunca
bloqueiam escritores concorrentes -- diferente do SQLite (que precisa
de WAL para isso, ver test_refresh_concurrency.py) -- o que torna a
prova em PostgreSQL a mais fiel ao motor efetivamente usado em
produção.

Segue exatamente o mesmo padrão de infraestrutura/guard já
estabelecido em test_pix_send_concurrency_postgres.py:

GUARD FAIL-CLOSED: este arquivo só lê
REFRESH_CONCURRENCY_TEST_DATABASE_URL -- nunca DATABASE_URL (a
variável real usada por produção/Alembic/app). Se a variável estiver
ausente, todos os testes deste arquivo são pulados (pytest.skip). Se
estiver presente mas não corresponder exatamente ao banco de teste
efêmero esperado (scheme=postgresql[+psycopg2], host=localhost/
127.0.0.1, database=auratest_ci, user=auratest), o teste falha
imediatamente (pytest.fail) ANTES de qualquer create_engine/drop_all/
create_all -- nunca há risco de rodar contra um banco real.

Chama a função real `refresh()` do endpoint diretamente -- nenhuma
lógica de rotação é reimplementada aqui. Sincronização determinística
via evento oficial do SQLAlchemy `after_cursor_execute`, anexado
apenas à Connection de T1, sempre removido em finally.
"""
import hashlib
import os
import secrets
import threading
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

os.environ.setdefault("SECRET_KEY", "refresh-cas-postgres-test-secret")
os.environ.setdefault("JWT_SECRET", "refresh-cas-postgres-test-secret")

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request as StarletteRequest

from app.api.v1.routes.auth import RefreshRequest, refresh as refresh_endpoint
from app.database import Base
from app.models.refresh_token import RefreshToken
from app.models.user_main import User
from app.utils.security import hash_password

TIMEOUT = 15

_ENV_VAR = "REFRESH_CONCURRENCY_TEST_DATABASE_URL"
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


@pytest.fixture()
def session_factory(engine):
    """Schema recriado do zero a cada função de teste -- isolamento
    total entre provas, sobre o mesmo database já validado pelo guard."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def _make_request(host: str) -> StarletteRequest:
    path = "/api/v1/auth/refresh"
    scope = {
        "type": "http",
        "method": "POST",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "headers": [],
        "query_string": b"",
        "server": ("testserver", 80),
        "client": (host, 12345),
        "scheme": "http",
        "app": None,
    }
    return StarletteRequest(scope)


def _create_user(session_factory, email: str) -> int:
    db = session_factory()
    try:
        user = User(email=email, hashed_password=hash_password("x"), role="customer")
        db.add(user)
        db.commit()
        return user.id
    finally:
        db.close()


def _create_refresh_token_row(session_factory, *, user_id, token_hash, expires_in_days=7):
    db = session_factory()
    try:
        db.add(
            RefreshToken(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(days=expires_in_days),
            )
        )
        db.commit()
    finally:
        db.close()


def _do_refresh(session_factory, *, host, raw_refresh_token):
    db = session_factory()
    req = _make_request(host)
    body = RefreshRequest(refresh_token=raw_refresh_token)
    try:
        return refresh_endpoint(body, req, db), None
    except HTTPException as exc:
        return None, exc
    finally:
        db.close()


class SelectPauseHook:
    """Pausa T1 logo depois que o SELECT real em refresh_tokens foi
    executado no PostgreSQL (after_cursor_execute -- statement já
    rodou no servidor, linha já lida), e ANTES de qualquer
    UPDATE/commit -- mesmo padrão de ForUpdatePauseHook em
    test_pix_send_concurrency_postgres.py, adaptado."""

    def __init__(self, connection):
        self.connection = connection
        self.paused_event = threading.Event()
        self.release_event = threading.Event()
        self.fired = False

    def after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        upper = statement.upper()
        if not self.fired and "SELECT" in upper and "REFRESH_TOKENS" in upper:
            self.fired = True
            self.paused_event.set()
            released = self.release_event.wait(timeout=TIMEOUT)
            if not released:
                raise TimeoutError("T1 nao foi liberada a tempo (select hook)")

    def attach(self):
        event.listen(self.connection, "after_cursor_execute", self.after_cursor_execute)

    def detach(self):
        event.remove(self.connection, "after_cursor_execute", self.after_cursor_execute)


def test_concurrent_rotation_exactly_one_winner_postgres(session_factory):
    user_id = _create_user(session_factory, "concurrency-pg@test.local")
    raw_rt = secrets.token_urlsafe(48)
    rt_hash = hashlib.sha256(raw_rt.encode("utf-8")).hexdigest()
    _create_refresh_token_row(session_factory, user_id=user_id, token_hash=rt_hash)

    db1 = session_factory()
    conn1 = db1.connection()  # força a Session a associar uma Connection real
    hook = SelectPauseHook(conn1)
    hook.attach()

    result_holder = {}

    def run_t1():
        req1 = _make_request("10.0.0.1")
        body1 = RefreshRequest(refresh_token=raw_rt)
        try:
            result_holder["t1"] = refresh_endpoint(body1, req1, db1)
        except HTTPException as exc:
            result_holder["t1_error"] = exc
        finally:
            hook.detach()
            db1.close()

    t1_thread = threading.Thread(target=run_t1)
    t1_thread.start()

    paused = hook.paused_event.wait(timeout=TIMEOUT)
    assert paused, "T1 nunca pausou -- hook do SELECT nao disparou"

    # T2 roda em Session/Connection TOTALMENTE separada, ciclo completo
    # (SELECT -> CAS -> commit) ENQUANTO T1 ainda segura a linha lida
    # (não commitada) -- READ COMMITTED do Postgres permite isso sem
    # bloqueio, diferente do SQLite sem WAL.
    db2 = session_factory()
    req2 = _make_request("10.0.0.2")
    body2 = RefreshRequest(refresh_token=raw_rt)
    try:
        result_holder["t2"] = refresh_endpoint(body2, req2, db2)
    except HTTPException as exc:
        result_holder["t2_error"] = exc
    finally:
        db2.close()

    hook.release_event.set()
    t1_thread.join(timeout=TIMEOUT)
    assert not t1_thread.is_alive(), "T1 nao terminou a tempo apos liberacao"

    # exatamente uma venceu (200), exatamente uma perdeu (401) -- nunca
    # as duas, nunca nenhuma.
    t1_won = "t1" in result_holder
    t2_won = "t2" in result_holder
    assert t1_won != t2_won, (
        "exatamente UMA das duas deveria vencer (200) e a outra perder (401)",
        result_holder,
    )

    winner_result = result_holder.get("t1") or result_holder.get("t2")
    loser_error = result_holder.get("t1_error") or result_holder.get("t2_error")
    assert loser_error is not None
    assert loser_error.status_code == 401

    # sem lost update: hash final no banco bate com o token da vencedora.
    verify = session_factory()
    try:
        final_row = verify.query(RefreshToken).filter(RefreshToken.user_id == user_id).first()
        winner_new_rt = winner_result["refresh_token"]
        assert final_row.token_hash == hashlib.sha256(winner_new_rt.encode("utf-8")).hexdigest()
        # exatamente 1 linha para este usuário -- nenhuma linha extra
        # foi criada por T2 (CAS nunca faz INSERT, só UPDATE
        # condicional na mesma linha).
        assert verify.query(RefreshToken).filter(RefreshToken.user_id == user_id).count() == 1
    finally:
        verify.close()

    # token perdedor NÃO foi persistido: nenhuma linha no banco
    # corresponde ao refresh_token que a perdedora teria devolvido, se
    # ela tivesse chegado a devolver um (não devolve, pois falha
    # fail-closed antes de retornar qualquer token).
    assert "t1_error" in result_holder or "t2_error" in result_holder

    # token da vencedora continua válido.
    result3, err3 = _do_refresh(session_factory, host="10.0.0.3", raw_refresh_token=winner_new_rt)
    assert err3 is None, err3

    # token antigo (pré-race) definitivamente morto.
    _, err_old = _do_refresh(session_factory, host="10.0.0.4", raw_refresh_token=raw_rt)
    assert err_old is not None
    assert err_old.status_code == 401
