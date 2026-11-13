# ADR-001: Python executes through the MetaTrader5 package; an independent MQL5 Guardian EA is the second safety layer

Status: Accepted (specification, 2026-11-13)

## Context

GoldBot trades gold on an Exness MT5 Standard Cent account from the user's local Windows computer.
Orders must reach the MT5 terminal either from Python (the MetaTrader5 package) or from an MQL5
Expert Advisor. The package ships Windows x86-64 wheels only [VERIFIED S18] and talks to a terminal
on the same machine [VERIFIED S9, S18]. The project needs one deterministic approval authority
(RISK-001/002), a conversion boundary for MT5 floats (RISK-003, RISK-020..024), and a safety layer
that does not depend on the engine being alive (GRD-001). The builder is an AI agent that must be
able to test the order path off Windows (ADR-006).

## Options

| Option | Summary | Assessment |
| --- | --- | --- |
| A | Python engine executes via the MetaTrader5 package; a separate MQL5 Guardian EA watches and intervenes | Chosen |
| B | EA-owned execution with a Python bridge (Python sends signals, the EA sends orders) | Rejected: more IPC, order logic split across two languages, harder for the builder agent to test |
| C | Python only, no Guardian | Rejected: nothing acts when the engine hangs or dies; no independent missing-stop response (GRD-020) or equity intervention (GRD-025/026) |

## Decision

- The Python `engine` is the only executor of `RiskApprovedAction`s. Only `mt5_adapter` calls the
  MetaTrader5 package, on one worker thread (EXE-003), and converts every float once with
  `Decimal(repr(x))` (RISK-003).
- The Guardian EA (GUARDIAN_SAFETY_SPEC) runs in the same terminal, independently of the engine
  (GRD-001). It never opens a position, never places a pending order, never widens an SL and never
  changes account settings (GRD-004). Its hard limits are user-set EA inputs that engine files can
  only tighten (GRD-002/003). It has no external DLLs and no web requests, with a size target of
  ≤ 1,000 lines (GRD-005).
- The two layers coordinate through atomic files (ADR-011) and avoid duplicate action with the
  lease and check-then-act rules (GRD-050..052).

## Consequences

- One language owns sizing, risk and execution, and the backtester shares that code (ADR-003).
- The Guardian adds a second, simpler check that still works when the engine is stale (GRD-015).
- Both layers depend on the terminal: when MT5, the host or the broker connection is unavailable,
  neither the engine nor the Guardian can act. Only SL/TP orders that were broker-confirmed before
  the outage remain at the broker, and they do not guarantee the exit price (GRD-030).
- The Guardian obeys its limits only within the terminal; it cannot force a buggy engine to stop
  (GUARDIAN_SAFETY_SPEC §2). That case is covered by RISK tests and reconciliation.
- MQL5 build and test needs its own loop (GUARDIAN_SAFETY_SPEC §13); the headless compile flags are
  [ASSUMPTION A-65], verified in M2.
- Same-host requirement: the runtime host is Windows (ADR-013); research may run on any OS.

## Reversal cost

High. Moving execution into the EA would rewrite `execution`, `reconciler`, the idempotency
protocol (EXE-002) and the conversion boundary, and would break backtest parity (BT-050). Removing
the Guardian would remove GRD-020/025/028 and invalidate the M7b tests and the M10 readiness checks.
