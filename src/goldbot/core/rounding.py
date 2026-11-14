"""Rounding table and price rules (TRADING_RISK_SPEC RISK-013, RISK-022, RISK-025)."""

from __future__ import annotations

from decimal import ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, ROUND_UP, Decimal
from typing import Literal

from goldbot.core.convert import DECIMAL_CONTEXT, MONEY_MINOR_UNIT, require_decimal
from goldbot.core.money import Money

Direction = Literal["UP", "DOWN"]
_INTEGRAL_ROUNDING = {"UP": ROUND_CEILING, "DOWN": ROUND_FLOOR}


class OffTickError(ValueError):
    """An order price that is not a multiple of tick_size (RISK-022, GV-31)."""

    reason = "OFF_TICK"

    def __init__(self, price: Decimal, tick_size: Decimal) -> None:
        super().__init__(f"OFF_TICK: price {price} is not a multiple of tick_size {tick_size}")
        self.price = price
        self.tick_size = tick_size


def _positive(value: object, name: str) -> Decimal:
    d = require_decimal(value, name)
    if d <= 0:
        raise ValueError(f"{name} must be > 0, got {d}")
    return d


def is_on_grid(value: Decimal, grid: Decimal) -> bool:
    return DECIMAL_CONTEXT.remainder(require_decimal(value, "value"), _positive(grid, "grid")) == 0


def round_volume_down(raw: Decimal, step: Decimal) -> Decimal:
    """Floor to a multiple of volume_step; never up (RISK-013, GV-03). 0 means skip, decided by the caller."""
    raw = require_decimal(raw, "raw")
    step = _positive(step, "step")
    if raw < 0:
        raise ValueError(f"raw volume must be >= 0, got {raw}")
    return DECIMAL_CONTEXT.multiply(DECIMAL_CONTEXT.divide_int(raw, step), step)


def order_price(price: Decimal, tick_size: Decimal, quantize: Direction | None = None) -> Decimal:
    """Return an order price on the tick grid. Off-grid: OFF_TICK unless the strategy opted in (RISK-025)."""
    if quantize is not None and quantize not in _INTEGRAL_ROUNDING:
        raise ValueError(f"quantize must be UP, DOWN or None, got {quantize!r}")
    price = _positive(price, "price")
    tick_size = _positive(tick_size, "tick_size")
    if is_on_grid(price, tick_size):
        return price
    if quantize is None:
        raise OffTickError(price, tick_size)
    ticks = DECIMAL_CONTEXT.divide(price, tick_size).to_integral_value(
        rounding=_INTEGRAL_ROUNDING[quantize], context=DECIMAL_CONTEXT
    )
    return DECIMAL_CONTEXT.multiply(ticks, tick_size)


def sl_direction(side: Literal["BUY", "SELL"]) -> Direction:
    """SL quantization direction that never increases the loss at SL (RISK-025 step 1)."""
    if side == "BUY":
        return "UP"
    if side == "SELL":
        return "DOWN"
    raise ValueError(f"side must be BUY or SELL, got {side!r}")


def _to_minor_unit(m: Money, rounding: str) -> Money:
    return Money(m.amount.quantize(MONEY_MINOR_UNIT, rounding=rounding, context=DECIMAL_CONTEXT), m.currency)


def round_budget(m: Money) -> Money:
    """Conservative: toward minus infinity, so a budget never rounds up (also for negatives)."""
    return _to_minor_unit(m, ROUND_FLOOR)


def round_loss(m: Money) -> Money:
    """Conservative: away from zero, so a modelled loss never shrinks."""
    return _to_minor_unit(m, ROUND_UP)


def round_display(m: Money) -> Money:
    return _to_minor_unit(m, ROUND_HALF_EVEN)
