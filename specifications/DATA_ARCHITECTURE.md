# DATA_ARCHITECTURE — Stores, schemas, classification, retention

> Status: **SPECIFICATION.** Classification classes C1–C4 are defined in `PRIVACY_POLICY.md` §2.

## 1. Stores

| Store | Technology | Writer(s) | Readers | Notes |
|---|---|---|---|---|
| Operational DB | SQLite, WAL mode, `PRAGMA synchronous=FULL` | `engine` (all trading tables); `api` writes **only** `commands` and `sessions` | engine, api, mcp_server (via api only) | One writer per table (DATA-001) |
| Research store | Parquet, partitioned `symbol/account_class/yyyy/mm/` + manifest JSON | `research` | research, backtester | Provenance per BT-011 |
| Experiment registry | SQLite `research.db` (separate file) | `research` | research, api | Append-only, hash-chained (RES-010) |
| IPC files | JSON in `TERMINAL_COMMONDATA_PATH\Files\goldbot\` | per `GUARDIAN_SAFETY_SPEC.md` §3 | engine, Guardian | Atomic rename, SHA-256 digest, seq, folder ACL (GRD-008) |
| Logs | JSON lines, daily rotation | all processes | user | Redacted (SEC-004) |
| Secrets | OS keyring | installer, user | engine, api, mcp_server (own token only) | Never on disk in plain text |
| Config | YAML in Git (`config/`) + schemas: `risk_limits.yaml` (with user-approval fields, RISK-092), `app.yaml`, `session_exceptions.yaml` (EXE-080). **No secrets in any config file** | user | all | `risk_limits.yaml` hashed (RISK-090) |

- **DATA-001 Single writer per table.** Cross-process writes happen only through the `commands`
  table (api → engine). The engine consumes commands and writes the results.
- **DATA-002 IDs.** UUIDv7 for every record (time-ordered). An order intent's `op_id` is the idempotency
  key (EXE-002).
- **DATA-003 Timestamps.** UTC, timezone-aware, ms precision (TIME-011), plus the engine's monotonic
  sequence number for ordering within a process.
- **DATA-004 Money columns** are stored as TEXT decimal strings plus a currency column. Never as REAL.
- **DATA-005 Env tagging.** Every row has `env` (LIVE/DEMO/BACKTEST/REPLAY). LIVE and DEMO use
  **separate database files**, and the engine refuses to open a DB whose `env` header doesn't match
  its config (prevents mixing real and simulated data).

## 2. Operational tables (summary)

| Table | Key fields | Class | Retention |
|---|---|---|---|
| `account_snapshots` | ts, login_hash + salt_version (PRV-012), currency, balance, equity, margin, margin_free, margin_level, leverage | C3 | 7 y (PRV) |
| `symbol_specs` | ts, symbol, spec_json, spec_hash, verified_by_user | C2 | forever (small) |
| `ticks_sample` | ts_msc, recv_mono, bid, ask, flags | C1 | 30 d (full history lives in Parquet) |
| `decision_records` | decision_id, ts, strategy@version, regime labels, outcome (BUY_CANDIDATE / SELL_CANDIDATE / WAIT / NO_TRADE), bullish and bearish scores, evidence ids by group, excluded evidence with reasons, data quality, invalidation, rationale, reason codes, params (MI-045) | C2 | candidates 7 y; WAIT / NO_TRADE 90 d |
| `setup_lifecycle_events` | id, setup_id, decision_id, ts, from_state, to_state (MI-160), reason codes, risk_decision_id, authorization mode | C2 | 7 y |
| `management_events` | id, ticket, op_id, ts, kind (TRAIL / BREAK_EVEN / PARTIAL / EXIT / PARTIAL_INFEASIBLE), method, old and new SL/TP, broker-confirmed SL after read-back, reason code, decision and evidence ids (MI-172, MI-185) | C2 | 7 y |
| `pattern_outcomes` (research store) | pattern evidence_id, type, timeframe, formation_ts, confirmation_ts, MFE and MAE in ATR, target reached before invalidation, horizon (MI-123) | C2 | with its research run |
| `signals` | id, decision_id (MI-002), strategy@version, ts, side, entry, sl, tp, gate_results | C2 | 7 y |
| `risk_decisions` | id, signal_id, inputs_hash, decision, reason_codes, volume, modelled_loss | C2 | 7 y |
| `proposals` | id, decision_id, proposal_hash, expires_mono, status | C2 | 7 y |
| `approvals` | id, proposal_hash, nonce, user, ts, outcome | C2 | 7 y |
| `order_intents` | op_id (UUIDv7, unique), action, volume, price, sl, tp, state (EXE §2, every transition timestamped), retcodes[], in_flight_lock, reconciliation evidence | C3 | 7 y |
| `positions_ledger` | ticket, op_id, magic, volume, open, sl, tp, state, reconciled_at | C3 | 7 y |
| `deals` | deal ticket, position, volume, price, profit, commission, fee, swap | C3 | 7 y |
| `limit_state` | day_start_equity, week_start_equity, hwm, consecutive_losses, ts | C3 | 7 y |
| `trading_state_events` | ts, trigger T#, from, to, actor, reason | C2 | 7 y |
| `emergency_actions` | id, type (CANCEL_PENDING / EMERGENCY_LIQUIDATE), requester, authorization, lifecycle state, attempts[] with timings, global deadline, scope, result, reconciliation | C3 | 7 y |
| `failure_events` | ts, trigger T#, severity, recovery class, cooldown, health-check results, resumed_by (AUTO/ACK/MANUAL) | C2 | 7 y |
| `admin_requests` | id, client_id, action, args_hash, status (PENDING/APPROVED/EXPIRED/REJECTED/DONE), approver, result hash | C2 | 1 y |
| `journal_notes` | id, trade_id, note, content_origin, hidden flag (append-only) | C3 | 7 y |
| `mcp_clients` | client_id, display name, allowed tools/actions, token hash, created, revoked | C2 | while registered + 1 y |
| `commands` | id, type, payload_json, actor, auth_context, status, result | C2 | 1 y |
| `audit_log` | seq, ts, actor, event, payload_hash, prev_hash, hash | C2 | 7 y |
| `health_events` | ts, component, from, to, detail | C2 | 1 y |
| `sessions` | session_id_hash, user, created, last_seen, scope | C4-adjacent (hashes only) | expiry |
| `consents` | flow, client/provider, granted_at, withdrawn_at | C2 | 7 y |
| `llm_calls` (optional) | ts, payload_hash, tokens, cost, response_json | C2 | 30 d |

## 3. Schemas (M0 generates `schemas/*.schema.json`; Python models are generated or checked against them)

`SymbolSpec`, `AccountSnapshot`, `Tick`, `Bar`, `Evidence`, `DecisionRecord`, `SetupLifecycleEvent`, `ManagementEvent`, `Signal`, `PreTradeGateResult`, `RiskDecision`,
`RiskApprovedAction`, `TradeProposal`, `Approval`, `OrderIntent`, `ExecutionReport`,
`PositionState`, `ReconciliationResult`, `TradingStateEvent`, `EmergencyAction`, `Command`,
`ModeChange`, `HealthStatus`, `AuditEvent`, `EngineHeartbeat`, `GuardianHeartbeat`,
`GuardianConfig`, `ExperimentRun`, `McpToolInput/*`, `McpToolOutput/*`, `LlmPayload`.

- **DATA-010** Every schema has `schema_version`. Breaking changes need a migration plus an ADR
  line.
- **DATA-011** A CI test keeps the Pydantic models, the TypeScript types (generated) and the JSON
  schemas in sync.

## 4. Migrations, backup, integrity

- **DATA-020** Migrations are versioned scripts. The engine refuses to start on a schema-version
  mismatch.
- **DATA-021** Backups and restore tests follow PRV-030/031.
- **DATA-022** `PRAGMA integrity_check` daily. Audit `verify_chain()` daily (SEC-022).
