"""RISK-022 (rounding table), RISK-013 (volume rounds down), RISK-025 (opt-in price quantization)."""

from decimal import Decimal, FloatOperation

import pytest

from goldbot.core.money import Money
from goldbot.core.rounding import (
    OffTickError,
    is_on_grid,
    order_price,
    round_budget,
    round_display,
    round_loss,
    round_volume_down,
    sl_direction,
)

D = Decimal
STEP = D("0.01")
TICK = D("0.01")

# --- volume: ROUND_DOWN to volume_step (RISK-013/022) -----------------------------------------


@pytest.mark.parametrize(
    ("raw", "step", "expected"),
    [
        ("0.0203", "0.01", "0.02"),
        ("0.0299", "0.01", "0.02"),
        ("0.03", "0.01", "0.03"),
        ("0.009", "0.01", "0.00"),
        ("0", "0.01", "0.00"),
        ("1.29", "0.1", "1.2"),
        ("0.149", "0.05", "0.10"),
        ("0.15", "0.05", "0.15"),
    ],
)
def test_volume_rounds_down_to_step(raw: str, step: str, expected: str) -> None:
    got = round_volume_down(D(raw), D(step))
    assert str(got) == expected


def test_volume_never_rounds_up_even_at_half() -> None:
    assert round_volume_down(D("0.0199999"), STEP) == D("0.01")


@pytest.mark.parametrize("step", [D("0"), D("-0.01"), D("NaN")])
def test_volume_rejects_non_positive_step(step: Decimal) -> None:
    with pytest.raises(ValueError):
        round_volume_down(D("0.02"), step)


def test_volume_rejects_negative_raw() -> None:
    with pytest.raises(ValueError, match="raw"):
        round_volume_down(D("-0.01"), STEP)


def test_volume_rejects_float() -> None:
    with pytest.raises(FloatOperation):
        round_volume_down(0.0203, STEP)  # type: ignore[arg-type]
    with pytest.raises(FloatOperation):
        round_volume_down(D("0.0203"), 0.01)  # type: ignore[arg-type]


# --- grid membership (RISK-020 step 4) ---------------------------------------------------------


@pytest.mark.parametrize(
    ("value", "grid", "on"),
    [
        ("4046.12", "0.01", True),
        ("4046.125", "0.01", False),
        ("4046.15", "0.05", True),
        ("4046.12", "0.05", False),
        ("0.03", "0.01", True),
        ("0.035", "0.01", False),
    ],
)
def test_is_on_grid(value: str, grid: str, on: bool) -> None:
    assert is_on_grid(D(value), D(grid)) is on


def test_is_on_grid_rejects_bad_grid() -> None:
    with pytest.raises(ValueError):
        is_on_grid(D("1"), D("0"))


def test_is_on_grid_rejects_float() -> None:
    with pytest.raises(FloatOperation):
        is_on_grid(4046.12, TICK)  # type: ignore[arg-type]


# --- order prices: OFF_TICK unless opted in (RISK-022/025) -------------------------------------


def test_on_tick_price_passes_unchanged() -> None:
    assert order_price(D("4046.12"), TICK) == D("4046.12")


def test_off_tick_price_rejected_by_default() -> None:
    with pytest.raises(OffTickError) as exc:
        order_price(D("4046.125"), TICK)
    assert exc.value.reason == "OFF_TICK"
    assert exc.value.price == D("4046.125")
    assert exc.value.tick_size == TICK


def test_opt_in_quantize_up() -> None:
    assert str(order_price(D("4046.121"), TICK, quantize="UP")) == "4046.13"


def test_opt_in_quantize_down() -> None:
    assert str(order_price(D("4046.129"), TICK, quantize="DOWN")) == "4046.12"


def test_opt_in_on_tick_price_unchanged() -> None:
    assert str(order_price(D("4046.12"), TICK, quantize="UP")) == "4046.12"


def test_opt_in_quantize_with_coarse_tick() -> None:
    assert order_price(D("4046.12"), D("0.05"), quantize="DOWN") == D("4046.10")
    assert order_price(D("4046.12"), D("0.05"), quantize="UP") == D("4046.15")


def test_invalid_quantize_direction_rejected() -> None:
    with pytest.raises(ValueError, match="quantize"):
        order_price(D("4046.121"), TICK, quantize="NEAREST")  # type: ignore[arg-type]


@pytest.mark.parametrize("price", [D("0"), D("-1"), D("NaN")])
def test_order_price_rejects_non_positive(price: Decimal) -> None:
    with pytest.raises(ValueError):
        order_price(price, TICK)


def test_order_price_rejects_float() -> None:
    with pytest.raises(FloatOperation):
        order_price(4046.12, TICK)  # type: ignore[arg-type]


def test_off_tick_error_is_value_error() -> None:
    assert issubclass(OffTickError, ValueError)


# --- SL quantization direction: never increases the loss at SL (RISK-025 step 1) --------------


def test_sl_direction_buy_moves_sl_up_toward_entry() -> None:
    assert sl_direction("BUY") == "UP"


def test_sl_direction_sell_moves_sl_down_toward_entry() -> None:
    assert sl_direction("SELL") == "DOWN"


def test_sl_direction_rejects_unknown_side() -> None:
    with pytest.raises(ValueError, match="side"):
        sl_direction("LONG")  # type: ignore[arg-type]


# --- money rounding table (RISK-022) ------------------------------------------------------------


def test_budget_rounds_down_to_minor_unit() -> None:
    assert round_budget(Money(D("25.009"), "USC")) == Money(D("25.00"), "USC")


def test_loss_rounds_up_to_minor_unit() -> None:
    assert round_loss(Money(D("24.301"), "USC")) == Money(D("24.31"), "USC")


def test_loss_round_up_is_away_from_zero_for_negative_amounts() -> None:
    assert round_loss(Money(D("-24.301"), "USC")) == Money(D("-24.31"), "USC")


def test_display_rounds_half_even() -> None:
    assert round_display(Money(D("0.245"), "USD")) == Money(D("0.24"), "USD")
    assert round_display(Money(D("0.235"), "USD")) == Money(D("0.24"), "USD")
    assert round_display(Money(D("-0.243"), "USD")) == Money(D("-0.24"), "USD")


def test_money_rounding_keeps_currency_and_exact_minor_unit() -> None:
    got = round_budget(Money(D("25"), "USD"))
    assert got.currency == "USD"
    assert str(got.amount) == "25.00"


def test_round_budget_floors_negative_amounts():
    # A budget never rounds toward a larger value; -0.005 must not become 0.00.
    assert round_budget(Money(Decimal("-0.005"), "USC")) == Money(Decimal("-0.01"), "USC")
    assert round_budget(Money(Decimal("0.019"), "USC")) == Money(Decimal("0.01"), "USC")
