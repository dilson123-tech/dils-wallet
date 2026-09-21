import os

os.environ.setdefault("SECRET_KEY", "ai-chat-balance-replies-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import pytest

from app.api.v1.routes.ai_chat import (
    _build_entradas_reply,
    _build_saidas_reply,
    _build_saldo_reply,
)


def test_saldo_real_positivo():
    r = _build_saldo_reply({"saldo": 123.45, "source": "real"})
    assert "R$ 123,45" in r


def test_saldo_real_zero_explicito_e_valido():
    r = _build_saldo_reply({"saldo": 0.0, "source": "real"})
    assert "Saldo disponível agora: R$ 0,00" in r


def test_source_lab_com_zero_indisponivel():
    r = _build_saldo_reply({"saldo": 0.0, "source": "lab"})
    assert "R$ 0,00" not in r
    assert "Saldo disponível agora: indisponível" in r
    assert "valor real" not in r


@pytest.mark.parametrize(
    "payload",
    [
        {"source": "real"},
        {"saldo": None, "source": "real"},
        {"saldo": True, "source": "real"},
        {"saldo": False, "source": "real"},
        {"saldo": "abc", "source": "real"},
        {"saldo": "10.0", "source": "real"},
        {"saldo": float("nan"), "source": "real"},
        {"saldo": float("inf"), "source": "real"},
        {"saldo": float("-inf"), "source": "real"},
        {"saldo": 10.0},
        {"saldo_atual": 10.0, "source": "real"},
    ],
)
def test_saldo_invalido_indisponivel(payload):
    r = _build_saldo_reply(payload)
    assert "Saldo disponível agora: indisponível" in r
    assert "R$" not in r
    assert "valor real" not in r


def test_payload_realista_nao_usa_ultimos_7d():
    payload = {
        "saldo": 50.0,
        "source": "real",
        "ultimos_7d": [
            {"dia": "2026-09-20", "entradas": 999.0, "saidas": 888.0},
            {"dia": "2026-09-21", "entradas": 777.0, "saidas": 666.0},
        ],
    }
    for fn in (_build_saldo_reply, _build_entradas_reply, _build_saidas_reply):
        r = fn(payload)
        for n in ("999", "888", "777", "666"):
            assert n not in r
    assert "R$ 50,00" in _build_saldo_reply(payload)


@pytest.mark.parametrize("fn", [_build_entradas_reply, _build_saidas_reply])
def test_entradas_saidas_indisponiveis(fn):
    r = fn({"saldo": 10.0, "source": "real", "entradas_mes": 500.0, "saidas_mes": 200.0})
    assert "indisponível" in r
    assert "R$" not in r
    assert "500" not in r and "200" not in r


def test_saldo_nao_inventa_entradas_saidas_mensais():
    r = _build_saldo_reply(
        {"saldo": 10.0, "source": "real", "entradas_mes": 500.0, "saidas_mes": 200.0}
    )
    assert "Entradas no mês: indisponível" in r
    assert "Saídas no mês: indisponível" in r
    assert "500" not in r and "200" not in r
    assert r.count("R$") == 1
