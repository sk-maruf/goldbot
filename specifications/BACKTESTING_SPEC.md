# BACKTESTING_SPEC — Execution realism

> Status: **SPECIFICATION.** Corrects V1 audit item **F**. A candle backtest is not an
> execution simulation, and this file keeps the two apart.

## 1. Four performance tiers PT0–PT3 (never mixed in one number)

"PT" = performance tier. This is distinct from the trading-state triggers T1–T27 in `TRADING_RISK_SPEC.md` §7.

| Tier | Name | What it measures | Where it comes from |
|---|---|---|---|
| PT0 | Theoretical | Signal logic only. Mid or close prices, no costs | Diagnostic only; **never** used in an acceptance decision |
| PT1 | Execution-adjusted backtest | Bid/ask ticks, costs, slippage, latency, rejects, sessions, swap | This spec |
| PT2 | Demo execution | Real order handling on the **Standard demo** (different symbol and economics) | M7/M9 forward test |
| PT3 | Standard Cent live | Real cent economics on `XAUUSDc` | M10 pilot |

- **BT-001** Every report, chart and dashboard number carries its tier label. Comparing tiers
  side by side is encouraged. Adding them up is forbidden.
- **BT-002** PT0 results may appear only in an appendix titled "Theoretical (no costs)".

## 2. Data

- **BT-010 Sources.** Bid/ask tick history for the exact symbol and account type: (a) MT5
  `copy_ticks_range` on the account itself [VERIFIED S10: tick fields]; (b) a broker tick archive if
  one is available for the cent symbol [OPEN]. Data from a *different* account type (e.g. Standard
  `XAUUSD` ticks used for a cent strategy) is labelled `PROXY`. Results built on it carry a
  `PROXY-DATA` warning and cannot pass the M6 gate alone.
- **BT-011 Provenance manifest** per partition: source, symbol, account class, server, download UTC
  time, row count, first/last `time_msc`, SHA-256, tool version.
- **BT-012 Quality checks** (results go into a report; failing rows are quarantined, never silently
  repaired):
  missing intervals during open sessions (gap > 60 s while the session is open); duplicates;
  out-of-order `time_msc` (TIME-021); `ask < bid`; zero or negative spread; spread outliers
  (> 20 × session median); ticks inside closed sessions; timestamp-zone sanity (TIME-005); weekend
  leakage; price jumps > 1% between consecutive ticks (flag, not removal).
- **BT-013** A dataset with > 0.5% quarantined ticks in any month is marked `DEGRADED`. Strategies
  evaluated on DEGRADED months report results with and without those months.

## 3. Simulation model

Event-driven, tick by tick, using **`goldbot.core` for sizing and every RiskEngine rule** (BT-050).

| Element | Model |
|---|---|
| **BT-020 Prices** | BUY fills at ask, SELL at bid, closes on the opposite side. Never mid. |
| **BT-021 Spread** | Taken from each tick, so widening is captured as it happened. The spread gate (P-13) is evaluated on the decision tick. |
| **BT-022 Costs** | Commission per lot from CENT-006. Until it is observed: pessimistic placeholder = 0.5 × median spread per round trip per lot [ASSUMPTION], labelled `PLACEHOLDER`. Swap: from the symbol spec at the time of the test, charged at the rollover time (TIME-041), × 3 on `swap_rollover3days`. A swap-free account uses 0 only after CENT-007 confirms it. |
| **BT-023 Latency** | Decision tick → order arrival = draw from the latency distribution (prior: uniform 150–600 ms [ASSUMPTION]; replaced by the M7 demo empirical distribution). The fill uses the first tick at or after arrival. |
| **BT-024 Slippage** | Market orders: price of the first tick at or after arrival, plus an extra slippage draw from an empirical distribution bucketed by session and by volatility (ATR tercile). Prior before M7 data: 0.25 × median spread for entries, 1.0 × median spread for stop exits [ASSUMPTION]. |
| **BT-025 Stop-loss** | An SL is triggered by the first tick whose closing-side price crosses it. The fill is at **that tick's price** (so a gap fills through the stop), plus stop slippage. Never at the SL price by assumption. |
| **BT-026 Take-profit** | Triggered when the closing-side price reaches TP. Fill at the TP price (limit), with no positive slippage assumed. |
| **BT-027 Stops/freeze levels** | Orders and modifications that would violate stops/freeze distances (spec at test time) are rejected as live would be (RISK-032). |
| **BT-028 Rejects** | Probability of reject per class (PRICE/THROTTLE/MARKET) from M7 data. Prior: 1% PRICE rejects on entries [ASSUMPTION]. A rejected entry is not retried (EXE-011). |
| **BT-029 Partial fills** | Prior probability 0 at minimum lot [ASSUMPTION]. M7 data replaces it. When it happens, EXE-040 logic applies. |
| **BT-030 Sessions and closures** | No fills while the session is closed. Orders arriving in a closed session are rejected (10018 analogue). Positions held over closures gap at reopen. |
| **BT-031 Currency conversion** | For the cent account, profit currency USD → account currency USC uses the spec-derived factor (`tick_value / tick_size`) at test time. If a future symbol's profit currency differs from the account currency's base, historical conversion rates are required [OPEN; not needed for v1]. |
| **BT-032 Candle data** | Bars are built from ticks for signal calculation only. Fills and SL/TP triggering always use ticks. A candle-only backtest is PT0 by definition. |
| **BT-033 Historical broker specs** | Each simulated day uses the symbol spec snapshot valid on that day (stored spec history from M2 onward). For earlier periods only the current spec exists; results then carry a `CURRENT-SPEC-ONLY` flag, and A9 stress covers spec uncertainty |
| **BT-034 Session-end close** | Every open position is force-closed at the P-33 deadline at the first tick's executable price, plus stop slippage. Entries in the P-19 window are rejected. A strategy cannot hold through the daily break or weekend in simulation (RES-072) |
| **BT-035 Entry authorization delay** | When simulating `MANUAL_APPROVAL` (or unapproved strategies under `AUTO_APPROVED_STRATEGIES`), add an approval delay drawn from a configured distribution (prior: 10–60 s [ASSUMPTION]); proposals that would expire under P-23 are dropped. Reports state which entry mode was simulated |

## 4. Determinism and parity

- **BT-040 Reproducibility.** The same data hash + code hash + config + random seed gives
  byte-identical trade lists. The seed is recorded in the experiment registry (RES-010).
- **BT-041 Live parity.** The M9 forward-test ticks are recorded and replayed through the backtester
  (`env=REPLAY`). For each trade, compare entry/exit times, prices, volume and P/L. Acceptance:
  same trade set (± trades blocked by real rejects); median |price difference| ≤ 1 × median spread;
  no volume differences. Differences are reported with an explanation.
- **BT-050 Shared core.** The backtester imports `goldbot.core` sizing and RiskEngine. The golden
  vectors (GV, CGV) run against both the backtest path and the live path in CI.

## 5. Stress scenarios (required for every candidate)

Spread × 1.5; stop slippage × 2; latency × 2; reject rate × 3; dropping the best 5% of trades;
an extra 1-tick adverse slippage on every exit; weekend-gap scenario (holding over a weekend with
the largest historical gap applied). A strategy passes M6 only if expectancy stays > 0 under the
combined "spread × 1.5 + stop slippage × 2" scenario (threshold A9, `STRATEGY_RESEARCH_SPEC.md` §5).

## 6. Bootstrap bands for the forward test (used by RISK-063)

Block bootstrap (block length = median trades per week) of PT1 per-trade R multiples, 10,000
resamples, giving a 95% band for mean R over a sample the size of the forward test. The forward test
"matches" the backtest if its mean R lies inside that band. *Limitation:* with 50 trades the band
is wide (often ± 0.3R). Matching shows the absence of gross mismatch, not proof of an edge.

## 7. Report contents (per strategy, per tier)

Trade count; net expectancy in R and in account currency; cost breakdown (spread, slippage,
commission, swap) as a share of gross; win rate (reported, not optimised); payoff ratio; max
drawdown; time in market; min-volume rejection rate (CENT-030); tier label; data-quality status;
PROXY-DATA and PLACEHOLDER flags. Strategies built on the market-intelligence layer also report
the MI-072 metrics (recovery factor, trade frequency, risk-adjusted return, per-regime results,
evidence-group ablation). These are reported, not acceptance criteria.
