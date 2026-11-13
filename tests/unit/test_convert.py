"""RISK-020 (MT5 float -> Decimal boundary), RISK-021 (decimal context), RISK-024 (Decimal -> MT5 float)."""

from decimal import Decimal, FloatOperation, localcontext

import pytest

from goldbot.core.convert import (
    DECIMAL_CONTEXT,
    MONEY_MINOR_UNIT,
    ConversionError,
    require_decimal,
    to_decimal,
    to_mt5_float,
)

# --- RISK-021: decimal context -------------------------------------------------------------


def test_context_has_precision_28() -> None:
    assert DECIMAL_CONTEXT.prec == 28


def test_context_traps_float_operation() -> None:
    assert DECIMAL_CONTEXT.traps[FloatOperation]


def test_context_raises_on_decimal_from_float() -> None:
    with localcontext(DECIMAL_CONTEXT), pytest.raises(FloatOperation):
        Decimal(1.1)  # the very construction RISK-020 forbids


def test_context_raises_on_mixed_float_comparison() -> None:
    with localcontext(DECIMAL_CONTEXT), pytest.raises(FloatOperation):
        _ = Decimal("1") < 1.0  # type: ignore[operator]


# --- RISK-020: to_decimal ----------------------------------------------------------------


def test_uses_shortest_repr_not_binary_expansion() -> None:
    d = to_decimal(1.1, "PRICE", digits=1)
    assert d == Decimal("1.1")
    assert str(d) == "1.1"


def test_money_quantized_to_minor_unit() -> None:
    assert MONEY_MINOR_UNIT == Decimal("0.01")
    d = to_decimal(10000.0, "MONEY")
    assert str(d) == "10000.00"


def test_money_float_noise_removed() -> None:
    assert str(to_decimal(0.1 + 0.2, "MONEY")) == "0.30"


def test_int_input_accepted() -> None:
    assert str(to_decimal(10000, "MONEY")) == "10000.00"


def test_price_quantized_to_symbol_digits() -> None:
    assert str(to_decimal(4046.12, "PRICE", digits=2)) == "4046.12"
    assert str(to_decimal(4046.1, "PRICE", digits=2)) == "4046.10"
    assert str(to_decimal(4046.0, "PRICE", digits=0)) == "4046"


def test_volume_quantized_to_volume_step_decimals() -> None:
    assert str(to_decimal(0.01, "VOLUME", volume_step=Decimal("0.01"))) == "0.01"
    assert str(to_decimal(1.0, "VOLUME", volume_step=Decimal("0.01"))) == "1.00"


@pytest.mark.parametrize(
    "bad",
    [None, float("nan"), float("inf"), float("-inf"), "1.0", b"1", True, False, Decimal("1"), object(), [1.0]],
)
def test_rejects_none_nan_inf_and_non_numeric(bad: object) -> None:
    with pytest.raises(ConversionError):
        to_decimal(bad, "MONEY")


def test_rejects_value_too_large_for_context() -> None:
    with pytest.raises(ConversionError):
        to_decimal(1e300, "MONEY")


def test_conversion_error_is_value_error() -> None:
    assert issubclass(ConversionError, ValueError)


def test_price_requires_digits() -> None:
    with pytest.raises(ValueError, match="digits"):
        to_decimal(1.0, "PRICE")


@pytest.mark.parametrize("digits", [-1, True])
def test_price_rejects_invalid_digits(digits: int) -> None:
    with pytest.raises(ValueError, match="digits"):
        to_decimal(1.0, "PRICE", digits=digits)


@pytest.mark.parametrize("step", [None, Decimal("0"), Decimal("-0.01"), Decimal("NaN")])
def test_volume_requires_positive_step(step: Decimal | None) -> None:
    with pytest.raises(ValueError, match="volume_step"):
        to_decimal(0.01, "VOLUME", volume_step=step)


def test_unknown_kind_rejected() -> None:
    with pytest.raises(ValueError, match="kind"):
        to_decimal(1.0, "LOTS")  # type: ignore[arg-type]


# --- RISK-024: to_mt5_float ----------------------------------------------------------------


def test_to_mt5_float_is_float_of_str() -> None:
    f = to_mt5_float(Decimal("4046.12"))
    assert type(f) is float
    assert f == 4046.12


def test_to_mt5_float_handles_exponent_form() -> None:
    assert to_mt5_float(Decimal("1E+2")) == 100.0


def test_to_mt5_float_rejects_float() -> None:
    with pytest.raises(FloatOperation):
        to_mt5_float(4046.12)  # type: ignore[arg-type]


@pytest.mark.parametrize("bad", [Decimal("NaN"), Decimal("Infinity"), Decimal("-Infinity")])
def test_to_mt5_float_rejects_non_finite(bad: Decimal) -> None:
    with pytest.raises(ValueError):
        to_mt5_float(bad)


# --- require_decimal (shared runtime guard) ------------------------------------------------


def test_require_decimal_passes_finite_decimal() -> None:
    d = Decimal("1.5")
    assert require_decimal(d, "x") is d


def test_require_decimal_float_raises_float_operation() -> None:
    with pytest.raises(FloatOperation, match="x"):
        require_decimal(1.5, "x")


@pytest.mark.parametrize("bad", [1, True, "1.5", None])
def test_require_decimal_other_types_raise_type_error(bad: object) -> None:
    with pytest.raises(TypeError, match="x"):
        require_decimal(bad, "x")


def test_require_decimal_rejects_nan() -> None:
    with pytest.raises(ValueError, match="x"):
        require_decimal(Decimal("NaN"), "x")
