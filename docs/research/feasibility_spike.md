# S0 Feasibility Spike — can the candidates fit the minimum lot?

> **PT0 — FEASIBILITY ONLY, NOT A RESULT (BT-001).** Every number in this file carries that label.
> This is the advisory S0 run of `prompts/00b_FEASIBILITY_SPIKE_PROMPT.md`. It informs D-02 and
> D-07..D-09 and gates nothing. It measures stop distances, spreads and sizing only. Profit, P/L,
> expectancy, win rate and returns were **not computed** (RES-021). Sizing uses the **fixture
> parameters and the `ILL-CENT` profile** (not `VER-CENT`, because M2 has not run). The P-01 levels
> 0.10 %, 0.25 % and 0.50 % are the recommended range. **None of them is approved by this report.**
> The user separately approved 0.25 % for live (`docs/STATUS.md` §8).

Code: `spikes/feasibility/s0_feasibility.py`, with a self-check on hand-computed sizing cases
(CGV-01, CGV-06, TRADING_RISK_SPEC §3.1, STRATEGY_CANDIDATES §2.2 rows). Raw output:
`spikes/feasibility/out/results.json` and `out/tables.md`. `src/goldbot` does not import any of it.

## 1. Data provenance

| Item | Value |
| --- | --- |
| Source | Exness MT5 **demo** terminal, server `Exness-MT5Trial7`, `copy_rates_from_pos`, read-only, fetched 2026-11-13 14:19 UTC (`spikes/feasibility/data/provenance.json`) |
| Login | **A-72:** the investor-login flag could not be confirmed from MT5 (`account_info().trade_allowed` reported `True`). The user stated it was the investor login. No order or trade function was called. |
| Symbol | `XAUUSDm`: a **Standard demo** symbol, contract 100, `volume_min` 0.01, step 0.01, point 0.001, digits 3. **It is not the cent account.** Its prices give the stop distances. Its spreads are a `PROXY` for the cent symbol (A-40). |
| M5 file | `XAUUSDm_M5.parquet`, 99,999 bars, 2025-06-18 11:10 .. 2026-11-13 14:15 |
| H1 file | `XAUUSDm_H1.parquet`, 58,235 bars, 2014-01-14 00:00 .. 2026-11-13 14:00 (sparse with zero spread before 2017; dense from **2017-03-01**, the first month with ≥ 400 bars) |
| Time base | Bar `time` is the MT5 bar-open label in **broker server time**, stored UTC-typed. It is **not verified true UTC.** S0 treats it as GMT+0 (CENT-005, S2). The bars show the daily break at 21:00–22:00 in US summer and 22:00–23:00 in US winter. The break therefore follows New York time, and S0 places it at 16:58–18:01 America/New_York. |
| Spread | The bar's recorded `spread` field (points × 0.001 USD). This is **not tick-level**, and MT5 does not document whether it is the bar's minimum or last spread. |

**RES-005 holdout (per dataset).** The holdout is the larger of 6 months and 20 % of the data, with
20 % measured both by time span and by bar count. The cut was floored to midnight. Only data
before the cut was used.

| Dataset | Rule that set the cut | Holdout cut (server time) | Window used |
| --- | --- | --- | --- |
| M5 | 6 months (> 20 % by span or by bars) | **2026-05-13 00:00** | 2025-06-18 11:10 .. 2026-05-12 23:55 (46.9 weeks) |
| H1 | 20 % of the time span (≈ 2.57 years) | **2024-04-20 00:00** | 2017-03-01 .. 2024-04-19 (372.4 weeks) |

Candidates A and C, and the `B-recent` run, take M15, H1 and H4 bars resampled from the **M5 dataset
only**. `B-hist` takes the H1 dataset (H4 resampled from it). **Overlap to note:** the M5 window
(2025-06 .. 2026-05) lies inside the H1 dataset's holdout period. Any future holdout defined on that
H1 file would therefore overlap bars S0 has examined. M6 is meant to use cent ticks (BT-010a), so
this matters only if those H1 bars are ever reused.

## 2. Sizing model and substitutions

- **Equity** is fixed at 10,000.00 USC, the fixture value. It is held constant because no P/L is
  computed, so CENT-032 (the rate rising after drawdown) is **not** shown.
- **`ILL-CENT`:** tick size 0.01, tick value 1.00 USC per 1.00 lot, so a $1 move at 0.01 lot costs
  1 USC. `volume_min` = step = 0.01. The RISK-011 loss per lot uses the RISK-014 formula
  (`D / tick_size × tick_value`) **in place of `order_calc_profit`**, which is not available offline.
- **RISK-010/013:** budget = equity × P-01, rounded down; volume rounded down; below 0.01 means
  `MIN_VOLUME_EXCEEDS_BUDGET`. Decimal arithmetic.
- **P-26 slippage allowance** = 1.0 × the P-13 component-B median spread. Per signal, this is the
  rolling 20-day median of the bar spread for the same server hour, using only bars before the
  signal.
- **P-13** = min(B, C) with A left out: B = 2 × that median, C = 10 % of D. A failure means
  `SPREAD_TOO_WIDE`. Without 20 days of history the check gives `CALC_UNAVAILABLE`, which fails
  closed and is excluded from the counts.
- **EXP-002..006 use ILLUSTRATIVE formulas**, because `order_calc_margin` and `account_info` are
  not available offline:
  - notional = volume × price × 100 USC;
  - P-09: notional ÷ equity ≤ 1.0, else `EFFECTIVE_LEVERAGE`. Per the "keep reject" rule
    (G1, 2026-11-13), there is no size-down;
  - margin = notional ÷ 200, the P-12 cap value standing in for the real account leverage
    (`BLOCKED` until M2). This feeds P-10 (`MARGIN_UTILISATION`), P-11 (`MARGIN_LEVEL`) and
    `FREE_MARGIN`;
  - stop-out move with an ILLUSTRATIVE `margin_so_so` of 100 %, which must be ≥ 3 × D, else
    `STOP_OUT_DISTANCE`.

  Under these stand-ins the four margin codes **cannot bind** while P-09 holds. They would need an
  account leverage below about 1:10. Their zero counts are a property of the stand-ins and are not
  a measurement.
- **RISK-015 / P-31 = P-01 (one slot):** a signal arriving while an earlier accepted signal of the
  **same candidate** is assumed open gives `AGGREGATE_RISK`. A position is treated as open for its
  full `max_hold_minutes`, because SL and TP exits are not simulated (simulating them would compute
  outcomes, RES-021). That makes this count an upper bound. Interaction between candidates (G7) is
  not modelled.
- **Gate order** (it decides which code a signal receives):
  1. pre-trade: envelope liquidity → `PRE_CLOSE` → `CALC_UNAVAILABLE` → `SPREAD_TOO_WIDE`;
  2. RiskEngine: `MIN_VOLUME_EXCEEDS_BUDGET` → `AGGREGATE_RISK` → `EFFECTIVE_LEVERAGE` → margin
     codes → `STOP_OUT_DISTANCE`.
- **A10 (CENT-030, CH-92):** signals rejected with any of the eight capital or cost codes, divided
  by the signals minus those excluded for `OUTSIDE_STRATEGY_ENVELOPE`, `PRE_CLOSE` or
  `CALC_UNAVAILABLE`. The **`MIN_VOLUME_EXCEEDS_BUDGET` rate** uses the CENT-030 denominator
  instead: the signals that passed every pre-trade gate.
- **Not modelled**, with the reason for each:
  - the P-18 news blackout (no historical event source, G3);
  - `session_exceptions.yaml` and early closes;
  - MI-192 anomalies;
  - "no re-entry after a stop-out" (it needs outcomes);
  - "TP reachable before P-33" (it needs the price path);
  - `OFF_TICK`: the SL prices are not on the `ILL-CENT` 0.01 tick, so the real system needs on-tick
    SL rules or a RISK-025 opt-in;
  - commission (A-08).

  P-27 passes by construction (TP = 1.5 × D or 2.0 × D net of the spread). `SL_TOO_CLOSE` is
  implied by P-13 C (stops level 0).
- **Verdict classes, declared in the code before the run:** A10 < 40 % is `FEASIBLE`; 40–60 % is
  `MARGINAL` (around CENT-031's 50 % line, which the walls can cross as equity and price move); and
  > 60 % is `INFEASIBLE`. The 95 % Wilson interval is shown because several samples are small.

## 3. Rule interpretations (simplest reading; frozen before any output; never iterated)

**Common to all candidates.**

- ATR(14) is Wilder's.
- Module-1 trend: the sign of the 20-bar close change when `|Δ| / (ATR × √20) ≥ 0.5`, otherwise
  neutral. B states this rule for H4. A and C reuse it on H1 for their G6 gate.
- Higher timeframes contribute only their last closed bar (MI-034).
- The decision time is the close of the confirming bar. The entry reference is that bar's close
  (bid), plus the bar spread for a BUY (the ask). Taking the next bar's open instead would read
  ahead of the decision.
- The "current spread" is the confirming bar's spread.
- "Rejection candle" (module 4 has no numeric rule) means the MI-031 **pin-bar** geometry: the
  rejecting wick is ≥ ⅔ of the range, and the range is ≥ 0.3 × ATR.
- **G4 gap (sessions):** London is 08:00–17:00 Europe/London and New York is 08:00–17:00
  America/New_York, with New York winning where they overlap. Times are converted from server time
  through the tz database, which assumes server time = UTC.
- **Daily break:** 16:58 New York (S2's 20:58 GMT+0, moving with US DST as the bars show).
- **P-33 deadline:** 16:28 New York, or 15:58 on Friday.
- **P-19:** no entry from 15:58 New York, or from 14:58 on Friday.
- **§2.1 cut-off:** entry time + `max_hold` ≤ the P-33 deadline. A failure gives `PRE_CLOSE`.
- The P-19 rule "30 min after an open" never meets the London or New York windows.
- **Liquidity proxy:** decision-bar tick volume ≥ the 20th percentile for the same server hour on
  the pre-cut window. A failure gives `OUTSIDE_STRATEGY_ENVELOPE`.
- **Trade quotas** count accepted trades only. A setup that would exceed its quota is *suppressed*:
  it is not a signal and counts in no rate.

**A — opening-range breakout and retest (M5 data; M15 and H1 resampled).**

- The range is the four M15 bars of 08:00–09:00 Europe/London or 09:30–10:30 America/New_York. A
  window with fewer than four bars is skipped. The range is valid if its width ≥ 0.3 × H1 ATR.
- **G1:** the first M15 bar that closes beyond the range, with its close ≤ the range end + 120 min,
  and whose leg holds a displacement record. The displacement is one to three consecutive candles
  in the break direction ending at that bar, with Σ body ≥ 1.5 × M15 ATR and Σ body ÷ Σ range ≥ 0.6.
- **G4:** within the next 12 M5 bars, a bar that trades to within 0.1 × M15 ATR of the broken
  boundary, closes on the breakout side, and is a pin bar.
- Before entry, the setup is invalidated if an M15 bar closes back beyond the range midpoint.
- **G6:** the H1 trend must not be opposite.
- SL = midpoint ∓ spread. D = |entry − SL|.
- At most one setup per session per day. `max_hold` = 240 min.

**B — H1 trend following (H4 resampled from H1).**

- **G6:** the H4 module-1 trend gives the direction.
- **G1:** the first H1 close beyond the latest confirmed H1 swing (k = 2) in the G6 direction. Each
  swing can be broken only once. No separate HH/HL structure label is required.
- The decision bar must close inside the London or New York session.
- D = 1.5 × H1 ATR(14) + spread.
- At most one accepted entry per New York date. `max_hold` = 360 min.
- B runs on two windows:
  - **`B-recent`:** H1 resampled from the M5 dataset. Its gold price (~$4,100) is close to today's,
    so this run sets the verdict.
  - **`B-hist`:** the H1 file, 2017–2024, with gold at ~$1,200–2,400. Both its stop sizes and its
    exposure floor reflect that older price level.

**C — M5 early-reversal scalping (M15 and H1 resampled).**

- **Pool:** only the latest confirmed M5 swing (k = 2). Equal highs and lows are not tracked
  separately, because they are swings too.
- **G2:** a wick beyond the pool by ≥ 0.05 × M5 ATR, with a close back inside on the same bar or
  the next. The pool is consumed once penetrated, and a newer sweep on the same side replaces a
  pending one.
- **G1 shift:** after the return close and within 6 bars of the sweep bar, a close beyond the latest
  confirmed opposite M5 swing. This is a simplified micro CHOCH: the prevailing-structure label is
  not checked.
- **G4:** a pin bar on the sweep bar or on the shift bar.
- **G3:** the entry reference sits on the discount side (long) or the premium side (short) of the
  latest confirmed M15 external swings (k = 5), with equilibrium 0.5.
- **G6:** the H1 trend must not be opposite.
- The shift bar must close inside the London or New York session.
- SL = sweep extreme ∓ (0.1 × M5 ATR + spread).
- At most three accepted trades per session per day. `max_hold` = 60 min.

Diagnostic counts (**PT0 — FEASIBILITY ONLY, NOT A RESULT**):

- **A:** 462 complete ranges, 171 breaks with displacement, 10 invalidated before a retest,
  1 `NO_TRADE REGIME_NOT_ELIGIBLE`, **17 setups**.
- **B-recent:** 480 H1 BOS events, 86 setups.
- **B-hist:** 4,076 BOS events, 731 setups.
- **C:** 4,880 confirmed sweeps. Of these, 3,024 had no shift in time, 576 lacked G4, 81 lacked G3,
  10 hit the G6 gate and 507 shifted outside the sessions, leaving **30 setups**.

## 4. Results

**PT0 — FEASIBILITY ONLY, NOT A RESULT** — stop distances and spreads per candidate (all signals, before any gate)

| Candidate | Window (server time) | Weeks | Signals | Stop D median (USD) | D P10 | D P90 | Median bar spread (USD) | Median round-trip spread ÷ D | Median P-26 (USD) | Median entry price (USD) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 2025-06-18 .. 2026-05-12 | 46.9 | 17 | 10.77 | 5.60 | 27.23 | 0.160 | 1.7% | 0.160 | 4158 |
| B-recent | 2025-06-18 .. 2026-05-12 | 46.9 | 86 | 20.87 | 11.21 | 44.44 | 0.160 | 0.9% | 0.160 | 4143 |
| B-hist | 2017-03-01 .. 2024-04-19 | 372.4 | 731 | 5.54 | 3.01 | 9.98 | 0.200 | 3.8% | 0.200 | 1721 |
| C | 2025-06-18 .. 2026-05-12 | 46.9 | 30 | 11.10 | 4.17 | 34.16 | 0.160 | 1.8% | 0.160 | 4509 |

The round-trip spread is one bar spread: a buy at the ask closed at the bid, or the reverse. This
is the standard-symbol spread from the bar field, not cent-symbol or tick-level data.

**PT0 — FEASIBILITY ONLY, NOT A RESULT** — sizing feasibility at 10,000.00 USC, `ILL-CENT`, fixture parameters

| Candidate | P-01 | Budget (USC) | Widest stop at min lot (USD) | Exposure floor: stops ≤ this rejected (USD) | Spread floor (USD) | Signals | Excluded (envelope / pre-close / calc) | A10 denominator | `MIN_VOLUME_EXCEEDS_BUDGET` rate (CENT-030) | A10 capital-feasibility rate [95% interval] | Survived | Survived per week | Class |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0.10% | 10.00 | 9.84 | 3.17 | 1.60 | 17 | 4/2/1 | 10 | 80.0% (8/10) | 80.0% (8/10) [49.0%–94.3%] | 2 | 0.04 | INFEASIBLE |
| A | 0.25% | 25.00 | 24.84 | 8.17 | 1.60 | 17 | 4/2/1 | 10 | 20.0% (2/10) | 30.0% (3/10) [10.8%–60.3%] | 7 | 0.15 | FEASIBLE |
| A | 0.50% | 50.00 | 49.84 | 16.51 | 1.60 | 17 | 4/2/1 | 10 | 0.0% (0/10) | 60.0% (6/10) [31.3%–83.2%] | 4 | 0.09 | MARGINAL |
| B-recent | 0.10% | 10.00 | 9.84 | 3.17 | 1.60 | 86 | 14/28/2 | 42 | 100.0% (42/42) | 100.0% (42/42) [91.6%–100.0%] | 0 | 0.00 | INFEASIBLE |
| B-recent | 0.25% | 25.00 | 24.84 | 8.17 | 1.60 | 84 | 14/26/2 | 42 | 38.1% (16/42) | 38.1% (16/42) [25.0%–53.2%] | 26 | 0.55 | FEASIBLE |
| B-recent | 0.50% | 50.00 | 49.84 | 16.51 | 1.60 | 80 | 14/24/2 | 40 | 2.5% (1/40) | 27.5% (11/40) [16.1%–42.8%] | 29 | 0.62 | FEASIBLE |
| B-hist | 0.10% | 10.00 | 9.80 | 1.47 | 2.00 | 634 | 99/142/6 | 387 | 10.4% (40/383) | 11.4% (44/387) [8.6%–14.9%] | 343 | 0.92 | FEASIBLE |
| B-hist | 0.25% | 25.00 | 24.80 | 3.97 | 2.00 | 632 | 99/140/6 | 387 | 0.5% (2/383) | 5.9% (23/387) [4.0%–8.8%] | 364 | 0.98 | FEASIBLE |
| B-hist | 0.50% | 50.00 | 49.80 | 8.13 | 2.00 | 699 | 103/178/6 | 412 | 0.0% (0/408) | 78.4% (323/412) [74.2%–82.1%] | 89 | 0.24 | INFEASIBLE |
| C | 0.10% | 10.00 | 9.84 | 3.17 | 1.60 | 30 | 11/0/1 | 18 | 66.7% (12/18) | 66.7% (12/18) [43.7%–83.7%] | 6 | 0.13 | INFEASIBLE |
| C | 0.25% | 25.00 | 24.84 | 8.17 | 1.60 | 30 | 11/0/1 | 18 | 22.2% (4/18) | 38.9% (7/18) [20.3%–61.4%] | 11 | 0.23 | FEASIBLE |
| C | 0.50% | 50.00 | 49.84 | 16.51 | 1.60 | 30 | 11/0/1 | 18 | 11.1% (2/18) | 72.2% (13/18) [49.1%–87.5%] | 5 | 0.11 | INFEASIBLE |

How the wall columns are derived:

- **Widest stop** = budget ÷ 1 USC per $ at 0.01 lot, minus the candidate's median P-26 (RISK-013).
- **Exposure floor** = the largest D whose budget-derived volume still exceeds the P-09 volume at
  the candidate's median entry price. That P-09 volume is 0.02 lot at ~$4,100–4,500 and 0.05 lot
  at ~$1,721.
- **Spread floor** = 10 × the median bar spread (P-13 C).
- Signal counts differ between levels only through the quota suppressions in the next table.

**PT0 — FEASIBILITY ONLY, NOT A RESULT** — A10 rejections split by code (count; share of the A10 denominator)

| Candidate | P-01 | `MIN_VOLUME_EXCEEDS_BUDGET` | `EFFECTIVE_LEVERAGE` | `MARGIN_UTILISATION` | `MARGIN_LEVEL` | `FREE_MARGIN` | `STOP_OUT_DISTANCE` | `AGGREGATE_RISK` | `SPREAD_TOO_WIDE` | Suppressed by the rule's own trade quota |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0.10% | 8 (80.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 |
| A | 0.25% | 2 (20.0%) | 1 (10.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 |
| A | 0.50% | 0 (0.0%) | 6 (60.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 |
| B-recent | 0.10% | 42 (100.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 |
| B-recent | 0.25% | 16 (38.1%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 2 |
| B-recent | 0.50% | 1 (2.5%) | 10 (25.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 6 |
| B-hist | 0.10% | 40 (10.3%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 4 (1.0%) | 97 |
| B-hist | 0.25% | 2 (0.5%) | 17 (4.4%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 4 (1.0%) | 99 |
| B-hist | 0.50% | 0 (0.0%) | 319 (77.4%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 4 (1.0%) | 32 |
| C | 0.10% | 12 (66.7%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 |
| C | 0.25% | 4 (22.2%) | 3 (16.7%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 |
| C | 0.50% | 2 (11.1%) | 11 (61.1%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 (0.0%) | 0 |

## 5. Verdicts (PT0 — FEASIBILITY ONLY, NOT A RESULT; advisory, no edge claim)

- **A — opening-range breakout and retest: feasible at 0.25 % only.** It is not feasible at
  ≥ 0.25 % overall, because 0.50 % is marginal (A10 60 %, all `EFFECTIVE_LEVERAGE`) and 0.10 % is
  infeasible (A10 80 %, all `MIN_VOLUME_EXCEEDS_BUDGET`). At 0.25 % the rate is 30 % on only
  10 countable signals (95 % interval 11–60 %), so the evidence is weak.
- **B — H1 trend following: feasible at ≥ 0.25 % at current gold prices** (`B-recent`). At 0.25 %,
  A10 is 38 %, all `MIN_VOLUME_EXCEEDS_BUDGET` (interval 25–53 %). At 0.50 % it is 28 %. At 0.10 %
  it is 100 % (infeasible). On 2017–2024 prices (`B-hist`) the walls sit elsewhere: feasible at
  0.10 % and 0.25 %, infeasible at 0.50 % through the exposure floor.
- **C — M5 early-reversal scalping: feasible at 0.25 % only.** At 0.25 %, A10 is 39 % on
  18 countable signals (interval 20–61 %). At 0.10 % it is 67 % (`MIN_VOLUME_EXCEEDS_BUDGET`) and
  at 0.50 % it is 72 % (`EFFECTIVE_LEVERAGE`), both infeasible. This contradicts the argued
  expectation of an A10 near 100 %. At ~$4,500 gold, C's stops (median $11.10) are much wider than
  the $1–6 that was argued, so the spread floor never binds.

## 6. Observations for D-02 and D-07..D-09 (no choice is marked approved)

- **The feasible window is narrow at every level, and it moves with P-01.** At 10,000 USC and
  ~$4,100 gold the window for D is about:

  | P-01 | Feasible window for D |
  | --- | --- |
  | 0.10 % | $3.17–9.84 |
  | 0.25 % | $8.17–24.84 |
  | 0.50 % | $16.51–49.84 |

  A higher P-01 lifts the exposure floor (P-09 allows only 0.02 lot) as much as the ceiling. That
  is why 0.25 % is the only level where all three candidates fall below the 40 % A10 line on this
  data.
- **The rules rarely fire.** The 47-week windows give few signals that survive at 0.25 %:

  | Candidate | Survivors at 0.25 % in 47 weeks | Per week | Per year (approx.) |
  | --- | --- | --- | --- |
  | A | 7 | 0.15 | 8 |
  | B-recent | 26 | 0.55 | 29 |
  | C | 11 | 0.23 | 12 |

  A1 needs 200 out-of-sample trades, which at these rates means many years of cent history
  (STRATEGY_CANDIDATES §2.5). This is a trade-count problem, separate from A10. For A the binding
  step is the pin-bar retest (17 of 171 breaks). For C it is the full conjunctive rule (30 of
  4,880 sweeps).
- **The walls depend on the gold price.** `B-hist` and `B-recent` share the same rules but reach
  opposite results at 0.50 %, because both ATR-based stops and the P-09 volume scale with price.
  Any future research window has to carry the price level with it.
- **The margin codes read zero only because of the stand-ins.** Under the ILLUSTRATIVE 1:200 margin
  they cannot bind while P-09 holds. The real `order_calc_margin`, leverage and `margin_so_so` are
  `BLOCKED` until M2.
- **Every number here leans on proxies:** standard-symbol bars and spreads, `ILL-CENT` and fixture
  equity, no news blackout and no exception days. The cent symbol's real specification (M2), cent
  spreads (A-40) and commission (A-08) can move every wall.
