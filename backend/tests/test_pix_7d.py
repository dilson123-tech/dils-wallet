import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_pix_7d_contract():
    response = client.get("/api/v1/pix/7d")
    assert response.status_code == 200

    data = response.json()

    # Deve conter chave principal
    assert "ultimos_7d" in data

    pontos = data["ultimos_7d"]

    # Deve sempre ter 7 dias
    assert isinstance(pontos, list)
    assert len(pontos) == 7

    for dia in pontos:
        assert "dia" in dia
        assert "entradas" in dia
        assert "saidas" in dia
        assert "saldo_dia" in dia

        assert isinstance(dia["dia"], str)
        assert isinstance(dia["entradas"], (int, float))
        assert isinstance(dia["saidas"], (int, float))
        assert isinstance(dia["saldo_dia"], (int, float))
