"""
GET /api/v1/partners/asaas/webhooks/sandbox/audit-history — ADMIN ONLY (A7).

O histórico lista todos os webhooks Asaas Sandbox, sem filtro por
usuário: é ferramenta técnica interna. Antes a rota usava
require_customer e qualquer cliente autenticado via eventos de outros
usuários. Agora usa require_admin:
- cliente comum recebe o 403 padrão de require_admin;
- sem token continua 401;
- administrador continua vendo o histórico completo do sandbox;
- nenhuma outra rota do wallet passou a exigir admin, e o histórico
  sandbox por usuário (/api/v1/wallet/pix/sandbox-audit-history)
  continua com require_customer.

Requisições HTTP reais (TestClient) com JWT assinado localmente e
SQLite em memória; só get_db é sobrescrito, a autenticação é a real.
"""
import json
import os
from types import SimpleNamespace

os.environ.setdefault("SECRET_KEY", "asaas-audit-admin-only-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.v1.routes import wallet
from app.database import Base
from app.models.idempotency import IdempotencyKey
from app.models.user_main import User
from app.utils.authz import require_admin, require_customer
from app.utils.security import ALGORITHM, SECRET_KEY

PATH = "/api/v1/partners/asaas/webhooks/sandbox/audit-history"
CUSTOMER_PATH = "/api/v1/wallet/pix/sandbox-audit-history"


@pytest.fixture()
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture()
def client(db_session, monkeypatch):
    monkeypatch.setattr(
        wallet, "_asaas_sandbox_webhook_config",
        lambda: SimpleNamespace(env="sandbox"),
    )
    app = FastAPI()
    app.include_router(wallet.router)
    app.dependency_overrides[wallet.get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client


def _seed(db):
    for email, role in (
        ("customer-a@example.test", "customer"),
        ("customer-b@example.test", "customer"),
        ("admin@example.test", "admin"),
    ):
        db.add(User(email=email, hashed_password="x", role=role))
    # Evento sandbox correlacionado ao cliente A.
    db.add(IdempotencyKey(
        key="asaas-sandbox-webhook:" + "a" * 64,
        request_hash="b" * 64,
        status_code=200,
        response_json=json.dumps({
            "event": {"event_type": "PAYMENT_RECEIVED", "accepted": True},
            "audit": {
                "provider": "asaas",
                "environment": "sandbox",
                "event_type": "PAYMENT_RECEIVED",
            },
        }),
    ))
    db.commit()


def _auth(email):
    token = jwt.encode({"sub": email}, SECRET_KEY, algorithm=ALGORITHM)
    return {"Authorization": f"Bearer {token}"}


def _dependency_calls(route):
    return {dep.call for dep in route.dependant.dependencies}


@pytest.mark.parametrize("email", [
    "customer-a@example.test",
    "customer-b@example.test",
])
def test_customer_gets_standard_403(client, db_session, email):
    _seed(db_session)

    response = client.get(PATH, headers=_auth(email))

    assert response.status_code == 403
    assert response.json() == {"detail": "Acesso negado."}
    assert "PAYMENT_RECEIVED" not in response.text


def test_without_token_still_401(client, db_session):
    _seed(db_session)

    response = client.get(PATH)

    assert response.status_code == 401


def test_admin_sees_full_sandbox_history(client, db_session):
    _seed(db_session)

    response = client.get(PATH, headers=_auth("admin@example.test"))

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["history"]["provider"] == "asaas"
    assert body["history"]["environment"] == "sandbox"
    assert body["history"]["total_returned"] == 1
    assert [i["event_type"] for i in body["items"]] == ["PAYMENT_RECEIVED"]


def test_only_this_wallet_route_requires_admin():
    admin_paths = {
        route.path
        for route in wallet.router.routes
        if require_admin in _dependency_calls(route)
    }

    assert admin_paths == {PATH}


def test_customer_sandbox_audit_history_still_require_customer():
    route = next(r for r in wallet.router.routes if r.path == CUSTOMER_PATH)

    calls = _dependency_calls(route)

    assert require_customer in calls
    assert require_admin not in calls
