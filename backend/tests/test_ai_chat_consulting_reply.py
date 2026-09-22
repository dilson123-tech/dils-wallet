import os

os.environ.setdefault("SECRET_KEY", "ai-chat-consulting-reply-test-secret")
os.environ.setdefault("JWT_SECRET", os.environ["SECRET_KEY"])

import pytest

from app.api.v1.routes.ai_chat import _ia3_build_consulting_reply

_FORBIDDEN = ["🟢", "🟡", "🔴", "Nível", "Alerta vermelho", "Resultado do mês", "Entradas - Saídas"]


def _assert_no_fabricated_conclusion(reply: str):
    for token in _FORBIDDEN:
        assert token not in reply
    low = reply.lower()
    assert "nan" not in low
    assert "inf" not in low.replace("informa", "")


def test_payload_real_atual_sem_dados_mensais():
    r = _ia3_build_consulting_reply(
        {"saldo": 1234.5, "source": "real", "ultimos_7d": [{"dia": "2026-01-01", "entradas": 5.0, "saidas": 1.0, "saldo_dia": 4.0}]}
    )
    _assert_no_fabricated_conclusion(r)
    assert "indisponível" in r
    assert "R$ 1234,50" in r
    assert "Entradas no mês via PIX" not in r


@pytest.mark.parametrize(
    "payload",
    [
        {"saldo": 0.0, "source": "lab", "ultimos_7d": []},
        {"saldo": 500.0, "source": "lab"},
        None,
        {},
        {"source": "real"},
        {"saldo": "123", "source": "real"},
        {"saldo": True, "source": "real"},
        {"saldo": float("nan"), "source": "real"},
        {"saldo": float("inf"), "source": "real"},
        {"saldo": float("-inf"), "source": "real"},
        {"saldo": None, "source": "real"},
    ],
)
def test_falha_fechado(payload):
    r = _ia3_build_consulting_reply(payload)
    _assert_no_fabricated_conclusion(r)
    assert "Não consegui confirmar" in r
    assert "R$" not in r


def test_campos_mensais_no_payload_sao_ignorados():
    r = _ia3_build_consulting_reply(
        {"saldo": 10.0, "source": "real", "entradas_mes": 100, "saidas_mes": 5000}
    )
    _assert_no_fabricated_conclusion(r)
    assert "5.000" not in r
