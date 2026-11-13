# ADR-006: A `BrokerPort` interface with `Mt5Broker` and a deterministic `FakeBroker`

Status: Accepted (specification, 2026-11-13)

## Context

The MetaTrader5 package ships Windows x86-64 wheels only [VERIFIED S18] and needs a running
terminal on the same host (SYSTEM_ARCHITECTURE §3, §7). Development and CI may run on any OS (SYSTEM_ARCHITECTURE §7). The safety
requirements need repeatable tests of rare broker behaviour: timeouts treated as UNKNOWN (EXE-013),
retcode classes (EXECUTION_SAFETY_SPEC §4), partial fills (§6), emergency runs against a closed
market and the session-close deadline (§11). These cannot be produced on demand from a live
terminal.

## Options

| Option | Summary | Assessment |
| --- | --- | --- |
| A | A `BrokerPort` interface; `Mt5Broker` wraps the MetaTrader5 package; `FakeBroker` is a deterministic in-process simulation | Chosen |
| B | Direct MT5 calls wherever needed | Rejected: untestable off Windows; failure modes cannot be scripted |
| C | Mocks per test with no shared fake | Rejected: each test reinvents broker behaviour; no single model to review |

## Decision

- All broker access goes through `BrokerPort`. `Mt5Broker` is the `mt5_adapter`: the only code that
  imports the MetaTrader5 package, on one worker thread (EXE-003), and the conversion boundary
  (RISK-003).
- `FakeBroker` is deterministic for a given seed and script. It simulates sessions, retcodes,
  timeouts, partial fills, stops and freeze levels, and closed markets, as the chaos tests require
  (EXECUTION_SAFETY_SPEC §11).
- [RECOMMENDATION] `FakeBroker` returns the same raw shapes as the package (floats included), so
  the conversion boundary and its `FloatOperation` trap are exercised in non-`mt5` tests.
- Tests that need the real terminal carry the `mt5` marker and run only on the Windows host
  (CLAUDE.md §6).

## Consequences

- The order path, reconciliation and emergency lifecycles are testable in CI without MT5.
- `FakeBroker` encodes beliefs about broker behaviour, not facts. Where behaviour is still
  unknown, its scripts must cover each possibility rather than pick one: comment preservation
  (A-30, BLOCKED until M7), SL attached on entry (A-31, BLOCKED until M7), filling modes (A-32,
  BLOCKED until M2), stops and freeze levels (A-07, BLOCKED until M2).
- A green `FakeBroker` suite never stands in for demo evidence (CENT-001..040, GOV-002); M7 demo and
  M10 cent results still decide.
- The port must stay narrow: it mirrors the MT5 calls the specs use (for example `order_check`,
  `order_send`, `positions_get`, `orders_get`, `history_deals_get`, `order_calc_margin`,
  `order_calc_profit`, `symbol_info`, `account_info`, `terminal_info`); the exact method set is
  fixed in M1/M2.

## Reversal cost

Low to medium. The port is a thin seam; removing it would not change behaviour but would make most
safety tests Windows-only, which conflicts with the CI command in CLAUDE.md §6.
