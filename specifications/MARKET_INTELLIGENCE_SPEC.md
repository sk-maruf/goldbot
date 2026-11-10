# MARKET_INTELLIGENCE_SPEC — Market intelligence modules, decision engine and strategy families

> Status: **SPECIFICATION (not implemented).** Added 2026-11-08 by the V2.1 intelligence merge
> (`quality/V1_V2_CHANGELOG.md` §5). Source: the user's brief "GoldBot V2.1 — Advanced Intelligence
> Upgrade", reproduced word for word in Appendix A. Every brief item is mapped to a requirement or to
> an existing rule in §11.
>
> **V2.2 (2026-11-10).** §1–11 are Part I. Part II (§12–23, MI-100..MI-199) adds the V2.2 upgrade
> from the user's master upgrade command; its Phase A review and the command itself are in
> `quality/V2_2_ARCHITECTURE_REVIEW.md`. Part II only adds: it changes no Part I rule.
>
> **Precedence.** This file specifies the *signal layer* only. It never overrides
> `TRADING_RISK_SPEC.md`, `EXECUTION_SAFETY_SPEC.md`, `GUARDIAN_SAFETY_SPEC.md`,
> `STRATEGY_RESEARCH_SPEC.md`, `BACKTESTING_SPEC.md` or `CLAUDE.md`. Where the brief and an existing
> rule differ, the **stricter** rule applies, and §11 says which one. No `P-xx` value is set or
> changed here. Every numeric default in this file is a **research default**: it is fixed per
> strategy version in the pre-registration (RES-002, RES-011), never a risk limit, and never an
> approved setting.
>
> **Honest framing.** These modules describe price behaviour. They do not observe institutional
> order flow, and no combination of them is known to produce an edge on this account. Each strategy
> built on them gets an honest verdict under `STRATEGY_RESEARCH_SPEC.md`, and "no edge found" is a
> valid result (RES-020).

## 1. Position in the architecture

- **MI-001 Location and purity.** The modules and the decision engine live in
  `src/goldbot/intelligence/`. They are pure, deterministic functions of their inputs (bars, a tick
  snapshot, the session calendar, the calendar events, the symbol spec and the strategy version's
  parameters). They perform no I/O, read no clock, call no MT5 function and import nothing from
  `engine`, `adapters`, `api`, `research`, `llm` or `mcp` (static import test). The engine **and**
  the backtester import them, so live and simulated signals come from the same code (BT-050).
- **MI-002 Data flow.** `market_data → intelligence modules (Evidence) → strategy + decision engine
  (DecisionRecord) → signal_validator (pre-trade gates) → RiskEngine evaluate() → …` exactly as in
  `SYSTEM_ARCHITECTURE.md` §5. Only a `BUY_CANDIDATE` or `SELL_CANDIDATE` leaves the intelligence
  layer, as a `Signal` (DATA_ARCHITECTURE §3) that references its `decision_id`.
- **MI-003 No authority.** The intelligence layer produces candidates only. It never constructs a
  `RiskApprovedAction`, never sets or scales volume, never selects or changes a `P-xx` value, a risk
  profile, an entry authorization mode or a trading state, and never sends or modifies an order.
  **A confidence or score never changes position size**: volume comes only from RISK-010..016.
  Confidence-weighted sizing would be new risk logic and needs the user's approval and a spec change
  (CLAUDE.md §7).
- **MI-004 No LLM in the signal path.** No module, weight, threshold or rationale is produced by an
  LLM at run time (LLM-001, LLM-006). Rationale text is a deterministic template (LLM-005). An LLM may
  only draft research hypotheses offline, and each tested one counts as a trial (LLM-002, RES-021).

## 2. Common output contract (every module)

- **MI-010 Evidence record.** Every module output is an `Evidence` record with: `evidence_id`
  (deterministic hash of module@version, concept, symbol, timeframe and anchor times); `module`
  and `module_version`; `concept` (a name from §4); `direction` (`BULLISH` / `BEARISH` /
  `NEUTRAL`); `timeframe`; `detected_at` (UTC time at which the evidence first became knowable,
  MI-013); `anchor` (bar open times and price levels that define it); `confidence` (MI-011);
  `data_quality` (`OK` / `DEGRADED` / `INSUFFICIENT`, with a reason); `invalidation` (the price or
  time condition that cancels it); `expires_at`; `reasons` (reason codes); `context` (descriptive
  fields, MI-032); `context_refs` and `derived_from` (other `evidence_id`s); `params_hash`; `env`.
- **MI-011 Confidence is a score, not a probability.** `confidence` is a number in [0, 1] computed by
  a documented deterministic function of the concept's own geometry (size relative to ATR, body
  ratio, touches, age, untested status, …) and rounded to 4 decimal places in records. It measures
  only its own concept, never the context around it (MI-032). No UI, report or log may call it a
  probability or a win chance unless a calibration study on out-of-sample data, registered as its own
  experiment, shows it is calibrated, and then only with that study's ID.
- **MI-012 Objective, versioned rules.** Each concept has an objective detection rule (§4), with its
  parameters, defaults, `detected_at` definition and confidence basis written in
  `docs/intelligence/<module>.md` (created in M6a/M6b). Parameters belong to the strategy version
  that uses them (RES-011): changing any of them creates a new minor version. Code defaults exist
  only for tests.
- **MI-013 No lookahead, no repainting.** An Evidence record uses only data with a timestamp
  ≤ `detected_at`. Bar-based concepts use **closed bars only**. A swing point is confirmed only after
  its right-hand bars close, so its `detected_at` is the close of the last confirming bar, never the
  swing bar itself; the same applies to every concept built on swings (structure, order blocks,
  divergence, pools). Tick-level concepts use only ticks received at or before the decision tick.
  An emitted record is never altered; a later invalidation is a new record that references it.
- **MI-014 Future-truncation test.** For every module and for the decision engine, a property test
  checks that outputs computed on data up to time *t* are identical to outputs computed on the full
  dataset and filtered to `detected_at ≤ t`, for many random *t*. Any difference is a lookahead bug
  and fails CI.
- **MI-015 Data quality fails closed.** `INSUFFICIENT`: stale ticks (P-15), a quarantined tick
  (BT-012) inside the record's lookback window, missing bars inside an open session, or too little
  history for the module's lookback. `DEGRADED`: the inputs are complete, but they lie in a month
  the dataset marks DEGRADED (BT-013). `OK`: neither. The decision engine returns `NO_TRADE` with
  reason `DATA_QUALITY` (MI-041) on any `INSUFFICIENT` input, and in LIVE and DEMO also on any
  `DEGRADED` input. In BACKTEST and REPLAY, `DEGRADED` inputs are used and every resulting record
  carries the flag, so reports can show results with and without those months (BT-013).
- **MI-016 Time and bars.** Bars are built from ticks (BT-032) using the TIME-005 interpretation of
  tick times; the D1 bar and every session boundary follow the trade-server day and sessions from the
  Guardian export (TIME-030, TIME-040). Records use UTC timestamps (DATA-003). Supported timeframes
  are M1, M5, M15, M30, H1, H4 and D1; each strategy version declares the ones it uses.
- **MI-017 Determinism.** The same inputs and parameters give byte-identical Evidence and
  DecisionRecords (BT-040).
- **MI-018 Module health.** Each module reports a health state to the observability layer
  (OBSERVABILITY_SPEC §3). An exception, a timeout or missing inputs makes that module `UNKNOWN`,
  and every decision that needs it is `NO_TRADE` with reason `MODULE_UNAVAILABLE`. Position
  management, exits and the safety components keep running unchanged.

## 3. Modules and concept ownership

- **MI-020 Module register.** There are twelve independent modules (11 and 12 added in V2.2). Each concept has exactly **one
  owning module** that detects it. Other modules consume it by `evidence_id` and never re-detect or
  re-emit it. This single-ownership rule is the basis of double-counting control (MI-043/044).

| # | Module | Owns (detects) | Consumes (by reference) |
|---|---|---|---|
| 1 | Trend Intelligence Engine | Trend direction and strength per timeframe (slope of a moving average, `|n-bar return| / (ATR × √n)`), pullback depth | Structure labels (SMC) |
| 2 | Smart Money Concepts Engine | Swings, HH/HL/LH/LL, BOS, CHOCH, MSS (internal and external), order blocks, breaker blocks, mitigation blocks, FVG, inverse FVG, premium/discount, inducement, displacement | Liquidity pools and sweeps |
| 3 | Advanced Candlestick Recognition Engine | The named patterns in MI-031 | Candle metrics (descriptors only) |
| 4 | Candle Behavior Analysis Engine | Wick/body ratios, closing strength (close position within the range), range relative to ATR, rejection candles, momentum candles; V2.2: consecutive directional candles, compression, expansion, failed continuation, impulse and retracement quality (MI-130) | — |
| 5 | Early Reversal Detection Engine | Failed breakouts, momentum exhaustion, RSI/MACD divergence, reversal warnings and confirmations (MI-033) | Sweeps, micro BOS/CHOCH, displacement, rejection, tick-activity anomalies |
| 6 | Early Reversal Scalping Engine | No market concept: it is the strategy implementation of MI-053 | Everything it needs, by reference |
| 7 | Live Market Perception Engine | Price velocity, momentum, realised volatility, tick rate and tick-activity anomalies, spread condition versus the P-13 components, session condition, news-window condition | False breakouts and exhaustion (from module 5) |
| 8 | Liquidity Intelligence Engine | Equal highs and lows, buy-side and sell-side liquidity pools, liquidity sweeps, internal versus external liquidity, which pools were taken; V2.2: confirmed sweeps versus wick penetrations, stop runs, failed grabs, sweep and reclaim, post-sweep displacement, liquidity target map (MI-140) | Swings (SMC) |
| 9 | Market Regime Detection Engine | Regime labels (MI-035) | Trend, volatility |
| 10 | Multi-Timeframe Confluence Engine | Alignment records between timeframes (MI-034) | Trend and structure evidence per timeframe |
| 11 | Fibonacci Intelligence Engine (V2.2) | Impulse-leg anchors, retracement and extension levels, golden and OTE zones, clusters, zone freshness (MI-110..117) | Swings and displacement (SMC), ATR, order blocks and FVGs (for confluence records) |
| 12 | Chart Pattern Intelligence Engine (V2.2) | Support/resistance levels and the MI-121 chart patterns with their states and outcomes (MI-120..123) | Swings (SMC), compression and range expansion (module 4), false breakouts (module 5) |

- **MI-021 No order-flow claims.** The modules use MT5 bid/ask ticks, tick counts and bars only.
  "Liquidity", "smart money", "order block" and similar names describe **price-structure hypotheses
  inferred from prices**, not observed orders. Tick activity is labelled `TICK_ACTIVITY_PROXY`,
  because retail CFD tick volume is not traded volume (A-34). No feature, label, UI text, log or
  report may claim access to centralised or institutional order flow unless a verified data source
  that provides it is added through an ADR. Order-flow strategies stay out of scope (RES-073).

## 4. Objective concept rules (research defaults)

Notation: `body = |close − open|`, `range = high − low`, `upper = high − max(open, close)`,
`lower = min(open, close) − low`, `ATR` = ATR(14) of the same timeframe. Every `×ATR` threshold is a
parameter. Every concept has a bullish and a bearish mirror unless stated.

### 4.1 MI-030 Smart Money Concepts and liquidity rules

| Concept | Objective rule (default) | Parameters (default) | `detected_at` | Confidence basis |
|---|---|---|---|---|
| Swing high / low | Bar *i* is a swing high if `high[i] > max(high[i−k..i−1])` and `high[i] ≥ max(high[i+1..i+k])` (mirror for lows) | `k_internal` = 2, `k_external` = 5 | close of bar *i+k* | prominence ÷ ATR |
| HH / HL / LH / LL | Compare each confirmed swing with the previous confirmed swing of the same kind; a difference below `min_swing_delta` × ATR counts as equal | `min_swing_delta` = 0 | confirmation of the newer swing | difference ÷ ATR |
| BOS | A closed bar closes beyond the latest confirmed swing in the direction of the prevailing structure by ≥ `break_buffer` | `break_mode` = close (or wick), `break_buffer` = 0 | close of the breaking bar | break distance ÷ ATR, displacement present |
| CHOCH | The first close beyond the latest confirmed swing **against** the prevailing structure (e.g. in LH/LL structure, a close above the latest LH) | as BOS | close of the breaking bar | as BOS |
| MSS | A CHOCH whose breaking leg contains a displacement candle | as CHOCH + displacement | close of the breaking bar | CHOCH score × displacement size |
| Displacement | One candle, or a run of ≤ `disp_max_bars` candles in one direction, with total body ≥ `disp_body_atr` × ATR and body/range ≥ `disp_body_ratio` | `disp_body_atr` = 1.5, `disp_body_ratio` = 0.6, `disp_max_bars` = 3 | close of the last candle | body ÷ ATR |
| FVG | Bullish if `low[c3] > high[c1]`; bearish if `high[c3] < low[c1]`; gap ≥ `min_fvg` × ATR. Partly mitigated when price trades into it; fully mitigated when a close passes through it | `min_fvg` = 0.1 | close of c3 | gap ÷ ATR, untested |
| Inverse FVG | An FVG fully violated by a close through it; the zone then counts with the opposite direction | — | close of the violating bar | original FVG score |
| Order block | Bullish: the last bearish-bodied candle before a displacement leg that produces a BOS up; zone = that candle's `[low, high]` (or its body, `ob_zone`) | `ob_zone` = range | close of the **BOS bar**, never the OB candle | displacement size, untested, age |
| Breaker block | An order block closed through **after** price swept the opposite liquidity (made a new extreme); the zone flips direction | — | close of the invalidating bar | sweep size, displacement |
| Mitigation block | An order block closed through **without** a new extreme first (the swing failed); the zone flips direction | — | close of the invalidating bar | as breaker |
| Equal highs / lows | ≥ 2 confirmed swing highs (lows) within `eq_tolerance` × ATR of each other within `eq_lookback` bars | `eq_tolerance` = 0.1, `eq_lookback` = 100 | confirmation of the second swing | number of touches |
| Buy-side / sell-side liquidity | Pools above swing highs and equal highs (buy-side) and below swing lows and equal lows (sell-side); level = the extreme | — | confirmation of the defining swing | touches, external vs internal |
| Liquidity sweep | A wick trades beyond a pool by ≥ `sweep_min` × ATR, then a close returns to the original side within `sweep_close_bars` bars | `sweep_min` = 0.05, `sweep_close_bars` = 1 | the close that returns | penetration ÷ ATR, pool strength |
| Premium / discount | Dealing range = latest confirmed external swing low to swing high on `range_tf`; above `equilibrium` = premium, below = discount | `range_tf` = strategy-declared, `equilibrium` = 0.5 | when the range is confirmed | distance from equilibrium |
| Inducement | An internal swing inside a leg whose level is swept before price reaches an untested order block or FVG of the same leg | — | close of the sweep bar | sweep and zone scores |
| Internal / external liquidity | External = pools at the dealing-range extremes (`k_external` swings); internal = pools and FVGs inside the range (`k_internal` swings) | as swings | as swings | — |

### 4.2 MI-031 Candlestick pattern rules

Every pattern also needs `range ≥ min_range_atr × ATR` (default 0.3) on its main candle, so noise bars
do not count. `detected_at` is the close of the pattern's last candle. Intraday gold rarely gaps, so
patterns whose classic definition needs a gap use `gap_rule` = `relaxed` by default (an open at or
beyond the prior close counts); `strict` is a parameter.

| Pattern | Rule (default) |
|---|---|
| Doji | `body ≤ 0.1 × range` |
| Marubozu | `body ≥ 0.9 × range`; direction = candle colour |
| Hammer / Hanging man geometry | `lower ≥ 2 × body`, `upper ≤ 0.15 × range`. Called **Hammer** after a decline and reported as bullish; after an advance the same geometry is reported as the bearish *hanging man* variant |
| Inverted hammer / Shooting star | `upper ≥ 2 × body`, `lower ≤ 0.15 × range`. **Inverted hammer** after a decline (bullish); **shooting star** after an advance (bearish) |
| Pin bar | One wick ≥ ⅔ of the range and the close in the opposite third of the range |
| Engulfing | Candle 2's body covers candle 1's body completely, opposite colours, `body2 ≥ body1` |
| Harami | Candle 2's body lies inside candle 1's body, opposite colours |
| Piercing line / Dark cloud cover | Candle 1 long (`body ≥ 0.6 × ATR`) bearish (bullish); candle 2 opens at or below (above) candle 1's close (`gap_rule`) and closes beyond candle 1's body midpoint without closing beyond its open |
| Morning star / Evening star | Candle 1 long bearish (bullish); candle 2 `body ≤ 0.3 × body1`; candle 3 bullish (bearish) and closes beyond candle 1's body midpoint |
| Tweezer bottom / top | Two consecutive candles with lows (highs) within `0.05 × ATR`, first bearish (bullish), second bullish (bearish) |
| Three white soldiers / Three black crows | Three consecutive candles of one colour, each closing beyond the previous close, each opening inside the previous body, each with the shadow beyond its close ≤ `0.3 × body` |
| Inside bar | `high2 ≤ high1` and `low2 ≥ low1` (neutral; direction comes only from context) |
| Outside bar | `high2 > high1` and `low2 < low1`; direction = candle 2's colour |
| Three inside up / down | A bullish (bearish) harami, then candle 3 closes beyond candle 1's open |
| Three outside up / down | A bullish (bearish) engulfing, then candle 3 closes beyond candle 2's close |

"After a decline / advance" is a descriptor: the sign of the close-to-close move over the previous
`prior_move_bars` bars (default 5). It is not trend evidence and is not scored.

- **MI-032 Pattern context without double counting.** As the brief requires, every candlestick record
  carries context **descriptors**: location (references to the liquidity pools, order blocks, FVGs
  or premium/discount zone it touches), trend context (reference to the trend evidence), volatility
  tercile, wick/body ratio and closing strength. These are references and descriptive fields only.
  The pattern's own `confidence` measures pattern geometry alone, and only the decision engine
  combines patterns with their context (MI-042). **A candlestick pattern alone is never a trading
  signal** (MI-042 minimum confluence).
- **MI-033 Early reversal: warning versus confirmed.** The Early Reversal Detection Engine emits two
  different record types with **separate scores**:
  - `REVERSAL_WARNING`: at least `warn_min_groups` (default 2) components from **different**
    correlation groups (MI-043) occur at one level within `warn_window` bars (default 5). Components:
    liquidity sweep; failed breakout (a close beyond a level by ≥ `break_buffer`, then a close back
    inside within `fb_bars`, default 3); momentum exhaustion (≥ `exh_bars`, default 3, consecutive
    candles in the trend direction with shrinking bodies, plus RSI(14) beyond 70/30); regular RSI(14)
    or MACD(12, 26, 9) histogram divergence between **two confirmed swings** no more than
    `div_max_bars` (default 60) apart; micro BOS/CHOCH on a lower timeframe; a rejection candle;
    displacement against the trend; a tick-activity anomaly (z-score ≥ 2.0 against the median for
    the same session hour over 20 days, `TICK_ACTIVITY_PROXY`).
  - `REVERSAL_CONFIRMED`: a warning followed, within `confirm_bars` (default 10), by a CHOCH or MSS
    in the reversal direction on the strategy's signal timeframe (closed bar), while the warning's
    invalidation level (beyond the sweep or exhaustion extreme) has not been breached.
  Both are derived records (`derived_from` lists their components). A warning alone can only produce
  `WAIT`, never a candidate.
- **MI-034 Multi-timeframe confluence uses closed higher-timeframe bars.** At decision time *t*, a
  higher timeframe contributes only its **last closed bar** and evidence with `detected_at ≤ t`. A
  forming higher-timeframe bar is never used. Alignment records are derived records that reference
  the per-timeframe evidence.
- **MI-035 Regime labels.** The Market Regime Detection Engine implements the RES-030 labels exactly
  (volatility tercile from 14-day ATR against its 1-year distribution; trend state from the sign of
  the 20-day return and `|20-day return| / (ATR × √20)`; session Asia/London/New York), so reports and
  live decisions use one definition. It may add intraday labels (for example trending, ranging,
  expanding) as versioned parameters. A regime label is never a trade signal by itself; it acts only
  through a strategy's declared envelope (MI-051) or a prevalidated selector (MI-052).

## 5. Intelligent decision engine

- **MI-040 Inputs.** For one strategy version at decision time *t*: every Evidence record with
  `detected_at ≤ t` that has not expired or been invalidated, the Live Market Perception state, the
  regime labels and that version's weights, group caps and thresholds.
- **MI-041 Outcomes.** Exactly one of:
  - `BUY_CANDIDATE` / `SELL_CANDIDATE`: the strategy's mandatory conditions hold and MI-042 is met.
    It becomes a `Signal` for the signal_validator and the RiskEngine.
  - `WAIT`: a setup is developing (for example a reversal warning without confirmation). No signal.
  - `NO_TRADE`: trading is not allowed now, with a reason code: `DATA_QUALITY`,
    `MODULE_UNAVAILABLE`, `OUTSIDE_ENVELOPE`, `REGIME_NOT_ELIGIBLE`, `NEWS_WINDOW`, `SPREAD`,
    `SESSION`, `CONFLICT`, `INSUFFICIENT_CONFLUENCE`, `CONFLICTING_POSITION`.
- **MI-042 Scoring and minimum confluence.** Bullish and bearish scores are computed separately as a
  weighted sum over correlation groups (MI-043). Within a group only the highest-weighted eligible
  record counts, and each group contributes at most its cap. A candidate requires all of:
  the chosen side's score ≥ `entry_threshold`; the opposite side's score ≤ `conflict_threshold`;
  contributions from **at least two different groups, at least one of which is not G4 (candles) or
  G5 (oscillators)**; and the strategy's mandatory evidence. So no entry ever rests on a single
  indicator or a single candle pattern. Context items (session, spread, news window, data quality,
  module health) are gates that can only block, never score points.
- **MI-043 Correlation groups (default).** Every concept in §3 and §4 belongs to exactly one group.
  G1 structure (swings, HH/HL/LH/LL, BOS, CHOCH, MSS, displacement, support/resistance levels, chart
  patterns); G2 liquidity (pools, equal highs/lows, sweeps, failed breakouts, inducement, pools taken,
  stop runs, failed grabs, sweep and reclaim, post-sweep displacement); G3 zones (order, breaker and
  mitigation blocks, FVG, inverse FVG, premium/discount, Fibonacci levels, zones and clusters); G4
  candles (patterns and candle behaviour, including rejection, consecutive directional candles and
  failed continuation); G5 momentum (divergence, exhaustion, velocity, momentum, compression,
  expansion); G6 trend and regime (trend direction and strength, pullback depth, impulse and
  retracement quality, realised volatility, multi-timeframe alignment, regime); G7 participation (tick-activity
  anomalies). Research reports the pairwise correlation of group contributions on training data;
  groups whose contributions correlate with `|ρ| > 0.7` (default) must be merged in the next strategy
  version.
- **MI-044 Derived records count once.** A derived record (a reversal warning or confirmation, a
  multi-timeframe alignment, a strategy-level confluence) and the records listed in its
  `derived_from` are never both counted: the engine counts either the derived record or its
  components, as the strategy version declares, and records the excluded ones with reason
  `COUNTED_VIA_DERIVED`. A counted derived record contributes its score once, in the one group the
  strategy version declares for it; the MI-042 minimum-confluence check uses the groups of its
  components.
- **MI-045 Decision record.** Every decision, including `WAIT` and `NO_TRADE`, is stored as a
  `DecisionRecord`: `decision_id`, `ts`, `env`, strategy@version, regime labels, outcome, bullish and
  bearish scores, contributing `evidence_id`s by group, excluded evidence with the reason (duplicate,
  expired, capped, counted via derived), data quality, the invalidation condition, the proposed
  entry, SL and TP from the strategy's rules, reason codes and the deterministic rationale text
  (LLM-005). Every record also carries `params=FIXTURE` when RISK-005/066 fixture values are in
  effect.
- **MI-046 Downstream gates are unchanged.** A candidate still passes the pre-trade gates, the
  strategy envelope and news policy (RISK-017/018), the signal-age limit (P-29) and the full
  RiskEngine `evaluate()`. A rejected candidate keeps its RiskEngine reason code (for example
  `MIN_VOLUME_EXCEEDS_BUDGET`, CENT-030), joined through `signal_id`. Under `MANUAL_APPROVAL` the
  approval card shows the deterministic rationale (UI-031).
- **MI-047 Conflicts and no hedging.** Simultaneous opposite candidates (from one strategy or from
  several) produce `NO_TRADE` with `CONFLICT` for all of them. A candidate opposite to an open GoldBot
  position on the same symbol produces `NO_TRADE` with `CONFLICTING_POSITION`: GoldBot never hedges
  (TRADING_RISK_SPEC §10). Exiting the open position remains the strategy's own exit rule.

## 6. Strategy families and adaptive selection

- **MI-050 Six strategy families.** The decision engine serves these families. Each one, and each
  variant of it, is a **separate strategy** with its own pre-registration (RES-002), version
  (RES-011), class (RES-023), operating envelope (RES-070), budget (P-32), verdict (RES-020) and
  degradation state (RES-040). Only strategies with verdict `PASS` may trade (RES-060). Which
  families are researched and traded is the user's choice (D-07, D-08, D-09); M0 proposes candidates
  from this list (RES-073).

| Family | Mandatory evidence (default) | Typical timeframes |
|---|---|---|
| Trend Following | G6 trend aligned on the context timeframe + G1 BOS in the trend direction | H1 signal, H4/D1 context |
| Trend Pullback | G6 trend + a G3 zone on the discount (uptrend) or premium (downtrend) side + G4 rejection or a G1 internal CHOCH back with the trend | M15/H1 |
| Reversal | `REVERSAL_CONFIRMED` (MI-033) at external liquidity or a higher-timeframe G3 zone | M15/H1 |
| Early Reversal Scalping | MI-053 | M1/M5 signal, M15/H1 context |
| Liquidity Sweep | G2 sweep of an external or equal-highs/lows pool + G1 MSS + retracement into the resulting G3 zone | M5/M15 |
| Breakout / Retest | G1 BOS of a range or session boundary with displacement + a retest of the broken level or FVG that holds (G3/G4) | M5/M15 (includes session opening-range variants) |

- **MI-051 Regime dependence through the envelope.** A strategy may declare in its pre-registration
  the regime labels (MI-035) in which it is eligible. That is part of its own validated rule and is
  enforced as the envelope (RISK-017). It is not strategy switching.
- **MI-052 Adaptive strategy selection = the prevalidated selector.** Choosing *between* PASS
  strategies by regime is allowed only through a selector registered and validated as a **C4
  strategy** (RES-061): fixed inputs (regime labels, session, spread state), its own pre-registration
  and version, and its own PASS. "Validated strategy performance" in the brief means performance
  recorded in the experiment registry for that strategy and regime (RES-030/031), frozen into the
  selector version. A strategy's **recent live or demo P/L is never a selection input** (RES-060).
  The selector exists only if the user chooses it (D-12); it is built in M6f and trades only after it
  PASSes. Until then, each PASS strategy runs only within its own envelope.
- **MI-053 Early reversal scalping strategy (XAUUSD M1/M5).**
  1. *Timeframes:* signal on M1 or M5 (declared per version); M15 and H1 closed bars (MI-034) as
     context filters, for example no long against an H1 downtrend and longs only from the M15
     discount side.
  2. *Setup (all required):* a micro liquidity sweep (G2) → a structure shift, micro CHOCH or MSS
     (G1) → rejection confirmation (G4). Optional: an FVG retracement entry.
  3. *Entry:* at market on the confirmation close, or, for an FVG retracement, at market when a tick
     trades into the FVG before `entry_expiry_bars`. Pending orders are not used while P-06 = 0
     (TRADING_RISK_SPEC §2); a version that needs them needs a P-06 change approved by the user.
  4. *Spread-adjusted levels:* BUY levels are measured from the ask and SELL levels from the bid; the
     SL lies beyond the sweep extreme by `sl_buffer` plus the current spread, and must satisfy
     RISK-032 and P-13 (component C, spread ≤ 10% of the SL distance, applies). The TP must satisfy
     P-27 net of spread and be reachable before P-33 (RISK-034).
  5. *Dynamic stop-loss:* the SL may only be tightened, by rules declared in the version (for example
     to break-even at +1R, then trailing behind M1 structure), through `evaluate_modification()`.
     It is never widened (RISK-033).
  6. *Latency controls:* the decision tick must be fresh (P-15), the signal must reach the RiskEngine
     within P-29, and the version may declare a stricter `max_decision_latency_ms`. Measured
     latencies are recorded; an EXE-060 breach moves the strategy to WATCH (RES-040).
  7. *Time-based exit:* the position is closed at `max_hold_minutes` (declared) through
     `evaluate_reduction()`, and in all cases by the session-close deadline (P-33).
  8. *Feasibility:* M1/M5 stops are tight, so spread is a large share of the risk. S0 measures the
     spread share and A10, and the strategy may end `CAPITAL-INFEASIBLE` or `FAIL`. Its trading-style
     choice is D-07.

## 7. Risk management (mapping; the RiskEngine stays the only authority)

- **MI-060 Mapping.** Every risk item of the brief is an existing control: daily loss P-02, weekly
  loss P-03, equity drawdown P-04, aggregate open risk P-31, position count P-05, effective leverage
  P-09, margin utilisation and margin level P-10/P-11 with EXP-001..009, spread P-13, minimum lot
  larger than the budget → reject (RISK-013, CENT-030), and the prohibited list (martingale, grid,
  averaging down, loss-recovery sizing; TRADING_RISK_SPEC §10). The intelligence layer adds no risk
  limit and no exception.
- **MI-061 Risk profiles.** A risk profile is a **named set of P-xx values chosen and approved by the
  user**. `config/risk_limits.yaml` may carry an optional `profile_name` label, which has no
  behaviour of its own. Every value in it needs the RISK-092 approval record; exactly one approved
  set is loaded at a time; changing profile is a `P-xx` change (file edit, restart, typed
  confirmation, RISK-090), and no component can switch it (RISK-091). The brief's word "aggressive"
  authorises no value: Claude Code never proposes, selects or defaults a profile (CLAUDE.md §3.22),
  and the system never suggests a looser profile after losses (R-11).
- **MI-062 Strategy budgets.** Each strategy family uses its own P-32 ≤ P-01 (RISK-016). A scalping or
  "aggressive" strategy never receives a larger budget than P-01.

## 8. Research and validation

- **MI-070 Same pipeline, no shortcuts.** Every strategy built on this layer goes through
  `STRATEGY_RESEARCH_SPEC.md` and `BACKTESTING_SPEC.md` unchanged: PT1 historical tick backtesting
  (BT-020..035) with bid/ask spreads (BT-020/021), slippage (BT-024), commission (BT-022) and latency
  (BT-023); chronological out-of-sample splits and a one-shot holdout (RES-005); walk-forward
  (RES-006); Monte Carlo (A7); parameter sensitivity (A8); cost stress (A9); the demo forward test
  (PT2, M9b). Lookahead and leakage are prevented by MI-013/014 and, for any fitted weight, by
  purging and embargo (RES-007).
- **MI-071 Weights are parameters, and every weight set is a trial.** Decision-engine weights, group
  caps and thresholds are numeric constants of the strategy version. Every evaluated set counts as a
  trial (RES-021). Evaluating more than one set makes the strategy C2; fitting the weights with a
  model makes it C3 and needs decision D-10 (RES-023).
- **MI-072 Extra report metrics (reported, not gates).** In addition to the BT §7 contents, reports
  for these strategies show the recovery factor (net profit ÷ maximum drawdown), trade frequency
  (trades per week), risk-adjusted return (Sharpe and Sortino of daily returns, and mean R ÷ σ_R),
  results per regime (RES-030/031), and an evidence-group ablation (the result with each group
  removed). Acceptance stays A1–A10. Win rate is reported and never optimised (RES-050), which is
  stricter than the brief's "not solely".

## 9. Explainability and monitoring

- **MI-080 Per-trade explanation.** Every trade can be explained from stored records joined by ID
  (`decision_records` → `signals` → `risk_decisions` → `proposals`/`approvals` → `order_intents` →
  `deals`): selected strategy@version; market regime; trend direction; SMC context (G1/G3 evidence);
  candlestick context (G4 evidence and its descriptors); reversal scores (warning and confirmed,
  separately); entry rationale; stop-loss rationale (rule, level, distance, spread and stops level);
  take-profit rationale (rule, R:R against P-27, reachable before P-33); risk budget and modelled loss
  (RiskDecision); execution result (ExecutionReport and reconciliation). A test checks that every
  field exists for every trade in a REPLAY run.
- **MI-081 Dashboard additions (built in M9a; read-only, `ui:read`).** An **Intelligence** screen
  with: active strategies with state (RES-040), regime labels and last decision; a **rejected
  signals** list (`NO_TRADE` decisions and RiskEngine rejections with reason codes, plus counts per
  reason); a decision explanation drawer (MI-080); and per-module health on the System screen
  (MI-018). Equity, drawdown and open risk are already in UI-021. The screen follows the
  status-truthfulness rules (UI-010/011): a missing or stale module is UNKNOWN, never green.
- **MI-082 Honest labels.** Chart overlays and panels label SMC zones and liquidity levels "inferred
  from price" (MI-021), show `confidence` as a score (MI-011), and carry the tier label (BT-001) and
  the FIXTURE banner where applicable (RISK-066).

## 10. Implementation rules

- **MI-090 Architecture impact report first.** Before writing any intelligence code, the M6a session
  inspects the repository and `docs/STATUS.md` and writes `docs/intelligence/ARCHITECTURE_IMPACT.md`:
  affected components, new files, interfaces, schema additions (`Evidence`, `DecisionRecord`), the
  `decision_records` table, tests by requirement ID, and risks. It waits for the user's approval
  (CLAUDE.md §4 milestone loop).
- **MI-091 Incremental build order.** M6a: contracts, bar and timeframe utilities, the
  future-truncation harness (MI-014), Candle Behavior, Candlestick, Liquidity, SMC. M6b: Trend,
  Regime, Multi-Timeframe Confluence, Live Market Perception, Early Reversal, the decision engine and
  DecisionRecord persistence. M6e: the strategy families the user selected (or the M0 candidates
  while D-08 is pending) and their research. M6f: the selector, only if D-12 chooses it. V2.2 inserts two parts before the research part:
  M6c builds modules 11 and 12 and the module 4 and 8 extensions (MI-110..140); M6d builds the
  setup fields, the lifecycle record, trailing and exit evaluation as pure functions, the
  timeframe roles and the market-condition gates (MI-150..192). One module
  at a time, each with its tests before the next starts.
- **MI-092 Tests.** Unit tests per concept on hand-labelled synthetic bar sequences (positive,
  negative and boundary cases for every rule in §4); the MI-014 future-truncation property tests;
  determinism tests (MI-017); regression tests that pin the Evidence hash list of a recorded dataset
  (any change needs a new version, RES-011); integration tests through the backtester with FakeBroker;
  a static test for MI-001; tests that a confidence value cannot reach sizing (MI-003), that a single
  group cannot produce a candidate (MI-042), that derived records are counted once (MI-044) and that
  conflicts never hedge (MI-047). Tests are never weakened (GOV-002).
- **MI-093 No autonomous live trading before every gate passes.** The intelligence layer changes no
  gate. LIVE needs Phase 0, every approved decision (RISK-005), the M10 GO (CLAUDE.md §3.17), and the
  promotion gate for any automatic mode (RISK-061/063). Every CRITICAL requirement in this file must
  be VERIFIED before M10 (03 prompt §2).

## 11. Brief-to-pack reconciliation

| Brief item | Where it lands | Reconciliation |
|---|---|---|
| "Upgrade the existing GoldBot V2.1"; "First inspect the existing repository" | M6a–M6f (`prompts/01_MILESTONE_PROMPTS.md`), MI-090 | Nothing is built when this pack starts, so the upgrade is built as M6 parts after the backtester (M5). If the repository already has some of it, MI-090 inventories it first |
| Preserve RiskEngine authority, Guardian, execution safety, audit, security, release gates | MI-003, MI-046, MI-093; CLAUDE.md §3.23 | Unchanged; the intelligence layer is upstream of every control |
| §1 ten modules | MI-020 | One owner per concept |
| §2 SMC concepts with objective rules, parameters, timestamps, confidence | MI-030, MI-010..013 | Defaults are research parameters fixed per version |
| §3 candlestick patterns; context; "not a signal alone" | MI-031, MI-032, MI-042 | Context by reference, so it is not counted twice |
| §4 early reversal; warning vs confirmed; separate scores | MI-033 | A warning alone gives WAIT |
| §5 M1/M5 scalping | MI-053 | No pending orders while P-06 = 0; SL tighten-only; style is D-07; feasibility via S0/A10 |
| §6 live perception; "actual MT5 data"; no order-flow claims | MI-020 (module 7), MI-021 | Tick volume is a labelled proxy (A-34); news only from the Guardian calendar export (ADR-007, RISK-018) |
| §7 decision engine; BUY/SELL/WAIT/NO TRADE; no double counting; timestamps, quality, confidence, invalidation, reasons | MI-040..047 | Correlation groups + derived-record rule |
| §8 adaptive strategy selection | MI-050..052 | Only through a C4 selector (RES-061), pending D-12; never on recent P/L (RES-060). CLAUDE.md §5 "not in v1: regime switching" is narrowed to "outside that selector" |
| §9 risk profiles, limits, no martingale, min lot → reject | MI-060..062 | No value chosen; profiles are user-approved P-xx sets |
| §10 research and validation | MI-070..072 | Existing pipeline; extra metrics reported, not gates; win rate never optimised (stricter) |
| §11 explainability and dashboard | MI-080..082 | Built in M9a on the local dashboard (ADR-013) |
| §12 impact report, incremental modules, tests, no live trading before gates | MI-090..093 | — |
| V2.2 master upgrade command (2026-11-10) | Part II, MI-100..199; `quality/V2_2_ARCHITECTURE_REVIEW.md` | Additive. Narrowed items (no second scorer or authority, no win probabilities, AUTO_ALL as intent only, partial exits only where volume allows) are listed in that file's §0 |

# Part II — V2.2 upgrade (2026-11-10)

> Source: the user's "MASTER UPGRADE COMMAND — GoldBot V2.1 → V2.2", kept word for word in
> `quality/V2_2_ARCHITECTURE_REVIEW.md` Appendix A, together with the Phase A review (inventory,
> gaps, architecture, dependencies, risk impact, sequence). Part II is **additive**: no requirement in
> Part I is removed or loosened, no `P-xx` value changes, and every Part I rule (MI-001..MI-093) also
> applies to everything here. In particular: modules stay pure (MI-001), produce candidates only
> (MI-003), never look ahead (MI-013/014), and pass the RiskEngine (MI-046).
>
> **Not new engines.** The command names a "High-Probability Setup Engine", a "Trade Authorization
> Engine" and an "Autonomous Trade Management Engine". Each one is specified here as an **extension of
> an existing component** (the decision engine, the existing approval path, the existing position
> manager), so there is still one scorer and one authority. Building them as separate engines would
> create a second score and a second path to an order.

## 12. Versioning, migration and rollback

- **MI-100 Additive V2.2.** V2.2 capabilities are reachable only through strategy versions that
  declare them (RES-011). A V2.1 strategy version that declares none of them behaves exactly as
  before, which gives the BASELINE in MI-196 at no extra cost.
- **MI-101 Migration and rollback.** Schema changes are additive versioned migrations (DATA-020), each
  with a tested down-migration. Rollback means pausing the V2.2 strategy versions (RES-040 `PAUSED`)
  and running the down-migration. A test proves that a V2.1 strategy version produces byte-identical
  decision records before and after the V2.2 migration (MI-017).

## 13. Fibonacci Intelligence Engine (module 11, group G3)

- **MI-110 Confirmed impulse legs only.** A Fibonacci anchor is an impulse leg between two confirmed
  external swings (MI-030) that contains displacement or a BOS and spans ≥ `impulse_min_atr` × ATR
  (default 2.0). Its `detected_at` is the confirmation of the ending swing. Until that swing is
  confirmed, levels are `PROVISIONAL`: they may be displayed and may produce `WAIT`, but they can
  never support a candidate.
- **MI-111 Levels.** For a bullish leg from low *L* to high *H*: retracement level *r* = *H* − *r* ×
  (*H* − *L*); extension level *e* = *L* + *e* × (*H* − *L*). A bearish leg is the mirror image.
  Retracements: 0.236, 0.382, 0.500, 0.618, 0.650, 0.705, 0.786, 0.886. Golden zone: 0.618–0.705.
  OTE zone: 0.618–0.786. Reference level: 0.705. Extensions: 1.000, 1.272, 1.414, 1.618, 2.000,
  2.618. `extension_mode` = `leg` (default, as above) or `abc` (projected from the retracement low)
  is a versioned parameter.
- **MI-112 ATR-normalised proximity.** Price is at a level when |price − level| ≤ `fib_tol_atr` × ATR
  (default 0.1). Zone membership is inclusive of both ends. No fixed price distance is used anywhere.
- **MI-113 Multi-timeframe clusters.** Levels from each timeframe use closed bars only (MI-034). A
  cluster is ≥ `cluster_min` (default 2) levels from **different** anchors (other legs or other
  timeframes) within `cluster_tol_atr` × ATR (default 0.15). A cluster is one derived record (MI-044),
  never one count per level.
- **MI-114 Confluence records.** Golden-zone and OTE overlap with an order block or FVG, a liquidity
  sweep inside the zone, and a CHOCH/MSS after the zone is touched are derived records that reference
  their components and count once (MI-044). The Fibonacci zone, order blocks and FVGs are all G3, so
  their overlap cannot score twice.
- **MI-115 Premium/discount.** For a bullish leg, every retracement ≥ 0.5 lies in the leg's discount
  half (mirror for bearish). This is a descriptor on the record, not extra evidence.
- **MI-116 Invalidation, freshness and mitigation.** A bullish anchor is invalidated by a close below
  *L* (mirror for bearish). A newly confirmed swing beyond *H* creates a new anchor and expires the
  old one. A zone is `FRESH` until first touched, then `TESTED`, and `MITIGATED` after a close through
  it or after `max_touches` (default 2) touches.
- **MI-117 Extension targets.** Extension levels and opposing liquidity pools (MI-140) are **target
  candidates** only. A target is used only if it satisfies P-27 net of costs, the stops level
  (RISK-032) and the session-close deadline (P-33, RISK-034).
- **MI-118 No inherent edge.** No Fibonacci level is assumed to be profitable. Its weight is a
  research parameter (MI-071), and any strategy that uses it must show its value in the MI-196
  comparison.

## 14. Chart Pattern Intelligence Engine (module 12, group G1)

- **MI-120 Pivot framework.** Every pattern is built only from confirmed swings (MI-030; the pivot `k`
  is a per-pattern parameter). A boundary is the least-squares line through its touching pivots; a
  touch is a pivot within `pat_tol_atr` × ATR of the line (default 0.15). The slope is in ATR per
  bar. Symmetry is the ratio of left to right duration and height. Quality score = touches, symmetry
  and the line-fit residual ÷ ATR (MI-011). `formation_ts` = the confirmation of the last defining
  pivot; `confirmation_ts` = the close of the breakout bar. Every pattern has a minimum and maximum
  formation length in bars of its timeframe (table defaults).
- **MI-121 Pattern rules (research defaults).** "Confirm" always means a **closed bar** beyond the
  boundary by ≥ `break_buffer_atr` × ATR (default 0.1). "Retest" means a return to within tolerance
  of the broken boundary, then a close back on the breakout side within `retest_bars` (default 10).

| Pattern | Geometry | Confirmation | Invalidation | Length (bars) |
|---|---|---|---|---|
| Head and shoulders / inverse | Three swing highs (lows): head beyond both shoulders by ≥ 0.5 ATR, shoulders within tolerance; neckline through the two troughs (peaks) | Close beyond the neckline | Close beyond the right shoulder | 20–150 |
| Double top / bottom | Two swing highs (lows) within tolerance, ≥ 5 bars apart, middle trough (peak) ≥ 1 ATR deep | Close beyond the middle trough (peak) | Close beyond the higher top (lower bottom) | 10–100 |
| Triple top / bottom | Three swing highs (lows) within tolerance; neckline through the two troughs (peaks) | Close beyond the neckline | Close beyond the extreme | 20–150 |
| Rounding top / bottom | ≥ 5 swing highs (lows) whose fitted quadratic curves down (up) with R² ≥ 0.8 and its vertex inside the formation | Close beyond the formation base (rim) | Close beyond the vertex | 30–200 |
| Broadening top / bottom | ≥ 2 higher highs and ≥ 2 lower lows alternating (diverging boundaries), after an advance (decline) | Close beyond the lower (upper) boundary | Close beyond the opposite boundary | 20–150 |
| Bullish / bearish flag | Pole: impulse ≥ 3 ATR within ≤ 15 bars; flag: parallel channel against the pole, retracing ≤ 50% of it | Close beyond the flag boundary in the pole direction | Retracement > 61.8% of the pole | flag 5–30 |
| Bullish / bearish pennant | Pole as for flags; converging boundaries | Close beyond the boundary in the pole direction | Close beyond the opposite boundary | 5–30 |
| Ascending / descending triangle | Flat upper (lower) boundary, \|slope\| ≤ 0.02 ATR/bar; rising lower (falling upper); ≥ 2 touches each | Close beyond the flat boundary | Close beyond the sloped boundary | 15–120 |
| Symmetrical triangle | Falling upper and rising lower boundaries, ≥ 2 touches each, apex ahead | Close beyond either boundary (direction = breakout side) | Price reaches the apex without a breakout | 15–120 |
| Bullish / bearish rectangle | Flat parallel boundaries, ≥ 2 touches each, after an advance (decline) | Close beyond the upper (lower) boundary | Close beyond the opposite boundary | 15–150 |
| Rising / falling / horizontal channel | Two parallel boundaries (slope > 0 / < 0 / flat), ≥ 3 touches in total | Close outside the channel (direction = exit side) | — (a channel is context until it breaks) | 20–200 |
| Cup and handle / inverse | Rounding bottom (top) with rims within tolerance and ≥ 2 ATR deep; handle retraces ≤ 50% of the cup depth | Close beyond the rim | Handle retraces > 50% of the cup | cup 30–200, handle 5–30 |
| Rising / falling wedge | Both boundaries rising (falling) and converging | Close beyond the lower (upper) boundary | Close beyond the opposite boundary | 15–120 |
| Breakout and retest | Close beyond a confirmed pattern or range boundary | Retest as defined above | Close back inside the formation | retest 3–30 |
| Support / resistance break and retest | Level = ≥ 2 confirmed pivots within tolerance (module 12 owns S/R levels) | Close beyond the level, then a retest | Close back beyond the level | retest 3–30 |
| False breakout / failed breakdown | **Owned by module 5** (MI-033 failed breakout); module 12 references it | — | — | — |
| Compression breakout | Compression from module 4 (MI-130) | Close outside the compression range | Close back inside it | compression 10–60 |
| Range expansion | **Owned by module 4** (MI-130); referenced | — | — | — |

- **MI-122 No trade from a shape.** Pattern states: `FORMING` → `CONFIRMED` → `RETESTED`, or
  `INVALIDATED`. Only `CONFIRMED` and `RETESTED` patterns can contribute to a candidate, and only for
  strategies whose pre-registration names them. Every other pattern is detected for display and
  research only, so it adds no trials.
- **MI-123 Historical outcome tracking (research only).** For every confirmed pattern, the research
  store records MFE and MAE in ATR and whether its target candidate was reached before invalidation
  within `outcome_horizon_bars`. These statistics feed research reports. They are never a live
  selection input (RES-060).

## 15. Advanced price action (extends module 4; nothing duplicated)

- **MI-130 Ownership map.** No new module is added. The Candle Behavior Analysis Engine (module 4)
  gains: consecutive directional candles (G4); compression, meaning ATR(5) ÷ ATR(50) ≤
  `comp_ratio` (default 0.6) for ≥ `comp_bars` (default 10) bars (G5); expansion, meaning a bar range
  ≥ `exp_range_atr` × ATR (default 2.0) (G5); failed continuation, meaning a close beyond the prior
  bar's extreme reversed by the next closed bar (G4); and impulse and retracement quality, meaning a
  leg's displacement ratio and its retracement depth and duration in ATR and bars (G6). Already owned
  elsewhere and only referenced: body strength, wick ratios, rejection strength and closing position
  (module 4, MI-020); inside and outside bars (module 3, MI-031); momentum exhaustion and failed
  breakouts (module 5, MI-033); support/resistance levels (module 12, MI-121); and microstructure
  shifts (micro BOS/CHOCH from module 2 on M1/M5).

## 16. Liquidity Intelligence upgrade (module 8, group G2)

- **MI-140 Confirmed sweeps versus wick penetrations.** A **confirmed sweep** needs penetration
  ≥ `sweep_min` × ATR beyond a pool, a close back on the original side within `sweep_close_bars`,
  **and** a post-sweep displacement (MI-030) or a CHOCH in the reversal direction within
  `post_sweep_bars` (default 5). A penetration that misses any of these is a `WICK_PENETRATION`
  descriptor, never evidence. New records: **stop run** (a confirmed sweep with penetration
  ≥ `stoprun_min_atr` × ATR, default 0.3); **failed liquidity grab** (after a sweep, a close beyond
  the swept level again within `fail_bars`, default 3; it invalidates the sweep); **sweep and
  reclaim** (closes hold back inside the swept level for `reclaim_bars`, default 3); **post-sweep
  displacement**; and **liquidity target map** (unswept opposing pools ordered by distance in ATR,
  used as target candidates, MI-117). The existing pools, equal highs/lows, internal/external
  liquidity and inducement rules (MI-030) are unchanged.

## 17. Setups and the high-probability setup view (extends the decision engine)

- **MI-150 One scorer.** A "setup" is the decision engine's candidate (MI-041) plus these fields,
  stored on its decision record: `setup_id`, strategy@version, direction, entry zone, stop-loss
  reference, target candidates, invalidation level, supporting evidence by group, conflicting
  evidence, evidence timestamps, expected execution cost in R (spread + commission + slippage per the
  BT-022/024 models), reward-to-risk net of cost, setup quality score (the MI-042 score) and rejection
  reasons. Nothing is scored a second time.
- **MI-151 Evidence categories map to the existing groups.** Trend (H4/H1 bias, M15 structure, M5
  confirmation, M1 entry): G6 plus MTF derived records (MI-034, MI-190). SMC: G1/G2/G3. Fibonacci: G3.
  Chart patterns: G1. Candles: G4 (displacement stays G1). Market conditions (spread, volatility,
  session, news, tick activity, latency): gates, never score; the regime is G6. RSI, MACD and momentum
  are all G5 and count once (MI-042/043).
- **MI-152 Ranking is not selection.** Setups are ranked for display. A quality score never chooses
  **which strategy** trades: that is a selector (RES-061), allowed only through a PASSed C4 selector
  (MI-052, MI-157). Without one, simultaneous same-direction candidates go to the RiskEngine in a fixed,
  pre-registered strategy priority, bounded by P-05 and P-31. Opposite candidates follow MI-047.
- **MI-153 Every score is explainable.** Each displayed score is broken down by group, evidence ID and
  weight, and the breakdown sums exactly to the score (test).
- **MI-154 Thresholds, not probabilities.** "High quality" means score ≥ a pre-registered threshold
  validated out of sample (MI-071). No 90%/95% win probability is hard-coded or displayed, and
  confidence is never a win probability (MI-011).
- **MI-155 No forced trades.** No input to the decision engine may depend on the time since the last
  trade, trade counts, inactivity or frequency targets (static test). Thresholds never fall because no
  trade has happened.
- **MI-156 Prefer WAIT.** Ties, missing evidence and unresolved contradictions resolve to `WAIT` or
  `NO_TRADE`, never to a candidate.
- **MI-157 Regime eligibility map (research defaults for the C4 selector, MI-052).** TRENDING → Trend
  Following, Trend Pullback. RANGING → a range-validated Reversal version, confirmed Liquidity Sweep.
  VOLATILE → only strategies whose envelope includes it; others are rejected, and no size change
  happens beyond P-36 if the user approved it. REVERSAL (a `REVERSAL_CONFIRMED` record present) →
  Reversal, Early Reversal Scalping. BREAKOUT (compression plus a confirmed boundary break) →
  Breakout/Retest. The selector uses per-strategy, per-version, per-regime records from the registry,
  never recent P/L (RES-060). It activates no unvalidated strategy and never bypasses RISK-061/063.

## 18. Trade authorization lifecycle (a record, not an authority)

- **MI-160 States.** Every setup carries a lifecycle state, recorded as `setup_lifecycle_events`:

| State | Meaning (source) |
|---|---|
| `OBSERVING` | Evidence exists; no setup |
| `DEVELOPING_SETUP` | The decision engine returns `WAIT` (MI-041) |
| `HIGH_QUALITY_SETUP` | Score ≥ threshold, but closed-candle confirmation is still missing |
| `CONFIRMED_SETUP` | `BUY_CANDIDATE` / `SELL_CANDIDATE` on closed-candle evidence (MI-013, MI-041) |
| `RISK_APPROVED` | RiskEngine `evaluate()` approved it (`RiskDecision`) |
| `EXECUTION_AUTHORIZED` | A `RiskApprovedAction` exists and the entry authorization mode permits sending (an approval token, or automatic permission under RISK-061), re-checked at send time (P-29, RISK-004) |
| `REJECTED` | Any gate, the RiskEngine or the user rejected it (with reason codes) |
| `INVALIDATED` | Its invalidation level or expiry was reached first |

  Transitions move forward one state at a time, or from any non-terminal state to `REJECTED` or
  `INVALIDATED`. A property test proves that no sequence skips a state, so `OBSERVING` can never reach
  `EXECUTION_AUTHORIZED` directly. The lifecycle **constructs nothing**: `RiskApprovedAction` stays
  private to the RiskEngine (RISK-001).
- **MI-161 Autonomous entry requirements.** `EXECUTION_AUTHORIZED` in an automatic mode requires all of
  the following, each an existing control: the strategy PASSed and is promoted (RES-060, RISK-061/063);
  data is valid and fresh (MI-015, P-15); confirmation is on closed candles (MI-013); directional
  alignment and independent groups (MI-042); no unresolved contradiction (MI-047, MI-156); spread
  (P-13); news (RISK-018); session (P-19, RISK-017); an objective SL (RISK-030); target and R:R per the
  pre-registration (P-27); feasible size (RISK-013); RiskEngine approval (RISK-001); and still valid at
  send time (P-29).
- **MI-162 AUTO_ALL intent.** The user stated AUTO_ALL as the desired final mode (2026-11-10). This is
  recorded as **intent**, not as an approval of P-37 (RISK-092). AUTO_ALL stays unavailable until
  RISK-061 and RISK-063 are met for every strategy concerned, P-37 is approved, Phase 0 is cleared and
  the release readiness review is GO. RISK-060..067, the demotion triggers, the Guardian and the three
  emergency controls apply unchanged. MCP and the LLM never execute (MCP-010, LLM-001).

## 19. Trailing stop management (pure computation; existing execution path)

- **MI-170 Three methods**, each computing a **candidate** SL:
  - ATR-based: the extreme since entry ∓ `trail_atr_mult` × the current ATR (default 2.0).
  - Structure-based: for a BUY, below the latest confirmed higher low − `trail_buffer_atr` × ATR; for
    a SELL, above the latest confirmed lower high (MI-030 confirmed swings only).
  - R-based milestones: break-even eligibility at +1R (MI-173); protection at +1.5R (SL to
    +`protect_R`, default 0.5R, or a partial exit if pre-registered and feasible, MI-174); progressive
    trailing from +2R; then structure trailing. These are research defaults, not optimums.
- **MI-171 Selection is pre-registered.** A strategy version declares one method or a fixed rule that
  picks among them by regime, volatility, trend strength, structure and available broker distance.
  Every method and every selection rule evaluated counts as a trial (MI-071). There is no runtime
  learning.
- **MI-172 Safety (existing rules, restated as tests).** A candidate is sent only if it is tighter than
  the current broker-confirmed SL (RISK-033) and satisfies the stops and freeze levels (RISK-032). It
  goes through `evaluate_modification()`, `TRADE_ACTION_SLTP` and read-back (RISK-034, EXE-030/031),
  with one in-flight modification per position (`op_id`, EXE-002/013), so duplicates are rejected. A
  modification is sent only if it improves the SL by ≥ `trail_min_step_atr` × ATR (default 0.1), so it
  does not spam the broker. After a partial fill or reconnect, reconciliation (EXE-040, EXE-050) runs
  before the next modification. On failure, the last broker-confirmed SL stays in force and is
  displayed. If it cannot be verified, T25/GRD-020 apply. The SL is never removed, risk is never
  increased, and every modification is audited.
- **MI-173 Net-of-cost break-even.** Break-even = entry ± (round-trip spread at entry + commission per
  unit + expected exit slippage), rounded in the protective direction (RISK-022). It becomes eligible
  only when a **closed bar** of the management timeframe is beyond +`be_trigger_R` (default 1.0) and
  that level satisfies the stops level. A brief touch is not enough.
- **MI-174 Partial exits need volume.** A partial exit is allowed only if it is pre-registered and both
  the closed and the remaining volume are ≥ `volume_min` and multiples of `volume_step`. At the
  minimum lot this is impossible, so the method uses SL protection only and records
  `PARTIAL_INFEASIBLE`.
- **MI-175 Independent backtests.** Each method is backtested on the same signal set. Its contribution
  is reported as the net-expectancy difference against a fixed SL/TP baseline (MI-196).

## 20. Trade management and exit evaluation

- **MI-180 Existing owners.** Position, SL and TP monitoring, reconciliation, session-end exits,
  execution-failure recovery and emergency protection already belong to the position manager,
  reconciler, emergency controller and Guardian (EXECUTION_SAFETY_SPEC, GUARDIAN_SAFETY_SPEC). The new
  part is a pure **exit evaluation layer** that only proposes risk-reducing actions: exits through
  `evaluate_reduction()` and SL tightening through `evaluate_modification()` (RISK-002). It runs in
  every trading state, including ENTRY_STOP and SUSPENDED.
- **MI-181 Exit conditions** (each used only if the strategy version pre-registers it): confirmed
  structure invalidation; opposite MSS/CHOCH; liquidity target reached; Fibonacci extension target
  reached; an opposing OB/FVG reached; momentum exhaustion; volatility expansion; session deadline
  (P-33); the existing SL/TP; and strategy-specific rules.
- **MI-182 Classification.** *Temporary retracement*: no close beyond the trade's invalidation level
  and no opposite CHOCH/MSS on the management timeframe. *Normal volatility*: the excursion stays
  within `noise_atr` × ATR (default 1.0) of the trailing reference. *Genuine invalidation*: a closed bar
  beyond the invalidation level. *Confirmed opposite reversal*: `REVERSAL_CONFIRMED` or a closed-bar
  opposite MSS. *Execution failure*: any EXE §4 failure class, handled by the existing machinery.
- **MI-183 Never one candle.** A single opposite candle never triggers an exit. An evidence-based exit
  needs a confirmed reversal (MI-033), a closed-bar opposite CHOCH/MSS, or a pre-registered rule with
  ≥ 2 groups.
- **MI-184 Exits never weaken protection.** No SL widening, no SL removal, no TP moved past what P-33
  allows (RISK-033/034), no new risk.
- **MI-185 Every exit has a reason.** Exit and trailing decisions are stored as `management_events`
  with a reason code, the decision and evidence IDs, and the old and new SL/TP.

## 21. Timeframes, market conditions and news

- **MI-190 Timeframe roles (defaults).** D1 major context, H4 external structure, H1 directional bias,
  M30 intermediate structure, M15 main setup, M5 confirmation, M1 precision entry. Each strategy uses
  only the timeframes it declares (MI-016). Higher-timeframe evidence referenced by several
  lower-timeframe records counts **once** per decision (MI-034, MI-044).
- **MI-191 Multi-timeframe detections.** Higher-timeframe alignment, lower-timeframe reversal,
  conflicting structure (handled by MI-042/047), Fibonacci overlap (MI-113), SMC overlap (a derived
  record) and entry-timeframe exhaustion (module 5 on the entry timeframe).
- **MI-192 Market-condition gates.** Spread anomaly (P-13 component B); volatility anomaly (ATR(14) ÷
  the median for the same session hour ≥ `vol_anom_ratio`, default 2.5 → `VOLATILITY_ANOMALY`); stale
  ticks (P-15); latency (P-29, EXE-060); and abnormal conditions (a reopen gap ≥ `gap_atr` × ATR,
  default 2.0, or spread and volatility anomalies together → `ABNORMAL_MARKET`). Each gate only blocks.
  News follows RISK-018 and TIME-042/043, and missing or stale calendar data fails closed. No
  evidence is derived from an event's forecast, actual value or assumed direction.

## 22. Dashboard views (built in M9a; read-only)

- **MI-195 Ten views in the Intelligence area** (MI-081): Fibonacci Intelligence; Chart Pattern
  Scanner; High-Probability Setup Scanner; Live Market Regime; Multi-Timeframe Confluence; Trade
  Authorization Explanation (the MI-160 lifecycle with reasons); Trailing SL Monitor; Autonomous
  Position Management; Strategy Performance (registry and forward-test results with tier labels,
  BT-001); and Signal Rejection Analytics. They show: the current setup, BUY/SELL candidate, setup
  quality with its breakdown (MI-153), conflicting evidence, entry zone, SL, TP, current R, trailing
  method, **last broker-confirmed SL**, strategy, risk authorization and rejection reasons. The UI
  truthfulness rules (UI-010..015) and MI-082 apply.

## 23. Evaluation, cent account and phases

- **MI-196 BASELINE versus UPGRADED.** BASELINE = the V2.1 strategy versions; UPGRADED = V2.2 versions
  of the same families. Both are pre-registered and evaluated on the same chronological splits
  (in-sample, validation, untouched holdout, RES-005), with walk-forward, Monte Carlo, parameter
  sensitivity, cost stress, historical news-event replay (RES-071 data), and the future-truncation,
  lookahead and repainting tests (MI-014). Every UPGRADED variant counts as a trial (RES-021). Reported
  (MI-072 plus): net expectancy, profit factor, win rate (reported, not optimised), maximum drawdown,
  recovery factor, average and median R, trade frequency, average holding time, spread, commission
  and slippage costs, missed opportunities, false-positive and false-negative rates (MI-197),
  per-strategy and per-regime results, trailing contribution (MI-175) and the minimum-lot rejection
  rate (A10). The goal is robust out-of-sample net expectancy with controlled drawdown. Nothing is
  optimised on the holdout. "The upgrade adds no edge" is a valid result, and the BASELINE is then
  kept.
- **MI-197 Counterfactual outcome labels (backtest only).** Every candidate and every rejected or `WAIT`
  setup is simulated with its own entry, SL and target under the BT-020..035 rules. False-positive rate
  = traded setups whose net R ≤ 0. False negatives and missed opportunities = rejected or `WAIT`
  setups whose simulated net R > 0. These labels are never used live.
- **MI-198 Cent account.** CENT_ACCOUNT_VALIDATION applies in full: no Standard Cent demo exists
  (A-01); Standard-demo results never validate cent economics (CENT-001..040, BT-010); every symbol and
  account property is discovered live (CENT-002..018); feasibility uses `order_calc_profit` and
  `order_calc_margin` (RISK-011, EXP-001..009); a minimum volume over the budget is rejected
  (RISK-013); lots are never increased and SL or limits never relaxed; an infeasible strategy is
  `CAPITAL-INFEASIBLE` (CENT-031).
- **MI-199 Phases A–J and evidence.** Phase A (architecture review and specification) is this Part II
  plus `quality/V2_2_ARCHITECTURE_REVIEW.md`. Phases B–D are built in M6c, E–H in M6d (pure parts),
  with live wiring in M9a, I in M9a, and J in M6e, M9b, M10 and the 02 reviews. Each phase records in
  `docs/STATUS.md`: the spec IDs, the tests (unit, integration, regression), the review verdict, the
  traceability update, the evidence and a verdict of `PASS`, `FAIL` or `INCONCLUSIVE`. Code that
  exists without passing evidence is not complete (GOV-002), and nothing here enables live automatic
  execution (MI-093, MI-162).

## Appendix A — Source brief (verbatim, as supplied by the user on 2026-11-08)

The text below is the user's original brief, kept unchanged for traceability. Where it and the
requirements above differ, the requirements and §11 apply.

```text
# **GOLDBOT V2.1 — ADVANCED INTELLIGENCE UPGRADE**

Upgrade the existing GoldBot V2.1 into a Multi-Strategy Intelligent XAUUSD Trading System.

IMPORTANT:  
Preserve the existing architecture, RiskEngine authority, independent Guardian, execution safety, audit logging, security controls, and release gates.

Do not bypass or weaken any existing risk controls.

## **1\. Market Intelligence Modules**

Implement independent modules for:

* Trend Intelligence Engine  
* Smart Money Concepts Engine  
* Advanced Candlestick Recognition Engine  
* Candle Behavior Analysis Engine  
* Early Reversal Detection Engine  
* Early Reversal Scalping Engine  
* Live Market Perception Engine  
* Liquidity Intelligence Engine  
* Market Regime Detection Engine  
* Multi-Timeframe Confluence Engine

## **2\. Full SMC Intelligence**

Support:  
BOS, CHOCH, MSS, HH, HL, LH, LL, Order Blocks, Breaker Blocks, Mitigation Blocks, FVG, Inverse FVG, Liquidity Sweeps, Equal Highs, Equal Lows, Buy-side Liquidity, Sell-side Liquidity, Premium/Discount Zones, Inducement, Displacement and Internal/External Liquidity.

Every concept must have an objective detection rule, configurable parameters, timestamps and confidence metrics.

## **3\. Advanced Candlestick Intelligence**

Recognize major bullish, bearish and neutral candlestick patterns.

Include:  
Engulfing, Hammer, Inverted Hammer, Shooting Star, Morning Star, Evening Star, Doji, Pin Bar, Tweezer Top/Bottom, Three White Soldiers, Three Black Crows, Harami, Piercing Line, Dark Cloud Cover, Marubozu, Inside Bar, Outside Bar and Three Inside/Outside patterns.

Do not treat pattern recognition alone as a trading signal.

Evaluate candle location, trend context, liquidity, volatility, wick/body ratio and closing strength.

## **4\. Early Reversal Intelligence**

Detect potential reversals using:

* Liquidity sweeps  
* Failed breakouts  
* Momentum exhaustion  
* RSI/MACD divergence  
* Micro BOS/CHOCH  
* Rejection candles  
* Displacement  
* Volume anomalies

Distinguish early reversal warnings from confirmed reversals.

Use separate confidence scores for early signals and confirmed signals.

## **5\. Early Reversal Scalping**

Develop a separate XAUUSD M1/M5 scalping strategy.

Use M15/H1 as contextual filters.

Support:

* Micro liquidity sweeps  
* Structure shifts  
* FVG retracement  
* Rejection confirmation  
* Dynamic stop-loss  
* Spread-adjusted entries  
* Execution latency controls  
* Time-based exits

Never enter based on a single indicator or candle pattern.

## **6\. Live Market Perception Engine**

Analyze:

* Market regime  
* Trend strength  
* Price velocity  
* Momentum  
* Volatility  
* Tick volume  
* Liquidity behavior  
* Spread conditions  
* Session conditions  
* Economic news  
* False breakouts  
* Market exhaustion

Use actual MT5 market data.

Do not claim access to centralized institutional order flow unless a verified data source provides it.

## **7\. Intelligent Decision Engine**

Create a centralized signal aggregation engine.

Combine independent module outputs using configurable, testable weights.

Support:

* BUY candidate  
* SELL candidate  
* WAIT  
* NO TRADE

Avoid double-counting correlated signals.

All signals must include timestamps, data quality, confidence, invalidation conditions and reasons.

## **8\. Adaptive Strategy Selection**

Select between:

* Trend Following  
* Trend Pullback  
* Reversal  
* Early Reversal Scalping  
* Liquidity Sweep  
* Breakout/Retest

Strategy selection must depend on market regime and validated strategy performance.

## **9\. Safe Aggressive Risk Management**

Preserve RiskEngine as the only authority for order authorization.

Support configurable risk profiles, strict daily and weekly loss limits, maximum exposure, equity drawdown protection, spread limits and margin protection.

Never use martingale, grid recovery, unlimited averaging or loss-based lot escalation.

If minimum tradable lot exceeds the risk budget, reject the trade.

## **10\. Research and Validation**

Every strategy must undergo:

* Historical tick-data backtesting  
* Bid/Ask spread modelling  
* Slippage modelling  
* Commission modelling  
* Out-of-sample validation  
* Walk-forward testing  
* Monte Carlo analysis  
* Parameter sensitivity analysis  
* Demo forward testing

Prevent lookahead bias and data leakage.

Do not optimize solely for win rate.

Evaluate expectancy, profit factor, maximum drawdown, recovery factor, trade frequency and risk-adjusted returns.

## **11\. Explainability and Monitoring**

For every trade, log:

* Selected strategy  
* Market regime  
* Trend direction  
* SMC context  
* Candlestick context  
* Reversal score  
* Entry rationale  
* Stop-loss rationale  
* Take-profit rationale  
* Risk budget  
* Execution result

Provide a real-time dashboard showing system health, active strategies, equity, drawdown, open risk and rejected signals.

## **12\. Implementation Rules**

First inspect the existing GoldBot V2.1 repository and specifications.

Produce an architecture impact report before modifying anything.

Implement modules incrementally.

Add unit tests, integration tests and regression tests.

Do not enable autonomous live trading until all existing and newly introduced release gates pass.

The objective is robust, explainable and risk-controlled XAUUSD trading, not guaranteed profitability or maximum trade frequency.
```
