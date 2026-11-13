# ADR-002: `engine`, `api` and optional `mcp_server` are separate processes; commands go through SQLite

Status: Accepted (specification, 2026-11-13)

## Context

The engine holds the protection logic: trading-state latches, reconciliation every P-24, emergency
lifecycles (EXECUTION_SAFETY_SPEC §8), the Guardian heartbeat every P-20 (GRD-010) and the
no-overnight close deadline (EXE-080..086). The dashboard API serves a browser and, optionally, an
MCP server. A fault, hang or memory leak in the UI-facing code must not delay any of that.
SYSTEM_ARCHITECTURE §4 marks the process model as [RECOMMENDATION, ADR-002].

## Options

| Option | Summary | Assessment |
| --- | --- | --- |
| A | Separate processes: `engine` (sole owner of the MT5 session), `api` (FastAPI on 127.0.0.1), optional `mcp_server` (stdio, talks only to the API); cross-process writes only through the SQLite `commands` table | Chosen |
| B | Single process hosting engine and API | Rejected: a UI fault could block protection logic |
| C | Separate processes with a message broker or RPC | Rejected: a new dependency outside CLAUDE.md §5 with no benefit at one host and one user |

## Decision

- `engine` is the only process that calls MT5 and the only writer of trading tables. `api` writes
  only `commands` and `sessions` (DATA_ARCHITECTURE §1, DATA-001). The API never calls MT5
  (API_SPEC header).
- Every UI or MCP action becomes a row in `commands`. The engine consumes it, re-validates it
  (API-020, SEC-023) and writes the result. The API cannot approve anything on its own; approvals
  are bound to the proposal hash, nonce and P-23 expiry, and the engine re-runs the RiskEngine
  (SYSTEM_ARCHITECTURE §5).
- `mcp_server` is a third, optional process that talks only to the API (ADR-009). The engine has
  no import of, call to or health dependency on it (MCP-001).

## Consequences

- An API or browser crash leaves trading-state enforcement, reconciliation, emergency operations
  and the Guardian channel running.
- The command path adds latency (one SQLite write plus an engine poll). The API reports command
  lifecycle states, never a bare "done" (UI-013).
- SQLite runs in WAL mode with `synchronous=FULL` (ADR-004) so the two processes can read
  concurrently while each table keeps one writer.
- Every command needs a schema (`Command` in DATA_ARCHITECTURE §3) and a re-validation test.
- Process supervision is a runbook item: the engine must start, and stay up, without the API.

## Reversal cost

Medium to high. Merging the processes would be easy mechanically, but it would weaken B4 in
SYSTEM_ARCHITECTURE §4, invalidate the API-020 re-validation design and the DATA-001 single-writer
tests, and need a threat-model update.
