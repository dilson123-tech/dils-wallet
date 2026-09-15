"""
Testes da correção CAS (compare-and-swap) da rotação do refresh token
opaco em POST /api/v1/auth/refresh (backend/app/api/v1/routes/auth.py).

Contexto: uma auditoria dedicada confirmou empiricamente (SQLite e
PostgreSQL 16.12 real efêmero) que duas requisições concorrentes
usando o MESMO refresh token podiam ambas receber HTTP 200 -- a última
transação a commitar sobrescrevia silenciosamente token_hash, e um dos
dois clientes ficava com um refresh_token que já nascia inválido
(lost update). A correção substitui a mutação+commit incondicional por
um UPDATE condicional (WHERE id = :id AND token_hash = :expected)
checando rowcount, preservando o fallback ultra-legacy (linhas cujo
token_hash foi salvo historicamente como o token cru, sem hash).

Este arquivo chama a função real `refresh()` do endpoint diretamente
-- nenhuma lógica de rotação é reimplementada aqui. Usa SQLite real em
arquivo temporário (nunca :memory: isolado por conexão, para permitir
duas Sessions concorrentes enxergarem o mesmo estado committed), nunca
o app.db real do projeto.

Sincronização determinística de concorrência via evento oficial do
SQLAlchemy `after_cursor_execute` (mesmo padrão já usado em
test_pix_send_concurrency_postgres.py), anexado somente à Connection
de T1, sempre removido em finally.
"""
import hashlib
import os
import secrets
import tempfile
import threading
from datetime import datetime, timedelta, timezone

os.environ.setdefault("SECRET_KEY", "refresh-cas-test-secret")
os.environ.setdefault("JWT_SECRET", "refresh-cas-test-secret")

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


@pytest.fixture()
def session_factory():
    """Retorna uma factory que cria uma Session NOVA a cada chamada,
    cada uma com seu PRÓPRIO Engine/connection pool dedicado, todos
    apontando para o MESMO arquivo SQLite temporário, em modo WAL.

    Duas exigências, ambas necessárias para reproduzir de forma
    determinística (sem lock espúrio) o cenário real de concorrência:

    1. Engine dedicado por Session (não um Engine/pool compartilhado):
       evita que o driver pysqlite retenha um lock de escrita já a
       partir do simples ato de associar uma Connection (necessário
       para anexar o hook de sincronização abaixo).

    2. PRAGMA journal_mode=WAL: no modo padrão (rollback-journal), o
       SQLite bloqueia QUALQUER commit de escrita enquanto outra
       conexão mantiver uma transação de leitura aberta (mesmo um
       simples SELECT já pausado) -- o que impediria a própria prova
       de concorrência que este arquivo precisa fazer (T2 completar
       COM SUCESSO enquanto T1 ainda segura a linha lida, sem commitar).
       Em WAL, leitores não bloqueiam escritores nem vice-versa
       (confirmado empiricamente antes de aplicar este fixture);
       apenas escritor-vs-escritor continua serializado -- exatamente
       o comportamento que expõe (e que o CAS corrige) a race real."""
    tmp = tempfile.mktemp(suffix=".db")
    engines = []

    def _make():
        engine = create_engine(
            f"sqlite:///{tmp}",
            connect_args={"check_same_thread": False, "timeout": 30},
        )
        with engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL")
        Base.metadata.create_all(bind=engine)
        engines.append(engine)
        return sessionmaker(bind=engine)()

    yield _make

    for engine in engines:
        engine.dispose()
    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(tmp + suffix)
        except OSError:
            pass


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
    """Chama refresh_endpoint() real diretamente, isolado em sua
    própria Session (mesmo lifecycle de app.database.get_db(): sem
    rollback artificial -- db.close() já reverte implicitamente)."""
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
    """Pausa T1 logo depois que a N-ésima consulta SELECT sobre
    refresh_tokens foi efetivamente executada no banco real
    (after_cursor_execute -- statement já rodou, não apenas
    construído), e ANTES de qualquer UPDATE/commit. select_index=1
    cobre o caminho normal (primeira SELECT já encontra a linha);
    select_index=2 cobre o fallback ultra-legacy (a primeira SELECT
    por sha256 não encontra nada, a segunda -- pelo valor cru -- é a
    que efetivamente encontra a linha)."""

    def __init__(self, connection, select_index: int = 1):
        self.connection = connection
        self.select_index = select_index
        self._count = 0
        self.paused_event = threading.Event()
        self.release_event = threading.Event()
        self.fired = False

    def after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        upper = statement.upper()
        if self.fired or "SELECT" not in upper or "REFRESH_TOKENS" not in upper:
            return
        self._count += 1
        if self._count == self.select_index:
            self.fired = True
            self.paused_event.set()
            released = self.release_event.wait(timeout=TIMEOUT)
            if not released:
                raise TimeoutError("T1 nao foi liberada a tempo (select hook)")

    def attach(self):
        event.listen(self.connection, "after_cursor_execute", self.after_cursor_execute)

    def detach(self):
        event.remove(self.connection, "after_cursor_execute", self.after_cursor_execute)


def _run_concurrent_rotation(session_factory, *, raw_rt, select_index):
    """Força a interleaving T1-le -> T2-le-e-completa -> T1-continua,
    exatamente o cenário descrito na auditoria. Retorna
    (result_holder, hook) para o teste fazer as asserções."""
    db1 = session_factory()
    conn1 = db1.connection()
    hook = SelectPauseHook(conn1, select_index=select_index)
    hook.attach()

    result_holder = {}

    def run_t1():
        req1 = _make_request("198.51.100.10")
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

    db2 = session_factory()
    req2 = _make_request("198.51.100.11")
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

    return result_holder


# ---------------------------------------------------------------------
# A) Rotação sequencial normal.
# ---------------------------------------------------------------------
def test_sequential_rotation_old_token_rejected_new_token_works(session_factory):
    user_id = _create_user(session_factory, "seq-rotation@test.local")
    raw_rt = secrets.token_urlsafe(48)
    rt_hash = hashlib.sha256(raw_rt.encode("utf-8")).hexdigest()
    _create_refresh_token_row(session_factory, user_id=user_id, token_hash=rt_hash)

    result, err = _do_refresh(session_factory, host="198.51.100.1", raw_refresh_token=raw_rt)
    assert err is None, err
    assert "access_token" in result
    new_rt = result["refresh_token"]
    assert new_rt != raw_rt

    _, err_old = _do_refresh(session_factory, host="198.51.100.1", raw_refresh_token=raw_rt)
    assert err_old is not None
    assert err_old.status_code == 401

    result2, err2 = _do_refresh(session_factory, host="198.51.100.1", raw_refresh_token=new_rt)
    assert err2 is None, err2
    assert "access_token" in result2


# ---------------------------------------------------------------------
# B) Concorrência SQLite -- exatamente um vencedor, sem lost update.
# ---------------------------------------------------------------------
def test_concurrent_rotation_exactly_one_winner_sqlite(session_factory):
    user_id = _create_user(session_factory, "concurrency@test.local")
    raw_rt = secrets.token_urlsafe(48)
    rt_hash = hashlib.sha256(raw_rt.encode("utf-8")).hexdigest()
    _create_refresh_token_row(session_factory, user_id=user_id, token_hash=rt_hash)

    result_holder = _run_concurrent_rotation(session_factory, raw_rt=raw_rt, select_index=1)

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

    # sem lost update: o hash final no banco bate com o token da vencedora.
    verify = session_factory()
    final_row = verify.query(RefreshToken).filter(RefreshToken.user_id == user_id).first()
    winner_new_rt = winner_result["refresh_token"]
    assert final_row.token_hash == hashlib.sha256(winner_new_rt.encode("utf-8")).hexdigest()
    verify.close()

    # token da vencedora continua utilizável.
    result3, err3 = _do_refresh(session_factory, host="198.51.100.12", raw_refresh_token=winner_new_rt)
    assert err3 is None, err3

    # token antigo (pré-race) definitivamente morto.
    _, err_old = _do_refresh(session_factory, host="198.51.100.13", raw_refresh_token=raw_rt)
    assert err_old is not None
    assert err_old.status_code == 401


# ---------------------------------------------------------------------
# D) Fallback ultra-legacy (token_hash == token cru, sem sha256).
# ---------------------------------------------------------------------
def test_ultra_legacy_row_rotates_correctly_with_cas(session_factory):
    user_id = _create_user(session_factory, "ultra-legacy@test.local")
    # token_hash == token cru (SEM sha256) -- simula linha histórica
    # salva "sem hash", exatamente o comentário original do endpoint
    # sobre o fallback ultra-legacy.
    raw_rt = secrets.token_hex(20)
    _create_refresh_token_row(session_factory, user_id=user_id, token_hash=raw_rt)

    result, err = _do_refresh(session_factory, host="198.51.100.20", raw_refresh_token=raw_rt)
    assert err is None, err
    new_rt = result["refresh_token"]

    _, err_old = _do_refresh(session_factory, host="198.51.100.20", raw_refresh_token=raw_rt)
    assert err_old is not None
    assert err_old.status_code == 401

    result2, err2 = _do_refresh(session_factory, host="198.51.100.20", raw_refresh_token=new_rt)
    assert err2 is None, err2


def test_ultra_legacy_row_concurrent_rotation_exactly_one_winner(session_factory):
    """Prova que expected_token_hash captura o valor REAL encontrado
    (nunca presumido como sha256(rt)) -- protege também a linha
    ultra-legacy contra a mesma corrida de B."""
    user_id = _create_user(session_factory, "ultra-legacy-race@test.local")
    raw_rt = secrets.token_hex(20)
    _create_refresh_token_row(session_factory, user_id=user_id, token_hash=raw_rt)

    # select_index=2: a 1a SELECT (por sha256(rt)) não encontra nada; a
    # 2a SELECT (fallback, pelo valor cru) é a que encontra a linha --
    # é ali que T1 deve pausar antes do CAS.
    result_holder = _run_concurrent_rotation(session_factory, raw_rt=raw_rt, select_index=2)

    t1_won = "t1" in result_holder
    t2_won = "t2" in result_holder
    assert t1_won != t2_won, (
        "exatamente UMA das duas deveria vencer (200) e a outra perder (401)",
        result_holder,
    )
    loser_error = result_holder.get("t1_error") or result_holder.get("t2_error")
    assert loser_error is not None
    assert loser_error.status_code == 401


# ---------------------------------------------------------------------
# E) Regressões.
# ---------------------------------------------------------------------
def test_nonexistent_token_returns_401(session_factory):
    _, err = _do_refresh(session_factory, host="198.51.100.40", raw_refresh_token="totally-unknown-token")
    assert err is not None
    assert err.status_code == 401


def test_expired_token_returns_401(session_factory):
    user_id = _create_user(session_factory, "expired@test.local")
    raw_rt = secrets.token_urlsafe(48)
    rt_hash = hashlib.sha256(raw_rt.encode("utf-8")).hexdigest()
    _create_refresh_token_row(session_factory, user_id=user_id, token_hash=rt_hash, expires_in_days=-1)

    _, err = _do_refresh(session_factory, host="198.51.100.41", raw_refresh_token=raw_rt)
    assert err is not None
    assert err.status_code == 401
