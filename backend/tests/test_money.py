"""Testes unitários de app.utils.money.to_money (offline, sem banco)."""
from decimal import Decimal, InvalidOperation

import pytest

from app.services.pix_service import round_pix_money
from app.utils.money import to_money


@pytest.mark.parametrize(
    "value,expected",
    [
        (Decimal("10"), "10.00"),
        (Decimal("10.1"), "10.10"),
        (Decimal("10.004"), "10.00"),
        (Decimal("10.005"), "10.01"),
        (Decimal("10.015"), "10.02"),
        (Decimal("0.005"), "0.01"),
        (Decimal("-0.005"), "-0.01"),
        (Decimal("-10.005"), "-10.01"),
        (Decimal("0"), "0.00"),
        (Decimal("123456789.995"), "123456790.00"),
        (10, "10.00"),
        (0, "0.00"),
        ("10.005", "10.01"),
        (" 2.5 ", "2.50"),
        (0.1 + 0.2, "0.30"),
        (1.005, "1.01"),  # via str: "1.005", sem erro binário
        (2.675, "2.68"),
    ],
)
def test_to_money_rounds_half_up_to_two_places(value, expected):
    result = to_money(value)
    assert isinstance(result, Decimal)
    assert str(result) == expected
    assert result.as_tuple().exponent == -2


@pytest.mark.parametrize(
    "value",
    [
        Decimal("NaN"),
        Decimal("sNaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
        float("nan"),
        float("inf"),
        float("-inf"),
        "NaN",
        "Infinity",
        "abc",
        "",
        "1,50",
        Decimal("1E+30"),  # excede a precisão do contexto ao quantizar
        True,
        False,
        None,
        [1],
        object(),
    ],
)
def test_to_money_rejects_invalid_values(value):
    with pytest.raises(ValueError):
        to_money(value)


@pytest.mark.parametrize(
    "raw",
    [
        "0", "0.01", "0.005", "0.004", "1", "1.5", "10.005", "10.015",
        "99.995", "100.00", "-0", "-0.005", "-12.345", "1234567.891",
        "0.0000001", "5E+2", "1E-10", "123456789012345.675",
    ],
)
def test_to_money_matches_round_pix_money_on_finite_decimals(raw):
    value = Decimal(raw)
    old = round_pix_money(value)
    new = to_money(value)
    assert new == old
    assert str(new) == str(old)  # str é usado no request hash do PIX
    assert new.as_tuple() == old.as_tuple()


def test_round_pix_money_differs_on_invalid_inputs():
    """
    Caracterização: round_pix_money devolve NaN para NaN e levanta
    InvalidOperation para infinito; to_money levanta ValueError. Por isso
    round_pix_money NÃO delega para to_money (preservação não é exata).
    """
    assert round_pix_money(Decimal("NaN")).is_nan()
    with pytest.raises(InvalidOperation):
        round_pix_money(Decimal("Infinity"))
    with pytest.raises(ValueError):
        to_money(Decimal("NaN"))
