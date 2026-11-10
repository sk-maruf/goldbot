# EXECUTION_SAFETY_SPEC — Order lifecycle, reconciliation, emergency operations

> Status: **SPECIFICATION.** Retcodes: [VERIFIED S14]. Terminal properties: [VERIFIED S15].
> Behaviour that depends on Exness execution settings is marked [BLOCKED: verify in M7 on demo].

## 1. Principles

- **EXE-001 A request is not a fill.** A position or order exists in the ledger as
  `CONFIRMED` only after it has been read back from `positions_get` / `orders_get` /
  `history_deals_get`. The `order_send` return value is evidence, never proof.
- **EXE-002 Idempotency and duplicate prevention.** MT5 has **no native idempotency key**: the
  trade request contains `magic` (an Expert Advisor ID), `comment` and tickets, but no
  client-supplied request identifier [VERIFIED S35]. GoldBot therefore provides its own:
  1. every operation gets a persistent `op_id` (UUIDv7), written durably to `order_intents`
     (unique index) **before** any broker call;
  2. at most one risk-increasing operation per symbol may be between `SUBMITTED` and a final state
     (in-flight lock, persisted, survives restarts);
  3. an operation is never resubmitted under the same `op_id`;
  4. after any ambiguous response, nothing is resubmitted until reconciliation (§2,
     `RECONCILING`) proves the original did not execute. A new attempt is then a new operation
     with a fresh RiskEngine evaluation within P-29;
  5. closes target a position ticket and re-read its current volume before every attempt, so a
     repeated close of an already-closed position returns 10036 instead of opening anything.
- **EXE-003 Single writer.** Only the `mt5_adapter` worker thread calls the MetaTrader5 package.
  Calls are serialised through a queue with per-call timeouts (C2 clock).
- **EXE-004 Fail closed.** These conditions mean no risk-increasing action is sent: missing or
  invalid SL; spec hash mismatch; `symbol_info`, `account_info` or `terminal_info` returning
  `None` or failing conversion; `terminal_info().connected` false; `terminal_info().trade_allowed`
  false; `account_info().trade_allowed` or `trade_expert` false; tick STALE; reconciliation not
  clean; Guardian not HEALTHY; trading state ≠ ACTIVE.

## 2. Order-submission state machine (risk-increasing actions)

Every state is persisted in `order_intents` with a timestamp before the next step starts.

```
CREATED ─persist op_id─► PERSISTED ─order_check ok─► PRECHECKED ─order_send called─► SUBMITTED
   PERSISTED ─order_check fails─► CLOSED_REJECTED (final)
SUBMITTED ─result received─► ACKNOWLEDGED ─classify retcode (§4)─┬─ SUCCESS ──► AWAITING_CONFIRMATION
                                                                  ├─ PARTIAL ──► AWAITING_CONFIRMATION (partial)
                                                                  ├─ REJECTED ─► CLOSED_REJECTED (final)
                                                                  └─ UNKNOWN class / None ─► UNKNOWN
SUBMITTED ─no result within the per-call timeout─► UNKNOWN          (a timeout is NEVER a failure)
AWAITING_CONFIRMATION ─read-back: filled volume = requested─► CONFIRMED
AWAITING_CONFIRMATION ─read-back: 0 < filled < requested──► PARTIALLY_FILLED
AWAITING_CONFIRMATION ─nothing found within confirm window─► UNKNOWN
UNKNOWN ─► RECONCILING (EXE-014)
RECONCILING ─evidence of execution─► CONFIRMED or PARTIALLY_FILLED
RECONCILING ─evidence of non-execution─► CLOSED_NOT_EXECUTED (final)
RECONCILING ─still ambiguous at the P-25 global deadline─► UNRESOLVED → T20 (SUSPENDED, manual)
CONFIRMED / PARTIALLY_FILLED ─SL verified by read-back (§5)─► COMPLETED (position lifecycle takes over)
CONFIRMED / PARTIALLY_FILLED ─SL missing or wrong─► CONFIRMED_UNPROTECTED → EXE-031
```

- **EXE-013 Timeouts are not failures.** `SUBMITTED` or `AWAITING_CONFIRMATION` without a definite
  answer always becomes `UNKNOWN`, never `REJECTED`.
- **EXE-014 Reconciling an UNKNOWN operation.** Query `positions_get`, `orders_get`,
  `history_orders_get` and `history_deals_get` for the window
  `[persisted_at − 5 s, now]`. Match on `magic` + the `op_id` tag in `comment`. If comment
  preservation is unverified or failed (EXE-021), use the fingerprint
  `(magic, symbol, side, volume, time within ±5 s of SUBMITTED)`.
  - *Evidence of execution:* a matching deal or position.
  - *Evidence of non-execution:* no matching order **or** deal across the full window in two
    queries at least 5 s apart, with the terminal connected throughout. More than one fingerprint
    candidate counts as ambiguous, never as non-execution.
- **EXE-015 Final states:** `COMPLETED`, `CLOSED_REJECTED`, `CLOSED_NOT_EXECUTED`, `UNRESOLVED`.
  Only `COMPLETED` operations create ledger positions. `UNRESOLVED` blocks all new entries (T20).

- **EXE-010** `order_check` runs before every `order_send`. A failed check is final for that
  intent. A new attempt needs a new signal and a new RiskEngine evaluation.
- **EXE-011 Entries are never blindly retried.** After REQUOTE (10004), PRICE_CHANGED (10020) or
  PRICE_OFF (10021), the intent is closed. A new intent may be created only by re-running the full
  RiskEngine at the new price, within the signal's validity (P-29).
- **EXE-012** When the entry needs human approval (TRADING_RISK_SPEC §9), a re-priced entry needs a **new approval**. The original approval
  token is bound to the original proposal hash (API-031).

## 3. Request construction and identification

- **EXE-020** Fields: `action`, `symbol`, `volume` (quantized, RISK-022), `type`, `price`
  (current executable side), `sl` (mandatory), `tp` (optional), `deviation` (P-14), `magic`
  (`MAGIC_ENGINE`), `comment` (`GB:` + 10-char base32 prefix of `intent_id`), `type_time` GTC,
  `type_filling` chosen from the symbol's `filling_mode` flags [VERIFIED S13]. Retcode 10030
  (invalid fill) is a configuration defect: ENTRY_STOP and alert.
- **EXE-021** Comment-field length and preservation by the broker are [BLOCKED: verify in M7].
  If the comment is not preserved, the identification fallback is
  `(magic, symbol, side, volume, open time within ±5 s of send)`, and resends of that intent are
  **disabled** (the engine treats it as UNKNOWN → lookup only).
- **EXE-022 Magic numbers.** `MAGIC_ENGINE` for engine orders; `MAGIC_GUARDIAN` for Guardian
  protective closes and SL placements. Both are configured once and audited. Anything else is
  foreign (EXP-009).

## 4. Retcode classification [VERIFIED S14]

| Class | Retcodes | Engine action |
|---|---|---|
| SUCCESS | 10009 DONE; 10008 PLACED (pending only) | → AWAITING_CONFIRMATION |
| PARTIAL | 10010 DONE_PARTIAL | → AWAITING_CONFIRMATION; §6 |
| PRICE | 10004 REQUOTE, 10020 PRICE_CHANGED, 10021 PRICE_OFF | Entries: CLOSED_REJECTED (EXE-011). Exits: retry within the P-25 deadline with a fresh price |
| THROTTLE | 10024 TOO_MANY_REQUESTS | Back off (P-25); exits retry, entries close |
| UNKNOWN | 10011 ERROR, 10012 TIMEOUT, 10031 CONNECTION, `None` result | → UNKNOWN → RECONCILING (EXE-014) before anything else |
| MARKET | 10018 MARKET_CLOSED, 10017 TRADE_DISABLED, 10044 CLOSE_ONLY | Entries: final reject. Exits: `BLOCKED_MARKET_CLOSED`, new emergency run at the next tradable moment (§8, §12) |
| AUTH/PERMISSION | 10026 SERVER_DISABLES_AT, 10027 CLIENT_DISABLES_AT, 10032 ONLY_REAL | ENTRY_STOP (T12) + alert |
| INVALID | 10013, 10014, 10015, 10016, 10022, 10030, 10035, 10038 | Final; defect alert; ENTRY_STOP if repeated twice |
| LIMIT | 10019 NO_MONEY, 10033, 10034, 10040, 10045, 10046 | Final; ENTRY_STOP + alert (should have been caught by EXP checks) |
| STATE | 10023 ORDER_CHANGED, 10025 NO_CHANGES, 10028 LOCKED, 10029 FROZEN, 10036 POSITION_CLOSED, 10039 CLOSE_ORDER_EXIST | Re-read broker state; reconcile; act on the fresh state |
| OTHER | any code not listed | Treat as UNKNOWN |

## 5. Stop-loss verification

- **EXE-030** After a fill, read the position back and compare `sl` with the intended SL (±1 tick).
- **EXE-031** If the SL is missing or wrong: immediately send `TRADE_ACTION_SLTP` with the intended
  SL (never a wider one). If that is not confirmed within P-22 (3 s): raise T25, then
  EMERGENCY_LIQUIDATE that position (§8). The Guardian independently acts at 10 s (GRD-020). Both
  paths are idempotent: the engine checks the current SL before modifying it, and so does the
  Guardian.

## 6. Partial fills

- **EXE-040** A partial fill is recorded with its actual volume. The engine **never tops up** the
  remainder, because that would be a new risk-increasing action without evaluation. The SL applies
  to the filled volume. Risk accounting uses the filled volume. Any remaining pending part is
  cancelled.
- **EXE-041** Partial **closes** during an exit or emergency: the remaining volume stays in the
  ledger, and the close is retried within the same P-25 global deadline.

## 7. Reconciliation

- **EXE-050** Runs on start, after every confirmed action, after every reconnect, and every P-24.
  It compares the ledger with broker positions, orders and recent deals.
- **EXE-051 Mismatch types:** `MISSING_AT_BROKER` (ledger has it, broker doesn't: closed by SL/TP,
  stop-out or manually → fetch the deal, update the ledger, then it counts as resolved);
  `MISSING_IN_LEDGER` (broker has it, ledger doesn't: adopt it if magic = engine and the intent is
  known; otherwise foreign → T14); `VOLUME_DIFF`; `SL_DIFF`/`TP_DIFF`; `FOREIGN`. Any unresolved
  mismatch → T7; persistent → T8.
- **EXE-052** Reconciliation never trades to "fix" a mismatch. The only exception is the SL
  protection in §5.

## 8. Emergency operations

Three **separate** operations, each a durable record with its own lifecycle. Requesting an action
is separate from completing it. The UI shows the lifecycle state, never a bare "done". There is
**no combined kill-switch button** (user decision; UI-030).

Lifecycle of CANCEL_PENDING and EMERGENCY_LIQUIDATE:
`REQUESTED → AUTHORIZED → SUBMITTED → CONFIRMED | PARTIAL | FAILED_DEADLINE | BLOCKED_MARKET_CLOSED`,
followed by a mandatory `RECONCILED` step that re-reads broker state before the record closes.

| | ENTRY_STOP | CANCEL_PENDING | EMERGENCY_LIQUIDATE |
|---|---|---|---|
| **Effect** | Trading state latch; blocks risk-increasing actions | Cancels eligible pending orders (engine- and Guardian-owned; foreign only if selected) | Attempts to close in-scope positions per EMG-030 |
| **Who may request** | User (dashboard "Stop Entries", CLI, `STOP` file); RiskEngine triggers T1–T27; Guardian | User ("Cancel Pending Orders"); RiskEngine (T2–T4); Guardian | User ("Emergency Liquidation"); RiskEngine (T2–T4, T25, T26); Guardian (GRD-020/026/028) |
| **Authorization (user requests)** | One confirmation | Two-step confirmation listing the orders | Two-step confirmation listing positions, volumes and "fills are not guaranteed", plus re-authentication (TOTP, API-013) |
| **Prerequisites** | None; always accepted | ENTRY_STOP is set first (automatically, and shown as a separate audited action) | ENTRY_STOP is set first (automatically, separately audited); the session state is read |
| **Execution** | Immediate latch | Per order: `TRADE_ACTION_REMOVE` | Per position: market close of the current volume (EMG-020) |
| **Timing** | Immediate | P-25: per-attempt timeout, back-off, max attempts, **global 60 s deadline** | P-25, same |
| **Confirmation rule** | Latch persisted and read back; Guardian echoes the kill flag | `orders_get` shows no eligible pending orders | `positions_get` shows no in-scope positions **and** closing deals are found in history |
| **Final failure** | — | `FAILED_DEADLINE` → T19 | `FAILED_DEADLINE` → T19 + **UNRESOLVED EXPOSURE** alert listing each open position and whether its SL is broker-confirmed |
| **Market closed** | n/a | `BLOCKED_MARKET_CLOSED`; a new run starts at the next tradable moment | `BLOCKED_MARKET_CLOSED`; a new run starts at the next tradable moment. Meanwhile the position has only its broker-side SL **if** one is broker-confirmed (UI-015) |
| **Disconnected / terminal down** | Latched locally and by the Guardian (if running) | Cannot execute → `FAILED_DEADLINE` → T19 | Cannot execute → `FAILED_DEADLINE` → T19. The alert states the last known SL status per position, with its confirmation time, or UNKNOWN |
| **Audit** | requester, reason, time, state before/after | each order ticket, retcode, attempt #, timings | each position, retcodes, fill prices, slippage vs request, residual volume, deadline used |

- **EMG-001** EMERGENCY_LIQUIDATE is **best-effort**. It can be delayed or worsened by gaps,
  slippage, rejects, closed markets, halts (10017/10044), partial closes, or terminal/broker
  outages. Nothing in the UI or docs may claim it is guaranteed.
- **EMG-010 Emergency sequence.** The supported sequence is Stop Entries → Cancel Pending Orders →
  Emergency Liquidation. Each step is a separate control, a separate confirmation and a separate
  audit record. An automatic trigger that needs several steps (T2–T4) records them as separate
  operations in that order.
- **EMG-020 Retry schedule.** Per P-25: an attempt is a market close (or removal) with
  `deviation = 2 × P-14`, followed by broker read-back. If not confirmed within the per-attempt
  timeout (5 s), wait the next back-off interval (1, 2, 4, 8 s) and re-read the position before the
  next attempt. Maximum 5 attempts. No attempt starts if the remaining global deadline is shorter
  than the per-attempt timeout. Worst case 40 s ≤ 60 s deadline. At the deadline: `FAILED_DEADLINE`.
- **EMG-030 Scope policy** (configurable, default shown): engine-owned and Guardian-owned
  positions and orders are in scope. Foreign ones are included **only** when the user ticks
  "include foreign positions" in the Emergency Liquidation or Cancel Pending dialog.
- **EMG-040** Emergency actions run on the engine's priority queue, ahead of all normal work. The
  Guardian runs its own path independently (GRD-040), using the lease and check-then-act rules to
  avoid duplicate closes (GRD-050/051).

## 9. Restart and recovery

- **EXE-070 Startup sequence:** load and validate config + hashes → Phase-0 guard (`env=LIVE`) →
  initialise MT5 → account/symbol discovery (CENT-002..005) → compare spec hash → read Guardian
  heartbeat → full reconciliation → rebuild limit state from deal history (TIME-056) → adopt
  engine-owned positions → resolve every operation left in `SUBMITTED`…`RECONCILING` (EXE-014)
  → trading state starts at **ENTRY_STOP**. It moves to ACTIVE automatically only if the previous
  shutdown was clean **and** every active trigger is `AUTO`-class with its checks passing
  (RISK-052). Otherwise manual recovery is required.
- **EXE-071** After an unclean restart, automatic entry permission is paused, whatever the
  configured mode (TRADING_RISK_SPEC §9). Only the user can re-enable it.
- **EXE-072 Broker maintenance and weekends.** During closed sessions, entries are not generated.
  Emergency actions record `BLOCKED_MARKET_CLOSED` and start a new run at the next tradable moment.
  Reconciliation continues while connected.

## 10. Execution-quality monitoring

- **EXE-060** Tracked per session: fill latency (send → confirm), entry slippage versus request
  price (in points and in account currency), reject rate by class, SL-attach failures, and partial
  fill count. A breach of any threshold set in M7 from demo data [BLOCKED: needs M7 measurements]
  → automatic entry is demoted to human approval (RISK-062) and the strategy goes to WATCH (RES-040).

## 11. Required chaos tests (M7/M9)

Kill the engine mid-order; kill the terminal with an open position; drop the network for 120 s;
inject a `None` result after a successful send (duplicate-prevention test); duplicate a UI command;
send an emergency close while the market is closed (session simulation in FakeBroker); return a
partial fill; return 10027 (algo trading disabled); move the wall clock ±1 h; corrupt the Guardian
heartbeat file; delete the SL right after the fill (both engine and Guardian paths fire, with no
duplicate modification); leave a position open at the session-close deadline in FakeBroker with
every close rejected (T26 and the UNRESOLVED EXPOSURE alert); simulate an early close that appears
only in the live session export (T27, deadlines recomputed); make an emergency run hit its 60 s
deadline (FAILED_DEADLINE, never "done").

## 12. No overnight or weekend holding (user decision)

The bot must not intentionally hold a position across the daily break/rollover or the weekend.
It cannot be assumed that a position can always be closed before the market closes, so every
step below has a failure path.

- **EXE-080 Session calendar.** Session ends come from the Guardian's live session export
  (CENT-005), converted with TIME-030. The export is a **weekday template only**: it has no
  calendar dates, holidays or one-off early closes [VERIFIED S36]. Known holidays and early closes
  therefore come from a user-maintained `config/session_exceptions.yaml`, filled from broker
  announcements (A-59). A broker session change appears as T27.
- **EXE-081 Pre-close entry restriction.** No new entries inside the P-19 window before any
  session end. A strategy whose expected holding time cannot finish before P-33 may not enter
  (GV-28).
- **EXE-082 Pending orders.** At the P-19 window start, CANCEL_PENDING runs automatically for all
  in-scope pending orders.
- **EXE-083 Close deadline.** At P-33, every in-scope position is closed by a normal strategy exit
  or, if still open, by an EMERGENCY_LIQUIDATE run (EMG-020). Closure counts only when it is
  broker-confirmed (closing deal found and position absent).
- **EXE-084 Failed-close escalation.** If a position is still open after that run: T26
  (SUSPENDED); further runs continue while the market is open; the dashboard shows an **UNRESOLVED
  EXPOSURE** state with the position, its volume and its broker-confirmed SL (or UNKNOWN). Close
  attempts never stop silently.
- **EXE-085 Weekend protection.** The final session of the week uses the longer P-19/P-33 values.
  If the session calendar is UNKNOWN (export missing, stale > 7 days, or inconsistent with the
  exceptions file), entries are blocked from the earliest plausible close: the published hours
  [S2] minus the P-19 window.
- **EXE-086 Disconnection near the close.** If the terminal is disconnected when the close deadline
  arrives, the engine cannot act, and neither can the Guardian. The alert states that any position
  is held over the break or weekend with only its broker-side SL **if** one was broker-confirmed.
  On reconnect, close runs start at the first tradable moment.
