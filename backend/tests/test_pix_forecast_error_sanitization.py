import os
from types import SimpleNamespace

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.routes import pix

SENTINEL = "SENTINEL_PRIVATE_TOKEN=secret-3n; postgres://private-db/internal"


class ExplodingDb:
    def query(self, *args, **kwargs):
        raise RuntimeError(SENTINEL)


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(pix.router)
    app.dependency_overrides[pix.require_customer] = lambda: SimpleNamespace(
        id=73, email="customer@example.test", role="customer",
    )
    app.dependency_overrides[pix.get_db] = lambda: ExplodingDb()
    with TestClient(app) as test_client:
        yield test_client


def test_forecast_failure_does_not_leak_internal_error(client):
    response = client.get("/api/v1/pix/forecast")

    assert response.status_code == 200
    payload = response.json()
    assert payload["nivel_risco"] == "indisponivel"
    assert "debug_error" not in payload
    assert "SENTINEL" not in response.text
    assert "postgres://" not in response.text
    assert "RuntimeError" not in response.text

    for key in ("saldo_atual", "entradas_mes", "saidas_mes", "previsao_fim_mes"):
        assert payload[key] == 0.0
    assert isinstance(payload["analise"], str) and payload["analise"]
    assert isinstance(payload["recomendacoes"], list) and payload["recomendacoes"]
    assert set(payload) == {
        "saldo_atual", "entradas_mes", "saidas_mes", "previsao_fim_mes",
        "nivel_risco", "analise", "recomendacoes",
    }
