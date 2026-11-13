# STRATEGY_CANDIDATES — M0c proposals for decision D-08

> Status: **PROPOSAL (M0c, 2026-11-13).** Nothing here has been tested. No candidate is claimed to
> have an edge, a win rate or a profit. "No edge found" is a valid and expected result (RES-020,
> A-55). Decision **D-08 (initial strategy selection) stays with the user**; this file only lists
> what the user can choose from (RES-073, MI-050). Every broker-dependent number is `ILLUSTRATIVE`
> (from the `ILL-CENT` fixture profile, CENT_ACCOUNT_VALIDATION §4) or `BLOCKED` with its A-id.
> The real symbol spec is `BLOCKED` until M2 (A-05, A-06, A-07); commission until M7 (A-08); the
> absolute spread cap until M2–M7 (A-40).

## 1. Scope

- Three rule-based candidates, each from an MI-050 family, each a **separate strategy** with its
  own pre-registration (RES-002), version (RES-011), class (RES-023), envelope (RES-070), budget
  P-32 ≤ P-01 (RISK-016), verdict (RES-020) and degradation state (RES-040).
- Decisions honoured: D-07 (research scalping **and** intraday; the verdict picks), D-09 (several
  strategies sharing P-31 = 0.25%, so at most one full-risk position at a time), D-10 (rule-based,
  no model in the signal path, so no C3), D-11 (the system may research and report; LLM disabled,
  P-28 = 0), D-12 (a prevalidated C4 selector, built in M6f only if its condition holds, §8).
- Every candidate obeys CLAUDE.md §3: intelligence proposes, the RiskEngine authorises (MI-003,
  RISK-001); no entry on a single indicator or a single candle pattern (MI-042); closed-candle
  evidence only (MI-013/034); no martingale, grid, averaging down, hedging or recovery sizing
  (TRADING_RISK_SPEC §10); SL never widened, trailing only tightens (RISK-033, MI-172); no
  overnight or weekend holding (RES-072, EXE-080..086).
- Out of scope: order-flow strategies (MI-021, A-34), swing styles (RES-072), any ML or fitted
  weight (D-10).

## 2. Common frame (applies to all three candidates)

### 2.1 Shared rules

- **Decision engine settings (MI-042).** Weight 1 per correlation group, group cap 1,
  `entry_threshold` = the number of mandatory groups, `conflict_threshold` = 1 (the opposite side
  may hold at most one group). Context items (spread, session, news, data quality, module health,
  MI-192 anomalies) only block. Ties and missing evidence resolve to `WAIT` or `NO_TRADE` (MI-156).
  These are numeric constants of the version; a second weight set is a second trial (MI-071).
- **Entries.** At market on the first tick after the confirming bar closes; BUY levels from the
  ask, SELL levels from the bid (MI-053.4). No pending orders (P-06 = 0). No price quantization
  opt-in, so off-tick prices are rejected `OFF_TICK` (RISK-025).
- **Exits.** Fixed SL and TP set at entry (the MI-196 BASELINE shape). No trailing and no
  break-even in the base version: each would be a separate, pre-registered version (MI-171/175)
  and evaluating it makes the strategy C2 (RES-023). No partial exits (MI-174:
  `PARTIAL_INFEASIBLE` at the minimum lot). A time exit at `max_hold_minutes` through
  `evaluate_reduction()`, and in every case closure by the P-33 deadline (BT-034, EXE-083).
- **Entry cut-off.** An entry is allowed only if `now + max_hold_minutes ≤ P-33 deadline`
  (EXE-081), and never inside the P-19 window. This is stricter than P-19 alone; P-19/P-33 are
  "widen only", so a stricter strategy rule is allowed (RISK-017).
- **One position slot.** With P-31 = P-01 = 0.25% (D-04, D-09), a candidate arriving while any
  GoldBot position is open is rejected `AGGREGATE_RISK` (RISK-015). Simultaneous same-direction
  candidates go to the RiskEngine in a fixed, pre-registered strategy priority (MI-152); opposite
  candidates produce `NO_TRADE CONFLICT` (MI-047). No re-entry in the same session after a
  stop-out, so a loss never triggers more trading.
- **SL is never sized to fit the budget.** If a rule-derived SL falls outside the feasible window
  (§2.2), the signal is rejected and counted. Moving the stop to make the trade fit would change
  the tested strategy and is not done.

### 2.2 Sizing feasibility at P-01 = 0.25% (ILLUSTRATIVE)

Inputs, all `ILLUSTRATIVE` until M2: equity 10,000.00 USC; `ILL-CENT` (tick size 0.01, tick value
1.00 USC per 1.00 lot, so a $1 move at 0.01 lot = 1 USC; `volume_min` = `volume_step` = 0.01);
median spread $0.30 (the value implied by the CGV-01/CGV-05 fixtures, P-26 = 1.0 × median spread
= 0.30 USC at 0.01 lot); gold at $4,070 (the EXP-003 example, so 0.01 lot ≈ 4,070 USC notional).
Budget (RISK-010) = 10,000 × 0.25% = **25.00 USC**.

Three walls bound the stop distance `D` (USD) a signal can have and still be traded:

| Wall | Rule | Formula | Value (ILLUSTRATIVE) | Rejection code | Counted in A10? |
| --- | --- | --- | --- | --- | --- |
| Spread floor | P-13 component C | `D ≥ spread / 0.10` | D ≥ $3.00 | `SPREAD` (pre-trade gate) | No |
| Exposure floor | RISK-013 volume vs EXP-003, P-09 = 1.0 | P-09 allows ≤ 0.02 lot; the budget gives ≥ 0.03 lot when `D ≤ 25/0.03/100 − 0.30` | D ≤ $8.03 is rejected | `EFFECTIVE_LEVERAGE` (GV-17) | **No** |
| Minimum-lot ceiling | RISK-013, CENT-030 | `D ≤ budget/1 USC − 0.30` | D ≤ $24.70 (≤ $22.20 at 9,000 USC equity) | `MIN_VOLUME_EXCEEDS_BUDGET` | Yes |

Worked rows (RISK-013, round down; EXP-003 at $4,070):

| Stop D | Volume | Effective leverage | Modelled loss incl. P-26 | Outcome under the current spec |
| --- | --- | --- | --- | --- |
| $2.50 | 0.08 | 3.26× | — | `SPREAD` first (0.30 > 10% of 2.50) |
| $5.00 | 0.04 | 1.63× | — | `EFFECTIVE_LEVERAGE` |
| $8.00 | 0.03 | 1.22× | — | `EFFECTIVE_LEVERAGE` |
| $10.00 | 0.02 | 0.81× | 20.60 USC | Tradeable |
| $15.00 | 0.01 | 0.41× | 15.30 USC | Tradeable |
| $24.70 | 0.01 | 0.41× | 25.00 USC | Tradeable (at the budget) |
| $30.00 | 0.00 | — | — | `MIN_VOLUME_EXCEEDS_BUDGET` (A10) |

Reading of the table:

- At this capital the **minimum lot binds against wide stops**, not tight ones (CGV-01, CGV-06).
- The **exposure floor binds against tight stops**: GV-17 rejects a trade whose budget-derived
  volume breaches P-09, and the spec does not say the volume is reduced to fit. If that reading is
  right, every stop ≤ ~$8.03 is rejected, and A10 never sees it (§9, gap G1/G2). This is a risk-rule
  question for the user (CLAUDE.md §7); this document does not answer it.
- The walls move: the ceiling falls with equity (CENT-032); the floor rises with the gold price
  (if 0.01 lot's notional exceeded half the equity, P-09 would allow only 0.01 lot and the floor
  would move to ~$12.20).
- Inside the window, actual risk per trade is often well below 25.00 USC because volume rounds
  down (for example 15.30 USC at $15). That is correct behaviour (RISK-013), not an error.

### 2.3 Costs (ILLUSTRATIVE, BT-022..024 priors)

Per-trade cost in R = `(spread + commission + entry slippage) / D`, plus `stop slippage / D` on stop
exits. Priors: spread $0.30; commission `PLACEHOLDER` = 0.5 × median spread = $0.15 (BT-022, until
A-08); entry slippage 0.25 × spread = $0.075; stop slippage 1.0 × spread = $0.30 (BT-024). A9 stress
= spread × 1.5 and stop slippage × 2 (commission held at the placeholder; §9 G11).

| Stop D | Cost, every trade | Extra on stop exits | A9 stress, every trade | A9 stress, stop exits |
| --- | --- | --- | --- | --- |
| $3.00 | 0.18R | 0.10R | 0.23R | 0.20R |
| $5.00 | 0.11R | 0.06R | 0.14R | 0.12R |
| $10.00 | 0.05R | 0.03R | 0.07R | 0.06R |
| $20.00 | 0.03R | 0.02R | 0.03R | 0.03R |

For scale: STRATEGY_RESEARCH_SPEC §4 needs about 749 trades to detect a true +0.10R edge. At $3–5
stops the costs alone are that size, before latency (BT-023) and rejects (BT-028).

### 2.4 Verdict frame (A1–A10, approved as proposed 2026-11-13, A-47)

- Every candidate is proposed as **C1** (one configuration, constants frozen in the
  pre-registration before any data is examined). Then A6 is `N/A` with registry evidence (RES-025),
  and A8 applies to every numeric constant. The registry, not the author, decides the class: a
  second evaluated configuration makes it C2 and A6 applies retroactively (RES-023/025).
- For C1 to hold, the constants in §3–§5 must be frozen **before S0 looks at any data** (§9 G5).
- Verdicts: `PASS` (every applicable criterion PASS and the holdout inside the walk-forward 95%
  band), `FAIL`, `INCONCLUSIVE` (for example A1 < 200 trades or the A2 interval straddling zero;
  never converted to PASS, RES-026), `CAPITAL-INFEASIBLE` (A10 > 50%, CENT-031).
- Falsification common to all three: the hypothesis is **rejected (FAIL)** if, on walk-forward
  out-of-sample PT1 trades, the net expectancy point estimate is ≤ 0 (A2), or profit factor after
  costs < 1.15 (A3), or < 60% of windows are positive (A4), or DSR < 0.95 with the honest trial
  count (A5, RES-021), or the Monte Carlo 95th-percentile drawdown exceeds P-04 = 5% (A7), or any
  constant ±20% keeps < 70% of base expectancy (A8), or expectancy ≤ 0 under the A9 stress. A10 >
  50% gives `CAPITAL-INFEASIBLE`.
- Win rate is reported, never optimised or used as a criterion (RES-050). Results are reported by
  volatility tercile, trend state and session (RES-030/031), with all rejection codes counted.

### 2.5 Data needed by all three

- Bid/ask ticks for the cent symbol from the account itself (BT-010a); availability and depth of
  `XAUUSDc` tick history is unknown until M2/M5. Standard `XAUUSD` ticks are `PROXY` and cannot pass
  the M6 gate alone (BT-010, MI-198).
- Daily spec snapshots from M2 onward (BT-033; earlier periods carry `CURRENT-SPEC-ONLY`).
- The Guardian session export and `config/session_exceptions.yaml` (EXE-080), and historical
  high-impact USD events with verified timestamps to replay the P-18 blackout (TIME-042/043,
  MI-196; the historical source is unspecified, §9 G3).
- Length, from RES-005/006 and A1: `years ≥ 1 (first train window) + 200 / f + holdout`, with the
  holdout ≥ max(6 months, 20% of the total), `f` = OOS trades per year. *Illustration:* f = 100 →
  1 + 2 + holdout, total ≥ 3.75 years. Eight 3-month windows (A4's coarse minimum) also need ≥ 2
  years of OOS. Whether that much cent tick history exists is `BLOCKED` until M2.

## 3. Candidate A — Session Opening-Range Breakout and Retest (London and New York)

| Field | Proposal |
| --- | --- |
| MI-050 family | Breakout / Retest, session opening-range variant (RES-073 example) |
| Style (D-07) | Intraday |
| Class (RES-023) | C1 intended |
| Timeframes | M15 range and break; M5 retest confirmation; H1 closed-bar context (MI-034) |
| News status (RES-071) | Not news-validated; RISK-018 and the P-18 blackout apply |
| Session-end exit (RES-072) | `max_hold_minutes` = 240 or the P-33 deadline, whichever is first |
| Trades by rule | At most one per session per day (two per day), one open at a time |

**Hypothesis and mechanism.** At the London and New York opens, quoting activity on gold rises
(a `TICK_ACTIVITY_PROXY`, not observed orders, MI-021) and the first hour often sets the day's
initial range. The hypothesis: when an M15 bar closes outside that range with displacement and a
later retest of the broken boundary holds, the continuation pays more than its costs. The
"resting stops beyond the range" story is a price-structure hypothesis inferred from prices only.
**How it fails:** false breakouts that return into the range; quiet days with no follow-through;
news spikes; the strongest breaks never retest, so the rule misses them by design.

**Entry rules** (all required, closed bars, `detected_at ≤ t`):

1. Opening range = high and low of the M15 bars in the range window. Proposed windows (DST-aware,
   frozen at pre-registration): London 08:00–09:00 Europe/London; New York 09:30–10:30
   America/New_York. The range is valid only if its width ≥ 0.3 × H1 ATR(14).
2. **G1 break:** an M15 bar closes beyond the range high (long) or low (short), the breaking leg
   contains a displacement record (MI-030 defaults), within 120 minutes of the range end.
3. **G4 retest rejection:** within 12 M5 bars after the break, an M5 bar trades to within
   0.1 × M15 ATR(14) of the broken boundary and closes back on the breakout side as a rejection
   candle (module 4). The broken level itself is G1 and does not count a second time (MI-043/044).
4. **G6 gate:** the H1 trend (module 1) is not opposite to the trade direction; otherwise
   `NO_TRADE REGIME_NOT_ELIGIBLE`.
5. Minimum confluence: G1 + G4 (two groups, one not G4/G5; MI-042). An FVG retest (G3) may add
   score but is not required. Invalidation before entry: an M15 close back beyond the range
   midpoint → `INVALIDATED`.

**SL / TP.** SL at the opening-range midpoint, minus (long) or plus (short) the current spread.
TP = 1.5 × SL distance net of round-trip spread (≥ P-27 = 1.0), and reachable before P-33
(RISK-034), otherwise no entry. No trailing, no break-even in the base version.

**Operating envelope (RES-070).** Eligible: the two range windows and up to the entry cut-off
(§2.1). Excluded: P-18 blackout, P-19 windows, the first 30 minutes after a broker session open,
days listed in `session_exceptions.yaml`, MI-192 `VOLATILITY_ANOMALY` and `ABNORMAL_MARKET`. Max
spread: P-13 (`min(B, C)` now; A after A-40). Volatility band: all terciles, reported per tercile.
Liquidity proxy: M5 tick count ≥ the 20th percentile for the same session hour on the training
split. Broker sessions: must close by P-33. Quantization: not opted in.

**News effect (argued).** 08:30 New York releases end their blackout at 08:45, before the New York
window; 10:00 releases block entries from 09:30 to 10:15 New York time, so on those days entries
can only come after the blackout. The range is still measured.

**Stop-distance distribution and A10 (argued in advance).** D ≈ half the range width plus the
breakout distance at entry, so D tracks the first-hour range. *ILLUSTRATIVE:* if first-hour ranges
were $8–25, stops would sit roughly between $5 and $20, straddling the exposure floor ($8.03) and
mostly below the minimum-lot ceiling ($24.70). **Expected A10 (`MIN_VOLUME_EXCEEDS_BUDGET`): low,
under ~15% at 10,000 USC**, rising with drawdown (CENT-032) and in the top volatility tercile.
**Expected `EFFECTIVE_LEVERAGE` share: material (possibly a third or more of signals) under the
current reading of GV-17.** S0 measures both (00b prompt).

**Costs that dominate.** Spread and slippage around the open, where spreads may be wider than the
daily median (measured, A-40); stop slippage on failed breakouts. At $10 stops the prior costs are
about 0.05R per trade plus 0.03R on stop exits (§2.3).

**Candidate-specific falsification notes.** London and New York results are reported separately
(RES-030) but are one strategy; splitting them into two strategies later is a new trial. A
positive result that comes from one session only must say so (RES-031).

**Data needed.** §2.5, plus Europe/London and America/New_York DST rules (tz database) for the
windows.

## 4. Candidate B — Volatility-Scaled H1 Trend Following with Session-End Exit

| Field | Proposal |
| --- | --- |
| MI-050 family | Trend Following (RES-073 example) |
| Style (D-07) | Intraday |
| Class (RES-023) | C1 intended |
| Timeframes | H1 signal; H4 closed-bar context |
| News status (RES-071) | Not news-validated; RISK-018 and the P-18 blackout apply |
| Session-end exit (RES-072) | `max_hold_minutes` = 360 or the P-33 deadline, whichever is first |
| Trades by rule | At most one entry per day, one open at a time |

**Hypothesis and mechanism.** Intraday gold moves that have already shown direction on H4 continue
over the next hours often enough, and far enough, to pay for wide stops and costs. Proposed
mechanism: information and position adjustment spread across the London and New York sessions
rather than arriving at once. This is a hypothesis; time-series momentum evidence at intraday
horizons on this symbol is exactly what M6e tests. **How it fails:** choppy, ranging days; reversals
at session transitions; and the forced exit at P-33 cuts off the tail of any longer trend, which may
be where the payoff of a trend rule lives (RES-072: if the edge needs holding past P-33, A9 fails).

**Entry rules** (all required, closed bars):

1. **G6 trend (H4):** sign of the 20-bar H4 return gives the direction; strength
   `|20-bar return| / (ATR_H4(14) × √20) ≥ 0.5` (module 1 definition).
2. **G1 BOS (H1):** an H1 bar closes beyond the latest confirmed H1 swing (`k_internal` = 2) in the
   G6 direction (`break_mode` = close, `break_buffer` = 0).
3. Minimum confluence: G6 + G1 (MI-050 mandatory evidence; G1 is not G4/G5, MI-042). The opposite
   side may hold at most one group, else `NO_TRADE CONFLICT`.
4. The bar closes within the eligible window and before the entry cut-off (§2.1). With
   `max_hold_minutes` = 360 and the daily break near the 21:00–22:00 UTC swap time (TIME-041), the
   last entry falls in the early New York afternoon; the exact time follows the live session export.

**SL / TP.** SL = entry ∓ (1.5 × ATR_H1(14) + current spread). TP = 2.0 × SL distance net of
round-trip spread, reachable before P-33. No trailing in the base version; an ATR or structure
trailing version (MI-170, tighten only) is a separate trial.

**Operating envelope (RES-070).** Eligible: London and New York sessions. Asia is excluded in the
base version to keep one hypothesis; an Asia variant would be a new strategy. Excluded: P-18, P-19,
first 30 minutes after a broker open, exception days, MI-192 anomalies. Max spread: P-13.
Volatility band: all terciles, reported per tercile. Liquidity proxy: H1 tick count ≥ the 20th
percentile for the same hour on the training split. Must close by P-33. Quantization: not opted in.

**Stop-distance distribution and A10 (argued in advance).** D = 1.5 × H1 ATR + spread, the widest
stops of the three. *ILLUSTRATIVE:* H1 ATR $6 → D ≈ $9.30 (0.02 lot); $10 → $15.30 (0.01 lot);
above about $16.27 → D > $24.70 → `MIN_VOLUME_EXCEEDS_BUDGET`. **Expected A10: the highest of the
three; plausibly 10–50% overall and possibly above 50% in the top volatility tercile or after a
drawdown (CENT-032), so `CAPITAL-INFEASIBLE` is a live possibility.** The exposure floor rarely
binds (only when H1 ATR < ~$5.15). If A10 is high only in one tercile, a version restricted to the
other terciles is a **new** pre-registered strategy, never a quiet filter (CENT-031, RES-022).

**Costs that dominate.** Per-trade costs are small in R (about 0.03R at $20 stops). The binding
problems are elsewhere: A10, the P-33 truncation, and A1 (one trade per day at most, so 200 OOS
trades need several years of data, §2.5).

**Candidate-specific falsification notes.** Report the share of trades closed by the time exit or
P-33 and their mean R. If the positive part of the result comes only from trades closed by time
exit near P-33, the hypothesis that the trend continues is weak and the verdict must say so.

**Data needed.** §2.5. H1 and H4 bars are built from ticks (BT-032); fills from ticks.

## 5. Candidate C — M5 Early Reversal Scalping (MI-053), as a falsifiable feasibility test

| Field | Proposal |
| --- | --- |
| MI-050 family | Early Reversal Scalping (MI-053) |
| Style (D-07) | Scalping |
| Class (RES-023) | C1 intended |
| Timeframes | M5 signal; M15 and H1 closed-bar context. No M1 version is proposed (spread share and the exposure floor are worse there); one would be a separate strategy |
| News status (RES-071) | Not news-validated; RISK-018 and the P-18 blackout apply |
| Session-end exit (RES-072) | `max_hold_minutes` = 60 or the P-33 deadline, whichever is first |
| Trades by rule | At most three per session per day, one open at a time |

**Hypothesis and mechanism.** A short run beyond nearby swing highs or lows on M5 that closes back
inside and then shifts structure marks a failed push, and the next move back pays more than the
costs. This is a price-structure hypothesis (MI-021), not a claim about stop orders.
**How it fails:** the "sweep" is the start of a trend leg; the reversal is smaller than the spread
and slippage; latency moves the fill.

**Entry rules** (MI-053.2, all required, closed bars):

1. **G2 sweep:** a wick beyond an M5 liquidity pool (confirmed swings with `k_internal` = 2, or
   equal highs/lows) by ≥ 0.05 × M5 ATR(14), and a close back inside within 1 bar (MI-030 defaults).
2. **G1 shift:** an M5 micro CHOCH or MSS in the reversal direction within 6 bars of the sweep.
3. **G4 rejection:** a rejection candle (module 4) on the sweep bar or the shift bar.
4. **G3 location:** longs only from the M15 discount side, shorts only from the premium side
   (MI-030 premium/discount on M15, `equilibrium` = 0.5).
5. **G6 gate:** no long against an H1 downtrend and no short against an H1 uptrend
   (`NO_TRADE REGIME_NOT_ELIGIBLE`).
6. Minimum confluence: G2 + G1 + G4 + G3, counted as components, not as a
   `REVERSAL_CONFIRMED` record (MI-044 declared). No FVG retracement entry in the base version.

**SL / TP.** SL beyond the sweep extreme by 0.1 × M5 ATR(14) plus the current spread (MI-053.4),
P-13 component C applies. TP = 1.5 × SL distance net of round-trip spread, reachable before P-33.
No break-even or trailing in the base version (A-70 is unknown). Latency: the decision tick must be
fresh (P-15) and the signal reach the RiskEngine within P-29; a stricter
`max_decision_latency_ms` is declared only after M7 latency data (A-42).

**Operating envelope (RES-070).** Eligible: London and New York sessions. Excluded: as A and B.
Max spread: P-13, whose component C already ties spread to ≤ 10% of D. Volatility band: all
terciles, reported per tercile. Liquidity proxy: M5 tick count ≥ the 20th percentile for the same
session hour on the training split. Must close by P-33. Quantization: not opted in.

**Stop-distance distribution and A10 (argued in advance).** Stops sit just beyond a nearby M5
extreme, so they are the tightest of the three. *ILLUSTRATIVE:* if M5 ATR were $2–4, most stops
would fall between about $1 and $6. **Expected A10: near 0%**, because the minimum-lot ceiling is
far away. **Expected tradeable share: low.** Stops under $3.00 fail the spread floor, and stops
under $8.03 fail the exposure floor under the current reading of GV-17. Neither is counted by A10,
so C could report A10 `PASS` while very few of its signals are actually tradeable (§9 G1/G2).
MI-053.8 anticipates exactly this (`CAPITAL-INFEASIBLE` or `FAIL`), and A-67 is `UNKNOWN by design`.

**Why it is still proposed.** D-07 asks for scalping to be researched, and the spec allows
scalping as a falsifiable test (MI-053.8, S0). S0 can show in a short throwaway run, without any
profit computation, whether enough of its signals survive the three walls. If they do not, the
honest record is "scalping infeasible at this capital under the current rules", and no M6e time is
spent on it unless the user changes an input (equity, P-01, or the exposure-floor question).

**Costs that dominate.** Spread and stop slippage: at $3–5 stops the priors give 0.11–0.18R per
trade before stop slippage, 0.14–0.23R under A9 stress (§2.3). Latency (BT-023 prior 150–600 ms)
matters more here than for A or B.

**Candidate-specific falsification notes.** Report the cost share of gross P/L (BT §7) and the
result with costs at the A9 stress. If net expectancy is positive only in one session or
tercile, RES-031 applies.

**Data needed.** §2.5, plus the M5 tick-rate distribution by session hour, and M7 demo latency
and slippage (A-41, A-42) to replace the BT-023/024 priors.

## 6. Comparison

| Item | A Opening-range retest | B H1 trend following | C M5 early reversal scalping |
| --- | --- | --- | --- |
| MI-050 family | Breakout / Retest | Trend Following | Early Reversal Scalping |
| D-07 style | Intraday | Intraday | Scalping |
| Class (intended) | C1 | C1 | C1 |
| Mandatory groups | G1 + G4 (G6 gate) | G6 + G1 | G2 + G1 + G4 + G3 (G6 gate) |
| Trades by rule | ≤ 2 per day | ≤ 1 per day | ≤ 3 per session |
| Stop basis | Range midpoint | 1.5 × H1 ATR | Beyond the M5 sweep extreme |
| Stop size (ILLUSTRATIVE) | ~$5–20 | ~$9–25+ | ~$1–6 |
| Binding wall (argued) | Exposure floor, some ceiling | Minimum-lot ceiling | Spread and exposure floors |
| Expected A10 (argued) | Low, < ~15% | Highest, 10–50%+ | Near 0% |
| Untradeable share outside A10 (argued) | Material | Small | Most signals |
| Cost share of R | Moderate | Small | Large |
| News | Not validated, P-18 applies | Not validated, P-18 applies | Not validated, P-18 applies |
| Session-end exit | 240 min or P-33 | 360 min or P-33 | 60 min or P-33 |
| Main failure risk | False breakouts; exposure floor | A10, P-33 truncation, low A1 | Costs, exposure floor |
| Data per 200 OOS trades | Moderate | Longest | Shortest (if tradeable) |

All "expected" and "argued" entries are reasoning before any test, not measurements. S0 replaces
them with PT0 feasibility numbers; M6e replaces them with PT1 verdicts.

## 7. How the user chooses (D-08)

D-08 can be made now or after S0. S0 is advisory and runs on every candidate in this file
regardless (00b prompt), so choosing after S0 costs nothing except time. The choices:

| Option | What it means | Trade-offs |
| --- | --- | --- |
| A + B + C | Research all three (fits D-07 and D-09) | Most research time; three pre-registrations; DSR trial counts include every evaluated configuration (RES-021); the only path that can later give M6f ≥ 2 PASS strategies across styles; one shared slot, so a priority order is needed (MI-152) |
| A + B | Intraday only | Less work; but D-07 says research scalping too, so this needs the user to revise D-07, or to record C as "deferred after S0 infeasibility" |
| A + C or B + C | One intraday, one scalping | Satisfies D-07 with less work; A and C share the exposure-floor problem, B and C have opposite walls |
| One only | Single strategy | Simplest; M6f becomes `NOT_APPLICABLE` (needs two PASS strategies) |

Points that matter for the choice:

- **Feasibility before edge.** At 10,000 USC and P-01 = 0.25%, B is most exposed to A10 and C to
  the exposure and spread floors. A sits between them. None of this says anything about edge.
- **The exposure-floor question (§9 G1)** decides whether A and C are mostly tradeable at all. It
  is a risk-rule question and needs the user's answer before S0 results can be read, because S0
  measures A10 only by default.
- **Trade count.** B gives the fewest trades; reaching A1 = 200 OOS trades may need more history
  than the cent account provides (§2.5, BLOCKED until M2).
- **Priority order.** With several strategies and one slot, the pre-registration must state which
  strategy's same-direction candidate goes to the RiskEngine first (MI-152). Recent results never
  set that order (RES-060).
- **Freezing constants.** Choosing a candidate also means accepting its constants as written (or
  changing them now), before S0 looks at data, so C1 stays honest (§9 G5).

## 8. Relation to the C4 selector (D-12)

- The user chose a prevalidated selector (D-12). It is built in M6f **only if** at least two
  strategies PASS in M6e (01 prompt, M6f); otherwise M6f is `NOT_APPLICABLE` and each PASS strategy
  runs only inside its own envelope. Nothing here promises that M6f will happen.
- If it happens, the natural inputs for these candidates are fixed in advance and never recent P/L
  (RES-060/061, MI-052): session label, volatility tercile, trend state (RES-030), spread state,
  and the MI-157 regime map (BREAKOUT → A, TRENDING → B, REVERSAL → C).
- The selector is its own C4 strategy: every candidate × selection-rule combination is a trial, it
  needs its own pre-registration, PBO and DSR, and its own PASS before it trades (RES-023/061).
- Without a selector, overlap between A, B and C is handled only by the single slot (RISK-015)
  and the fixed priority (MI-152). That is not selection by performance.

## 9. Spec gaps and contradictions found (for the M0c review; nothing edited)

| # | Where | Finding |
| --- | --- | --- |
| G1 | TRADING_RISK_SPEC RISK-013, EXP-003, GV-17 | Volume comes from the budget only; GV-17 rejects `EFFECTIVE_LEVERAGE` instead of reducing volume. At ILL-CENT and $4,070, every stop ≤ ~$8.03 is rejected. Whether the RiskEngine may reduce volume to meet P-09/P-10/P-11 is unstated. Risk-rule question for the user |
| G2 | CENT-030/031, A10 | The feasibility rate counts only `MIN_VOLUME_EXCEEDS_BUDGET`. `EFFECTIVE_LEVERAGE`, `SPREAD` (P-13 C) and `AGGREGATE_RISK` (shared slot) are not in any capital-feasibility criterion, so a strategy can pass A10 while mostly untradeable |
| G3 | BACKTESTING_SPEC §3; TIME-042/043; MI-196 | No BT rule simulates the P-18 blackout (RISK-018) for non-news-validated strategies, and no historical event source is named (TIME-043 validates only a live export < 24 h old). MI-196 mentions "historical news-event replay" without a source |
| G4 | RES-030, MI-035 | Session labels Asia/London/New York have no defined hours or DST rule |
| G5 | RES-023 (C1) vs 00b S0 prompt | C1 needs constants fixed "before any data was examined"; S0 examines stop distances on the same history before pre-registration. Whether S0 counts as examining data is unstated |
| G6 | RES-061, MI-052 | Both still say D-12 is pending; STATUS §8 records it decided 2026-11-13 |
| G7 | RES/BT per-strategy testing vs D-09 + P-31 = P-01 | Strategies sharing one slot block each other live; per-strategy backtests do not simulate that, so the live trade set differs from the tested one. No criterion covers the joint run |
| G8 | P-19 | "None in the first 30 min after an open": unclear whether "open" means only a broker session open or also the London/New York labels |
| G9 | EXE-081 vs RES-070 | EXE-081 uses a strategy's "expected holding time", but RES-070's envelope list has no `max_hold` field to declare it |
| G10 | RES-073 vs kickoff §5 row c | RES-073 also requires a stop-distance distribution per candidate; the kickoff row omits it (included here, argued) |
| G11 | BT-022 vs BT §5 / A9 | The commission placeholder is 0.5 × median spread; whether the A9 spread × 1.5 stress also scales it is unstated |

## 10. Next

1. User chooses D-08 (now or after S0) and answers G1.
2. S0 (00b prompt) measures, per candidate, at P-01 = 0.10/0.25/0.50% (none an approval): the
   stop-distance distribution, the widest feasible stop, the A10 rate, the spread share and
   surviving signals per week, labelled `PT0 — FEASIBILITY ONLY, NOT A RESULT`, without touching the
   RES-005 holdout and without computing profit (RES-021).
3. M6e: one pre-registration per chosen candidate (`research/prereg/<strategy>@<version>.md`),
   committed before any OOS run, with the constants above, the priority order and the A1–A10
   thresholds. Verdicts follow §2.4; "no candidate passed" is a successful M6 outcome (RES-020).
