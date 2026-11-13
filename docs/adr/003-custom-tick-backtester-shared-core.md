# ADR-003: Custom event-driven bid/ask tick backtester that imports `goldbot.core`

Status: Accepted (specification, 2026-11-13)

## Context

A candle backtest is not an execution simulation (BACKTESTING_SPEC header). The edge verdict
(RES-020) depends on costs, spread, slippage, latency, rejects, sessions and the cent minimum-lot
rule (CENT-030). At this capital the cost share is large, so the backtest must apply exactly the
same sizing and RiskEngine rules as live trading, or sizing and risk parity cannot be shown.

## Options

| Option | Summary | Assessment |
| --- | --- | --- |
| A | Custom event-driven tick-by-tick simulator that imports `goldbot.core` (and `goldbot.intelligence`) | Chosen |
| B | Third-party Python backtesting framework | Rejected: its own sizing, fill and order model; sizing and risk parity with live becomes unprovable |
| C | MT5 Strategy Tester | Rejected: strategy and risk logic would have to exist in MQL5, so it could not import `goldbot.core` |

## Decision

- The backtester is event-driven, tick by tick, and uses `goldbot.core` for sizing and every
  RiskEngine rule (BT-050). The golden vectors (GV, CGV) run against both the backtest path and the
  live path in CI.
- Fills follow BT-020..035: BUY at ask and SELL at bid, never mid; spread from each tick; SL
  triggered by the first crossing tick and filled at that tick's price plus stop slippage (BT-025);
  forced close at the P-33 deadline (BT-034); approval delay when a manual mode is simulated
  (BT-035). Bars are built from ticks for signals only (BT-032).
- Cost, latency, slippage and reject priors are [ASSUMPTION] values (BT-022..029; A-43, A-44)
  labelled `PLACEHOLDER` until the M7 demo measurements replace them. Commission stays BLOCKED until
  A-08 is resolved.
- Results carry their performance tier PT0..PT3; tiers are never added together (BT-001).
- Runs are reproducible: same data hash, code hash, config and seed give byte-identical trade
  lists (BT-040). M9 forward-test ticks are replayed as `env=REPLAY` for live parity (BT-041).

## Consequences

- Parity is testable: one implementation of sizing and risk, exercised by both paths.
- The project owns the simulator, its fill model and its bugs; the M5 review must check BT-020..035
  one by one.
- Data quality limits every result: tick data for the cent symbol must come from the account
  itself or be labelled `PROXY` (BT-010); historical specs before M2 carry `CURRENT-SPEC-ONLY`
  (BT-033).
- A passing backtest is not evidence of an edge on its own; the research method and verdicts are in
  STRATEGY_RESEARCH_SPEC, and "no edge found" is a valid result (RES-020).

## Reversal cost

High. Replacing the simulator would invalidate every recorded experiment (RES-010), the BT-041
parity procedure and the golden-vector CI jobs, and every M6 verdict would have to be re-run.
