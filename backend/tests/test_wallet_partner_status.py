"""
Regressão: GET /api/v1/wallet/partner/status não deve retornar HTTP 500
quando WALLET_MODE=partner + WALLET_PARTNER_PROVIDER=asaas (sem Partner
Adapter registrado). HTTP 200 aqui é sucesso da consulta de diagnóstico,
não disponibilidade operacional: provider_adapter_ready=false.

Offline: nenhuma chamada externa, nenhuma operação financeira.
"""
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.routes import wallet
from app.partner import registry

PATH = "/api/v1/wallet/partner/status"


def _configure(monkeypatch, mode, provider):
    is_sandbox = mode == "partner" and provider == "sandbox"
    is_partner = mode == "partner" and not is_sandbox
    monkeypatch.setattr(registry, "WALLET_MODE", mode)
    monkeypatch.setattr(registry, "WALLET_PARTNER_PROVIDER", provider)
    monkeypatch.setattr(registry, "IS_SANDBOX_PARTNER", is_sandbox)
    monkeypatch.setattr(wallet, "WALLET_MODE", mode)
    monkeypatch.setattr(wallet, "WALLET_PARTNER_PROVIDER", provider)
    monkeypatch.setattr(wallet, "IS_PARTNER_WALLET", is_partner)


@pytest.fixture
def client():
    registry.get_partner_adapter.cache_clear()
    app = FastAPI()
    app.include_router(wallet.router)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    registry.get_partner_adapter.cache_clear()


def test_partner_asaas_without_adapter_returns_diagnostic(client, monkeypatch):
    _configure(monkeypatch, "partner", "asaas")

    # Pré-condição: o registry real ainda não tem adapter para asaas.
    with pytest.raises(RuntimeError):
        registry.get_partner_adapter()

    response = client.get(PATH)

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "service": "aurea-wallet",
        "wallet_mode": "partner",
        "provider": "asaas",
        "real_money": False,
        "provider_adapter_ready": False,
        "provider_adapter_error": "partner_adapter_unavailable",
    }


def test_demo_mode_unchanged(client, monkeypatch):
    _configure(monkeypatch, "demo", "demo")

    response = client.get(PATH)

    assert response.status_code == 200
    payload = response.json()
    assert payload["wallet_mode"] == "demo"
    assert payload["provider"] == "demo"
    assert payload["real_money"] is False
    assert payload["provider_adapter_ready"] is True
    assert payload["provider_adapter_error"] is None


def test_partner_sandbox_unchanged(client, monkeypatch):
    _configure(monkeypatch, "partner", "sandbox")

    response = client.get(PATH)

    assert response.status_code == 200
    payload = response.json()
    assert payload["wallet_mode"] == "partner"
    assert payload["provider"] == "sandbox"
    assert payload["real_money"] is False
    assert payload["provider_adapter_ready"] is True
    assert payload["provider_adapter_error"] is None


@pytest.mark.parametrize(
    "mode,provider,error",
    [
        # Erro inesperado de outro tipo, mesmo no modo partner.
        ("partner", "asaas", ValueError("unexpected")),
        # RuntimeError inesperado (mensagem diferente da do registry) no
        # próprio modo partner + asaas.
        ("partner", "asaas", RuntimeError("unexpected adapter failure")),
        # RuntimeError fora do caso conhecido (modo não-partner).
        ("demo", "demo", RuntimeError("unexpected")),
        ("partner", "sandbox", RuntimeError("unexpected")),
    ],
)
def test_unexpected_failures_propagate(client, monkeypatch, mode, provider, error):
    _configure(monkeypatch, mode, provider)

    def fail():
        raise error

    monkeypatch.setattr(wallet, "get_partner_adapter", fail)

    with pytest.raises(type(error)):
        wallet.get_wallet_partner_status()

    response = client.get(PATH)
    assert response.status_code == 500
