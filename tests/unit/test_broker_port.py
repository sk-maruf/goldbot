"""BrokerPort shape tests (ADR-006): narrow, MT5-shaped, raw."""

import inspect

from goldbot.adapters import broker_port as bp

# Each method is used by a spec; see the docstrings in broker_port.py.
EXPECTED_METHODS = {
    "initialize",
    "shutdown",
    "last_error",
    "terminal_info",
    "account_info",
    "symbols_get",
    "symbol_select",
    "symbol_info",
    "symbol_info_tick",
    "copy_ticks_range",
    "order_calc_margin",
    "order_calc_profit",
    "order_check",
    "order_send",
    "orders_get",
    "positions_get",
    "history_orders_get",
    "history_deals_get",
}


def _protocol_methods() -> set[str]:
    return {
        name
        for name, member in inspect.getmembers(bp.BrokerPort, inspect.isfunction)
        if not name.startswith("_")
    }


def test_port_lists_exactly_the_spec_used_mt5_calls() -> None:
    # ADR-006: the port stays narrow; adding a call needs a spec that uses it.
    assert _protocol_methods() == EXPECTED_METHODS


def test_port_is_runtime_checkable_and_rejects_incomplete_objects() -> None:
    class Partial:
        def initialize(self) -> bool:
            return True

    assert not isinstance(Partial(), bp.BrokerPort)


def test_result_shapes_use_mt5_field_names() -> None:
    assert {"retcode", "deal", "order", "volume", "price", "bid", "ask", "comment", "request"} <= set(
        bp.OrderSendResult._fields
    )
    assert {"retcode", "margin", "margin_free", "margin_level", "request"} <= set(
        bp.OrderCheckResult._fields
    )
    # EXE-014 matches on magic + comment; fingerprint uses symbol, type, volume, time.
    for shape in (bp.TradeOrder, bp.TradePosition, bp.TradeDeal):
        assert {"ticket", "magic", "symbol", "type", "comment"} <= set(shape._fields)
    assert {"time_msc", "bid", "ask"} <= set(bp.Tick._fields)  # TIME-020/021
    assert {"connected", "trade_allowed"} <= set(bp.TerminalInfo._fields)  # EXE-004
    # CENT-002 and EXP-001 account fields
    assert {
        "login", "server", "company", "currency", "trade_mode", "leverage", "margin_so_mode",
        "margin_so_call", "margin_so_so", "trade_allowed", "trade_expert", "limit_orders",
        "balance", "equity", "margin", "margin_free", "margin_level",
    } <= set(bp.AccountInfo._fields)


def test_symbol_info_carries_every_cent_004_snapshot_field() -> None:
    cent_004 = {
        "digits", "point", "trade_tick_size", "trade_tick_value", "trade_tick_value_profit",
        "trade_tick_value_loss", "trade_contract_size", "volume_min", "volume_max", "volume_step",
        "volume_limit", "trade_stops_level", "trade_freeze_level", "trade_mode", "trade_exemode",
        "filling_mode", "order_mode", "swap_mode", "swap_long", "swap_short", "swap_rollover3days",
        "currency_base", "currency_profit", "currency_margin", "margin_initial", "margin_maintenance",
    }
    assert cent_004 | {"name"} == set(bp.SymbolInfo._fields)


def test_money_and_price_fields_are_typed_as_raw_floats() -> None:
    # RISK-020: the port does not convert; the M2 adapter boundary does.
    hints = inspect.get_annotations(bp.AccountInfo)
    assert hints["equity"] is float
    assert inspect.get_annotations(bp.SymbolInfo)["trade_tick_value"] is float
    assert inspect.get_annotations(bp.OrderSendResult)["price"] is float


def test_mt5_constants_match_the_mql5_enum_values() -> None:
    assert (bp.ORDER_TYPE_BUY, bp.ORDER_TYPE_SELL) == (0, 1)
    assert (bp.TRADE_ACTION_DEAL, bp.TRADE_ACTION_PENDING, bp.TRADE_ACTION_SLTP, bp.TRADE_ACTION_REMOVE) == (
        1, 5, 6, 8,
    )
    assert (bp.DEAL_ENTRY_IN, bp.DEAL_ENTRY_OUT) == (0, 1)
    # EXECUTION_SAFETY_SPEC §4 [VERIFIED S14]
    assert bp.TRADE_RETCODE_PLACED == 10008
    assert bp.TRADE_RETCODE_DONE == 10009
    assert bp.TRADE_RETCODE_DONE_PARTIAL == 10010
    assert bp.TRADE_RETCODE_MARKET_CLOSED == 10018
    assert bp.TRADE_RETCODE_POSITION_CLOSED == 10036
