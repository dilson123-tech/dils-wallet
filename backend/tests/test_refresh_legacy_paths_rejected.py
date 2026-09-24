"""
Regressão de segurança: POST /api/v1/auth/refresh aceita SOMENTE o
refresh token OPACO emitido pelo backend (DB guarda sha256 dele em
refresh_tokens.token_hash).

Caminhos removidos, que agora devem terminar em 401 sem tocar no DB:
  - refresh JWT stateless (token com dois pontos, typ="refresh",
    assinado com SECRET_KEY/ALGORITHM);
  - access token enviado como refresh token;
  - fallback ultra-legacy (linha cujo token_hash é o token cru, sem
    sha256);
  - o próprio hash enviado como se fosse o token.

Estratégia: TestClient real contra app.main.app, com override apenas
de get_db (SQLite em memória, StaticPool). Rate limit do /refresh
desligado via env para isolar o comportamento de validação.
"""
import os

os.environ.setdefault("SECRET_KEY", "refresh-legacy-paths-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.refresh_token import RefreshToken
from app.models.user_main import User
from app.utils.security import ALGORITHM, SECRET_KEY, create_access_token

REFRESH_PATH = "/api/v1/auth/refresh"
GENERIC_401 = "Refresh token inválido/expirado"


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session, monkeypatch):
    monkeypatch.setenv("REFRESH_RL_ENABLED", "0")

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)


def _create_user(db, email: str) -> User:
    user = User(email=email, hashed_password="x", role="customer")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _add_row(db, *, user_id: int, token_hash: str) -> None:
    db.add(
        RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
    )
    db.commit()


def _snapshot(db):
    db.expire_all()
    return sorted(
        (r.id, r.user_id, r.token_hash, str(r.expires_at))
        for r in db.query(RefreshToken).all()
    )


def _assert_generic_401(response):
    assert response.status_code == 401
    assert response.json() == {"detail": GENERIC_401}


def test_stateless_refresh_jwt_is_rejected(client, db_session):
    user = _create_user(db_session, "jwt-refresh@test.local")
    # Uma sessão opaca legítima existe para o usuário; o JWT não pode
    # nem ser aceito nem mexer nela.
    _add_row(db_session, user_id=user.id, token_hash=hashlib.sha256(b"opaque").hexdigest())
    before = _snapshot(db_session)

    legacy_jwt = jwt.encode(
        {
            "sub": user.email,
            "typ": "refresh",
            "exp": datetime.now(timezone.utc) + timedelta(days=7),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    assert legacy_jwt.count(".") == 2

    _assert_generic_401(client.post(REFRESH_PATH, json={"refresh_token": legacy_jwt}))
    assert _snapshot(db_session) == before


def test_access_token_is_rejected_as_refresh_token(client, db_session):
    user = _create_user(db_session, "access-as-refresh@test.local")
    access = create_access_token({"sub": user.email})

    _assert_generic_401(client.post(REFRESH_PATH, json={"refresh_token": access}))
    assert _snapshot(db_session) == []


def test_ultra_legacy_raw_row_is_rejected_and_untouched(client, db_session):
    user = _create_user(db_session, "ultra-legacy-http@test.local")
    raw = secrets.token_hex(20)
    _add_row(db_session, user_id=user.id, token_hash=raw)  # SEM sha256
    before = _snapshot(db_session)

    _assert_generic_401(client.post(REFRESH_PATH, json={"refresh_token": raw}))
    assert _snapshot(db_session) == before


def test_sending_the_stored_hash_is_rejected_but_raw_token_works(client, db_session):
    user = _create_user(db_session, "hash-as-token@test.local")
    raw = secrets.token_urlsafe(32)
    stored_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    _add_row(db_session, user_id=user.id, token_hash=stored_hash)
    before = _snapshot(db_session)

    # Quem vazar só o conteúdo da coluna token_hash não consegue usá-lo.
    _assert_generic_401(client.post(REFRESH_PATH, json={"refresh_token": stored_hash}))
    assert _snapshot(db_session) == before

    # O token opaco verdadeiro continua funcionando (rotação intacta).
    ok = client.post(REFRESH_PATH, json={"refresh_token": raw})
    assert ok.status_code == 200
    body = ok.json()
    assert body["token_type"] == "bearer"
    assert body["refresh_token"] and body["refresh_token"] != raw

    rows = _snapshot(db_session)
    assert len(rows) == 1
    assert rows[0][2] == hashlib.sha256(body["refresh_token"].encode("utf-8")).hexdigest()


@pytest.mark.parametrize("value", ["", "   ", "a.b.c", "not-a-real-token"])
def test_garbage_tokens_are_rejected(client, db_session, value):
    _assert_generic_401(client.post(REFRESH_PATH, json={"refresh_token": value}))
