# ADR-004: SQLite (WAL) for operational state and Parquet for research data; no PostgreSQL in v1

Status: Accepted (specification, 2026-11-13)

## Context

GoldBot runs on one local Windows computer with one user (ADR-013). It needs durable operational
state (ledger, `order_intents` with `op_id`, trading-state events, emergency actions, a hash-chained
audit log), a research store for tick history, and an append-only experiment registry. Money must
never be stored as a float (DATA-004). LIVE and DEMO data must never mix (DATA-005).

## Options

| Option | Summary | Assessment |
| --- | --- | --- |
| A | SQLite in WAL mode for operational data and the experiment registry; Parquet with manifests for research data | Chosen |
| B | PostgreSQL | Rejected: a server to install, patch, back up and secure, with no benefit at this scale |
| C | Flat JSON or CSV files | Rejected: no transactions, no unique index for `op_id` (EXE-002), weak crash safety |

## Decision

- Operational DB: SQLite, WAL mode, `PRAGMA synchronous=FULL` (DATA_ARCHITECTURE §1). One writer
  per table; cross-process writes only through `commands` (DATA-001, ADR-002).
- LIVE and DEMO use separate database files, and the engine refuses to open a DB whose `env`
  header does not match its config (DATA-005).
- IDs are UUIDv7; `op_id` is the idempotency key with a unique index (DATA-002, EXE-002).
- Money columns are TEXT decimal strings plus a currency column, never REAL (DATA-004).
- Timestamps are timezone-aware UTC with milliseconds (DATA-003, TIME-011).
- Research store: Parquet partitioned `symbol/account_class/yyyy/mm/` with a provenance manifest
  per partition (BT-011). Experiment registry: separate SQLite `research.db`, append-only and
  hash-chained (RES-010).
- Integrity: `PRAGMA integrity_check` and audit `verify_chain()` daily (DATA-022, SEC-022);
  versioned migrations, and the engine refuses to start on a schema-version mismatch (DATA-020).

## Consequences

- No database server to run; backups are file copies under PRV-030.
- SQLite allows one writer at a time per database file; the single-writer-per-table rule and the
  command table keep contention low, but long write transactions in the engine must be avoided.
- Decimal-as-TEXT means arithmetic happens in Python, never in SQL.
- Parquet keeps tick history out of the operational DB; `ticks_sample` keeps only 30 days.
- A future multi-user or multi-host design would need a new ADR (not in v1, SYSTEM_ARCHITECTURE §8).

## Reversal cost

Medium. Schemas live in `schemas/*.schema.json` and migrations are versioned, so a move to
PostgreSQL is a port of the persistence layer plus data migration, but it would add a dependency
outside CLAUDE.md §5 and needs user approval and a threat-model update.
