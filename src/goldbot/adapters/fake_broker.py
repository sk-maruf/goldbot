"""FakeBroker: a deterministic in-process stand-in for MT5 behind ``BrokerPort`` (ADR-006).

ILLUSTRATIVE. It encodes beliefs about broker behaviour, never evidence (ADR-006, GOV-002):

* Values are RAW floats in MT5 shapes, so the M2 conversion boundary is exercised (RISK-020).
* Deterministic for a given seed, script and clock: the seed only picks the first ticket number.
* Sessions come from the profile, read in server time = UTC + ``server_offset_minutes`` (TIME-031).
  Closed session -> 10018 MARKET_CLOSED.
* Scripts per call (``order_check``, ``order_send``): ``Accept``, ``Reject(retcode)``,
  ``PartialFill(volume)``, ``Timeout`` (returns ``None``; the fill, if any, shows up only in
  positions and history, optionally later: the EXE-013 UNKNOWN case).
* Comments are preserved, dropped or truncated per the profile's ``comment_max_len`` (A-30 is
  BLOCKED until M7; the default ``null`` preserves).
* There is no idempotency: the same request sent twice fills twice (EXE-002).
* ``order_calc_profit``/``order_calc_margin`` use ILLUSTRATIVE formulas from the profile's tick
  size, tick value and leverage, rounded to 2 digits; real MT5 uses the symbol's calc mode.

``order_check`` and ``order_send`` validate (beliefs about MT5, verify in M2; GOV-003), with no state
change on reject: symbol (10013), session (10018), action (10013), volume grid/min/max and close volume
above the position (10014), off-tick price (10015), SL/TP off-tick, on the wrong side or inside
``trade_stops_level`` (10016), margin above free margin (10019), unchanged SLTP (10025), missing
position (10036). Not validated: freeze level, pending orders, requotes/deviation, disconnects.
Scripted replies bypass validation.
"""

from __future__ import annotations

import json
import random
from collections import deque
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from goldbot.adapters.broker_port import (
    DEAL_ENTRY_IN,
    DEAL_ENTRY_OUT,
    ORDER_STATE_FILLED,
    ORDER_STATE_PARTIAL,
    ORDER_TYPE_BUY,
    TRADE_ACTION_DEAL,
    TRADE_ACTION_SLTP,
    TRADE_RETCODE_DONE,
    TRADE_RETCODE_DONE_PARTIAL,
    TRADE_RETCODE_INVALID,
    TRADE_RETCODE_INVALID_PRICE,
    TRADE_RETCODE_INVALID_STOPS,
    TRADE_RETCODE_INVALID_VOLUME,
    TRADE_RETCODE_MARKET_CLOSED,
    TRADE_RETCODE_NO_CHANGES,
    TRADE_RETCODE_NO_MONEY,
    TRADE_RETCODE_POSITION_CLOSED,
    AccountInfo,
    OrderCheckResult,
    OrderSendResult,
    SymbolInfo,
    TerminalInfo,
    Tick,
    TradeDeal,
    TradeOrder,
    TradePosition,
    TradeRequest,
)
from goldbot.core.clock import Clock

ORDER_CHECK_OK = 0  # belief: MetaTrader5 docs show order_check retcode 0 ("Done") on success
_NO_ERROR = (1, "Success")
_ERR_TIMEOUT = (-10005, "IPC timeout")
_ERR_INVALID_PARAMS = (-2, "Invalid params")
_DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_MS = timedelta(milliseconds=1)


@dataclass(frozen=True)
class Accept:
    pass


@dataclass(frozen=True)
class Reject:
    retcode: int


@dataclass(frozen=True)
class PartialFill:
    volume: float


@dataclass(frozen=True)
class Timeout:
    executed: bool = True
    visible_after_ms: int = 0


Reply = Accept | Reject | PartialFill | Timeout
Scriptable = Literal["order_check", "order_send"]


def load_profile(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class FakeBroker:
    def __init__(self, profile: Mapping[str, Any], clock: Clock, *, seed: int = 0) -> None:
        if "label" not in profile:
            raise ValueError("broker profile has no label (ILLUSTRATIVE or VER-*)")
        self.label: str = profile["label"]
        self._profile = profile
        self._clock = clock
        self._symbol = SymbolInfo(**profile["symbol"])
        self._balance = float(profile["account"]["balance"])
        self._ticket = random.Random(seed).randrange(10**7, 10**8)  # noqa: S311 - simulation, not crypto
        self._scripts: dict[str, deque[Reply]] = {"order_check": deque(), "order_send": deque()}
        self._positions: dict[int, tuple[int, TradePosition]] = {}  # ticket -> (visible_from_ns, row)
        self._orders: list[tuple[int, TradeOrder]] = []
        self._deals: list[tuple[int, TradeDeal]] = []
        self._ticks: list[Tick] = []
        self._error = _NO_ERROR
        self.set_tick(**profile["tick"])

    # --- test controls ---------------------------------------------------------------------------

    def script(self, method: Scriptable, *replies: Reply) -> None:
        if method not in self._scripts:
            raise ValueError(f"{method} is not scriptable")
        self._scripts[method].extend(replies)

    def set_tick(self, bid: float, ask: float) -> None:
        ms = self._server_ms(self._clock.utc_now())
        self._ticks.append(Tick(ms // 1000, bid, ask, ms))

    # --- BrokerPort: session and discovery -------------------------------------------------------

    def initialize(self) -> bool:
        return True

    def shutdown(self) -> None:
        return None

    def last_error(self) -> tuple[int, str]:
        return self._error

    def terminal_info(self) -> TerminalInfo | None:
        return TerminalInfo(**self._profile["terminal"])

    def account_info(self) -> AccountInfo | None:
        positions = self.positions_get() or ()
        profit = round(sum(p.profit for p in positions), 2)
        margin = sum(self._margin(p.type, p.volume, p.price_open) for p in positions)
        equity = round(self._balance + profit, 2)
        return AccountInfo(**(self._profile["account"] | {
            "balance": self._balance, "profit": profit, "equity": equity, "margin": margin,
            "margin_free": round(equity - margin, 2),
            "margin_level": round(equity / margin * 100, 2) if margin else 0.0,
        }))

    def symbols_get(self) -> tuple[SymbolInfo, ...] | None:
        return (self._symbol,)

    def symbol_select(self, symbol: str, enable: bool = True) -> bool:
        return symbol == self._symbol.name

    def symbol_info(self, symbol: str) -> SymbolInfo | None:
        return self._symbol if self._known(symbol) else None

    def symbol_info_tick(self, symbol: str) -> Tick | None:
        return self._ticks[-1] if self._known(symbol) else None

    def copy_ticks_range(
        self, symbol: str, date_from: datetime, date_to: datetime, flags: int
    ) -> list[Tick] | None:
        if not self._known(symbol):
            return None
        lo, hi = self._server_ms(date_from), self._server_ms(date_to)
        return [t for t in self._ticks if lo <= t.time_msc <= hi]

    # --- BrokerPort: calculations (ILLUSTRATIVE) -------------------------------------------------

    def order_calc_margin(self, action: int, symbol: str, volume: float, price: float) -> float | None:
        return self._margin(action, volume, price) if self._known(symbol) else None

    def order_calc_profit(
        self, action: int, symbol: str, volume: float, price_open: float, price_close: float
    ) -> float | None:
        return self._profit(action, volume, price_open, price_close) if self._known(symbol) else None

    # --- BrokerPort: trading ---------------------------------------------------------------------

    def order_check(self, request: TradeRequest) -> OrderCheckResult | None:
        self._error = _NO_ERROR
        reply = self._next("order_check")
        if isinstance(reply, Timeout):
            return self._timeout()
        retcode = reply.retcode if isinstance(reply, Reject) else self._precheck(request) or ORDER_CHECK_OK
        account = self.account_info()
        assert account is not None
        side, volume = request.get("type", ORDER_TYPE_BUY), request.get("volume", 0.0)
        required = self._margin(side, volume, self._ticks[-1].ask)
        used = account.margin + required
        return OrderCheckResult(
            retcode, account.balance, account.equity, account.profit, required,
            round(account.equity - used, 2), round(account.equity / used * 100, 2) if used else 0.0,
            "", request,
        )

    def order_send(self, request: TradeRequest) -> OrderSendResult | None:
        self._error = _NO_ERROR
        reply = self._next("order_send")
        if isinstance(reply, Reject):
            return self._result(request, reply.retcode)
        if isinstance(reply, Timeout) and not reply.executed:
            return self._timeout()
        delay_ms = reply.visible_after_ms if isinstance(reply, Timeout) else 0
        fill = reply.volume if isinstance(reply, PartialFill) else None
        result = self._execute(request, fill, delay_ms)
        return self._timeout() if isinstance(reply, Timeout) else result

    def orders_get(
        self, *, symbol: str | None = None, ticket: int | None = None
    ) -> tuple[TradeOrder, ...] | None:
        # shortcut: pending orders are not simulated, so there is never an active order; add them
        # when an engine path places or cancels pending orders (CANCEL_PENDING tests, M7).
        return ()

    def positions_get(
        self, *, symbol: str | None = None, ticket: int | None = None
    ) -> tuple[TradePosition, ...] | None:
        return tuple(
            self._marked(p)
            for p in self._visible(self._positions.values())
            if symbol in (None, p.symbol) and ticket in (None, p.ticket)
        )

    def history_orders_get(self, date_from: datetime, date_to: datetime) -> tuple[TradeOrder, ...] | None:
        lo, hi = self._server_ms(date_from), self._server_ms(date_to)
        return tuple(o for o in self._visible(self._orders) if lo <= o.time_setup_msc <= hi)

    def history_deals_get(self, date_from: datetime, date_to: datetime) -> tuple[TradeDeal, ...] | None:
        lo, hi = self._server_ms(date_from), self._server_ms(date_to)
        return tuple(d for d in self._visible(self._deals) if lo <= d.time_msc <= hi)

    # --- simulation ------------------------------------------------------------------------------

    def _execute(self, request: TradeRequest, fill: float | None, delay_ms: int) -> OrderSendResult:
        retcode = self._precheck(request)
        if retcode:
            return self._result(request, retcode)
        if request.get("action") == TRADE_ACTION_SLTP:
            return self._modify(request)
        if request.get("position"):
            return self._close(request)
        return self._open(request, fill, delay_ms)

    def _precheck(self, request: TradeRequest) -> int:
        if not self._known(request.get("symbol", "")):
            return TRADE_RETCODE_INVALID
        if not self._market_open():
            return TRADE_RETCODE_MARKET_CLOSED
        action = request.get("action")
        if action == TRADE_ACTION_SLTP:
            return self._check_sltp(request)
        if action != TRADE_ACTION_DEAL:
            # shortcut: pending orders / removal are not simulated; add them with their first user (M7).
            return TRADE_RETCODE_INVALID
        if request.get("position"):
            return self._check_close(request)
        return self._check_open(request)

    def _check_open(self, request: TradeRequest) -> int:
        side, volume = request.get("type", ORDER_TYPE_BUY), request.get("volume", 0.0)
        price = request.get("price")
        if not self._volume_ok(volume):
            return TRADE_RETCODE_INVALID_VOLUME
        # belief (GOV-003): verify in M2 - market execution accepts a missing price, rejects an off-tick one
        if price is not None and not self._on_grid(price, self._symbol.trade_tick_size):
            return TRADE_RETCODE_INVALID_PRICE
        stops = self._check_stops(side, request.get("sl", 0.0), request.get("tp", 0.0))
        if stops:
            return stops
        tick = self._ticks[-1]
        required = self._margin(side, volume, tick.ask if side == ORDER_TYPE_BUY else tick.bid)
        account = self.account_info()
        assert account is not None
        return TRADE_RETCODE_NO_MONEY if required > account.margin_free else 0

    def _check_close(self, request: TradeRequest) -> int:
        pos = self._live_position(request.get("position", 0))
        if pos is None:
            return TRADE_RETCODE_POSITION_CLOSED
        volume = request.get("volume", 0.0)
        if not self._volume_ok(volume) or volume > pos.volume:
            return TRADE_RETCODE_INVALID_VOLUME
        return 0

    def _check_sltp(self, request: TradeRequest) -> int:
        pos = self._live_position(request.get("position", 0))
        if pos is None:
            return TRADE_RETCODE_POSITION_CLOSED
        sl, tp = request.get("sl", 0.0), request.get("tp", 0.0)
        if (sl, tp) == (pos.sl, pos.tp):
            return TRADE_RETCODE_NO_CHANGES
        return self._check_stops(pos.type, sl, tp)

    def _check_stops(self, side: int, sl: float, tp: float) -> int:
        # belief (GOV-003): verify in M2 - MQL5 "Requirements and Limitations": SL/TP are checked against
        # the closing side (bid for BUY, ask for SELL), strictly on the correct side and at least
        # trade_stops_level points away. Freeze level is not checked.
        s, tick = self._symbol, self._ticks[-1]
        ref = tick.bid if side == ORDER_TYPE_BUY else tick.ask
        sign = 1 if side == ORDER_TYPE_BUY else -1
        min_gap = s.trade_stops_level * s.point
        for level, below in ((sl, True), (tp, False)):
            if not level:
                continue
            gap = (ref - level) * sign if below else (level - ref) * sign
            if not self._on_grid(level, s.trade_tick_size) or gap <= 0 or gap < min_gap - s.point / 2:
                return TRADE_RETCODE_INVALID_STOPS
        return 0

    def _volume_ok(self, volume: float) -> bool:
        s = self._symbol
        return s.volume_min <= volume <= s.volume_max and self._on_grid(volume, s.volume_step)

    @staticmethod
    def _on_grid(value: float, step: float) -> bool:
        units = value / step
        return abs(units - round(units)) < 1e-6

    def _open(self, request: TradeRequest, fill: float | None, delay_ms: int) -> OrderSendResult:
        side = request.get("type", ORDER_TYPE_BUY)
        tick = self._ticks[-1]
        price = tick.ask if side == ORDER_TYPE_BUY else tick.bid
        asked = request.get("volume", 0.0)
        volume = asked if fill is None else fill
        magic, sl, tp = request.get("magic", 0), request.get("sl", 0.0), request.get("tp", 0.0)
        symbol, comment = self._symbol.name, self._comment(request)
        visible = self._clock.monotonic_ns() + delay_ms * 1_000_000
        now = self._server_ms(self._clock.utc_now())
        order, deal = self._new_ticket(), self._new_ticket()
        # belief: a partial market fill leaves the order in history as PARTIAL with the rest unfilled
        state = ORDER_STATE_FILLED if fill is None else ORDER_STATE_PARTIAL
        self._orders.append((visible, TradeOrder(
            order, now, now, side, state, magic, asked, round(asked - volume, 8), price, sl, tp, symbol,
            comment, order,
        )))
        self._deals.append((visible, TradeDeal(
            deal, order, now, side, DEAL_ENTRY_IN, magic, order, volume, price, 0.0, 0.0, 0.0, 0.0, symbol,
            comment,
        )))
        self._positions[order] = (visible, TradePosition(
            order, now, side, magic, order, volume, price, sl, tp, price, 0.0, 0.0, symbol, comment,
        ))
        code = TRADE_RETCODE_DONE if fill is None else TRADE_RETCODE_DONE_PARTIAL
        return self._result(request, code, deal=deal, order=order, volume=volume, price=price)

    def _close(self, request: TradeRequest) -> OrderSendResult:
        pos = self._live_position(request.get("position", 0))
        if pos is None:
            return self._result(request, TRADE_RETCODE_POSITION_CLOSED)
        tick = self._ticks[-1]
        price = tick.bid if pos.type == ORDER_TYPE_BUY else tick.ask
        volume = request.get("volume", 0.0)
        profit = self._profit(pos.type, volume, pos.price_open, price)
        side, magic, comment = 1 - pos.type, request.get("magic", 0), self._comment(request)
        now, visible = self._server_ms(self._clock.utc_now()), self._clock.monotonic_ns()
        order, deal = self._new_ticket(), self._new_ticket()
        self._orders.append((visible, TradeOrder(
            order, now, now, side, ORDER_STATE_FILLED, magic, volume, 0.0, price, 0.0, 0.0, pos.symbol,
            comment, pos.ticket,
        )))
        self._deals.append((visible, TradeDeal(
            deal, order, now, side, DEAL_ENTRY_OUT, magic, pos.ticket, volume, price, 0.0, 0.0, profit, 0.0,
            pos.symbol, comment,
        )))
        self._balance = round(self._balance + profit, 2)
        remaining = round(pos.volume - volume, 8)
        if remaining > 0:
            self._positions[pos.ticket] = (visible, pos._replace(volume=remaining))
        else:
            del self._positions[pos.ticket]
        return self._result(request, TRADE_RETCODE_DONE, deal=deal, order=order, volume=volume, price=price)

    def _modify(self, request: TradeRequest) -> OrderSendResult:
        pos = self._live_position(request.get("position", 0))
        if pos is None:
            return self._result(request, TRADE_RETCODE_POSITION_CLOSED)
        visible = self._positions[pos.ticket][0]
        modified = pos._replace(sl=request.get("sl", 0.0), tp=request.get("tp", 0.0))
        self._positions[pos.ticket] = (visible, modified)
        return self._result(request, TRADE_RETCODE_DONE)

    def _live_position(self, ticket: int) -> TradePosition | None:
        found = self.positions_get(ticket=ticket)
        return found[0] if found else None

    def _result(
        self, request: TradeRequest, retcode: int, *, deal: int = 0, order: int = 0, volume: float = 0.0,
        price: float = 0.0,
    ) -> OrderSendResult:
        tick = self._ticks[-1]
        return OrderSendResult(retcode, deal, order, volume, price, tick.bid, tick.ask, "", 0, 0, request)

    def _timeout(self) -> None:
        self._error = _ERR_TIMEOUT
        return None

    def _next(self, method: str) -> Reply:
        script = self._scripts[method]
        return script.popleft() if script else Accept()

    def _new_ticket(self) -> int:
        self._ticket += 1
        return self._ticket

    def _known(self, symbol: str) -> bool:
        # belief (GOV-003): verify in M2 - last_error is reset by each call, not sticky
        self._error = _NO_ERROR if symbol == self._symbol.name else _ERR_INVALID_PARAMS
        return symbol == self._symbol.name

    def _comment(self, request: TradeRequest) -> str:
        comment, max_len = request.get("comment", ""), self._profile.get("comment_max_len")
        return comment if max_len is None else comment[:max_len]

    def _marked(self, pos: TradePosition) -> TradePosition:
        tick = self._ticks[-1]
        current = tick.bid if pos.type == ORDER_TYPE_BUY else tick.ask
        profit = self._profit(pos.type, pos.volume, pos.price_open, current)
        return pos._replace(price_current=current, profit=profit)

    def _profit(self, action: int, volume: float, price_open: float, price_close: float) -> float:
        sign = 1 if action == ORDER_TYPE_BUY else -1
        ticks = (price_close - price_open) / self._symbol.trade_tick_size
        return round(sign * ticks * self._symbol.trade_tick_value * volume, 2)

    def _margin(self, action: int, volume: float, price: float) -> float:
        notional = abs(self._profit(ORDER_TYPE_BUY, volume, price, 2 * price))  # EXP-002 notional
        return round(notional / self._profile["account"]["leverage"], 2)

    def _visible[T](self, rows: Iterable[tuple[int, T]]) -> list[T]:
        now = self._clock.monotonic_ns()
        return [row for visible, row in rows if visible <= now]

    def _server_now(self) -> datetime:
        return self._clock.utc_now() + timedelta(minutes=self._profile["server_offset_minutes"])

    def _server_ms(self, at: datetime) -> int:
        shifted = at + timedelta(minutes=self._profile["server_offset_minutes"])
        return (shifted - _EPOCH) // _MS  # integer arithmetic: float timestamps lose milliseconds

    def _market_open(self) -> bool:
        now = self._server_now()
        hhmm = now.strftime("%H:%M")
        return any(start <= hhmm < end for start, end in self._profile["sessions"][_DAYS[now.weekday()]])
