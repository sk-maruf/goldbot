# MCP_SECURITY_SPEC — Optional MCP interface (read tools + approved non-trading admin actions)

> Status: **SPECIFICATION.** New in V2 (V1 had no MCP design). MCP spec version to pin in ADR-009:
> **2026-07-28** (current at access date [VERIFIED S22]). Re-verify at M8.

## 1. What MCP is (and is not) here

- **MCP-001** The MCP server is an **optional**, separate process that lets an external AI client
  (e.g. Claude Desktop) *read* GoldBot status and research, and request a small set of explicitly
  approved **non-trading** administrative actions (§4.1). **Order execution is strictly prohibited.** The engine, Guardian, RiskEngine and
  dashboard work identically whether it exists or not. The engine has **no** import of, call to or
  health dependency on it.
- **MCP-002 Not to be confused with:**
  - the **REST/WebSocket API** (`API_SPEC.md`), which is GoldBot's own interface that the MCP server
    calls;
  - **Claude Code skills/plugins** (ECC, Karpathy, design skills), which shape how the code is
    *written* and do not exist at runtime;
  - **ordinary tool functions** inside the engine;
  - **LLM features** (LLM-xxx), which are outbound calls from GoldBot to a provider. MCP is inbound
    requests from a client.

## 2. Architecture

```
External AI client (Claude Desktop, etc.)
   │ stdio (client launches the server process)                         [trust boundary B6]
   ▼
mcp_server (Python, separate process, runs as the same user; profile = GOLDBOT_MCP_CLIENT)
   ├─ tool allowlist (9 read tools + enabled admin actions, §4) + JSON-schema validation
   ├─ rate limiter + audit
   ├─ output sanitiser / redactor
   ▼ HTTP to 127.0.0.1 with that client's own token (scopes: mcp:read [+ mcp:admin:<action>])
api (enforces scopes on every route server-side; no trading or safety route accepts any mcp scope)
   ├─ read routes ─► SQLite (never MT5)
   └─ admin routes ─► create a PENDING admin request ─► user approves in the dashboard ─► executes
      in its declared boundary (§4.1)
```

- **MCP-005 Transport.** Local **stdio** only in v1. The MCP security guidance recommends stdio for
  locally run servers to limit access to the launching client [VERIFIED S21].
- **MCP-006 Credentials.** Per the MCP authorization spec, stdio servers should not run the OAuth
  flow and should take credentials from the environment [VERIFIED S20]. The MCP server reads the
  API token of **its client profile** (`GOLDBOT_MCP_CLIENT`) from the OS keyring at start-up
  (keyring entry `goldbot/mcp/<client_id>`; the environment-equivalent secure source).
  It never accepts a token from the client, never forwards client tokens (no token passthrough
  [VERIFIED S21]), and never holds MT5 credentials.
- **MCP-007 Network transport (not in v1).** If ever needed: Streamable HTTP per the pinned spec
  [S22, S23]; TLS; loopback only (remote access is outside the design, ADR-013); OAuth 2.1 authorization with PKCE, resource
  indicators and audience-bound tokens, with tokens validated as issued for this server [VERIFIED
  S20]; per-client consent; a separate ADR, threat-model update and user approval. Without all of
  these, network MCP is **prohibited**.

## 3. Prohibited capabilities

- **MCP-010** No MCP tool, resource, prompt or any other feature may: place trades; approve or
  reject a trade proposal; close positions; cancel orders; modify stop-losses; modify take-profits;
  change risk limits or any P-xx; change leverage; change the entry authorization mode or enable
  autonomous trading; clear, trigger or disable any safety control (entry stop, emergency
  operations, recovery); modify Guardian configuration; bypass or call the RiskEngine; read
  credentials or keyring entries; access arbitrary files or paths; execute shell commands; run
  arbitrary SQL; fetch URLs.
- **MCP-011 Enforcement in depth:**
  1. the server exposes only the §4 tools and the admin actions the user enabled (no
     resources/prompts features in v1);
  2. its code has no MT5 import and no route builder for trading or safety endpoints (static test);
  3. each client token holds only `mcp:read` plus the specific `mcp:admin:<action>` scopes enabled
     for that client;
  4. the API rejects every `mcp:*` scope on every trading, safety, config and approval route
     (API-040), and admin routes only create pending requests that a human must approve.

  Any one layer failing still leaves the others.

## 4. Tool catalogue

### 4.0 Read-only tools

Every input schema uses `additionalProperties: false`. Every output carries
`{"env", "tier", "as_of_utc", "health"}` so that a client cannot mistake demo, backtest or stale data
for live data.

| Tool | Inputs (bounded) | Output (summary) |
|---|---|---|
| `get_account_status` | none | account class, currency, balance, equity, margin used/free, margin level, effective leverage, trading state, operating mode. Login shown hashed (PRV-011) |
| `get_market_snapshot` | `symbol` (enum of the configured symbol) | bid, ask, spread, tick age, freshness state (REAL_TIME/DELAYED/STALE/CLOSED), session state, next blackout |
| `get_open_positions` | none | broker-confirmed positions and ledger positions side by side, with reconciliation status |
| `get_trade_history` | `from_utc`, `to_utc` (≤ 90 days), `limit` ≤ 500 | closed trades: times, side, volume, entry/exit, P/L in account currency and R, strategy@version |
| `get_risk_status` | none | each P-xx limit vs current utilisation, active triggers (T#), emergency action lifecycles |
| `get_strategy_performance` | `strategy` (enum), `tier` (PT1/PT2/PT3) | expectancy and CI, trade count, min-volume rejection rate (CENT-030), strategy state (RES-040) |
| `get_system_health` | none | per-component health (OBS) incl. MT5 terminal, broker connection, Guardian, clock, last reconciliation |
| `get_audit_summary` | `from_utc`, `to_utc` (≤ 30 days), `limit` ≤ 200 | event types, counts, chain-verification status; no secrets, no raw payloads |
| `get_research_report` | `report_id` (from an enum list endpoint) | the stored report's structured fields + markdown body (user/system-authored only) |

### 4.1 Approved non-trading administrative actions (each disabled by default)

These actions cannot increase trading risk or bypass security controls. Each is enabled per client
by the user (MCP-030). **Every invocation** creates a PENDING admin request that the user approves
in the dashboard within 5 minutes, otherwise it expires.

| Action | Exact permission | User authorization | Input validation | Audit record | Execution boundary | Rollback / recovery |
|---|---|---|---|---|---|---|
| `generate_report` | `mcp:admin:generate_report` | Per-invocation dashboard approval | `report_type` enum (daily, weekly, strategy, risk); `from_utc`/`to_utc` ≤ 90 days | client, request id, args hash, approver, output file hash | Research worker with a **read-only** DB connection; writes one **new** file under `reports/` with a generated name; never overwrites | Delete the generated file from the dashboard; nothing else changes |
| `annotate_trade_journal` | `mcp:admin:annotate_journal` | Per-invocation dashboard approval (shows the note text) | `trade_id` must exist and be closed; `note` plain text ≤ 1,000 chars, control characters stripped | client, trade id, note hash, approver | Appends to `journal_notes` (append-only), tagged `content_origin=mcp_client`. No decision path reads this table (static test) | The note can be hidden (soft flag) but never edited; the audit keeps both events |
| `queue_research_job` | `mcp:admin:queue_research` | Per-invocation dashboard approval + TOTP (resource use) | `template` enum of pre-registered research templates; parameters bounded by the template schema | client, job id, template, params hash, approver; registry row with `origin=mcp` (counts as a trial, RES-021) | Separate research process at low OS priority with a CPU cap. Starts only when no position is open and the engine is ACTIVE and HEALTHY; pauses automatically when a position opens, an entry window starts, or health degrades | Cancel from the dashboard; the registry row stays (status `aborted`) — registry rows are never deleted (RES-012) |

- **MCP-016** Adding any other admin action requires a written entry with all seven columns above,
  an ADR line, a threat-model update and user approval. An action that could alter trading,
  risk, safety, Guardian, credential or audit state can never be added.

- **MCP-015 Validation.** Strict schema validation. Strings are capped at 128 characters and must be
  enum-checked where possible. Dates are parsed as UTC with bounded ranges. Unknown tools and extra
  fields are rejected with a generic error.

## 5. Authorization, client trust and consent

- **MCP-020** The API checks every request's scopes server-side, against the client's own token
  (token audience `goldbot-api`). The MCP server's own allowlist is a second layer, not the primary
  control.
- **MCP-021 Client identity (what is realistic locally).** Each registered client gets a
  `client_id` and its **own** random token in the keyring. The client's MCP configuration launches
  the server with `GOLDBOT_MCP_CLIENT=<client_id>`, and the server loads only that client's token.
  The API attributes every call to that `client_id` and enforces that client's scopes.
- **MCP-022 Same-Windows-user limits (stated honestly).** Over stdio, the server cannot
  cryptographically verify which program launched it. Any process running as the same Windows
  user can start the server with any profile, or read that user's keyring entries. Per-client
  tokens therefore provide **separation of permissions, attribution in the audit, and independent
  revocation among cooperating clients**. They do **not** provide isolation against a malicious
  same-user process (TM-07). The control that does hold against automated misuse is the
  **per-invocation human approval** for admin actions (MCP-030). Read access remains exposed to a
  same-user attacker, which is accepted residual risk (TM-03).
- **MCP-023 Unauthorized clients.** An unknown or revoked `client_id` → the server refuses to start.
  A token that doesn't match the profile → 401 at the API. Five failures in 10 minutes → a dashboard
  security alert. Scope violations → 403, audited.
- **MCP-024 Revocation.** Disabling a client in the dashboard deletes its keyring token and adds the
  token hash to the API deny list immediately. Pending admin requests from that client are expired.
- **MCP-030 Client registration and consent.** The user enables MCP per client in Settings (re-auth,
  API-013). This records the `client_id`, display name, the read tools allowed, any admin actions
  allowed, and the consent date (PRV-018). The server refuses to start if no client is registered.
- **MCP-031 Client trust boundary.** The external AI client and its model provider receive whatever
  the tools return. The UI consent screen says so explicitly and shows a sample output.
- **MCP-035 Rate limits.** 30 calls/min overall; 5 calls/min for `get_trade_history` and
  `get_research_report`. Excess calls get a rate-limit error, and the event is audited.

## 6. Output safety

- **MCP-040 Redaction.** No C4 data, ever. The login is hashed. An optional "privacy mode" (default
  **on**) returns amounts as % of equity and R instead of currency.
- **MCP-041 Prompt-injection defence.** Outputs are structured JSON. Free-text fields are limited to
  user- or system-authored text (strategy notes, reports), carry a `content_origin` field, have
  control characters stripped, and are length-capped. No text from external sources (news, web) is
  ever returned.
- **MCP-042** Errors are generic (`{"error": "unavailable" | "invalid_input" | "rate_limited" |
  "not_permitted"}`) with no stack traces, paths or SQL.

## 7. Audit, failure behaviour, testing

- **MCP-045** Every call is audited: `client_id`, tool or action, SHA-256 of the arguments, outcome,
  result size, latency, and for admin actions the approval id and approver.
- **MCP-050 Failure behaviour.** MCP server down → nothing else changes. API down → tools return
  `unavailable` (no retries inside a single call). The MCP server never caches C3 data on disk.
- **MCP-060 Security tests (M8):** call every non-listed tool name; inject extra properties, SQL
  strings, path traversal, oversized strings and out-of-range dates; use the `mcp:read` token
  directly against every API command route (expect 403); scan outputs for secrets; flood the rate
  limiter; kill the API mid-call; verify that the engine's behaviour is identical with MCP
  enabled vs disabled (same trades in a REPLAY run); call each admin action without approval
  (expires, nothing executes); approve with a revoked client (rejected); use client A's profile to
  request an action enabled only for client B (403); attempt every MCP-010 operation through every
  route with every `mcp:*` scope (403); check that `queue_research_job` pauses when a position opens;
  confirm that MCP admin rows never reach a decision path.
