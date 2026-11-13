# ADR-009: MCP is optional and stdio-only: read tools plus approved non-trading admin actions; no order execution

Status: Accepted (specification, 2026-11-13)

## Context

The user may want an external AI client (for example Claude Desktop) to read GoldBot status and
research. Any such interface is an inbound path from software the project does not control. MCP
must never become a path to trading actions (MCP-010), and the engine must work identically with
or without it (MCP-001). Kickoff question 5 (build an MCP server in M8, and which admin actions) is
NOT ANSWERED, so M8 builds no MCP server until the user chooses it (`docs/STATUS.md` §9).

## Options

| Option | Summary | Assessment |
| --- | --- | --- |
| A | Optional stdio MCP server: nine read tools plus admin actions the user enables per client, each approved per invocation in the dashboard | Chosen as the design, if the user opts in |
| B | MCP with trading or safety tools | Rejected: an unacceptable path to trading actions; permanently prohibited (MCP-010, SYSTEM_ARCHITECTURE §8) |
| C | Network MCP (Streamable HTTP) | Prohibited in v1 (MCP-007); would need TLS, OAuth 2.1 with PKCE, a separate ADR, a threat-model update and user approval |
| D | No MCP server | The state until the user answers kickoff question 5 |

## Decision

- Pinned MCP specification version: **2026-07-28** [VERIFIED S22; A-53 VERIFIED at access date,
  re-check in M8].
- Transport is local stdio only (MCP-005) [VERIFIED S21]. The server is a separate, optional process
  that calls only the loopback API with its client profile's own token from the OS keyring (MCP-006,
  MCP-021); it never accepts or forwards client tokens [VERIFIED S20, S21] and holds no MT5
  credentials.
- Tools: the nine read tools of MCP_SECURITY_SPEC §4.0, each output carrying `env`, `tier`,
  `as_of_utc` and `health`. Admin actions: only `generate_report`, `annotate_trade_journal` and
  `queue_research_job` (§4.1), each disabled by default, enabled per client, and approved per
  invocation in the dashboard within 5 minutes. Adding another needs MCP-016.
- Enforcement in depth (MCP-011): allowlist; no MT5 import and no trading or safety route builder
  (static test); per-client scopes; the API rejects every `mcp:*` scope on trading, safety, config
  and approval routes (API-040).

## Consequences

- No MCP feature can place, modify or close orders, or change risk, Guardian or safety state.
- Same-Windows-user limits are stated, not hidden (MCP-022, [ASSUMPTION A-63]): per-client tokens give
  attribution and separation among cooperating clients, not isolation from a malicious same-user
  process. Read access stays exposed to such a process (TM-03, accepted residual risk).
- The external client and its model provider receive whatever tools return (MCP-031); privacy mode
  is on by default (MCP-040).
- M8 carries the MCP-060 security tests if the server is built.

## Reversal cost

Low to remove (the engine has no dependency on it). Adding any trading capability is not a
reversal this ADR allows; it is prohibited.
