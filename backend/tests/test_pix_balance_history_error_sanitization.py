"""
Pendência #5 do handoff: GET /api/v1/pix/balance e GET /api/v1/pix/history
não podem mais esconder falha de banco com 200 (saldo 0.0 "lab" / extrato
vazio). Agora respondem 503 com detail fixo, sem o texto da exceção
original, e preservam a causa via `from exc` do lado do servidor.
"""
import logging
import os
from types import SimpleNamespace

os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.v1.routes import pix


SENTINEL = "SENTINEL_PRIVATE_DSN=DO_NOT_LEAK"

BALANCE_DETAIL = "Saldo PIX indisponível no momento."
HISTORY_DETAIL = "Histórico PIX indisponível no momento."


class _BrokenSession:
    """Sessão falsa: qualquer consulta simula falha de banco."""

    def __init__(self, error):
        self.error = error

    def query(self, *args, **kwargs):
        raise self.error


def _customer():
    return SimpleNamespace(
        id=73, email="customer@example.test", full_name="Test Customer",
        type="pf", role="customer",
    )


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(pix.router)
    app.dependency_overrides[pix.require_customer] = _customer
    app.dependency_overrides[pix.get_db] = lambda: _BrokenSession(RuntimeError(SENTINEL))
    with TestClient(app) as test_client:
        yield test_client


def _assert_sanitized_503(response, expected_detail):
    assert response.status_code == 503
    assert response.json() == {"detail": expected_detail}
    assert SENTINEL not in response.text
    assert "SENTINEL" not in response.text


def test_balance_db_failure_returns_sanitized_503_without_fake_balance(client, caplog):
    with caplog.at_level(logging.ERROR, logger="aurea.pix"):
        response = client.get("/api/v1/pix/balance")

    _assert_sanitized_503(response, BALANCE_DETAIL)
    body = response.json()
    assert "saldo" not in body
    assert "source" not in body
    assert "ultimos_7d" not in body
    assert SENTINEL not in caplog.text


def test_history_db_failure_returns_sanitized_503_without_fake_empty_history(client, caplog):
    with caplog.at_level(logging.ERROR, logger="aurea.pix"):
        response = client.get("/api/v1/pix/history")

    _assert_sanitized_503(response, HISTORY_DETAIL)
    assert response.json() != []
    assert SENTINEL not in caplog.text


@pytest.mark.parametrize(
    "handler,expected_detail",
    [
        (pix.get_balance, BALANCE_DETAIL),
        (pix.get_history, HISTORY_DETAIL),
    ],
)
def test_db_failure_keeps_exception_chain_server_side(handler, expected_detail):
    original = RuntimeError(SENTINEL)

    with pytest.raises(HTTPException) as captured:
        handler(db=_BrokenSession(original), current_user=_customer())

    assert captured.value.status_code == 503
    assert captured.value.detail == expected_detail
    assert captured.value.__cause__ is original
    assert SENTINEL not in str(captured.value.detail)
