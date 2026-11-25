"""Precisão monetária canônica: Decimal com 2 casas e ROUND_HALF_UP."""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

MONEY_QUANTUM = Decimal("0.01")


def to_money(value: Decimal | int | float | str) -> Decimal:
    """
    Converte ``value`` para Decimal monetário (2 casas, ROUND_HALF_UP).

    float é convertido via ``str`` para não herdar o erro binário
    (0.1 + 0.2 -> Decimal("0.30")). Rejeita com ValueError: bool, tipos
    não suportados, strings inválidas, NaN, infinito e valores que não
    cabem na precisão do contexto decimal.
    """
    if isinstance(value, bool) or not isinstance(value, (Decimal, int, float, str)):
        raise ValueError("Valor monetário inválido.")
    try:
        amount = value if isinstance(value, Decimal) else Decimal(str(value).strip())
    except InvalidOperation:
        raise ValueError("Valor monetário inválido.") from None
    if not amount.is_finite():
        raise ValueError("Valor monetário inválido.")
    try:
        return amount.quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ValueError("Valor monetário inválido.") from None
