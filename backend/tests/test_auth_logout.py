"""
POST /api/v1/auth/logout e POST /api/v1/auth/logout-all.

Garantias cobertas:
  - logout é efetivo no backend: o refresh token revogado recebe 401
    em /refresh (inclusive um token obtido por rotação);
  - logout é idempotente e sem oráculo (token desconhecido/vazio/já
    revogado -> 204, nenhuma linha removida);
  - logout de uma sessão não invalida outra sessão do mesmo usuário;
  - logout-all exige Bearer válido, invalida todas as sessões do
    usuário autenticado e não toca sessões de outros usuários;
  - logout-all é idempotente;
  - /logout tem rate limit por IP (429 + Retry-After).

Estratégia: TestClient real contra app.main.app, com override apenas
de get_db (SQLite em memória, StaticPool). Sessões são criadas pelo
/login real (hash bcrypt verdadeiro), para exercitar o fluxo de ponta
a ponta.
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
from app.utils import rate_limit
from app.utils.security import create_access_token, hash_password

LOGIN_PATH = "/api/v1/auth/login"
REFRESH_PATH = "/api/v1/auth/refresh"
LOGOUT_PATH = "/api/v1/auth/logout"
LOGOUT_ALL_PATH = "/api/v1/auth/logout-all"

PASSWORD = "correct-password"


def _clear_logout_buckets():
    for key in [k for k in rate_limit._BUCKETS if k.startswith("logout:")]:
        rate_limit._BUCKETS.pop(key, None)


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
    # Rate limits desligados por padrão; o teste de 429 religa o de logout.
    monkeypatch.setenv("LOGIN_RL_ENABLED", "0")
    monkeypatch.setenv("REFRESH_RL_ENABLED", "0")
    monkeypatch.setenv("LOGOUT_RL_ENABLED", "0")
    _clear_logout_buckets()

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
        _clear_logout_buckets()


def _create_user(db, email: str) -> User:
    user = User(email=email, hashed_password=hash_password(PASSWORD), role="customer")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(client, email: str) -> dict:
    r = client.post(LOGIN_PATH, json={"username": email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["refresh_token"]
    return body


def _refresh(client, rt: str):
    return client.post(REFRESH_PATH, json={"refresh_token": rt})


def _logout(client, rt: str):
    return client.post(LOGOUT_PATH, json={"refresh_token": rt})


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _rows(db, user_id=None):
    db.expire_all()
    q = db.query(RefreshToken)
    if user_id is not None:
        q = q.filter(RefreshToken.user_id == user_id)
    return sorted((r.id, r.user_id, r.token_hash) for r in q.all())


# ---------------------------------------------------------------------
# /logout
# ---------------------------------------------------------------------
def test_logout_revokes_refresh_token(client, db_session):
    user = _create_user(db_session, "logout-a@test.local")
    session = _login(client, user.email)
    assert len(_rows(db_session, user.id)) == 1

    r = _logout(client, session["refresh_token"])
    assert r.status_code == 204
    assert r.content == b""
    assert _rows(db_session, user.id) == []

    assert _refresh(client, session["refresh_token"]).status_code == 401


def test_logout_revokes_rotated_refresh_token(client, db_session):
    user = _create_user(db_session, "logout-rotated@test.local")
    first = _login(client, user.email)

    rotated = _refresh(client, first["refresh_token"])
    assert rotated.status_code == 200
    rotated_rt = rotated.json()["refresh_token"]

    assert _logout(client, rotated_rt).status_code == 204
    assert _rows(db_session, user.id) == []
    assert _refresh(client, rotated_rt).status_code == 401
    assert _refresh(client, first["refresh_token"]).status_code == 401


def test_logout_is_idempotent(client, db_session):
    user = _create_user(db_session, "logout-idem@test.local")
    session = _login(client, user.email)

    assert _logout(client, session["refresh_token"]).status_code == 204
    assert _logout(client, session["refresh_token"]).status_code == 204
    assert _rows(db_session, user.id) == []
    assert _refresh(client, session["refresh_token"]).status_code == 401


@pytest.mark.parametrize("value", ["", "   ", "unknown-token", "a.b.c"])
def test_logout_unknown_or_empty_token_is_204_and_deletes_nothing(client, db_session, value):
    user = _create_user(db_session, "logout-unknown@test.local")
    session = _login(client, user.email)
    before = _rows(db_session)

    r = _logout(client, value)
    assert r.status_code == 204
    assert _rows(db_session) == before
    assert _refresh(client, session["refresh_token"]).status_code == 200


def test_logout_does_not_accept_stored_hash(client, db_session):
    user = _create_user(db_session, "logout-hash@test.local")
    session = _login(client, user.email)
    before = _rows(db_session)
    stored_hash = before[0][2]

    assert _logout(client, stored_hash).status_code == 204
    assert _rows(db_session) == before
    assert _refresh(client, session["refresh_token"]).status_code == 200


def test_logout_of_one_session_keeps_other_sessions_of_same_user(client, db_session):
    user = _create_user(db_session, "logout-multi@test.local")
    session_a = _login(client, user.email)
    session_b = _login(client, user.email)
    assert len(_rows(db_session, user.id)) == 2

    assert _logout(client, session_a["refresh_token"]).status_code == 204
    assert len(_rows(db_session, user.id)) == 1

    assert _refresh(client, session_a["refresh_token"]).status_code == 401
    assert _refresh(client, session_b["refresh_token"]).status_code == 200


def test_logout_requires_refresh_token_field(client):
    assert client.post(LOGOUT_PATH, json={}).status_code == 422


def test_logout_rate_limit_returns_429_with_retry_after(client, db_session, monkeypatch):
    monkeypatch.setenv("LOGOUT_RL_ENABLED", "1")
    monkeypatch.setenv("LOGOUT_RL_MAX_PER_IP", "3")
    monkeypatch.setenv("LOGOUT_RL_WINDOW_SEC", "60")
    _clear_logout_buckets()

    user = _create_user(db_session, "logout-rl@test.local")
    session = _login(client, user.email)

    for _ in range(3):
        assert _logout(client, "unknown-token").status_code == 204

    blocked = _logout(client, session["refresh_token"])
    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) >= 1
    assert blocked.json() == {"detail": "Muitas tentativas. Aguarde e tente novamente."}

    # bloqueado antes de tocar o banco: a sessão continua existindo.
    assert len(_rows(db_session, user.id)) == 1


# ---------------------------------------------------------------------
# /logout-all
# ---------------------------------------------------------------------
def test_logout_all_requires_bearer(client, db_session):
    user = _create_user(db_session, "logout-all-noauth@test.local")
    _login(client, user.email)
    before = _rows(db_session)

    assert client.post(LOGOUT_ALL_PATH).status_code == 401
    assert client.post(LOGOUT_ALL_PATH, headers=_bearer("not-a-jwt")).status_code == 401
    assert _rows(db_session) == before


def test_logout_all_revokes_every_session_of_user_only(client, db_session):
    alice = _create_user(db_session, "alice@test.local")
    bob = _create_user(db_session, "bob@test.local")

    alice_1 = _login(client, alice.email)
    alice_2 = _login(client, alice.email)
    alice_3 = _login(client, alice.email)
    bob_1 = _login(client, bob.email)
    bob_rows_before = _rows(db_session, bob.id)
    assert len(_rows(db_session, alice.id)) == 3

    r = client.post(LOGOUT_ALL_PATH, headers=_bearer(alice_1["access_token"]))
    assert r.status_code == 204
    assert r.content == b""

    assert _rows(db_session, alice.id) == []
    assert _rows(db_session, bob.id) == bob_rows_before

    for s in (alice_1, alice_2, alice_3):
        assert _refresh(client, s["refresh_token"]).status_code == 401
    assert _refresh(client, bob_1["refresh_token"]).status_code == 200


def test_logout_all_is_idempotent(client, db_session):
    user = _create_user(db_session, "logout-all-idem@test.local")
    _login(client, user.email)
    access = create_access_token({"sub": user.email})

    assert client.post(LOGOUT_ALL_PATH, headers=_bearer(access)).status_code == 204
    assert client.post(LOGOUT_ALL_PATH, headers=_bearer(access)).status_code == 204
    assert _rows(db_session, user.id) == []
