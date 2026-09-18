import os
from types import SimpleNamespace

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.routes import wallet


ENDPOINTS = [
    "account-status",
    "structured-balance",
    "structured-statement",
    "receipt-reconciliation",
    "operational-limits",
    "onboarding-status",
]
ERRORS = [
    "controlled adapter configuration failure",
    "SENTINEL_PRIVATE_TOKEN=secret-3k; postgres://private-db/internal",
]


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(wallet, "WALLET_MODE", "partner")
    monkeypatch.setattr(wallet, "IS_PARTNER_WALLET", True)
    app = FastAPI()
    app.include_router(wallet.router)
    app.dependency_overrides[wallet.require_customer] = lambda: SimpleNamespace(
        id=73, email="customer@example.test", full_name="Test Customer",
        type="pf", role="customer",
    )
    app.dependency_overrides[wallet.get_db] = lambda: None
    with TestClient(app) as test_client:
        yield test_client


def assert_error_response(response, endpoint, original_error):
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["service"] == "aurea-wallet"
    metadata = payload["wallet"]
    key = "provider_adapter_error" if endpoint == "account-status" else "adapter_error"
    assert key in metadata
    assert metadata[key] == "partner_adapter_unavailable"
    assert original_error not in response.text
    assert "SENTINEL" not in response.text
    assert metadata["provider"] == "not_configured"
    assert metadata["mode"] == "partner"
    assert metadata["real_money_enabled"] is False
    if endpoint == "structured-balance":
        assert payload["balance"] == {
            "available": "0.00", "blocked": "0.00", "pending": "0.00",
            "currency": "BRL",
        }
    if endpoint == "structured-statement":
        assert payload["statement"] == {
            "items": [], "count": 0, "limit": 50, "currency": "BRL",
        }


@pytest.mark.parametrize("endpoint", ENDPOINTS)
@pytest.mark.parametrize("error_text", ERRORS)
def test_adapter_failure_response(client, monkeypatch, endpoint, error_text):
    def fail(**_kwargs):
        raise RuntimeError(error_text)

    target = (
        "get_partner_wallet_balance"
        if endpoint == "structured-balance" else "get_partner_adapter"
    )
    monkeypatch.setattr(wallet, target, fail)
    response = client.get(f"/api/v1/wallet/{endpoint}")
    assert_error_response(response, endpoint, error_text)


def test_structured_statement_database_failure_response(client, monkeypatch):
    error_text = "SENTINEL_DB_PASSWORD=private-3k; SELECT internal_credentials"

    class FailingDb:
        def query(self, _model):
            raise SQLAlchemyError(error_text)

    monkeypatch.setattr(
        wallet, "get_partner_adapter", lambda: SimpleNamespace(provider_name="sandbox")
    )
    monkeypatch.setattr(wallet, "get_partner_wallet_statement", lambda **_kwargs: [])
    client.app.dependency_overrides[wallet.get_db] = lambda: FailingDb()
    response = client.get("/api/v1/wallet/structured-statement")
    assert_error_response(response, "structured-statement", error_text)
