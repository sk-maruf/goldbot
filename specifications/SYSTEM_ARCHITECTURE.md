# SYSTEM_ARCHITECTURE — GoldBot V2

> Status: **SPECIFICATION (not implemented).** Sources: `quality/SOURCES.md`.
> Labels: **[VERIFIED Sx]** documented fact, **[REPORTED Sx]** unconfirmed doc claim,
> **[ASSUMPTION]**, **[RECOMMENDATION]**, **[OPEN]**, **[BLOCKED: needs …]**.

## 1. Purpose and honest framing

GoldBot is a risk-first, fail-closed, rules-based trading system for gold on an Exness MT5
**Standard Cent** account with about $100 of capital (about 10,000 USC). It is
**AI-assisted**: statistics generate signals, ML models are optional research artefacts, and
an LLM may help with research and explanations. **No LLM output can create, approve or alter
an order.**

**Objective function.** Maximise *net expectancy after all costs*, subject to the risk
limits in `TRADING_RISK_SPEC.md`. **Win rate is reported but never optimised.** A high win
rate usually comes from small targets and wide stops (negative skew). That profile is the
one most easily destroyed by spreads, gaps and stop slippage, and it is the profile most
likely to be skipped by the cent minimum-lot rule. See `STRATEGY_RESEARCH_SPEC.md` §6.

**Economics.** At ~$100, even a strong validated edge produces single-digit dollars per
month (worked in `CENT_ACCOUNT_VALIDATION.md` §7). Success is defined as **safe, correct,
auditable behaviour and an honest edge verdict**. "No edge found" is a valid, successful
outcome (RES-020).

## 2. Canonical terminology (every other file uses these exact terms)

| Term | Definition |
|---|---|
| **Entry authorization mode** (operating mode) | `MANUAL_APPROVAL`, `AUTO_ALL` or `AUTO_APPROVED_STRATEGIES` (`TRADING_RISK_SPEC.md` §9). **Pending user decision (D-01, P-37)**; LIVE entries are blocked until it is decided, and fixture demo (RISK-066) sets a mode per test run. Position closing is automatic in every mode. |
| **Trading state** | Latching permission state enforced by the RiskEngine: `ACTIVE` → `ENTRY_STOP` → `SUSPENDED`. Higher states block more. See `TRADING_RISK_SPEC.md` §7. |
| **Pre-trade gate** | A stateless check that rejects one signal (stale tick, wide spread, blackout window, closed session). A failed gate does **not** change the trading state on its own. |
| **Emergency action** | `CANCEL_PENDING` or `EMERGENCY_LIQUIDATE`. Each is a *request* with a lifecycle (`REQUESTED → SUBMITTED → CONFIRMED / PARTIAL / FAILED / TIMED_OUT / BLOCKED_MARKET_CLOSED`). Requesting an action never implies it completed. See `EXECUTION_SAFETY_SPEC.md` §8. |
| **ENTRY_STOP** | A trading state that blocks all new entries and all risk-increasing modifications. Exits and risk-reducing modifications remain allowed. |
| **SUSPENDED** | ENTRY_STOP plus automatic-strategy shutdown. Leaving it requires **manual recovery approval** (RISK-050). |
| **Emergency controls** | Three separate dashboard controls: **Stop Entries**, **Cancel Pending Orders**, **Emergency Liquidation**. Each has its own visual identity, confirmation, lifecycle and audit record. There is **no** combined kill-switch button (user decision; the V2 "Panic" shortcut was removed). |
| **Recovery class** | `AUTO`, `ACK` or `MANUAL` per trigger (`TRADING_RISK_SPEC.md` §7). |
| **UNRECONCILED** | Display state when the last reconciliation is older than 2 × P-24, failed, or is still running after a reconnect (UI-012). |
| **UNRESOLVED EXPOSURE** | An open position that should have been closed (emergency or session end) but has no broker-confirmed close (EXE-084). |
| **Environment (`env`)** | `LIVE`, `DEMO`, `BACKTEST` or `REPLAY`. Every record, screen and report carries it. |
| **Account class** | `CENT` or `STANDARD`, derived from live account and symbol discovery (CENT-002), never from configuration alone. |
| **Health** | `HEALTHY`, `DEGRADED`, `UNHEALTHY`, `FAILED` or `UNKNOWN`, per component (`OBSERVABILITY_SPEC.md` §3). Unknown is never shown as healthy (UI-010). |
| **Broker-confirmed** | State read back from MT5 (`positions_get`, `orders_get`, `history_deals_get`) *after* an action, as opposed to the local ledger. |
| **Risk budget** | Maximum modelled loss for one trade, in account currency, from `TRADING_RISK_SPEC.md` §3. |
| **Intervention threshold** | A loss/drawdown level that **triggers** protective actions. It is **not** a guaranteed maximum loss (RISK-040). |
| **Evidence** | One detection by one market-intelligence module (for example a liquidity sweep or a BOS), with `detected_at`, confidence score, data quality, invalidation and reasons (MI-010). |
| **Decision record** | The decision engine's output for one strategy version at one time: `BUY_CANDIDATE`, `SELL_CANDIDATE`, `WAIT` or `NO_TRADE`, with the evidence used and excluded (MI-041, MI-045). |
| **Candidate** | A `BUY_CANDIDATE` or `SELL_CANDIDATE`. It is only a proposal for the pre-trade gates and the RiskEngine and never an approval (MI-003). |

## 3. Component model

```
                     ┌──────────────────── Windows runtime host ───────────────────────┐
                     │                                                                 │
  Broker trade  ◄────┤ MT5 terminal                                                    │
  server             │   ├─ Guardian EA (MQL5) — independent safety component          │
  (Exness)           │   │     heartbeats, ownership checks, missing-stop response,    │
                     │   │     equity interventions, calendar export, kill latch       │
                     │   │        ▲ atomic JSON files in TERMINAL_COMMONDATA_PATH      │
                     │   │        ▼                                                    │
                     │   └─ MetaTrader5 Python bridge (same machine) [VERIFIED S9,S18] │
                     │                                                                 │
                     │ engine (Python process; sole owner of the MT5 Python session)   │
                     │   mt5_adapter (single worker thread) → conversion boundary      │
                     │   market_data → intelligence → strategy → signal_validator      │
                     │   → RiskEngine (pure, deterministic, ONLY approval authority)   │
                     │   → execution → reconciler → position_manager                   │
                     │   trading_state · emergency_controller · clock · audit_log      │
                     │        │ SQLite (WAL): state, ledger, commands, audit (hash-chain)│
                     │ api (FastAPI, 127.0.0.1)  ◄── web (React SPA, desktop-first)    │
                     │ mcp_server (OPTIONAL, stdio; read + approved non-trading admin)  │
                     │            ──► api (per-client mcp scopes, MCP_SECURITY_SPEC)     │
                     └─────────────────────────────────────────────────────────────────┘
  research (any OS): tick ingestion → Parquet → backtester → experiment registry
  shared library goldbot.core: money, conversion, specs, sizing, RiskEngine rules,
                               strategy interface (imported by engine AND backtester)
  shared library goldbot.intelligence: market-intelligence modules + decision engine,
                               pure (imported by engine AND backtester; MARKET_INTELLIGENCE_SPEC)
```

| Component | Responsibility | Must never |
|---|---|---|
| `goldbot.core` | Pure functions: `Money`, decimal conversion, sizing, RiskEngine rules, limit state maths, strategy interface. | Perform I/O, read clocks or call MT5. |
| `intelligence` | Market-intelligence modules and the decision engine (`MARKET_INTELLIGENCE_SPEC.md`): pure functions that turn bars and ticks into Evidence and decision records; candidates only. V2.2 adds modules 11–12 and the pure setup, lifecycle, trailing and exit-evaluation functions (MI-150..185), which the position manager calls; their proposals go to the RiskEngine. | Perform I/O, read clocks, call MT5, set volume or limits, or produce a `RiskApprovedAction` (MI-001/003). |
| `mt5_adapter` | The only code that calls the MetaTrader5 package; runs on one worker thread; converts every float at the conversion boundary (RISK-003). | Make decisions; retry orders without the idempotency protocol. |
| `RiskEngine` | The only constructor of `RiskApprovedAction` (entries, risk-increasing modifications). | Be bypassed, configured by an LLM, or loosened at runtime. |
| `execution` | Turns `RiskApprovedAction` into broker requests; confirms through broker read-back. | Treat a request as a fill (EXE-001). |
| `reconciler` | Compares broker-confirmed state with the ledger on start and every `P-24` seconds. | Auto-"fix" a mismatch by trading. |
| `emergency_controller` | Runs CANCEL_PENDING / EMERGENCY_LIQUIDATE lifecycles. | Report completion without broker confirmation. |
| Guardian EA | Independent safety layer inside MT5 (`GUARDIAN_SAFETY_SPEC.md`). | Open positions; loosen any limit; act when MT5 is down (it cannot). |
| `api` | Local REST + WebSocket for the UI; commands go through a validated `commands` table. | Bind to non-loopback interfaces by default; expose secrets. |
| `web` | Watercolor Glass dashboard (`prompts/UI_DESIGN_BRIEF.md`). | Show green when health is UNKNOWN. |
| `mcp_server` | Optional, stdio MCP interface: read-only tools plus explicitly approved, non-trading administrative actions (`MCP_SECURITY_SPEC.md`). | Execute, modify or close orders; change any risk, Guardian or trading state; be a dependency of the engine. |
| `research` | Data pipeline, backtester, validation, registry. | Import `engine` or `mt5_adapter` order paths. |
| `llm` (optional) | Summaries and hypothesis drafts from sanitised statistics. | Have tools, see secrets/PII, or reach the order path. |

## 4. Process and trust boundaries

| Boundary | Between | Control |
|---|---|---|
| B1 | Broker ⇄ MT5 terminal | Broker-side SL/TP; outside our control while the terminal is offline. |
| B2 | Python engine ⇄ MT5 terminal | Single adapter thread; conversion boundary; retcode handling (`EXECUTION_SAFETY_SPEC.md`). |
| B3 | Python engine ⇄ Guardian EA | Atomic files with SHA-256 integrity digests, sequence numbers, instance checks and a Windows folder ACL; no shared secret (`GUARDIAN_SAFETY_SPEC.md` §3, GRD-008). |
| B4 | UI/API ⇄ engine | `commands` table; every command is re-validated by the engine (API-020). |
| B5 | Browser ⇄ API | Loopback bind, auth, CSRF, session expiry (`API_SPEC.md`). |
| B6 | MCP client ⇄ MCP server ⇄ API | stdio, per-client scopes, allowlist, per-invocation dashboard approval for admin actions, redaction (`MCP_SECURITY_SPEC.md`). |
| B7 | LLM provider ⇄ engine | Outbound only, sanitised minimum data, spend cap (PRV-020). |
| B8 | Research ⇄ live | Shared `core` only; research never holds trading credentials. |

**Process model [RECOMMENDATION, ADR-002].** `engine` and `api` are separate processes. A UI
crash cannot stop protection logic. The API never calls MT5. The MCP server is a third,
optional process that talks only to the API.

## 5. Key data flows

**Entry needing human approval** (`MANUAL_APPROVAL`, or a strategy not auto-approved under
`AUTO_APPROVED_STRATEGIES`). strategy signal → signal_validator (pre-trade gates) → RiskEngine
`evaluate()` → `TradeProposal` stored with hash → UI shows proposal → user approves (token
bound to proposal hash, nonce, expiry `P-23`) → engine **re-runs the RiskEngine** with fresh
market/account state → `RiskApprovedAction` → execution → broker read-back → ledger →
reconciliation.

**Automatic entry** (`AUTO_ALL`, or an auto-approved strategy). Identical, except that the
approval step is replaced by the promotion-gated automatic permission (RISK-061). The RiskEngine
evaluation is never skipped.

**Session end.** P-19 window → no entries + CANCEL_PENDING → P-33 deadline → strategy exits or
EMERGENCY_LIQUIDATE → broker-confirmed close, or T26 + UNRESOLVED EXPOSURE (EXE-080..086).

**Exit / risk-reducing modification.** Strategy, position manager or Guardian requests it →
RiskEngine `evaluate_reduction()` checks only that the action reduces risk (e.g. SL moves
toward price, partial close) → execution. Exits are allowed in every trading state.

**Emergency.** Trigger (manual, limit intervention, Guardian) → trading state latch →
emergency actions with lifecycle → broker confirmation or explicit FAILED state → alert.

## 6. Architecture decisions (M0 writes these as `docs/adr/*.md`)

| ADR | Decision (recommended default) | Rejected alternative and reason |
|---|---|---|
| 001 | Python executes via the MetaTrader5 package; an independent MQL5 Guardian EA is the second safety layer. | EA-owned execution with a Python bridge: more IPC and harder for the builder agent to test. |
| 002 | `engine`, `api`, optional `mcp_server` are separate processes; commands go through SQLite. | Single process: a UI fault could block protection logic. |
| 003 | Custom event-driven bid/ask tick backtester that imports `goldbot.core`. | Third-party frameworks: sizing/risk parity with live becomes unprovable. |
| 004 | SQLite (WAL) + Parquet; no PostgreSQL in v1. | Postgres: operational cost with no benefit at this scale. |
| 005 | Local desktop dashboard: React + TypeScript SPA served on loopback, opened in a desktop browser window, responsive. Flutter desktop remains an open user choice (M0 question). | — |
| 006 | `BrokerPort` interface with `Mt5Broker` and a deterministic `FakeBroker`. | Direct MT5 calls everywhere: untestable off Windows. |
| 007 | The Guardian exports the MQL5 economic calendar to a file (no third-party API key). Fallback: manual blackout schedule. | External calendar API: extra key, extra trust boundary. |
| 008 | The LLM is off the order path, disabled by default, spend-capped, schema-validated, tool-less. | LLM signal generation: weak evidence [S30, S31]; prompt-injection surface [S24]. |
| 009 | MCP is optional and stdio-only: read tools plus approved non-trading admin actions, each approved per invocation in the dashboard; no order execution. | MCP with trading tools: an unacceptable path to trading actions. |
| 010 | Time architecture per `TIME_AND_CLOCK_SPEC.md` (Guardian exports server time). | Using the last tick time as "server now": wrong when the market is quiet or closed. |
| 011 | Engine ⇄ Guardian channel: SHA-256 integrity + seq + instance + Windows folder ACL; **no shared secret** (GRD-008). | HMAC key in a file or in EA inputs: breaks the keyring-only rule and gives no protection against same-user processes. DLL access to Credential Manager: forbidden by GRD-005 without a new ADR. |
| 012 | Entry authorization mode: **pending user decision** (D-01). All three modes are specified; none is chosen. | Choosing on the user's behalf. |
| 013 | Local-only deployment on the user's Windows computer; dashboard-only notifications; no remote access or external monitoring without a separate ADR. | Cloud hosting, VPS, external notification services. |

## 7. Deployment

- **Runtime host (user decision):** the user's **local Windows computer**. No cloud-hosted
  trading architecture. Remote access and external monitoring are not part of the design; adding
  them requires a separate ADR and a threat-model update (ADR-013). The MetaTrader5 Python package ships
  Windows x86-64 wheels only [VERIFIED S18]. The MT5 terminal, Guardian EA, engine and API
  run on the same host.
- **Development host:** any OS, using `FakeBroker` and recorded fixtures. `mt5`-marked tests
  run only on the Windows host.
- **Availability limits [by design].** If the computer sleeps or shuts down, or the terminal or
  broker connection is down, neither Python nor the Guardian can act. Only SL/TP orders that were
  broker-confirmed earlier remain at the broker, and they do not guarantee the exit price (GRD-030).
  The runbook therefore requires power and sleep settings that keep the computer awake during
  trading sessions, and the no-overnight rule (EXE-080) limits how long any position is exposed.
- **Independence from external services.** Order authorization, risk, sizing, stop calculation,
  emergency operations, reconciliation and the Guardian run fully locally. They keep working
  when LLM providers, MCP clients or the internet beyond the broker connection are unavailable
  (LLM-006).

## 8. Explicitly not in v1 (moved to `docs/BACKLOG.md` by M0)

Strategy selector outside M6f (M6f builds one only if the user chooses it in D-12 and at least two
strategies PASS; it trades only after it PASSes as a C4 strategy, RES-061, MI-052); ML signal models
(pending decision D-10); PostgreSQL; multi-symbol trading. **Not in the design at all unless the
user decides otherwise through a separate ADR:** cloud or VPS hosting, remote access, Telegram,
email, SMS or any other external notification channel. **Permanently prohibited:** MCP trading
tools (MCP-010) and any LLM-generated trade logic (LLM-001).

## 9. LLM policy (applies everywhere)

- **LLM-001** No LLM output can create, approve, size, modify or cancel an order, or change any
  limit, mode or state. The order path has no import of the `llm` module (static test).
- **LLM-002** Permitted uses: drafting research hypotheses (each tested hypothesis counts as a trial,
  RES-021), summarising deterministic reports, explaining metrics in plain language. Outputs are
  labelled "AI-generated, advisory".
- **LLM-003** Inputs follow PRV-020/021. Outputs follow SEC-031 (schema-validated, never executed).
- **LLM-004** Disabled by default. When enabled: provider pinned in config, monthly spend cap P-28
  enforced in code (calls refused at the cap), and consent recorded (PRV-018).
- **LLM-005** The trade-proposal rationale shown to the user is a **deterministic template**, not LLM
  text, so the user always sees the actual rule that fired.
- **LLM-006 No AI dependency for safety.** No external AI service is a dependency of order
  authorization, risk calculation, stop-loss calculation, position sizing, emergency operations or
  broker reconciliation. If the AI provider is unavailable, AI features show "unavailable", nothing
  is queued that contains user data, there are no retry storms (maximum 1 retry, then wait 5 min),
  and the trading system continues unchanged. A test runs the full REPLAY suite with the network to
  every AI provider blocked and expects identical trades.
