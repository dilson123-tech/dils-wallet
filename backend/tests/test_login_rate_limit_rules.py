"""
Regras do rate limit de POST /api/v1/auth/login (app/utils/rate_limit.py
via rl_peek/rl_check em app/api/v1/routes/auth.py).

Garantias cobertas:
  - limite por username (login:ident:{ip}:{ident}) bloqueia com 429 mesmo
    com o limite por IP folgado, inclusive quando a senha é correta, e
    não afeta outro username vindo do mesmo IP;
  - login bem-sucedido NÃO consome tentativa (nenhuma chave "login:" é
    criada) e não "zera" o contador de falhas;
  - todo 429 do login traz Retry-After inteiro em [1, janela] e o detail
    exato.

Observação: o 429 emitido dentro de _rl_fail() (rl_check bloqueando
depois que o pre-check rl_peek liberou) só é alcançável sob concorrência
— sequencialmente o pre-check sempre bloqueia primeiro. Por isso o
Retry-After é validado nos dois gatilhos sequenciais reais: bloqueio
por username e bloqueio por IP.

Estratégia: TestClient real contra app.main.app, com override apenas de
get_db (SQLite em memória, StaticPool), mesmo padrão de
test_auth_logout.py. SlowAPI não participa do /login. As chaves "login:"
de _BUCKETS são limpas antes e depois de cada teste.
"""
import os

os.environ.setdefault("SECRET_KEY", "login-rate-limit-rules-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.user_main import User
from app.utils import rate_limit
from app.utils.security import hash_password

LOGIN_PATH = "/api/v1/auth/login"

PASSWORD = "correct-password"
WINDOW_SEC = 60
RL_DETAIL = {"detail": "Muitas tentativas. Aguarde e tente novamente."}


def _login_keys():
    return [k for k in rate_limit._BUCKETS if k.startswith("login:")]


def _clear_login_buckets():
    for key in _login_keys():
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
    monkeypatch.setenv("LOGIN_RL_ENABLED", "1")
    monkeypatch.setenv("LOGIN_RL_WINDOW_SEC", str(WINDOW_SEC))
    monkeypatch.setenv("REFRESH_RL_ENABLED", "0")
    monkeypatch.setenv("LOGOUT_RL_ENABLED", "0")
    _clear_login_buckets()

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
        _clear_login_buckets()


def _create_user(db, email: str) -> User:
    user = User(email=email, hashed_password=hash_password(PASSWORD), role="customer")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _login(client, username: str, password: str):
    return client.post(LOGIN_PATH, json={"username": username, "password": password})


def _assert_rl_429(response):
    assert response.status_code == 429, response.text
    assert response.json() == RL_DETAIL
    retry_after = int(response.headers["Retry-After"])
    assert 1 <= retry_after <= WINDOW_SEC


def test_login_blocks_per_username_even_with_ip_limit_free(client, db_session, monkeypatch):
    monkeypatch.setenv("LOGIN_RL_MAX_PER_IP", "100")
    monkeypatch.setenv("LOGIN_RL_MAX_PER_IDENT", "3")
    alice = _create_user(db_session, "alice-rl@test.local")
    bob = _create_user(db_session, "bob-rl@test.local")

    for _ in range(3):
        r = _login(client, alice.email, "wrong-password")
        assert r.status_code == 401, r.text

    _assert_rl_429(_login(client, alice.email, "wrong-password"))

    # Bloqueio vale mesmo com a senha correta (pre-check antes da senha).
    _assert_rl_429(_login(client, alice.email, PASSWORD))

    # Username diferente no mesmo IP continua com o próprio contador.
    assert _login(client, bob.email, "wrong-password").status_code == 401
    assert _login(client, bob.email, PASSWORD).status_code == 200


def test_login_ident_key_is_case_insensitive(client, db_session, monkeypatch):
    monkeypatch.setenv("LOGIN_RL_MAX_PER_IP", "100")
    monkeypatch.setenv("LOGIN_RL_MAX_PER_IDENT", "2")
    user = _create_user(db_session, "case-rl@test.local")

    assert _login(client, user.email, "wrong-password").status_code == 401
    assert _login(client, user.email.upper(), "wrong-password").status_code == 401
    _assert_rl_429(_login(client, user.email, "wrong-password"))


def test_successful_login_does_not_consume_attempts(client, db_session, monkeypatch):
    monkeypatch.setenv("LOGIN_RL_MAX_PER_IP", "2")
    monkeypatch.setenv("LOGIN_RL_MAX_PER_IDENT", "2")
    user = _create_user(db_session, "success-rl@test.local")

    for _ in range(5):
        r = _login(client, user.email, PASSWORD)
        assert r.status_code == 200, r.text

    # Sucesso usa só rl_peek: nenhuma chave de login é criada.
    assert _login_keys() == []

    # Contador de falhas continua intacto: 2 falhas permitidas, a 3ª bloqueia.
    assert _login(client, user.email, "wrong-password").status_code == 401
    assert _login(client, user.email, "wrong-password").status_code == 401
    _assert_rl_429(_login(client, user.email, "wrong-password"))


def test_login_429_by_ip_has_retry_after(client, db_session, monkeypatch):
    monkeypatch.setenv("LOGIN_RL_MAX_PER_IP", "3")
    monkeypatch.setenv("LOGIN_RL_MAX_PER_IDENT", "1000")
    user = _create_user(db_session, "ip-rl@test.local")

    # Usernames distintos: só o contador por IP enche.
    for i in range(3):
        r = _login(client, f"unknown-{i}@test.local", "wrong-password")
        assert r.status_code == 401, r.text

    _assert_rl_429(_login(client, "unknown-x@test.local", "wrong-password"))
    _assert_rl_429(_login(client, user.email, PASSWORD))


def test_login_429_by_username_has_retry_after(client, db_session, monkeypatch):
    monkeypatch.setenv("LOGIN_RL_MAX_PER_IP", "100")
    monkeypatch.setenv("LOGIN_RL_MAX_PER_IDENT", "1")
    user = _create_user(db_session, "ident-ra-rl@test.local")

    assert _login(client, user.email, "wrong-password").status_code == 401
    blocked = _login(client, user.email, "wrong-password")
    _assert_rl_429(blocked)
    assert blocked.headers["Retry-After"].isdigit()
