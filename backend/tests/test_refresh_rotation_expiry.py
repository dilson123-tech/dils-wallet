"""
POST /api/v1/auth/refresh — expiração do refresh token na rotação (R1).

Política configurada: REFRESH_TOKEN_EXPIRE_DAYS = 7 (app/utils/security.py),
aplicada no login via refresh_token_expiry_dt().

Antes da correção, a rotação opaca gravava expires_at = now + 30 dias
(valor fixo em auth.py), elevando a validade de 7 para 30 dias já na
primeira rotação e renovando os 30 dias a cada nova rotação.

Chama as funções reais `login()` e `refresh()` diretamente, com SQLite em
arquivo temporário (nunca o app.db real do projeto).
"""
import hashlib
import os
import tempfile
from datetime import datetime, timedelta, timezone

os.environ.setdefault("SECRET_KEY", "refresh-rotation-expiry-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request as StarletteRequest

from app.api.v1.routes.auth import (
    LoginRequest,
    RefreshRequest,
    login as login_endpoint,
    refresh as refresh_endpoint,
)
from app.database import Base
from app.models.refresh_token import RefreshToken
from app.models.user_main import User
from app.utils.security import REFRESH_TOKEN_EXPIRE_DAYS, hash_password

# Folga para o tempo decorrido entre a chamada e a leitura do banco.
TOLERANCE = timedelta(minutes=1)


@pytest.fixture()
def session_factory():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    engine = create_engine(
        f"sqlite:///{path}", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield sessionmaker(bind=engine)
    finally:
        engine.dispose()
        os.remove(path)


def _request(path, host):
    return StarletteRequest({
        "type": "http",
        "method": "POST",
        "path": path,
        "raw_path": path.encode(),
        "headers": [],
        "query_string": b"",
        "server": ("testserver", 80),
        "client": (host, 12345),
        "scheme": "http",
    })


def _as_utc(dt):
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _assert_policy_expiry(expires_at, called_at):
    expected = called_at + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    assert abs(_as_utc(expires_at) - expected) <= TOLERANCE


def _row(session_factory, raw):
    db = session_factory()
    try:
        token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).one()
    finally:
        db.close()


def _login(session_factory, email, password, host):
    db = session_factory()
    try:
        resp = login_endpoint(
            LoginRequest(username=email, password=password),
            _request("/api/v1/auth/login", host),
            db,
        )
        return resp.refresh_token
    finally:
        db.close()


def _refresh(session_factory, raw, host):
    db = session_factory()
    try:
        resp = refresh_endpoint(
            RefreshRequest(refresh_token=raw),
            _request("/api/v1/auth/refresh", host),
            db,
        )
        return resp["refresh_token"]
    finally:
        db.close()


def _create_user(session_factory, email, password):
    db = session_factory()
    try:
        db.add(User(email=email, hashed_password=hash_password(password), role="customer"))
        db.commit()
    finally:
        db.close()


def test_policy_is_seven_days():
    assert REFRESH_TOKEN_EXPIRE_DAYS == 7


def test_login_and_rotations_respect_refresh_policy(session_factory):
    _create_user(session_factory, "r1@test.local", "pw-r1")

    called_at = datetime.now(timezone.utc)
    raw0 = _login(session_factory, "r1@test.local", "pw-r1", "198.51.100.10")
    _assert_policy_expiry(_row(session_factory, raw0).expires_at, called_at)

    called_at = datetime.now(timezone.utc)
    raw1 = _refresh(session_factory, raw0, "198.51.100.11")
    assert raw1 != raw0
    _assert_policy_expiry(_row(session_factory, raw1).expires_at, called_at)

    called_at = datetime.now(timezone.utc)
    raw2 = _refresh(session_factory, raw1, "198.51.100.12")
    assert raw2 != raw1
    _assert_policy_expiry(_row(session_factory, raw2).expires_at, called_at)


def test_rotation_does_not_extend_to_thirty_days(session_factory):
    _create_user(session_factory, "r1b@test.local", "pw-r1b")
    raw0 = _login(session_factory, "r1b@test.local", "pw-r1b", "198.51.100.20")

    called_at = datetime.now(timezone.utc)
    raw1 = _refresh(session_factory, raw0, "198.51.100.21")

    expires_at = _as_utc(_row(session_factory, raw1).expires_at)
    assert expires_at <= called_at + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS) + TOLERANCE
    assert expires_at < called_at + timedelta(days=30) - TOLERANCE
