"""FakeBroker behaviour (ADR-006): deterministic, raw MT5 shapes, scripted failure modes.

A green FakeBroker suite encodes beliefs about broker behaviour, never evidence (ADR-006, GOV-002).
"""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from goldbot.adapters import broker_port as bp
from goldbot.adapters.fake_broker import (
    Accept,
    FakeBroker,
    PartialFill,
    Reject,
    Timeout,
    load_profile,
)
from goldbot.core.clock import FakeClock

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "broker"
WED_OPEN = datetime(2026, 1, 7, 10, 0, tzinfo=UTC)  # Wednesday, inside the 00:00-20:58 session
WED_BREAK = datetime(2026, 1, 7, 21, 30, tzinfo=UTC)  # daily break 20:58-22:01
SATURDAY = datetime(2026, 1, 10, 12, 0, tzinfo=UTC)
MAGIC = 4242
TAG = "GB:ABCDEFGHIJ"  # EXE-020 shape: GB: + 10 base32 chars


def make(
    profile: str = "ILL-CENT", *, seed: int = 1, at: datetime = WED_OPEN, **overrides: Any
) -> tuple[FakeBroker, FakeClock]:
    clock = FakeClock(at)
    data = load_profile(FIXTURES / f"{profile}.json") | overrides
    return FakeBroker(data, clock, seed=seed), clock


def buy(volume: float = 0.01, comment: str = TAG) -> bp.TradeRequest:
    return {
        "action": bp.TRADE_ACTION_DEAL, "symbol": "XAUUSDc", "volume": volume, "type": bp.ORDER_TYPE_BUY,
        "price": 4070.3, "sl": 4046.3, "deviation": 20, "magic": MAGIC, "comment": comment,
    }


def close(position: int, volume: float = 0.01) -> bp.TradeRequest:
    return {
        "action": bp.TRADE_ACTION_DEAL, "symbol": "XAUUSDc", "volume": volume, "type": bp.ORDER_TYPE_SELL,
        "position": position, "deviation": 40, "magic": MAGIC,
    }


def one[T](rows: tuple[T, ...] | None) -> T:
    assert rows is not None and len(rows) == 1, rows
    return rows[0]


def window(clock: FakeClock) -> tuple[datetime, datetime]:
    now = clock.utc_now()
    return now - timedelta(hours=1), now + timedelta(hours=1)


# --- conformance -------------------------------------------------------------------------------


def test_fake_broker_conforms_to_broker_port_statically_and_at_runtime() -> None:
    broker, _ = make()
    port: bp.BrokerPort = broker  # pyright checks this assignment
    assert isinstance(port, bp.BrokerPort)
    assert port.initialize() is True


@pytest.mark.parametrize("name", ["ILL-CENT", "ILL-STD"])
def test_fixture_profiles_are_labelled_illustrative(name: str) -> None:
    raw = json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))
    assert raw["label"] == "ILLUSTRATIVE"
    broker, _ = make(name)
    assert broker.label == "ILLUSTRATIVE"


def test_unlabelled_profile_is_refused() -> None:
    data = load_profile(FIXTURES / "ILL-CENT.json")
    del data["label"]
    with pytest.raises(ValueError, match="label"):
        FakeBroker(data, FakeClock(WED_OPEN))


def test_values_are_returned_as_raw_floats() -> None:
    # RISK-020: conversion is the M2 adapter's job; the fake must exercise it.
    broker, _ = make()
    account = broker.account_info()
    symbol = broker.symbol_info("XAUUSDc")
    tick = broker.symbol_info_tick("XAUUSDc")
    result = broker.order_send(buy())
    assert account is not None and symbol is not None and tick is not None and result is not None
    for value in (account.balance, account.equity, symbol.trade_tick_value, symbol.volume_min,
                  tick.bid, tick.ask, result.price, result.volume):
        assert type(value) is float
    assert type(broker.order_calc_profit(bp.ORDER_TYPE_BUY, "XAUUSDc", 0.01, 4070.0, 4094.0)) is float
    assert type(broker.order_calc_margin(bp.ORDER_TYPE_BUY, "XAUUSDc", 0.01, 4070.0)) is float


def test_discovery_calls_return_the_profile() -> None:
    broker, _ = make()
    terminal, account, symbols = broker.terminal_info(), broker.account_info(), broker.symbols_get()
    assert terminal is not None and terminal.connected
    assert account is not None and account.currency == "USC"
    assert symbols is not None and [s.name for s in symbols] == ["XAUUSDc"]
    assert broker.symbol_select("XAUUSDc") is True
    assert broker.symbol_select("EURUSD") is False
    assert broker.symbol_info("EURUSD") is None


# --- calc functions (ILLUSTRATIVE formulas) ----------------------------------------------------


@pytest.mark.parametrize(("profile", "symbol"), [("ILL-CENT", "XAUUSDc"), ("ILL-STD", "XAUUSD")])
def test_calc_profit_is_one_unit_per_dollar_at_min_lot_in_account_currency(profile: str, symbol: str) -> None:
    # CENT_ACCOUNT_VALIDATION §4: same number, 100x different money; the currency is the account's.
    broker, _ = make(profile)
    assert broker.order_calc_profit(bp.ORDER_TYPE_BUY, symbol, 0.01, 4070.0, 4046.0) == -24.0
    assert broker.order_calc_profit(bp.ORDER_TYPE_SELL, symbol, 0.01, 4070.0, 4046.0) == 24.0


def test_calc_profit_notional_matches_the_exp_003_illustration() -> None:
    # EXP-002: notional = |profit(BUY, P -> 2P)|; EXP-003: 0.01 lot at 4,070 under ILL-CENT = 4,070 USC.
    broker, _ = make()
    assert broker.order_calc_profit(bp.ORDER_TYPE_BUY, "XAUUSDc", 0.01, 4070.0, 8140.0) == 4070.0


def test_calc_margin_is_notional_over_leverage() -> None:
    broker, _ = make()  # leverage 200 (fixture filler)
    assert broker.order_calc_margin(bp.ORDER_TYPE_BUY, "XAUUSDc", 0.01, 4070.0) == pytest.approx(20.35)


def test_calc_functions_return_none_for_an_unknown_symbol() -> None:
    broker, _ = make()
    assert broker.order_calc_profit(bp.ORDER_TYPE_BUY, "EURUSD", 0.01, 1.0, 2.0) is None
    assert broker.order_calc_margin(bp.ORDER_TYPE_BUY, "EURUSD", 0.01, 1.0) is None
    assert broker.last_error()[0] != 1


# --- fills and state consistency ---------------------------------------------------------------


def test_accepted_buy_is_consistent_across_position_order_and_deal() -> None:
    broker, clock = make()
    check = broker.order_check(buy())
    assert check is not None and check.retcode == 0
    result = broker.order_send(buy())
    assert result is not None
    assert (result.retcode, result.volume, result.price) == (bp.TRADE_RETCODE_DONE, 0.01, 4070.3)

    pos = one(broker.positions_get(symbol="XAUUSDc"))
    assert (pos.ticket, pos.identifier) == (result.order, result.order)
    assert (pos.volume, pos.price_open, pos.sl, pos.magic, pos.comment) == (0.01, 4070.3, 4046.3, MAGIC, TAG)

    order = one(broker.history_orders_get(*window(clock)))
    assert (order.ticket, order.state, order.volume_initial, order.comment) == (
        result.order, bp.ORDER_STATE_FILLED, 0.01, TAG,
    )
    deal = one(broker.history_deals_get(*window(clock)))
    assert (deal.ticket, deal.order, deal.position_id, deal.entry) == (
        result.deal, result.order, result.order, bp.DEAL_ENTRY_IN,
    )
    assert broker.orders_get() == ()  # market orders leave no active order


def test_open_position_moves_equity_and_margin() -> None:
    broker, _ = make()
    broker.order_send(buy())
    broker.set_tick(4080.0, 4080.3)
    account = broker.account_info()
    assert account is not None
    assert account.profit == pytest.approx(9.7)  # (4080.0 - 4070.3) x 1 USC per $ at 0.01 lot
    assert account.equity == pytest.approx(10009.7)
    assert account.margin == pytest.approx(20.35)  # illustrative: notional at the open price / 200, 2 digits


def test_close_by_position_ticket_books_an_out_deal_and_updates_balance() -> None:
    broker, clock = make()
    opened = broker.order_send(buy())
    assert opened is not None
    broker.set_tick(4080.0, 4080.3)
    closed = broker.order_send(close(opened.order))
    assert closed is not None and closed.retcode == bp.TRADE_RETCODE_DONE and closed.price == 4080.0
    assert broker.positions_get() == ()
    deals = broker.history_deals_get(*window(clock))
    assert deals is not None
    assert [d.entry for d in deals] == [bp.DEAL_ENTRY_IN, bp.DEAL_ENTRY_OUT]
    assert deals[1].position_id == opened.order and deals[1].profit == pytest.approx(9.7)
    account = broker.account_info()
    assert account is not None and account.balance == pytest.approx(10009.7)


def test_closing_a_missing_position_returns_position_closed() -> None:
    broker, _ = make()
    result = broker.order_send(close(999))
    assert result is not None and result.retcode == bp.TRADE_RETCODE_POSITION_CLOSED


def test_sltp_modifies_the_position_stop() -> None:
    # EXE-031 SL repair path.
    broker, _ = make()
    opened = broker.order_send(buy())
    assert opened is not None
    result = broker.order_send(
        {"action": bp.TRADE_ACTION_SLTP, "symbol": "XAUUSDc", "position": opened.order, "sl": 4050.0,
         "tp": 0.0}
    )
    assert result is not None and result.retcode == bp.TRADE_RETCODE_DONE
    pos = one(broker.positions_get(ticket=opened.order))
    assert pos.sl == 4050.0


def test_unsimulated_actions_are_rejected_as_invalid() -> None:
    broker, _ = make()
    result = broker.order_send(buy() | {"action": bp.TRADE_ACTION_PENDING})
    assert result is not None and result.retcode == bp.TRADE_RETCODE_INVALID
    assert broker.positions_get() == ()


def test_same_request_twice_opens_two_positions_mt5_has_no_idempotency() -> None:
    # EXE-002: duplicate prevention is GoldBot's job; the broker never deduplicates.
    broker, _ = make()
    broker.order_send(buy())
    broker.order_send(buy())
    assert len(broker.positions_get() or ()) == 2


# --- scripted replies --------------------------------------------------------------------------


def test_scripted_reject_returns_the_retcode_and_changes_nothing() -> None:
    broker, clock = make()
    broker.script("order_send", Reject(10004))
    result = broker.order_send(buy())
    assert result is not None and (result.retcode, result.order, result.deal) == (10004, 0, 0)
    assert broker.positions_get() == ()
    assert broker.history_deals_get(*window(clock)) == ()


def test_scripted_order_check_reject() -> None:
    broker, _ = make()
    broker.script("order_check", Reject(10019))
    check = broker.order_check(buy())
    assert check is not None and check.retcode == 10019


def test_script_is_consumed_in_order_then_defaults_to_accept() -> None:
    broker, _ = make()
    broker.script("order_send", Reject(10004), Accept())
    codes = [r.retcode for r in (broker.order_send(buy()) for _ in range(3)) if r is not None]
    assert codes == [10004, bp.TRADE_RETCODE_DONE, bp.TRADE_RETCODE_DONE]


def test_partial_fill_records_only_the_filled_volume() -> None:
    broker, clock = make()
    broker.script("order_send", PartialFill(0.02))
    result = broker.order_send(buy(0.05))
    assert result is not None and (result.retcode, result.volume) == (bp.TRADE_RETCODE_DONE_PARTIAL, 0.02)
    pos = one(broker.positions_get())
    order = one(broker.history_orders_get(*window(clock)))
    deal = one(broker.history_deals_get(*window(clock)))
    assert pos.volume == deal.volume == 0.02
    assert (order.volume_initial, order.state) == (0.05, bp.ORDER_STATE_PARTIAL)


def test_timeout_returns_none_and_the_fill_is_found_only_by_lookup() -> None:
    # EXE-013/014: no reply is UNKNOWN; the evidence is in positions and history, matched on magic + tag.
    broker, clock = make()
    broker.script("order_send", Timeout())
    assert broker.order_send(buy()) is None
    assert broker.last_error()[0] != 1
    deals = broker.history_deals_get(*window(clock)) or ()
    assert [(d.magic, d.comment) for d in deals] == [(MAGIC, TAG)]
    assert [p.comment for p in broker.positions_get() or ()] == [TAG]


def test_timeout_fill_can_appear_in_history_only_later() -> None:
    broker, clock = make()
    broker.script("order_send", Timeout(visible_after_ms=5000))
    assert broker.order_send(buy()) is None
    assert broker.history_deals_get(*window(clock)) == ()
    assert broker.history_orders_get(*window(clock)) == ()
    assert broker.positions_get() == ()
    clock.advance(5000)
    assert len(broker.history_deals_get(*window(clock)) or ()) == 1
    assert len(broker.positions_get() or ()) == 1


def test_timeout_without_execution_leaves_no_trace() -> None:
    broker, clock = make()
    broker.script("order_send", Timeout(executed=False))
    assert broker.order_send(buy()) is None
    assert broker.positions_get() == ()
    assert broker.history_orders_get(*window(clock)) == ()
    assert broker.history_deals_get(*window(clock)) == ()


def test_script_rejects_an_unscriptable_method() -> None:
    broker, _ = make()
    with pytest.raises(ValueError, match="positions_get"):
        broker.script("positions_get", Accept())  # type: ignore[arg-type]


# --- sessions ----------------------------------------------------------------------------------


@pytest.mark.parametrize("at", [SATURDAY, WED_BREAK])
def test_closed_session_returns_market_closed(at: datetime) -> None:
    broker, _ = make(at=at)
    send, check = broker.order_send(buy()), broker.order_check(buy())
    assert send is not None and send.retcode == bp.TRADE_RETCODE_MARKET_CLOSED
    assert check is not None and check.retcode == bp.TRADE_RETCODE_MARKET_CLOSED
    assert broker.positions_get() == ()


def test_emergency_close_while_market_closed_leaves_the_position() -> None:
    # EXECUTION_SAFETY_SPEC §11 chaos case: close attempt during a closed session.
    broker, clock = make(at=datetime(2026, 1, 9, 20, 0, tzinfo=UTC))  # Friday, before 20:58
    opened = broker.order_send(buy())
    assert opened is not None
    clock.advance(60 * 60 * 1000)  # 21:00 Friday: closed until Sunday 22:05
    result = broker.order_send(close(opened.order))
    assert result is not None and result.retcode == bp.TRADE_RETCODE_MARKET_CLOSED
    assert len(broker.positions_get() or ()) == 1


def test_session_uses_server_time_offset() -> None:
    # TIME-031: the profile's offset turns UTC into server time before the session lookup.
    broker, _ = make(at=datetime(2026, 1, 7, 20, 0, tzinfo=UTC), server_offset_minutes=120)  # 22:00 server
    result = broker.order_send(buy())
    assert result is not None and result.retcode == bp.TRADE_RETCODE_MARKET_CLOSED


# --- comment handling (A-30 BLOCKED until M7) --------------------------------------------------


@pytest.mark.parametrize(("max_len", "expected"), [(None, TAG), (0, ""), (5, "GB:AB")])
def test_comment_is_preserved_dropped_or_truncated_per_profile(max_len: int | None, expected: str) -> None:
    broker, clock = make(comment_max_len=max_len)
    opened = broker.order_send(buy())
    assert opened is not None
    pos = one(broker.positions_get())
    order = one(broker.history_orders_get(*window(clock)))
    deal = one(broker.history_deals_get(*window(clock)))
    assert pos.comment == order.comment == deal.comment == expected


# --- determinism -------------------------------------------------------------------------------


def _run(seed: int) -> list[object]:
    broker, clock = make(seed=seed)
    broker.script("order_send", Accept(), PartialFill(0.01), Reject(10004), Timeout())
    out: list[object] = [broker.order_send(buy(0.02)) for _ in range(4)]
    clock.advance(1500)
    broker.set_tick(4075.0, 4075.3)
    out += [broker.positions_get(), broker.history_orders_get(*window(clock)),
            broker.history_deals_get(*window(clock)), broker.account_info()]
    return out


def test_same_seed_and_script_give_identical_results() -> None:
    assert _run(7) == _run(7)


def test_different_seeds_give_different_tickets() -> None:
    assert _run(7) != _run(8)
