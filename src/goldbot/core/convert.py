"""The float <-> Decimal boundary (TRADING_RISK_SPEC RISK-020, RISK-021, RISK-024).

`_exact()` holds the project's only `Decimal(repr(x))` call; the GV-26 static test enforces that.
"""

from __future__ import annotations

import math
import re
from decimal import (
    ROUND_HALF_EVEN,
    Context,
    Decimal,
    DivisionByZero,
    FloatOperation,
    Inexact,
    InvalidOperation,
    Overflow,
)
from typing import Literal

Kind = Literal["PRICE", "VOLUME", "MONEY"]

# RISK-021: prec=28, FloatOperation trapped so any float mixing raises.
DECIMAL_CONTEXT = Context(
    prec=28,
    rounding=ROUND_HALF_EVEN,
    traps=[InvalidOperation, DivisionByZero, Overflow, FloatOperation],
)
_EXACT_CONTEXT = DECIMAL_CONTEXT.copy()
_EXACT_CONTEXT.traps[Inexact] = True

MONEY_MINOR_UNIT = Decimal("0.01")

# schemas/common.schema.json $defs/decimal (DATA-004).
_DECIMAL_TEXT = re.compile(r"(-?)(0|[1-9][0-9]*)(?:\.([0-9]+))?")
_DECIMAL_TEXT_MAX_LEN = 64


class ConversionError(ValueError):
    """An MT5 value that cannot be converted safely; callers fail closed (RISK-020 step 1)."""


def _exact(x: int | float) -> Decimal:
    return Decimal(repr(x))  # the sanctioned site: shortest round-trip text, never the binary expansion


def _places(step: Decimal) -> int:
    exponent = step.normalize().as_tuple().exponent
    assert isinstance(exponent, int)  # step is finite, checked by the caller
    return max(0, -exponent)


def require_decimal(value: object, name: str) -> Decimal:
    """Return `value` if it is a finite Decimal; a float raises FloatOperation (RISK-021)."""
    if isinstance(value, float):
        raise FloatOperation(f"{name}: float given where Decimal is required")
    if not isinstance(value, Decimal):
        raise TypeError(f"{name}: expected Decimal, got {type(value).__name__}")
    if not value.is_finite():
        raise ValueError(f"{name}: must be finite, got {value}")
    return value


def to_decimal(
    x: object,
    kind: Kind,
    *,
    digits: int | None = None,
    volume_step: Decimal | None = None,
) -> Decimal:
    """Convert one MT5 number to Decimal and quantize it by `kind` (RISK-020)."""
    if kind == "PRICE":
        if not isinstance(digits, int) or isinstance(digits, bool) or digits < 0:
            raise ValueError(f"PRICE needs digits >= 0, got {digits!r}")
        quantum = Decimal(1).scaleb(-digits)
    elif kind == "VOLUME":
        if volume_step is None or not volume_step.is_finite() or volume_step <= 0:
            raise ValueError(f"VOLUME needs a positive volume_step, got {volume_step!r}")
        quantum = Decimal(1).scaleb(-_places(volume_step))
    elif kind == "MONEY":
        quantum = MONEY_MINOR_UNIT
    else:
        raise ValueError(f"unknown kind {kind!r}")

    if isinstance(x, bool) or not isinstance(x, int | float):
        raise ConversionError(f"{kind}: not a number: {type(x).__name__}")
    if isinstance(x, float) and not math.isfinite(x):
        raise ConversionError(f"{kind}: non-finite value {x!r}")
    try:
        d = _exact(x).quantize(quantum, context=DECIMAL_CONTEXT)
    except InvalidOperation as exc:
        raise ConversionError(f"{kind}: {x!r} does not fit the decimal context") from exc
    if volume_step is not None and d % volume_step != 0:
        raise ConversionError(f"VOLUME {d} is not a multiple of volume_step {volume_step}")
    return d


def parse_decimal(text: object, name: str) -> Decimal:
    """Parse a DATA-004 decimal string exactly; never rounds, never accepts a float."""
    if isinstance(text, float):
        raise FloatOperation(f"{name}: float given where a decimal string is required")
    if not isinstance(text, str):
        raise TypeError(f"{name}: expected a decimal string, got {type(text).__name__}")
    match = _DECIMAL_TEXT.fullmatch(text) if len(text) <= _DECIMAL_TEXT_MAX_LEN else None
    if match is None:
        raise ValueError(f"{name}: not a schema decimal string: {text[:70]!r}")
    sign, whole, fraction = match.groups()
    fraction = fraction or ""
    try:
        d = _exact(int(whole + fraction)).scaleb(-len(fraction), context=_EXACT_CONTEXT)
    except Inexact as exc:
        raise ValueError(f"{name}: more than {DECIMAL_CONTEXT.prec} significant digits") from exc
    return d.copy_negate() if sign else d


def to_mt5_float(d: Decimal) -> float:
    """Decimal -> float for a value sent to MT5, after quantization (RISK-024)."""
    return float(str(require_decimal(d, "mt5 value")))
