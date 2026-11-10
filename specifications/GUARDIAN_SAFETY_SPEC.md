# GUARDIAN_SAFETY_SPEC — The independent MQL5 safety component

> Status: **SPECIFICATION.** Corrects V1 audit item **D**. The Guardian is **not** a second copy
> of the engine. It has no strategy, never opens positions, and does not depend on the Python
> engine being alive.

## 1. Role and independence

- **GRD-001** The Guardian is an MQL5 Expert Advisor attached to one chart in the same MT5
  terminal. It runs whether or not the engine is running.
- **GRD-002 Hard limits come from EA input parameters** that the user sets by hand when attaching
  the EA: daily-loss %, drawdown %, max open positions, max volume per position, the per-position
  **emergency-SL loss budget %** (GRD-020), missing-stop grace seconds, the Guardian close deadline
  (GRD-028), emergency retry settings (same structure as P-25), `MAGIC_ENGINE`, `MAGIC_GUARDIAN`,
  and a `rearm_counter` (GRD-016). The inputs contain **no secret**.
- **GRD-003** The engine's `guardian_config.json` may only **tighten** these inputs. For every
  limit, the Guardian uses `min(input, file)` for loss and size limits and `max(input, file)` for
  grace and margin floors where stricter means larger. Loosening values in the file are ignored and
  reported.
- **GRD-004** The Guardian never opens a position, never places a pending order, never widens an
  SL, and never changes account settings.
- **GRD-005** Size target: ≤ 1,000 lines of MQL5, no external DLLs, no web requests.

## 2. What the Guardian can and cannot guarantee

| It CAN (only while the terminal runs, is connected, and algo trading is allowed) | It CANNOT |
|---|---|
| Detect a stale or missing engine heartbeat | Act when the PC is off or asleep, the terminal is closed, or the EA is removed |
| Add an SL **within its approved loss budget** to an engine-owned position that has none, or request a close when no budget-compliant SL is possible | Act when the broker connection is down or the market is closed. It can only latch and log |
| Request closes when its own equity thresholds are crossed | Guarantee a close fills, or fills at any particular price (gaps, slippage, rejects, halts, closed market) |
| Latch a kill flag that the engine must obey | Prevent the engine from sending orders by force. The engine obeys the flag by design; a buggy engine could ignore it, and that case is covered by RISK tests and reconciliation |
| Export server time, sessions and calendar | Protect against a compromised Windows user account (`SECURITY_THREAT_MODEL.md` TM-10) |

- **GRD-030** All documentation and UI text must state: *when MT5, the host or the broker
  connection is unavailable, neither the engine nor the Guardian can act. Only SL/TP orders that
  were broker-confirmed before the outage remain at the broker, and they do not guarantee the exit
  price.* The UI never claims that a position is protected unless its SL is broker-confirmed
  (UI-015).

## 3. Files and atomic exchange

All files live in `TERMINAL_COMMONDATA_PATH\Files\goldbot\` [VERIFIED S15: file operations are
allowed in the data and common-data paths].

| File | Writer | Reader | Purpose |
|---|---|---|---|
| `engine_hb.json` | engine | Guardian | Engine heartbeat and state summary |
| `guardian_hb.json` | Guardian | engine | Guardian heartbeat, clocks (TIME-030), kill flag, effective limits |
| `guardian_config.json` | engine | Guardian | Tighten-only overrides |
| `guardian_sessions.json` | Guardian | engine | `SymbolInfoSessionTrade` export (CENT-005) |
| `guardian_calendar.json` | Guardian | engine | High-impact USD events (TIME-042) |
| `guardian_audit.jsonl` | Guardian | engine (ingest) | Hash-chained action log |
| `guardian_state.json` | Guardian | Guardian | Persisted day-start equity, HWM, kill flag (also mirrored in terminal GlobalVariables) |

- **GRD-006 Atomic write.** The writer writes `<name>.tmp`, flushes, closes, then renames over the
  target: Python `os.replace` (atomic rename on the same NTFS volume [ASSUMPTION, standard Windows
  behaviour; verified by a test in M2]); MQL5 `FileMove(tmp, FILE_COMMON, name,
  FILE_REWRITE|FILE_COMMON)` [VERIFIED S16].
- **GRD-007 Reader rules.** Open with shared read; up to 3 attempts 50 ms apart; parse; validate
  schema version, required fields, the integrity digest (GRD-008) and `seq > last_seq`. A file that fails is
  ignored, the last good one is kept, and the failure is counted. Age is measured with the
  **reader's** monotonic clock since `seq` last changed (TIME-015). The writer's clock is never
  trusted for staleness.
- **GRD-008 Channel integrity without a shared secret (resolves the keyring contradiction).**
  V2 originally used an HMAC key stored both in the keyring and in a `guardian.key` file. That broke
  the keyring-only rule (CLAUDE.md §3.14), and it added no protection against the realistic
  attacker. The corrected design:

  | Element | Decision |
  |---|---|
  | Why no secret | The MQL5 reference documents no function for the Windows Credential Manager [ASSUMPTION, A-60]. Reaching it would need DLL imports (`advapi32` `CredReadW`), which GRD-005 forbids. MQL5 also has no native HMAC or asymmetric signatures [VERIFIED S17]. Any key the Guardian could read would sit in an ordinary file or in EA inputs (terminal profile files), both forbidden for secrets. And any process running as the same Windows user can read that user's keyring entries anyway, so a key would not stop same-user malware (TM-07/TM-10) |
  | Integrity | Every message carries `digest = SHA-256(canonical_json_without_digest)` (`CRYPT_HASH_SHA256` [VERIFIED S17]; Python `hashlib`). This detects corruption and torn or partial writes |
  | Freshness / replay | `instance_id` (random per process start, not secret) + strictly increasing `seq`; age is measured by the reader's monotonic clock (GRD-007) |
  | Writer authentication | **Windows ACL** on `…\Files\goldbot\`: owner = the trading Windows account; inheritance disabled; full control for that account and SYSTEM only. The engine verifies the ACL at start and hourly; any deviation → T22 |
  | Duplicate writers | Two different live `instance_id`s writing `engine_hb.json` within P-21 → the Guardian latches `kill_flag` (reason `DUPLICATE_ENGINE`) and the engine raises T22 |
  | Key generation / storage / delivery / rotation | **Not applicable**: no shared secret exists. Nothing to deliver, rotate or revoke |
  | Revocation of a writer | Stop the process. Its `instance_id` goes stale. A new instance is accepted only after the previous one has been stale for > P-21 |
  | Recovery | Runbook: stop the engine, restore the folder ACL (scripted `icacls` command), delete the IPC files, restart, complete manual recovery (RISK-050) |
  | Compromise handling | ACL changed, unknown file owner, digest failures without a known cause, or a duplicate engine → T22 (MANUAL). The user is told to scan the PC and rotate the MT5 and dashboard passwords (SEC-007) |
  | Failure behaviour | An invalid message is ignored and the last good one is kept. Three consecutive failures, or any ACL failure → T22 |
  | Residual risk | Same-Windows-user malware can forge messages. This is accepted and stated (TM-07/TM-10). Cryptographic authentication between same-user processes is not achievable without a secret that the same malware could also read |
  | Future alternative | DLL-based Credential Manager access is possible only through a new ADR, a threat-model update and explicit user approval. It is not part of v1 |

## 4. Heartbeat protocol

- **GRD-010** The engine writes `engine_hb.json` every P-20 (2 s). Fields: `schema`, `instance_id`
  (random per engine start), `seq`, `utc_ms`, `trading_state`, `operating_mode`, `env`,
  `ledger_positions` (`ticket`, `volume`, `sl`), `sl_pending` (tickets awaiting SL confirmation with
  their deadlines), `emergency_lease_until_utc` (GRD-050), `config_hash`, `digest`.
- **GRD-011** The Guardian writes `guardian_hb.json` every 5 s. Fields: `schema`, `instance_id`,
  `seq`, clock fields (TIME-030), `tick_age_ms` (TIME-023), `terminal_connected`, `trade_allowed`,
  `kill_flag`, `effective_limits` (after GRD-003), `positions_seen`, `takeover` (bool + last action),
  `config_status` (`OK` / `INVALID` / `STALE`), `unresolved_exposure` (GRD-020/028), `last_error`, `digest`.
- **GRD-012 Staleness.** The Guardian considers the engine STALE when `seq` hasn't changed for
  15 s (P-21). The engine considers the Guardian stale after 20 s → T9.
- **GRD-013** If the engine's `effective_limits` check finds the Guardian **looser** than the
  approved P-02/P-04/P-05/P-32, or its close deadline later than the session end minus 2 × the P-25
  global deadline → ENTRY_STOP and alert ("Guardian inputs looser than policy"). Tighter is
  acceptable and is displayed. While any of those parameters is still USER_DECISION_REQUIRED, the
  check compares against the fixture values, and the engine can then start only in fixture demo
  (RISK-066), never in LIVE (RISK-005).

## 5. Engine-health response (no takeover just because the engine is quiet)

- **GRD-015** When the engine is STALE, the Guardian sets `kill_flag = ENTRY_STOP` and enters
  **protective duty**: it continues the GRD-020 missing-stop checks and the GRD-025 equity checks.
  It does **not** close positions merely because the engine is stale, because the positions carry
  broker-side SLs. Closing would add cost and risk without cause.
- **GRD-016 Clearing the Guardian's kill flag.** When the engine returns, it reads `kill_flag` and
  starts in ENTRY_STOP (EXE-070).
  - Reason `ENGINE_STALE` only: the flag clears automatically when the engine has been HEALTHY for
    60 s, its heartbeat shows a clean reconciliation, and no other Guardian reason is active.
  - Any other reason (`TAKEOVER`, `EQUITY_INTERVENTION`, `STATE_LOST`, `DUPLICATE_ENGINE`,
    `UNRESOLVED_EXPOSURE`, `DISCONNECTED` with an SL re-verification failure): the flag clears
    **only** when the user changes the EA input `rearm_counter` by hand in the terminal. A file from
    the engine cannot clear it. This keeps the Guardian independent of a faulty engine. The engine
    shows "Guardian re-arm required" during manual recovery (RISK-050).

## 6. Ownership and position identification

- **GRD-018** Positions with `magic == MAGIC_ENGINE` or `MAGIC_GUARDIAN` are in scope. Others are
  **foreign**: the Guardian reports them and never acts on them. Only the user's Emergency
  Liquidation with "include foreign positions" ticked (EMG-030, executed by the engine) closes them.
- **GRD-019** Every Guardian trade request uses `MAGIC_GUARDIAN` and a comment `GG:<action-id>`.

## 7. Missing-stop response and stop verification

- **GRD-020 Missing-stop response within an approved loss budget.** Triggered by
  `OnTradeTransaction` [SEARCH-ONLY S34] and a 1-second timer scan. For each in-scope position with
  no SL:
  1. If the engine is HEALTHY and the ticket is listed in `sl_pending` with an unexpired deadline,
     wait.
  2. After the grace input (default 10 s, P-22), re-select the position. If the SL is still
     missing, **determine the permitted emergency loss**:
     `L = emergency-SL loss budget % × equity` (account currency).
  3. **Calculate a broker-valid stop price.** Start from the price at which the loss from
     `price_open` equals L. Move it **toward the current price** onto the tick grid. Check that its
     distance from the current price satisfies the stops and freeze levels.
  4. **Calculate the actual monetary loss** at that stop with `OrderCalcProfit(type, symbol, volume,
     price_open, sl, profit)` [VERIFIED S38: account currency; returns false on failure].
  5. **Compare** that loss with L. If `OrderCalcProfit` fails, or loss > L, or no stop satisfies both
     the budget and the broker distance rules (for example, the position is already losing more
     than L), then **do not place the stop**. The Guardian **never widens** a stop distance to satisfy
     broker restrictions.
  6. Otherwise place the SL (`TRADE_ACTION_SLTP`) and verify it by re-selecting the position.
  7. If no budget-compliant SL was placed or verified, **follow the emergency-close policy**: request
     a market close with the Guardian's retry settings (same structure as P-25, global deadline).
  8. If the close fails: set `takeover=true` and `unresolved_exposure=[tickets]` in the heartbeat,
     write the audit record, and keep starting new close runs while the market is open. The engine
     raises T18 and T26/T25 as applicable.
- **GRD-021** The Guardian never moves an existing SL.

## 8. Independent equity interventions

- **GRD-025** The Guardian keeps its own day-start equity (00:00 UTC via TIME-030 offset) and equity
  high-water mark. They are persisted in `guardian_state.json` and in terminal GlobalVariables.
- **GRD-026** When equity loss ≥ its daily-loss input, or drawdown ≥ its drawdown input: set
  `kill_flag`, cancel in-scope pending orders, request closes of in-scope positions with retries,
  and set `takeover=true`. This mirrors T2/T4, so if the engine is alive it has normally acted first.
  GRD-050 prevents double action.
- **GRD-028 Session-end backstop.** If an in-scope position is still open at the Guardian's close
  deadline input (later than P-33 and at least 2 × the P-25 global deadline before the session end,
  taken from its own session export plus the exceptions the engine passes in `guardian_config.json`),
  and no engine emergency lease is active, the Guardian requests a close using its retry settings.
  On failure: `takeover=true`, `unresolved_exposure` reported, and new runs while the market is open.
- **GRD-027** On restart (`OnInit`): load persisted values. If they are missing or invalid, rebuild
  day-start equity from today's deal history. If the HWM cannot be rebuilt, set HWM = current equity
  and **set kill_flag = ENTRY_STOP** with reason `STATE_LOST`. A user re-arm is then required (GRD-016).

## 9. Duplicate-action and conflict prevention

- **GRD-050 Lease.** When the engine starts an emergency action, it writes
  `emergency_lease_until_utc` (now + 30 s) in its heartbeat. While the lease is valid and the engine
  is HEALTHY, the Guardian does not start the same action and only verifies. After the lease expires
  or the engine goes stale, the Guardian may act.
- **GRD-051 Check-then-act.** Before every action, both sides re-read the specific position
  (`PositionSelectByTicket` / `positions_get(ticket=…)`). Retcode 10036 (position already closed)
  and 10039 (close order exists) count as "already done", not as failures.
- **GRD-052** SL placement by the engine and by the Guardian are both conditional on "SL is missing
  right now". A second modification therefore becomes a no-op (10025 NO_CHANGES is treated as
  success).

## 10. Disconnection, failure detection and audit

- **GRD-033 Terminal disconnected** (`TERMINAL_CONNECTED` false [VERIFIED S15]): the Guardian
  latches `kill_flag`, logs it, and on reconnect re-verifies SLs and equity before anything else.
- **GRD-031 Guardian failure detection by the engine:** stale heartbeat → T9 (AUTO class); three
  consecutive integrity failures, an ACL failure or a duplicate engine instance → T22 (MANUAL) +
  security alert; `trade_allowed` false in `terminal_info()` → T12; on `OnDeinit` the Guardian
  writes a final heartbeat with the deinit reason.
- **GRD-032 Audit.** Every Guardian decision and action is appended to `guardian_audit.jsonl` with
  `seq`, `prev_hash` and `hash` (SHA-256 chain). The engine ingests it into the main audit log and
  verifies the chain.

## 11. Exports

- **GRD-040 Takeover reporting.** Any Guardian trading action (SL placement or close) sets
  `takeover=true` → engine T18 (SUSPENDED).
- **GRD-041 Sessions/calendar.** Weekly export of `SymbolInfoSessionTrade` for the configured symbol,
  and of high-impact USD events for the next 7 days, refreshed every 6 h.

## 12. Tests (M7)

SHA-256 digests against NIST test vectors (MQL5 script + Python), with identical canonical JSON on
both sides; a pure-function test script for limit and budget maths; scripted demo scenarios: engine
killed with a position (no close, SL verified); SL removed manually (Guardian adds a
**budget-compliant** SL at 10 s and the `OrderCalcProfit` loss ≤ L is logged); a position already
losing more than L with its SL removed (no SL placed, close requested); stops level forcing a stop
beyond budget (no SL placed, close requested); daily-loss threshold simulated with the Guardian's
input tightened to 0.01% on demo (closes, takeover reported); corrupt/partial heartbeat files;
replayed heartbeat (old `seq`); a second engine instance (DUPLICATE_ENGINE); folder ACL changed to
grant another account write access (engine T22); kill flag cleared only by `rearm_counter`; engine
and Guardian both trying to add the same SL (one no-op); session-end backstop with the engine
stopped; terminal disconnect and reconnect; EA removed (engine raises T9 within 20 s).

## 13. Build and test loop (how the builder compiles and tests MQL5)

- **Layout.** `mql5/Include/GoldBot/guardian_core.mqh` holds the pure logic: limit maths, the
  GRD-020 budget stop calculation, canonical JSON, digests and the kill-flag rules.
  `mql5/Experts/GoldBotGuardian.mq5` is a thin EA around it. `mql5/Scripts/GuardianTests.mq5`
  includes the same `.mqh`, runs assertion tests and writes `guardian_test_results.json` to the
  common `Files\goldbot\` folder.
- **Compile.** `metaeditor64.exe /compile:"<file>.mq5" /log:"<file>.log"` [ASSUMPTION A-65: verify
  the flags and the log format in M2]. The exit code is not trusted. A build passes only when the
  log reports 0 errors and 0 warnings. `uv run goldbot mql5-build` wraps this, and its test fails on
  any error or warning.
- **Automated tests.** The pure-logic tests run in `GuardianTests.mq5`; a Python test (marker
  `mt5`) asserts on the results file. Python and MQL5 share the canonical-JSON and NIST SHA-256
  fixtures.
- **`[HUMAN]` steps.** Some §12 scenarios need hands on the terminal. Each is marked `[HUMAN]` in
  `docs/TEST_PLAN.md` with an exact instruction for the user and the evidence to collect (a log line,
  a heartbeat field or a screenshot). The builder pauses and asks for it. A `[HUMAN]` test passes
  only with that evidence (GOV-002). In §12 these are: attaching the EA and setting its inputs;
  changing `rearm_counter`; removing an SL by hand; tightening the daily-loss input to 0.01%;
  removing the EA; disconnecting the terminal. The folder-ACL change and the duplicate-engine test
  are scripted.
