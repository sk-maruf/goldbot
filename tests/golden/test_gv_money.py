"""Golden vectors touching money, conversion and rounding (TRADING_RISK_SPEC §11).

Implemented here: GV-06, GV-25, plus the rounding parts of GV-03 (volume floor), GV-31 (OFF_TICK)
and GV-32 (quantization direction). GV-26 (static `Decimal(x)` lint) lives in
tests/security/test_no_decimal_float.py. The risk recalculation and recording parts of GV-32 belong
to the RiskEngine (M3).
"""

from decimal import Decimal, FloatOperation

import pytest

from goldbot.core.money import CurrencyMismatchError, Money
from goldbot.core.rounding import OffTickError, order_price, round_volume_down, sl_direction


def test_gv06_usc_plus_usd_raises_currency_mismatch() -> None:
    with pytest.raises(CurrencyMismatchError):
        _ = Money(Decimal("1.00"), "USC") + Money(Decimal("1.00"), "USD")


def test_gv25_float_passed_into_money_raises_float_operation() -> None:
    with pytest.raises(FloatOperation):
        Money(24.30, "USC")  # type: ignore[arg-type]


def test_gv25_float_in_json_money_raises_float_operation() -> None:
    with pytest.raises(FloatOperation):
        Money.from_json({"amount": 24.30, "currency": "USC"})


def test_gv03_raw_volume_0_0203_floors_to_0_02() -> None:
    assert round_volume_down(Decimal("0.0203"), Decimal("0.01")) == Decimal("0.02")


def test_gv31_off_tick_sl_without_opt_in_rejected() -> None:
    with pytest.raises(OffTickError) as exc:
        order_price(Decimal("4046.005"), Decimal("0.01"))
    assert exc.value.reason == "OFF_TICK"


@pytest.mark.parametrize(
    ("side", "entry", "sl", "expected"),
    [
        ("BUY", "4070.00", "4046.005", "4046.01"),  # BUY SL below entry: moved up, distance shrinks
        ("SELL", "4022.00", "4046.005", "4046.00"),  # SELL SL above entry: moved down, distance shrinks
    ],
)
def test_gv32_opt_in_quantizes_sl_away_from_extra_loss(side: str, entry: str, sl: str, expected: str) -> None:
    q = order_price(Decimal(sl), Decimal("0.01"), quantize=sl_direction(side))  # type: ignore[arg-type]
    assert q == Decimal(expected)
    assert abs(Decimal(entry) - q) < abs(Decimal(entry) - Decimal(sl))
