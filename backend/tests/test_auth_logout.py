"""
POST /api/v1/auth/logout e POST /api/v1/auth/logout-all — revogação de
sessão no servidor.

Achado da auditoria do ciclo de sessão: o router de auth só tinha
/login e /refresh. O "Sair" do cliente apagava apenas o localStorage e
o refresh token seguia válido no servidor (reproduzido: refresh com o
RT de quem já saiu devolvia 200). Não havia forma de revogar uma sessão
nem todas as sessões de um usuário.

Estratégia: TestClient real contra app.main.app, com override apenas de
get_db (SQLite em memória, StaticPool). Login/refresh/logout reais;
rate limit de login/refresh desligado só para não interferir.
"""
import os

os.environ.setdefault("SECRET_KEY", "auth-logout-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.refresh_token import RefreshToken
from app.models.user_main import User
from app.utils.security import hash_password

LOGIN = "/api/v1/auth/login"
REFRESH = "/api/v1/auth/refresh"
LOGOUT = "/api/v1/auth/logout"
LOGOUT_ALL = "/api/v1/auth/logout-all"


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


def _user(db, email, password="pw-logout"):
    u = User(email=email, hashed_password=hash_password(password), role="customer")
    db.add(u)
    db.commit()
    return u


def _login(client, email, password="pw-logout"):
    r = client.post(LOGIN, json={"username": email, "password": password})
    assert r.status_code == 200, r.text
    return r.json()


def _rows(db, user_id):
    db.expire_all()
    return db.query(RefreshToken).filter(RefreshToken.user_id == user_id).count()


def test_logout_revokes_refresh_token(client, db_session):
    _user(db_session, "a@test.local")
    tok = _login(client, "a@test.local")

    r = client.post(LOGOUT, json={"refresh_token": tok["refresh_token"]})
    assert r.status_code == 204
    assert r.content == b""

    r = client.post(REFRESH, json={"refresh_token": tok["refresh_token"]})
    assert r.status_code == 401


def test_logout_only_revokes_that_session(client, db_session):
    u = _user(db_session, "b@test.local")
    s1 = _login(client, "b@test.local")
    s2 = _login(client, "b@test.local")

    assert client.post(LOGOUT, json={"refresh_token": s1["refresh_token"]}).status_code == 204

    assert _rows(db_session, u.id) == 1
    assert client.post(REFRESH, json={"refresh_token": s2["refresh_token"]}).status_code == 200


def test_logout_after_rotation_revokes_current_token(client, db_session):
    _user(db_session, "c@test.local")
    tok = _login(client, "c@test.local")
    rotated = client.post(REFRESH, json={"refresh_token": tok["refresh_token"]}).json()

    assert client.post(LOGOUT, json={"refresh_token": rotated["refresh_token"]}).status_code == 204
    assert client.post(REFRESH, json={"refresh_token": rotated["refresh_token"]}).status_code == 401


@pytest.mark.parametrize("rt", ["", "   ", "token-que-nao-existe"])
def test_logout_is_idempotent_and_does_not_leak(client, db_session, rt):
    u = _user(db_session, "d@test.local")
    tok = _login(client, "d@test.local")

    r = client.post(LOGOUT, json={"refresh_token": rt})
    assert r.status_code == 204

    # nenhuma outra sessão foi afetada
    assert _rows(db_session, u.id) == 1
    assert client.post(REFRESH, json={"refresh_token": tok["refresh_token"]}).status_code == 200


def test_logout_twice_is_204(client, db_session):
    _user(db_session, "e@test.local")
    tok = _login(client, "e@test.local")
    for _ in range(2):
        assert client.post(LOGOUT, json={"refresh_token": tok["refresh_token"]}).status_code == 204


def test_logout_rejects_stored_hash_as_token(client, db_session):
    # O hash armazenado (ex.: vazado de um backup) não pode servir para
    # apagar a sessão: o lookup é sempre sha256(valor recebido).
    u = _user(db_session, "f@test.local")
    _login(client, "f@test.local")
    stored = db_session.query(RefreshToken).filter(RefreshToken.user_id == u.id).one().token_hash

    assert client.post(LOGOUT, json={"refresh_token": stored}).status_code == 204
    assert _rows(db_session, u.id) == 1


def test_logout_all_revokes_every_session_of_the_user(client, db_session):
    u = _user(db_session, "g@test.local")
    other = _user(db_session, "h@test.local")
    sessions = [_login(client, "g@test.local") for _ in range(3)]
    other_tok = _login(client, "h@test.local")

    r = client.post(
        LOGOUT_ALL,
        headers={"Authorization": f"Bearer {sessions[0]['access_token']}"},
    )
    assert r.status_code == 204

    assert _rows(db_session, u.id) == 0
    for s in sessions:
        assert client.post(REFRESH, json={"refresh_token": s["refresh_token"]}).status_code == 401

    # isolamento: sessões de outro usuário seguem válidas
    assert _rows(db_session, other.id) == 1
    assert client.post(REFRESH, json={"refresh_token": other_tok["refresh_token"]}).status_code == 200


def test_logout_all_requires_access_token(client, db_session):
    u = _user(db_session, "i@test.local")
    tok = _login(client, "i@test.local")

    assert client.post(LOGOUT_ALL).status_code == 401
    # refresh token não vale como Bearer
    r = client.post(LOGOUT_ALL, headers={"Authorization": f"Bearer {tok['refresh_token']}"})
    assert r.status_code == 401

    assert _rows(db_session, u.id) == 1
