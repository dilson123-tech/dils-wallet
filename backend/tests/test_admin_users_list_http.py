"""
GET /api/v1/admin/users: listagem administrativa real, somente leitura.

Contrato: {"items": [{id, email, full_name, role}], "total": n}, paginado
por skip (>= 0) e limit (1..100, padrão 50), ordenado por id. Protegido por
require_admin (401 sem credencial válida, 403 para não-admin). Nunca expõe
hash de senha nem tokens.

TestClient contra app.main.app, com override apenas de get_db (SQLite em
memória, StaticPool) — nenhum banco real é tocado.
"""
import os

os.environ.setdefault("SECRET_KEY", "admin-users-list-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.rate_limit import limiter
from app.database import Base, get_db
from app.main import app
from app.models.user_main import User
from app.utils.security import ALGORITHM, SECRET_KEY, create_access_token

ADMIN_USERS_PATH = "/api/v1/admin/users"

ADMIN_EMAIL = "admin-users-list-admin@test.local"
CUSTOMER_EMAIL = "admin-users-list-customer@test.local"
MANAGER_EMAIL = "admin-users-list-manager@test.local"
CREDENTIALS_DETAIL = "Credenciais inválidas ou token expirado."
FORBIDDEN_DETAIL = "Acesso negado."

PASSWORD_HASH_MARKER = "$2b$12$admin-users-list-secret-hash-marker"
EXPECTED_ITEM_KEYS = {"id", "email", "full_name", "role"}
SENSITIVE_KEYS = {"password", "password_hash", "hashed_password", "token", "access_token", "refresh_token"}


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


def _create_user(db, email: str, role: str, full_name: str | None = None) -> User:
    user = User(email=email, hashed_password=PASSWORD_HASH_MARKER, role=role, full_name=full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def users(db_session):
    return [
        _create_user(db_session, ADMIN_EMAIL, "admin", "Admin Teste"),
        _create_user(db_session, CUSTOMER_EMAIL, "customer", "Cliente Teste"),
        _create_user(db_session, MANAGER_EMAIL, "manager"),
    ]


def _bearer(email: str) -> dict:
    return {"Authorization": f"Bearer {create_access_token({'sub': email})}"}


def _assert_no_sensitive_data(response) -> None:
    assert PASSWORD_HASH_MARKER not in response.text
    for item in response.json()["items"]:
        assert set(item) == EXPECTED_ITEM_KEYS
        assert not (set(item) & SENSITIVE_KEYS)


def test_anonymous_is_rejected_with_401(client, users):
    response = client.get(ADMIN_USERS_PATH)

    assert response.status_code == 401
    assert ADMIN_EMAIL not in response.text


def test_invalid_token_is_rejected_with_401(client, users):
    response = client.get(ADMIN_USERS_PATH, headers={"Authorization": "Bearer not-a-jwt"})

    assert response.status_code == 401
    assert response.json() == {"detail": CREDENTIALS_DETAIL}


def test_admin_refresh_jwt_is_rejected_with_401(client, users):
    exp = datetime.now(timezone.utc) + timedelta(days=7)
    token = jwt.encode({"sub": ADMIN_EMAIL, "typ": "refresh", "exp": exp}, SECRET_KEY, algorithm=ALGORITHM)

    response = client.get(ADMIN_USERS_PATH, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json() == {"detail": CREDENTIALS_DETAIL}
    assert CUSTOMER_EMAIL not in response.text


@pytest.mark.parametrize("email", [CUSTOMER_EMAIL, MANAGER_EMAIL])
def test_non_admin_is_rejected_with_403(client, users, email):
    response = client.get(ADMIN_USERS_PATH, headers=_bearer(email))

    assert response.status_code == 403
    assert response.json() == {"detail": FORBIDDEN_DETAIL}
    assert ADMIN_EMAIL not in response.text
    assert PASSWORD_HASH_MARKER not in response.text


def test_admin_gets_real_users_list(client, users):
    response = client.get(ADMIN_USERS_PATH, headers=_bearer(ADMIN_EMAIL))

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"items", "total"}
    assert body["total"] == 3
    assert body["items"] == [
        {"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role}
        for u in sorted(users, key=lambda u: u.id)
    ]
    _assert_no_sensitive_data(response)


def test_pagination_skip_and_limit(client, users):
    ordered_ids = sorted(u.id for u in users)

    first = client.get(ADMIN_USERS_PATH, params={"skip": 0, "limit": 2}, headers=_bearer(ADMIN_EMAIL))
    second = client.get(ADMIN_USERS_PATH, params={"skip": 2, "limit": 2}, headers=_bearer(ADMIN_EMAIL))
    beyond = client.get(ADMIN_USERS_PATH, params={"skip": 10}, headers=_bearer(ADMIN_EMAIL))

    assert first.status_code == second.status_code == beyond.status_code == 200
    assert [i["id"] for i in first.json()["items"]] == ordered_ids[:2]
    assert [i["id"] for i in second.json()["items"]] == ordered_ids[2:]
    assert beyond.json() == {"items": [], "total": 3}
    assert first.json()["total"] == second.json()["total"] == 3


@pytest.mark.parametrize(
    "params",
    [{"limit": 101}, {"limit": 0}, {"limit": -1}, {"skip": -1}, {"limit": "abc"}],
)
def test_pagination_out_of_bounds_is_rejected_with_422(client, users, params):
    response = client.get(ADMIN_USERS_PATH, params=params, headers=_bearer(ADMIN_EMAIL))

    assert response.status_code == 422
    assert ADMIN_EMAIL not in response.text


def test_limit_at_cap_is_accepted(client, users):
    response = client.get(ADMIN_USERS_PATH, params={"limit": 100}, headers=_bearer(ADMIN_EMAIL))

    assert response.status_code == 200
    assert len(response.json()["items"]) == 3
