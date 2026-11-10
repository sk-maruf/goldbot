# TIME_AND_CLOCK_SPEC — Clocks, timestamps and freshness

> Status: **SPECIFICATION.** Added in V2 (not in the requested file list) because V1's clock
> design was a confirmed defect: it used the latest tick time as a proxy for broker "now".
> Corrects V1 audit item **E**.

## 1. Five different clocks (never interchange them)

| Clock | Source | Used for | Never used for |
|---|---|---|---|
| C1 Local UTC wall clock | OS clock, NTP-disciplined | Timestamps in records, day/week boundaries, display | Measuring elapsed time |
| C2 Local monotonic | `time.monotonic_ns()` (Python), `GetTickCount64()` (MQL5) | Timeouts, staleness, heartbeats, approval expiry, retry back-off | Calendar time |
| C3 Tick-receive time | C2 value recorded when the engine first sees a new tick | Data freshness (TIME-020) | Broker server time |
| C4 Broker server time (estimated) | Guardian export of `TimeTradeServer()` and offset (TIME-030) | Interpreting sessions, swap time, calendar events | Freshness |
| C5 Tick timestamp | `tick.time_msc` from MT5 | Ordering ticks, bar building, research | "Current time" |

## 2. What the MT5 time functions do and don't tell us

| Function | What it returns | Limitation for GoldBot |
|---|---|---|
| `TimeCurrent()` (MQL5) | Last known server time = time of the last quote received for any Market Watch symbol; formed on the server [VERIFIED S6] | Stops advancing when no quotes arrive (quiet market, closed market, disconnection). **Not "now".** V1's error was treating the latest tick time this way. |
| `TimeTradeServer()` (MQL5) | Calculated current server time, computed in the client terminal [VERIFIED S7] | Depends on the local computer clock [VERIFIED S7], hence TIME-010. In the Strategy Tester it equals `TimeCurrent()` [VERIFIED S7]. |
| `TimeGMT()` (MQL5) | GMT derived from local time with local DST [VERIFIED S8] | Wrong if the local clock, time zone or DST setting is wrong. |
| `GetTickCount64()` (MQL5) | Milliseconds since system start | Monotonic for elapsed time only. |
| Python package | **No equivalent of `TimeTradeServer` exists** [VERIFIED S9]. Tick/bar times are documented as stored "in UTC time zone (without the shift)" [VERIFIED S10] | The phrase is ambiguous (TIME-005). |

- **TIME-001** The engine never calls any value "server now" unless it comes from TIME-030.
- **TIME-005 Tick timestamp interpretation.** V2 assumes neither reading of S10. In M2:
  for 1,000 fresh ticks, compute `d = tick.time_msc − local_utc_ms_at_receive`. Then
  `d ≈ server_offset_ms − network/processing latency`. Record the median and IQR in
  `docs/VERIFIED_SPECS.md`. Exness publishes server time as GMT+0 [VERIFIED S2], so both
  readings should coincide (median ≈ −latency). The test still runs, so that a change of server
  zone or a local clock error is detected. If `|median| > 2 s`, the result is ENTRY_STOP (T11) and
  a BLOCKED item is raised until it is explained.

## 3. Local UTC synchronisation (C1)

- **TIME-010** The OS time service must be enabled (runbook check). In addition, the engine
  queries at least two NTP servers every 5 minutes and computes the offset. Thresholds come from
  P-16 (warn 500 ms, ENTRY_STOP 1,000 ms). If NTP is unreachable for more than 10 minutes, the
  result is T11.
- **TIME-011** All persisted timestamps are timezone-aware UTC, ISO-8601 with milliseconds.
  Naive `datetime` objects are forbidden (lint rule and test).

## 4. Monotonic time (C2)

- **TIME-015** Every duration (P-15, P-20–P-25, approval expiry, retry back-off, heartbeat age)
  is measured with monotonic time. Wall-clock jumps (NTP step, DST, manual change) must not
  change any timeout. A test injects a wall-clock jump of ±1 h and checks that nothing expires
  early or late.

## 5. Tick freshness (C3)

- **TIME-020** The adapter polls `symbol_info_tick` (default every 250 ms). A tick counts as
  **new** when `(time_msc, bid, ask)` differs from the previous one. Its C2 receive time is
  recorded. Then `tick_age = monotonic_now − last_new_tick_receive`.
- **TIME-021** `time_msc` must be non-decreasing. Equal values are allowed. A decrease is
  recorded as an out-of-order event. More than 3 in 60 s → data-quality DEGRADED and the gate
  rejects entries.
- **TIME-022 Quiet market vs dead feed.** If `terminal_info().connected` is false, the state is
  DISCONNECTED (T12). If connected, the session is open, and `tick_age > P-15`, the state is STALE:
  entries are rejected by the gate, and the UI shows STALE (UI-012). If the session is closed,
  staleness is expected and shown as MARKET CLOSED, not as an error.
- **TIME-023** The Guardian measures freshness independently from `OnTick` arrival with
  `GetTickCount64()`, and reports it in its heartbeat. The engine and Guardian views are compared;
  persistent disagreement → DEGRADED.

## 6. Broker server time (C4)

- **TIME-030** On every Guardian heartbeat (every 5 s, GRD-011) the Guardian exports `TimeTradeServer()`,
  `TimeGMT()`, `TimeCurrent()`, `TimeLocal()` and `GetTickCount64()`.
  `server_offset = TimeTradeServer() − TimeGMT()`, rounded to the nearest 15 minutes. The engine
  accepts a new offset only if two consecutive estimates agree within P-17. A change of offset is
  logged and alerted, and the session/calendar tables are re-derived.
- **TIME-031** The expected offset for Exness is 0 (server time GMT+0 [VERIFIED S2]). A measured
  value other than 0 is not an error in itself, but it raises a BLOCKED item for the user to
  confirm.
- **TIME-032** Both `TimeTradeServer()` and `TimeGMT()` are computed from the local clock
  [VERIFIED S7, S8]. The offset estimate is therefore only as good as TIME-010. Neither value is
  used for freshness.

## 7. Sessions, swap time and news events

- **TIME-040** Trading sessions come from the Guardian's `SymbolInfoSessionTrade` export
  (CENT-005). They are converted to UTC with TIME-030 and cached per week. Published Exness hours
  [VERIFIED S2] serve only as a cross-check. `SymbolInfoSessionTrade` describes a **weekday
  template only**, with no dates, holidays or early closes [VERIFIED S36]. Date-specific exceptions
  therefore come from `config/session_exceptions.yaml` (EXE-080).
- **TIME-041** Swap time moves between 21:00 and 22:00 GMT+0 across summer and winter
  [VERIFIED S3]. Session blackouts (P-19) are therefore computed from the live session table each
  week, never hardcoded.
- **TIME-042** High-impact USD events come from the Guardian's MQL5 calendar export (ADR-007).
  Event times are converted to UTC with TIME-030. [ASSUMPTION: MQL5 calendar times are in
  trade-server time; verify in M7 by comparing three known events with an independent public
  calendar.] **Unknown-calendar policy:** if the calendar file is older than 24 h, missing,
  unparseable, or fails TIME-043, every strategy is treated as not news-validated (RISK-018), **and**
  every entry is blocked during the US session window (fail closed) until valid data returns.
- **TIME-043 Calendar validity.** An event set is VALID only if: it was exported < 24 h ago; every
  event has a timestamp converted through a server offset accepted under TIME-030; the
  timezone-interpretation check from TIME-042 has passed at least once on this installation; each
  event has an impact level and a currency; and each event carries a relevance class (`RELEVANT_USD`,
  `RELEVANT_GOLD`, `IRRELEVANT`) from a versioned mapping file. Anything else is AMBIGUOUS. Ambiguous
  data is treated exactly like missing data.

## 8. Drift and inconsistency handling

| ID | Condition | Action |
|---|---|---|
| TIME-050 | Local vs NTP offset above P-16 entry-stop level | T11 ENTRY_STOP |
| TIME-051 | Server-offset estimate changes or two estimates disagree | ENTRY_STOP until two agreeing estimates |
| TIME-052 | Tick timestamps drift from local receive time by > 2 s (rolling median) | DEGRADED + alert; > 5 s → ENTRY_STOP |
| TIME-053 | Guardian heartbeat clock fields missing or non-numeric | Guardian status UNKNOWN → T9 |
| TIME-054 | Deal/order timestamps from history earlier than the request's local send time minus 5 s | Data-quality flag on that record; reconciliation re-reads |
| TIME-055 | Missing `time_msc` on a tick | Tick discarded and counted; > 1% of ticks → DEGRADED |
| TIME-056 | Day/week boundary crossed while the engine was down | On start, recompute limit state from deal history (RISK limits are rebuilt, never assumed reset) |

## 9. Tests

Unit tests with an injectable clock for C1/C2, a wall-clock jump test (TIME-015), out-of-order
tick fixtures (TIME-021), a quiet-market vs disconnected-feed simulation (TIME-022), offset
change (TIME-030/051), stale calendar (TIME-042), and a restart across midnight UTC (TIME-056).
