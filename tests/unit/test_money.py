"""RISK-023 (Money type), DATA-004 (decimal-string JSON form), CGV-03 (labelled display conversion)."""

import dataclasses
from decimal import Decimal, FloatOperation

import pytest

from goldbot.core.money import CurrencyMismatchError, Money, convert_display


def usc(s: str) -> Money:
    return Money(Decimal(s), "USC")


def usd(s: str) -> Money:
    return Money(Decimal(s), "USD")


# --- construction ----------------------------------------------------------------------------


def test_construct_holds_amount_and_currency() -> None:
    m = usc("24.30")
    assert m.amount == Decimal("24.30")
    assert m.currency == "USC"


def test_float_amount_raises_float_operation() -> None:
    with pytest.raises(FloatOperation):
        Money(24.3, "USC")  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [24, "24.30", None, True])
def test_non_decimal_amount_raises_type_error(bad: object) -> None:
    with pytest.raises(TypeError):
        Money(bad, "USC")  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [Decimal("NaN"), Decimal("Infinity"), Decimal("sNaN")])
def test_non_finite_amount_rejected(bad: Decimal) -> None:
    with pytest.raises(ValueError):
        Money(bad, "USC")


@pytest.mark.parametrize("bad", ["EUR", "usc", "", None, "USCX"])
def test_unknown_currency_rejected(bad: object) -> None:
    with pytest.raises(ValueError, match="currency"):
        Money(Decimal("1"), bad)  # type: ignore[arg-type]


def test_money_is_frozen() -> None:
    m = usc("1.00")
    with pytest.raises(dataclasses.FrozenInstanceError):
        m.amount = Decimal("2.00")  # type: ignore[misc]


def test_money_is_hashable_and_equal_by_value() -> None:
    assert {usc("1.00"), usc("1.00")} == {usc("1.00")}


# --- arithmetic within one currency -----------------------------------------------------------


def test_add_same_currency() -> None:
    assert usc("24.00") + usc("0.30") == usc("24.30")


def test_sub_same_currency() -> None:
    assert usc("25.00") - usc("24.30") == usc("0.70")


def test_negation() -> None:
    assert -usc("24.30") == usc("-24.30")


def test_ordering_same_currency() -> None:
    a, b = usc("22.50"), usc("24.30")
    assert a < b
    assert a <= b
    assert b > a
    assert b >= a
    assert a <= usc("22.50")
    assert a >= usc("22.50")


# --- cross-currency: always an error (GV-06 also in golden) ----------------------------------


@pytest.mark.parametrize(
    "op",
    [
        lambda a, b: a + b,
        lambda a, b: a - b,
        lambda a, b: a < b,
        lambda a, b: a <= b,
        lambda a, b: a > b,
        lambda a, b: a >= b,
    ],
)
def test_cross_currency_operation_raises(op) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(CurrencyMismatchError):
        op(usc("1.00"), usd("1.00"))


def test_cross_currency_equality_is_false_not_error() -> None:
    assert usc("1.00") != usd("1.00")


@pytest.mark.parametrize("other", [Decimal("1.00"), 1, 1.0])
def test_arithmetic_with_non_money_is_type_error(other: object) -> None:
    with pytest.raises(TypeError):
        _ = usc("1.00") + other  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = usc("1.00") - other  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = usc("1.00") < other  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = usc("1.00") <= other  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = usc("1.00") > other  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = usc("1.00") >= other  # type: ignore[operator]


def test_currency_mismatch_error_names_both_currencies() -> None:
    with pytest.raises(CurrencyMismatchError, match=r"USC.*USD"):
        _ = usc("1.00") + usd("1.00")


# --- JSON form (DATA-004) --------------------------------------------------------------------


def test_to_json_is_decimal_string_and_currency() -> None:
    assert usc("-24.30").to_json() == {"amount": "-24.30", "currency": "USC"}


def test_to_json_never_uses_exponent_notation() -> None:
    assert Money(Decimal("1E+2"), "USD").to_json()["amount"] == "100"
    assert Money(Decimal("0E-8"), "USD").to_json()["amount"] == "0.00000000"


def test_json_round_trip_exact() -> None:
    m = usc("10000.00")
    back = Money.from_json(m.to_json())
    assert back == m
    assert str(back.amount) == "10000.00"


def test_from_json_float_amount_raises_float_operation() -> None:
    with pytest.raises(FloatOperation):
        Money.from_json({"amount": 24.3, "currency": "USC"})


@pytest.mark.parametrize("amount", [24, None, True])
def test_from_json_non_string_amount_type_error(amount: object) -> None:
    with pytest.raises(TypeError):
        Money.from_json({"amount": amount, "currency": "USC"})


@pytest.mark.parametrize("amount", ["1E+2", " 1.00", "1.", ".5", "01.00", "+1.00", "NaN", "Infinity", "", "1" * 65])
def test_from_json_rejects_non_schema_strings(amount: str) -> None:
    with pytest.raises(ValueError, match="amount"):
        Money.from_json({"amount": amount, "currency": "USC"})


@pytest.mark.parametrize(
    "data",
    [{"amount": "1.00"}, {"currency": "USC"}, {"amount": "1.00", "currency": "USC", "extra": "x"}],
)
def test_from_json_requires_exact_keys(data: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        Money.from_json(data)


def test_from_json_rejects_unknown_currency() -> None:
    with pytest.raises(ValueError, match="currency"):
        Money.from_json({"amount": "1.00", "currency": "EUR"})


# --- display-only conversion (RISK-023, CENT-011, CGV-03) ------------------------------------


def test_convert_display_usc_to_usd() -> None:
    assert convert_display(usc("-24.30"), rate_source="ACCOUNT_DEFINITION") == usd("-0.243")


def test_convert_display_usd_to_usc() -> None:
    assert convert_display(usd("100.00"), rate_source="ACCOUNT_DEFINITION") == usc("10000.00")


def test_convert_display_requires_account_definition_rate_source() -> None:
    with pytest.raises(ValueError, match="rate_source"):
        convert_display(usc("1.00"), rate_source="LIVE_FX")  # type: ignore[arg-type]
