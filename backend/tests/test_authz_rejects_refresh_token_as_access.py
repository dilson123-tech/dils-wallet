"""
Pendência #10 do handoff: o refresh JWT legado (claim typ="refresh",
emitido por app/api/v1/routes/auth.py::create_refresh_token) não pode ser
aceito como Bearer de acesso nas rotas protegidas
(app/utils/authz.py::get_current_user). Ele continua válido apenas em
POST /api/v1/auth/refresh. Access tokens atuais (sem "typ") seguem
funcionando sem mudança.

TestClient contra app.main.app, com override apenas de get_db (SQLite em
memória, StaticPool). Tokens reais, assinados pelas funções de produção.
"""
import os

os.environ.setdefault("SECRET_KEY", "authz-refresh-as-access-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.routes.auth import create_refresh_token
from app.core.rate_limit import limiter
from app.database import Base, get_db
from app.main import app
from app.models.user_main import User
from app.utils.security import create_access_token

WHOAMI_PATH = "/api/v1/whoami"
USERS_ME_PATH = "/api/v1/users/me"
PIX_BALANCE_PATH = "/api/v1/pix/balance"
ADMIN_USERS_PATH = "/api/v1/admin/users"
REFRESH_PATH = "/api/v1/auth/refresh"

CUSTOMER_EMAIL = "refresh-as-access-customer@test.local"
ADMIN_EMAIL = "refresh-as-access-admin@test.local"
CREDENTIALS_DETAIL = "Credenciais inválidas ou token expirado."

PROTECTED_CUSTOMER_PATHS = [WHOAMI_PATH, USERS_ME_PATH, PIX_BALANCE_PATH]


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    limiter.reset()
    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
        limiter.reset()


def _create_user(db, email: str, role: str) -> User:
    user = User(email=email, hashed_password="x", role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def customer(db_session):
    return _create_user(db_session, CUSTOMER_EMAIL, "customer")


@pytest.fixture()
def admin(db_session):
    return _create_user(db_session, ADMIN_EMAIL, "admin")


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _assert_rejected_without_user_data(response, email: str) -> None:
    assert response.status_code == 401
    assert response.json() == {"detail": CREDENTIALS_DETAIL}
    assert email not in response.text


@pytest.mark.parametrize("path", PROTECTED_CUSTOMER_PATHS)
def test_refresh_jwt_as_bearer_is_rejected(client, customer, path):
    token = create_refresh_token(CUSTOMER_EMAIL)

    response = client.get(path, headers=_bearer(token))

    _assert_rejected_without_user_data(response, CUSTOMER_EMAIL)


def test_admin_refresh_jwt_as_bearer_is_rejected_on_admin_route(client, admin):
    token = create_refresh_token(ADMIN_EMAIL)

    response = client.get(ADMIN_USERS_PATH, headers=_bearer(token))

    _assert_rejected_without_user_data(response, ADMIN_EMAIL)


@pytest.mark.parametrize("path", PROTECTED_CUSTOMER_PATHS)
def test_access_token_without_typ_keeps_working(client, customer, path):
    token = create_access_token({"sub": CUSTOMER_EMAIL})

    response = client.get(path, headers=_bearer(token))

    assert response.status_code == 200


def test_admin_access_token_keeps_working_on_admin_route(client, admin):
    token = create_access_token({"sub": ADMIN_EMAIL})

    response = client.get(ADMIN_USERS_PATH, headers=_bearer(token))

    assert response.status_code == 200


def test_refresh_jwt_keeps_working_on_refresh_endpoint(client, customer):
    token = create_refresh_token(CUSTOMER_EMAIL)

    response = client.post(REFRESH_PATH, json={"refresh_token": token})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["refresh_token"]

    me = client.get(USERS_ME_PATH, headers=_bearer(body["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == CUSTOMER_EMAIL


def test_access_token_is_still_rejected_on_refresh_endpoint(client, customer):
    token = create_access_token({"sub": CUSTOMER_EMAIL})

    response = client.post(REFRESH_PATH, json={"refresh_token": token})

    assert response.status_code == 401
    assert CUSTOMER_EMAIL not in response.text
