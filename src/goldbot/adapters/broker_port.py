"""BrokerPort: the narrow seam between GoldBot and MT5 (ADR-006).

The port mirrors the MetaTrader5 package calls the specs use, and nothing else. It returns RAW
broker-shaped values: floats exactly as MT5 gives them, field names as MT5 names them. It does not
convert. The M2 ``Mt5Broker`` adapter is the conversion boundary (RISK-003, RISK-020): it turns
these floats into Decimal with ``Decimal(repr(x))``. MT5 has no idempotency key (EXE-002), and
neither does this port.

The NamedTuples below are subsets of the MT5 result tuples, limited to the fields the specs read.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import NamedTuple, Protocol, TypedDict, runtime_checkable

# MQL5 enum values used by the specs.
ORDER_TYPE_BUY = 0
ORDER_TYPE_SELL = 1
TRADE_ACTION_DEAL = 1  # market entry / close (EXE-020, EMG-020)
TRADE_ACTION_PENDING = 5  # pending order (retcode 10008 PLACED, §4)
TRADE_ACTION_SLTP = 6  # SL repair (EXE-031)
TRADE_ACTION_REMOVE = 8  # CANCEL_PENDING (§8)
ORDER_STATE_PLACED = 1
ORDER_STATE_CANCELED = 2
ORDER_STATE_PARTIAL = 3
ORDER_STATE_FILLED = 4
DEAL_ENTRY_IN = 0
DEAL_ENTRY_OUT = 1
COPY_TICKS_ALL = -1

# Retcodes produced by FakeBroker itself; the full classification is EXECUTION_SAFETY_SPEC §4.
TRADE_RETCODE_PLACED = 10008
TRADE_RETCODE_DONE = 10009
TRADE_RETCODE_DONE_PARTIAL = 10010
TRADE_RETCODE_INVALID = 10013
TRADE_RETCODE_MARKET_CLOSED = 10018
TRADE_RETCODE_POSITION_CLOSED = 10036


class TerminalInfo(NamedTuple):
    connected: bool
    trade_allowed: bool


class AccountInfo(NamedTuple):
    login: int
    trade_mode: int
    leverage: int
    limit_orders: int
    margin_so_mode: int
    trade_allowed: bool
    trade_expert: bool
    balance: float
    profit: float
    equity: float
    margin: float
    margin_free: float
    margin_level: float
    margin_so_call: float
    margin_so_so: float
    currency: str
    server: str
    company: str


class SymbolInfo(NamedTuple):
    """``name`` plus the CENT-004 spec-snapshot fields."""

    name: str
    digits: int
    point: float
    trade_tick_size: float
    trade_tick_value: float
    trade_tick_value_profit: float
    trade_tick_value_loss: float
    trade_contract_size: float
    volume_min: float
    volume_max: float
    volume_step: float
    volume_limit: float
    trade_stops_level: int
    trade_freeze_level: int
    trade_mode: int
    trade_exemode: int
    filling_mode: int
    order_mode: int
    swap_mode: int
    swap_long: float
    swap_short: float
    swap_rollover3days: int
    currency_base: str
    currency_profit: str
    currency_margin: str
    margin_initial: float
    margin_maintenance: float


class Tick(NamedTuple):
    time: int
    bid: float
    ask: float
    time_msc: int


class TradeOrder(NamedTuple):
    ticket: int
    time_setup_msc: int
    time_done_msc: int
    type: int
    state: int
    magic: int
    volume_initial: float
    volume_current: float
    price_open: float
    sl: float
    tp: float
    symbol: str
    comment: str
    position_id: int


class TradePosition(NamedTuple):
    ticket: int
    time_msc: int
    type: int
    magic: int
    identifier: int
    volume: float
    price_open: float
    sl: float
    tp: float
    price_current: float
    profit: float
    swap: float
    symbol: str
    comment: str


class TradeDeal(NamedTuple):
    ticket: int
    order: int
    time_msc: int
    type: int
    entry: int
    magic: int
    position_id: int
    volume: float
    price: float
    commission: float
    swap: float
    profit: float
    fee: float
    symbol: str
    comment: str


class TradeRequest(TypedDict, total=False):
    """The MT5 trade-request dict (EXE-020 fields)."""

    action: int
    symbol: str
    volume: float
    type: int
    price: float
    sl: float
    tp: float
    deviation: int
    magic: int
    comment: str
    type_time: int
    type_filling: int
    position: int
    order: int


class OrderCheckResult(NamedTuple):
    retcode: int
    balance: float
    equity: float
    profit: float
    margin: float
    margin_free: float
    margin_level: float
    comment: str
    request: TradeRequest


class OrderSendResult(NamedTuple):
    retcode: int
    deal: int
    order: int
    volume: float
    price: float
    bid: float
    ask: float
    comment: str
    request_id: int
    retcode_external: int
    request: TradeRequest


@runtime_checkable
class BrokerPort(Protocol):
    """The MT5 calls GoldBot may make. ``None`` means the call failed (see ``last_error``)."""

    def initialize(self) -> bool:
        """EXE-070 startup. Credentials come from the keyring inside the adapter (SEC-001)."""
        ...

    def shutdown(self) -> None:
        """EXE-070 clean shutdown (the counterpart of ``initialize``)."""
        ...

    def last_error(self) -> tuple[int, str]:
        """Cause of the last ``None`` result, for the audit record (EXE-004, §4 ``None`` class)."""
        ...

    def terminal_info(self) -> TerminalInfo | None:
        """EXE-004 / TIME-022: ``connected`` and ``trade_allowed``."""
        ...

    def account_info(self) -> AccountInfo | None:
        """CENT-002 discovery and EXP-001 exposure inputs."""
        ...

    def symbols_get(self) -> tuple[SymbolInfo, ...] | None:
        """CENT-003 symbol discovery (the caller filters on ``XAU``)."""
        ...

    def symbol_select(self, symbol: str, enable: bool = True) -> bool:
        """CENT-003: select each candidate before reading its ``symbol_info``."""
        ...

    def symbol_info(self, symbol: str) -> SymbolInfo | None:
        """CENT-003/004 spec snapshot."""
        ...

    def symbol_info_tick(self, symbol: str) -> Tick | None:
        """TIME-020 tick polling."""
        ...

    def copy_ticks_range(
        self, symbol: str, date_from: datetime, date_to: datetime, flags: int
    ) -> Sequence[Tick] | None:
        """BT-010 tick history. MT5 returns a numpy record array; the adapter yields ``Tick`` rows."""
        ...

    def order_calc_margin(self, action: int, symbol: str, volume: float, price: float) -> float | None:
        """EXP-004, CENT-013."""
        ...

    def order_calc_profit(
        self, action: int, symbol: str, volume: float, price_open: float, price_close: float
    ) -> float | None:
        """RISK-011 sizing, EXP-002 notional, CENT-010."""
        ...

    def order_check(self, request: TradeRequest) -> OrderCheckResult | None:
        """EXE-010: runs before every ``order_send``."""
        ...

    def order_send(self, request: TradeRequest) -> OrderSendResult | None:
        """EXE-020. The result is evidence, never proof (EXE-001); ``None`` is UNKNOWN (EXE-013)."""
        ...

    def orders_get(self, *, symbol: str | None = None, ticket: int | None = None) -> tuple[TradeOrder, ...] | None:
        """EXE-014 reconciliation, CANCEL_PENDING confirmation (§8)."""
        ...

    def positions_get(
        self, *, symbol: str | None = None, ticket: int | None = None
    ) -> tuple[TradePosition, ...] | None:
        """EXE-001 read-back, EXE-002.5 close re-read, EXE-030 SL check, §8 confirmation."""
        ...

    def history_orders_get(self, date_from: datetime, date_to: datetime) -> tuple[TradeOrder, ...] | None:
        """EXE-014 reconciliation window."""
        ...

    def history_deals_get(self, date_from: datetime, date_to: datetime) -> tuple[TradeDeal, ...] | None:
        """EXE-014, §8 closing deals, CENT-006 commission, CENT-016 balance operations."""
        ...
