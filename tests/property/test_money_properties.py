"""Property tests for RISK-020/021/023/024 and RISK-013/022."""

import math
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from goldbot.core.convert import ConversionError, to_decimal, to_mt5_float
from goldbot.core.money import CurrencyMismatchError, Money
from goldbot.core.rounding import is_on_grid, round_volume_down

D = Decimal
STEPS = st.sampled_from([D("0.01"), D("0.1"), D("0.001"), D("0.05"), D("1")])
# Integer coefficients scaled by a fixed exponent: exact decimals, no float anywhere.
AMOUNTS = st.integers(min_value=-(10**12), max_value=10**12).map(lambda n: D(n).scaleb(-2))
CURRENCIES = st.sampled_from(["USC", "USD"])


@given(ticks=st.integers(min_value=0, max_value=10**9), digits=st.integers(min_value=0, max_value=5))
def test_price_round_trips_mt5_float_decimal_mt5_float(ticks: int, digits: int) -> None:
    exact = D(ticks).scaleb(-digits)
    mt5_value = float(str(exact))  # what the terminal would hand us for this on-grid price
    d = to_decimal(mt5_value, "PRICE", digits=digits)
    assert d == exact
    assert d.as_tuple().exponent == -digits
    assert to_mt5_float(d) == mt5_value


@given(x=st.floats(allow_nan=True, allow_infinity=True))
def test_any_float_is_finite_decimal_or_conversion_error(x: float) -> None:
    try:
        d = to_decimal(x, "MONEY")
    except ConversionError:
        assert not math.isfinite(x) or abs(x) >= 1e25
        return
    assert d.is_finite()
    assert d == D(repr(x)).quantize(D("0.01"))


@given(
    raw=st.integers(min_value=0, max_value=10**8).map(lambda n: D(n).scaleb(-6)),
    step=STEPS,
)
def test_volume_round_down_never_exceeds_input_and_is_on_grid(raw: Decimal, step: Decimal) -> None:
    v = round_volume_down(raw, step)
    assert v <= raw
    assert raw - v < step
    assert is_on_grid(v, step)


@given(a=AMOUNTS, b=AMOUNTS, c=AMOUNTS, cur=CURRENCIES)
def test_add_is_associative_within_one_currency(a: Decimal, b: Decimal, c: Decimal, cur: str) -> None:
    ma, mb, mc = Money(a, cur), Money(b, cur), Money(c, cur)  # type: ignore[arg-type]
    assert (ma + mb) + mc == ma + (mb + mc)


@given(a=AMOUNTS, b=AMOUNTS, cur=CURRENCIES)
def test_sub_inverts_add_within_one_currency(a: Decimal, b: Decimal, cur: str) -> None:
    ma, mb = Money(a, cur), Money(b, cur)  # type: ignore[arg-type]
    assert (ma + mb) - mb == ma
    assert ma - ma == Money(D("0.00"), cur)  # type: ignore[arg-type]


@given(a=AMOUNTS, b=AMOUNTS)
def test_mixed_currency_always_raises(a: Decimal, b: Decimal) -> None:
    x, y = Money(a, "USC"), Money(b, "USD")
    for op in (
        lambda: x + y,
        lambda: y - x,
        lambda: x < y,
        lambda: x <= y,
        lambda: y > x,
        lambda: y >= x,
    ):
        with pytest.raises(CurrencyMismatchError):
            op()


@given(a=AMOUNTS, cur=CURRENCIES)
def test_json_round_trip_is_exact(a: Decimal, cur: str) -> None:
    m = Money(a, cur)  # type: ignore[arg-type]
    back = Money.from_json(m.to_json())
    assert back == m
    assert back.to_json() == m.to_json()
