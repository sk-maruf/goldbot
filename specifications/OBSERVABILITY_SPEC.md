# OBSERVABILITY_SPEC — Logs, metrics, health, alerts

> Status: **SPECIFICATION.** The rule above all others: **unknown is never shown as healthy**
> (OBS-001 / UI-010).

## 1. Structured logs

- **OBS-010** JSON lines with: `ts_utc`, `mono_seq`, `level`, `component`, `env`, `event`,
  `trace_id`, `op_id`/`command_id` where relevant, and `details`. Secrets are redacted (SEC-004).
  Logs never contain the account login in clear (PRV-011).
- **OBS-011** Levels: DEBUG (dev only), INFO, WARN, ERROR, CRITICAL. CRITICAL is reserved for safety
  events: every trigger that `TRADING_RISK_SPEC.md` §7 marks CRITICAL, plus T2, T3 and T17, a Guardian
  takeover, an emergency action ending `FAILED_DEADLINE`, and an audit-chain verification failure.

## 2. Metrics (stored in SQLite, shown in the System screen)

Tick age; ticks/s; spread (current, session median); NTP offset; server-offset estimate;
reconciliation duration and mismatch count; order latency; slippage; reject counts by class;
heartbeat ages (engine→Guardian, Guardian→engine); API latency; command queue depth; DB write
latency; min-volume rejection rate (CENT-030); lifecycle transitions and rejections by reason (MI-160); trailing modifications sent, rejected and the last broker-confirmed SL (MI-172); exits by reason code (MI-185); decisions by outcome and `NO_TRADE` reason per
strategy (MI-045); risk utilisation per P-xx; LLM spend (if enabled);
MCP calls by tool.

## 3. Health model

Each component has a state of `HEALTHY | DEGRADED | UNHEALTHY | FAILED | UNKNOWN`, with a reason and the
time of the last state change.

| Component | HEALTHY when | UNKNOWN when |
|---|---|---|
| MT5 terminal | `terminal_info()` OK, `connected` true, `trade_allowed` true | No successful `terminal_info()` in 10 s |
| Broker connection | `connected` true and ping < 1 s (`TERMINAL_PING_LAST` [S15]) | Terminal UNKNOWN |
| Market data | Tick age ≤ P-15 (session open) or market correctly CLOSED | No tick read ever / adapter down |
| Guardian | Heartbeat fresh (P-21), integrity digest valid, folder ACL check passed, `config_status=OK`, limits not looser. **FAILED** (not just unhealthy) on an integrity, ACL or duplicate-instance failure (T22) | Heartbeat never seen or file unreadable |
| Clock | NTP offset < warn (P-16) and server offset stable | NTP never reached since start |
| Reconciliation | Last run < 2 × P-24 ago and clean. Shown as **UNRECONCILED** when older, failed, or still running after a reconnect | Never run since start |
| Stop-loss protection | Every open position has an SL that was broker-confirmed by read-back at the last reconciliation | Any open position whose SL has not been read back, or broker data is unavailable → shown as **UNKNOWN**, never as protected |
| Session-end readiness | The live session calendar is valid (EXE-080) and the next close deadline is known | Calendar missing or stale → UNKNOWN; entries blocked (EXE-085) |
| RiskEngine | Config hash matches; last evaluation succeeded | Engine down |
| Intelligence modules | Every module returned within its timeout without an error (MI-018); `data_quality` INSUFFICIENT (MI-015) is a data condition, not a module fault | A module error or timeout → UNKNOWN; decisions that need it are `NO_TRADE` |
| Execution | No UNKNOWN intents older than P-25 window | Engine down |
| API / Web | Serving; stream messages within 5 s | Stream silent > 5 s (client-side) |
| MCP (optional) | Running, last call OK | Not configured → shown as "Off", not as UNKNOWN |

- **OBS-001** The aggregate status shown in the top bar is the **worst** component state, and
  UNKNOWN ranks worse than DEGRADED for display purposes. GREEN is shown only when every required
  component is HEALTHY.
- **OBS-002** Every health computation has a timeout. A computation that times out yields UNKNOWN,
  never the previous value.

## 4. Alerts

- **OBS-020 Channels (user decision): the local dashboard only.** Critical alerts stay visible as
  persistent banners until acknowledged, and they remain in an alert history. No Telegram, email, SMS
  or other external channel is a dependency or a default. Windows notifications are
  local, so they are allowed: approval notifications are on by default (OBS-024), and other alerts
  may use them as an optional add-on, off by default. Any external channel requires a separate ADR
  (ADR-013).
- **OBS-023 Missed-alert protection.** Because alerts live only in the dashboard, the dashboard shows
  on open every CRITICAL alert raised while it was closed, with timestamps, before anything else.
- **OBS-024 Approval notifications.** Whenever an entry needs human approval, the open dashboard
  raises a browser notification (Notification API; loopback counts as a secure context, A-66) with a
  short chime. It is on by default and can be switched off in Settings. The text names no amount,
  account or price: "GoldBot: trade proposal waiting, expires in <P-23> s". The dashboard must be
  open (a minimised window is enough); with it closed, the proposal expires unseen. An engine-side
  Windows toast that works with the dashboard closed needs a new dependency (CLAUDE.md §7) and goes
  to the backlog.
- **OBS-021** Alert on: every CRITICAL event; any component UNKNOWN or UNHEALTHY > 30 s; NTP warn;
  min-volume rejection rate > 50% (CENT-031); strategy WATCH/PAUSED; backup or restore-test failure;
  dependency-audit failure.
- **OBS-022** Each alert links to a RUNBOOK section and states what the system has *already* done
  (e.g. "ENTRY_STOP set; liquidation REQUESTED, not yet confirmed").

## 5. Operational targets (measured in M9; failures block M10)

| Target | Value |
|---|---|
| Reconciliation runs on schedule | ≥ 99.5% of intervals during sessions |
| Mismatch resolution | 100% resolved or escalated within 60 s |
| Heartbeat freshness (both directions) | ≥ 99.9% of minutes within limits |
| Safety-event alert delivery | 100% of CRITICAL events produce a visible alert within 5 s |
| Audit-chain verification | 100% daily passes |
