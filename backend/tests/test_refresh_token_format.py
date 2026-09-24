"""
Contrato de formato do refresh token opaco entre backend e cliente.

O cliente (aurea-gold-client/src/lib/fetch-refresh.ts, looksLikeRt) só
lê/guarda refresh tokens que casam com /^[a-f0-9]{64}$/i; qualquer
outro formato é descartado e a sessão é limpa no primeiro 401.

Garantias cobertas:
  - generate_refresh_token() emite 64 hex (256 bits) e não repete;
  - o token emitido pelo /login casa com o contrato do cliente;
  - o token rotacionado pelo /refresh casa com o mesmo contrato;
  - o token inicial do /login é aceito pelo /refresh e a cadeia de
    rotações continua funcionando (fluxo de ponta a ponta do cliente).

Estratégia: TestClient real contra app.main.app, com override apenas
de get_db (SQLite em memória, StaticPool).
"""
import os

os.environ.setdefault("SECRET_KEY", "refresh-token-format-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import hashlib
import re

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.refresh_token import RefreshToken
from app.models.user_main import User
from app.utils.security import generate_refresh_token, hash_password

LOGIN_PATH = "/api/v1/auth/login"
REFRESH_PATH = "/api/v1/auth/refresh"

PASSWORD = "correct-password"

# Espelho exato de looksLikeRt em aurea-gold-client/src/lib/fetch-refresh.ts.
CLIENT_RT_CONTRACT = re.compile(r"^[a-f0-9]{64}$", re.IGNORECASE)


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
    monkeypatch.setenv("LOGIN_RL_ENABLED", "0")
    monkeypatch.setenv("REFRESH_RL_ENABLED", "0")

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)


def _create_user(db, email: str) -> User:
    user = User(email=email, hashed_password=hash_password(PASSWORD), role="customer")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(client, email: str) -> dict:
    r = client.post(LOGIN_PATH, json={"username": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()


def _stored_hashes(db):
    db.expire_all()
    return [r.token_hash for r in db.query(RefreshToken).all()]


def test_generate_refresh_token_is_64_lowercase_hex():
    tokens = {generate_refresh_token() for _ in range(50)}
    assert len(tokens) == 50
    for t in tokens:
        assert re.fullmatch(r"[0-9a-f]{64}", t)


def test_login_refresh_token_matches_client_contract(client, db_session):
    user = _create_user(db_session, "rt-format-login@test.local")
    rt = _login(client, user.email)["refresh_token"]

    assert CLIENT_RT_CONTRACT.match(rt)
    assert _stored_hashes(db_session) == [hashlib.sha256(rt.encode("utf-8")).hexdigest()]


def test_initial_token_refreshes_and_rotation_chain_keeps_contract(client, db_session):
    user = _create_user(db_session, "rt-format-chain@test.local")
    rt = _login(client, user.email)["refresh_token"]
    assert CLIENT_RT_CONTRACT.match(rt)

    seen = {rt}
    for _ in range(3):
        r = client.post(REFRESH_PATH, json={"refresh_token": rt})
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["access_token"]
        new_rt = body["refresh_token"]
        assert CLIENT_RT_CONTRACT.match(new_rt)
        assert new_rt not in seen
        seen.add(new_rt)

        # token anterior não é mais aceito após a rotação
        assert client.post(REFRESH_PATH, json={"refresh_token": rt}).status_code == 401
        rt = new_rt

    assert _stored_hashes(db_session) == [hashlib.sha256(rt.encode("utf-8")).hexdigest()]
