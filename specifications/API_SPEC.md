# API_SPEC — Local REST + WebSocket interface

> Status: **SPECIFICATION.** The API serves the dashboard and the optional MCP server. It never
> calls MT5 and never makes trading decisions. Every command is re-validated by the engine
> (API-020).

## 1. Binding and transport

- **API-001** Default bind `127.0.0.1:<port>`. A `Host` header allowlist (`127.0.0.1:<port>`,
  `localhost:<port>`) defends against DNS rebinding.
- **API-002** The startup self-check refuses any non-loopback bind (TM-17). Remote access is not
  part of the design (user decision, ADR-013). Enabling it later requires a separate ADR, TLS, a
  threat-model update and user approval.
- **API-003 Security headers:** `Content-Security-Policy: default-src 'self'; frame-ancestors 'none'`;
  `X-Content-Type-Options: nosniff`; `Referrer-Policy: no-referrer`; no CORS (same-origin SPA
  served by the API).

## 2. Authentication and sessions

- **API-010** Single local user. Password (argon2id hash) + TOTP at login. The session cookie is
  `HttpOnly`, `SameSite=Strict`, `Secure` when TLS is used, `__Host-` prefix when TLS is used. Idle
  expiry 30 min, absolute 12 h, rotated on login and on privilege elevation.
- **API-011** Login rate limit: 5 attempts / 15 min per process, then a 15-min lockout (audited).
- **API-012 CSRF:** synchronizer token header on every state-changing request, plus the `Origin`
  check.
- **API-013 Re-authentication** (TOTP within the last 2 min) is required for: enabling any automatic
  entry mode or strategy auto-approval (RISK-061), clearing ENTRY_STOP/SUSPENDED (RISK-050 and ACK
  class), EMERGENCY_LIQUIDATE, enabling LLM/MCP flows, registering or re-scoping an MCP client,
  approving a `queue_research_job` admin request, and tightening limits.

## 3. Authorization scopes

| Scope | Held by | Allows |
|---|---|---|
| `ui:read` | Logged-in dashboard session | All GET routes and WebSocket read channels |
| `ui:command` | Logged-in dashboard session | Command routes (§4), each with extra conditions |
| `mcp:read` | Per-client MCP token (keyring, MCP-021) | Only the GET routes backing the 9 MCP read tools |
| `mcp:admin:<action>` | Per-client MCP token, only for actions the user enabled for that client | Only `POST /v1/mcp/admin-requests` for that action; it creates a PENDING request and never executes directly |

- **API-040** Authorization is checked server-side on **every** route against an explicit
  route × scope table. Unlisted pairs are denied. A test iterates the full matrix (TM-15).

## 4. Routes (v1)

**Read (`ui:read`; `*` = also `mcp:read`)**
`GET /v1/account*` · `/v1/market/snapshot*` · `/v1/positions*` · `/v1/orders` ·
`/v1/trades?from&to&limit*` · `/v1/risk*` · `/v1/strategies/performance*` · `/v1/health*` ·
`/v1/audit/summary*` · `/v1/research/reports*` · `/v1/research/reports/{id}*` · `/v1/proposals` ·
`/v1/emergency/actions` · `/v1/config/limits` (read-only view)

**Commands (`ui:command`)**: each creates a row in `commands`. The engine validates and executes it,
and the result streams back over the WebSocket.

| Route | Command | Extra conditions |
|---|---|---|
| `POST /v1/proposals/{id}/approve` | APPROVE | Approval token (API-031); hold-to-confirm in the UI |
| `POST /v1/proposals/{id}/reject` | REJECT | — |
| `POST /v1/state/entry-stop` | ENTRY_STOP | — (always allowed) |
| `POST /v1/state/clear` | CLEAR_STATE | Re-auth; RISK-050 checklist confirmed |
| `POST /v1/emergency/cancel-pending` | CANCEL_PENDING | Two-step confirm |
| `POST /v1/emergency/liquidate` | EMERGENCY_LIQUIDATE | Re-auth; two-step confirm; scope flag (EMG-030) |
| `POST /v1/mode` | MODE_CHANGE | Values `MANUAL_APPROVAL` / `AUTO_ALL` / `AUTO_APPROVED_STRATEGIES`; moving to `MANUAL_APPROVAL` always allowed; enabling automation needs re-auth + typed phrase + RISK-061 |
| `POST /v1/strategies/{id}/auto-approval` | STRATEGY_AUTO_APPROVAL | Re-auth; that strategy passed RISK-063; used only in `AUTO_APPROVED_STRATEGIES` |
| `POST /v1/mcp/admin-requests/{id}/approve` | MCP_ADMIN_APPROVE | Dashboard session only (never an `mcp:*` scope); re-auth where MCP §4.1 requires it |
| `POST /v1/mcp/clients` | MCP_CLIENT_REGISTER / REVOKE | Re-auth; MCP-030/024 |
| `POST /v1/limits/tighten` | TIGHTEN_LIMIT | Re-auth; the engine verifies the new value is stricter (RISK-090) |
| `POST /v1/consents` | CONSENT | Re-auth for LLM/MCP |

There are **no** routes to loosen limits, change leverage, place arbitrary orders, edit config files,
run SQL or read secrets. There is **no** combined "panic" route: the three emergency operations
have separate routes (user decision; EMG-010). Approve/reject routes exist only for entries that
need human approval (TRADING_RISK_SPEC §9).

- **API-020** The engine re-validates every command against current state (trading state, mode,
  freshness, RiskEngine). The API's checks are a convenience and never the authority.
- **API-021 Idempotency.** Every command carries a client UUID. A duplicate UUID returns the original
  result.

## 5. Approvals

- **API-030** A proposal is shown with `proposal_hash = sha256(canonical proposal JSON)`.
- **API-031 Approval token** = `HMAC(server_key, proposal_hash ‖ nonce ‖ session_id ‖ expiry)`,
  issued when the card is displayed. It is single-use (nonce stored), expires per P-23, and is
  invalid if the proposal hash changes. On use, the engine re-runs the RiskEngine (RISK-004).
- **API-033** Approve buttons sit in a page that cannot be framed (API-003) and need a hold-to-confirm
  gesture of ≥ 800 ms, or a keyboard confirm dialog.

## 6. WebSocket

- **API-050** `GET /v1/stream` upgrades only with a valid session cookie **and** an `Origin` matching
  the served origin. A per-connection token (from `/v1/stream/token`, 60-s TTL) is sent in the first
  message. Read-only channels: `account`, `market`, `positions`, `risk`, `health`, `proposals`,
  `commands`, `emergency`. Clients cannot send commands over the WebSocket.
- **API-051** Every message carries `env`, `as_of_utc`, `seq`, and a `freshness` field. The client
  shows UNKNOWN when messages stop for > 5 s (UI-010).

## 7. Validation, errors, limits, audit

- **API-060** Pydantic models with `extra="forbid"` for every body and query. Numeric bounds;
  string caps.
- **API-061 Errors:** RFC 9457-style problem JSON with `type`, `title`, `status`, a `trace_id`, and
  **no** stack traces, SQL or paths.
- **API-062 Rate limits** (per session): 60 req/min reads; 10 req/min commands; the MCP scope per
  MCP-035.
- **API-063 Audit:** every command and every authentication event → `audit_log`.
