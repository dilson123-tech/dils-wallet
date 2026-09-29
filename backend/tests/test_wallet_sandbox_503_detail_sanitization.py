"""
Pendência 14 do handoff: os 503 do sandbox em
backend/app/api/v1/routes/wallet.py não podem devolver ao cliente o texto
da exceção original (ex.: WALLET_PARTNER_PROVIDER, tokens, DSNs). O status
continua 503 e o detail passa a ser uma mensagem fixa.
"""
import os
from types import SimpleNamespace

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.v1.routes import wallet
from app.core.rate_limit import limiter
from app.partner.asaas_config import AsaasConfigError


SENTINEL = "SENTINEL_PRIVATE_TOKEN=DO_NOT_LEAK"

ADAPTER_CASES = [
    (
        "post",
        "/api/v1/wallet/pix/sandbox-payment",
        {"amount": "10.00"},
        "Adapter financeiro indisponível para sandbox.",
    ),
    (
        "post",
        "/api/v1/wallet/pix/sandbox-webhook",
        {"provider_reference": "sandbox-ref-1"},
        "Adapter financeiro indisponível para webhook sandbox.",
    ),
    (
        "get",
        "/api/v1/wallet/pix/sandbox-reconciliation/sandbox-ref-1",
        None,
        "Adapter financeiro indisponível para reconciliação sandbox.",
    ),
    (
        "get",
        "/api/v1/wallet/pix/sandbox-audit-history",
        None,
        "Adapter financeiro indisponível para histórico sandbox.",
    ),
]

ASAAS_CONFIG_DETAIL = "Configuração Asaas Sandbox inválida para webhook."
ASAAS_CONFIG_CASES = [
    ("post", "/api/v1/partners/asaas/webhooks/sandbox", {}),
    ("get", "/api/v1/partners/asaas/webhooks/sandbox/audit-history", None),
]


@pytest.fixture
def client():
    limiter.reset()
    app = FastAPI()
    app.include_router(wallet.router)
    app.dependency_overrides[wallet.require_customer] = lambda: SimpleNamespace(
        id=73, email="customer@example.test", full_name="Test Customer",
        type="pf", role="customer",
    )
    app.dependency_overrides[wallet.get_db] = lambda: None
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        limiter.reset()


def _request(client, method, path, body):
    if method == "post":
        return client.post(path, json=body)
    return client.get(path)


def _assert_sanitized_503(response, expected_detail):
    assert response.status_code == 503
    assert response.json() == {"detail": expected_detail}
    assert SENTINEL not in response.text
    assert "SENTINEL" not in response.text


@pytest.mark.parametrize("method,path,body,expected_detail", ADAPTER_CASES)
def test_adapter_failure_returns_sanitized_503(
    client, monkeypatch, method, path, body, expected_detail,
):
    def fail():
        raise RuntimeError(SENTINEL)

    monkeypatch.setattr(wallet, "get_partner_adapter", fail)

    response = _request(client, method, path, body)

    _assert_sanitized_503(response, expected_detail)


@pytest.mark.parametrize("method,path,body", ASAAS_CONFIG_CASES)
def test_asaas_config_error_returns_sanitized_503(
    client, monkeypatch, method, path, body,
):
    def fail():
        raise AsaasConfigError(SENTINEL)

    monkeypatch.setattr(wallet, "load_asaas_sandbox_config", fail)

    response = _request(client, method, path, body)

    _assert_sanitized_503(response, ASAAS_CONFIG_DETAIL)


def test_asaas_config_error_keeps_exception_chain_server_side(monkeypatch):
    original = AsaasConfigError(SENTINEL)

    def fail():
        raise original

    monkeypatch.setattr(wallet, "load_asaas_sandbox_config", fail)

    with pytest.raises(HTTPException) as captured:
        wallet._asaas_sandbox_webhook_config()

    assert captured.value.status_code == 503
    assert captured.value.__cause__ is original
    assert SENTINEL not in str(captured.value.detail)
