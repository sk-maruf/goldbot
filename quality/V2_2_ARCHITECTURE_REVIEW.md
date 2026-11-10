# V2.2 ARCHITECTURE REVIEW — Phase A of the GoldBot V2.1 → V2.2 upgrade

> Status: **Phase A deliverable (specification only, 2026-11-10).** Source: the user's "MASTER UPGRADE
> COMMAND", kept word for word in Appendix A. The requirements themselves are in
> `specifications/MARKET_INTELLIGENCE_SPEC.md` Part II (MI-100..MI-199). This file holds the six
> Phase A analyses the command asks for. Every change is listed in `quality/V1_V2_CHANGELOG.md` §6.
>
> **Phase A verdict: PASS (specification).** Phases B–J need code, so they are **not done**. They are
> assigned to builder milestone parts (§6), and each records its own PASS / FAIL / INCONCLUSIVE
> evidence in `docs/STATUS.md` (MI-199). When the builder starts M6c, it repeats §1–2 against the
> real repository (MI-090), because this pack contains no code to inspect.

## 0. Where the command was narrowed (the stricter rule wins)

| Command item | What the pack does instead | Why |
|---|---|---|
| Three new "engines": High-Probability Setup, Trade Authorization, Autonomous Trade Management | Extensions of the decision engine (MI-150), a lifecycle **record** (MI-160) and a pure exit-evaluation layer behind the existing position manager (MI-180) | A second scorer or a second authority would double-count evidence (MI-043/044) or create a path to an order outside the RiskEngine (RISK-001, invariant 23) |
| "Select the best strategy", rank setups | Ranking is display-only. Selection happens only through a PASSed C4 selector (MI-152, MI-157) | RES-060/061: no selection on recent P/L, and no unvalidated selector |
| "90%/95% high-probability" language | Pre-registered score thresholds; no win probability anywhere (MI-154) | MI-011: confidence is not a probability |
| "Desired final mode AUTO_ALL" | Recorded as intent; D-01 stays PENDING (MI-162) | RISK-092: only the user's recorded approval sets P-37, and only after RISK-061/063 |
| Partial exits at +1.5R | Only when volume allows; at the minimum lot SL protection is used instead (MI-174) | CENT-010..018, RISK-013: the cent minimum lot cannot be split |
| Fibonacci, chart patterns as signals | Evidence only, from confirmed swings, with no assumed edge (MI-110, MI-118, MI-122) | MI-013/014 no repainting; RES-020 "no edge" is a valid result |
| Phases B–J implemented now | Specified now, built in M6c, M6d, M6e, M9a, M9b and M10 | The pack has no code; code without evidence is not complete (GOV-002) |

## 1. Existing architecture inventory (V2.1)

| Area | Owner (spec) | Already covers |
|---|---|---|
| Risk authority | TRADING_RISK_SPEC (RISK-001..092, P-01..P-37) | Only creator of `RiskApprovedAction`; `evaluate()`, `evaluate_reduction()`, `evaluate_modification()`; tighten-only SL (RISK-033); session deadline (RISK-034); min-lot rejection (RISK-013); three entry modes, promotion gate and demotion (RISK-060..067) |
| Execution | EXECUTION_SAFETY_SPEC (EXE-xxx) | One in-flight operation per `op_id`, timeouts, `TRADE_ACTION_SLTP` with read-back, reconciliation, failure classes, latency metrics |
| Independent safety | GUARDIAN_SAFETY_SPEC (GRD-xxx), EMG-xxx | Missing-stop response, kill switch, flatten, Guardian EA |
| Signal layer | MARKET_INTELLIGENCE_SPEC Part I (MI-001..093) | 10 modules with single concept ownership, Evidence contract, no lookahead/repainting, correlation groups G1–G7, decision engine (BUY/SELL candidate, WAIT, NO_TRADE), six strategy families, explainability |
| Research | STRATEGY_RESEARCH_SPEC (RES-xxx), BACKTESTING_SPEC (BT-xxx) | Pre-registration, trial counting, walk-forward, DSR/PBO, holdout, tiers PT0–PT3, C4 selector |
| Cent economics | CENT_ACCOUNT_VALIDATION (CENT-xxx), EXP-xxx | Live symbol discovery, `order_calc_*`, A10 min-lot rejection rate, CAPITAL-INFEASIBLE |
| Time, news, sessions | TIME_AND_CLOCK_SPEC (TIME-xxx), RISK-017/018 | Sessions, calendar export from the Guardian, fail-closed news window |
| Data, UI, ops | DATA_ARCHITECTURE, UI_DESIGN_BRIEF, OBSERVABILITY_SPEC | `decision_records`, Intelligence screen (MI-081), module health |
| LLM, MCP | LLM-xxx, MCP-xxx | Never on the order path (LLM-001, MCP-010); `.claude/settings.json` denies MT5 order tools |

## 2. Missing functionality inventory

| Command item | V2.1 status | V2.2 requirement |
|---|---|---|
| Fibonacci engine | Missing | MI-110..118 (module 11) |
| Chart pattern engine (33 patterns) | Missing | MI-120..123 (module 12) |
| Advanced price action | Partly in modules 3, 4, 5 | MI-130 (module 4 extension; ownership map) |
| Liquidity upgrade | Pools, sweeps, inducement exist; no stop-run, failed grab, reclaim, post-sweep displacement, target map | MI-140 |
| Setup fields, evidence categories, ranking | Candidate exists; setup fields and categories missing | MI-150..157 |
| Trade authorization states | Approval flow exists; no lifecycle record | MI-160..162 |
| Intelligent trailing, net break-even | Tighten-only SL rule exists; no method | MI-170..175 |
| Trade management, exit evaluation | Position manager exists; no evidence-based exit layer | MI-180..185 |
| Timeframe roles, anomaly gates | MTF alignment (MI-034), spread/staleness gates exist; roles, volatility and abnormal-market gates missing | MI-190..192 |
| Ten dashboard views | One Intelligence screen | MI-195 |
| BASELINE vs UPGRADED evaluation, FP/FN | Research pipeline exists; comparison and labels missing | MI-196, MI-197 |
| Versioning, migration, rollback | Strategy versioning and DATA-020 exist | MI-100, MI-101 |
| Cent-account rules | Complete | MI-198 restates and maps |

## 3. Proposed V2.2 architecture

```
ticks/bars ─► intelligence modules 1–12 (pure; Evidence) ─► decision engine (one scorer; setup fields MI-150)
                    ▲ new: 11 Fibonacci, 12 Chart Pattern;            │ candidate / WAIT / NO_TRADE
                    │ extended: 4 price action, 8 liquidity            ▼
                    │                                   setup lifecycle record (MI-160, records only)
                    │                                                  ▼
                    │                          pre-trade gates (+ MI-192 anomaly gates) ─► RiskEngine
                    │                                                  ▼ RiskApprovedAction (RiskEngine only)
                    │                                 execution (EXE) ─► broker ─► read-back ─► Guardian
open positions ─────┴──► exit evaluation + trailing (pure, MI-170..185) ─► evaluate_reduction() /
                                                                            evaluate_modification()
```

Package placement: modules 11 and 12, the setup fields and the pure lifecycle, trailing and
exit-evaluation functions live in `goldbot.intelligence` (no I/O, MI-001). The position manager
calls the exit-evaluation functions and sends their proposals to the RiskEngine. Persistence adds
`setup_lifecycle_events`, `management_events` and the research-store table `pattern_outcomes`
(DATA_ARCHITECTURE §2).

## 4. Dependency analysis

| New part | Depends on | Blocks |
|---|---|---|
| Module 11 Fibonacci | Confirmed swings and displacement (module 2), ATR (module 4) | Setup fields, targets (MI-117), research |
| Module 12 Chart Pattern | Confirmed swings (module 2), compression (module 4), failed breakouts (module 5) | Setup fields, research |
| Module 4 / 8 extensions | Module 2 swings and displacement | Modules 11, 12, setup fields, exits |
| Setup fields and categories | Decision engine (MI-040..047), modules 1–12 | Lifecycle, dashboard, research |
| Lifecycle record | Setup fields, RiskEngine decisions, entry modes (RISK-060..067) | M9a wiring, dashboard |
| Trailing and exit evaluation | Modules 2, 5, 8, 11; `evaluate_modification()` / `evaluate_reduction()`; EXE read-back | M9a wiring, research comparison |
| MTF roles, anomaly gates | MI-034, P-13, P-15, P-29, TIME-042/043 | Setups |
| BASELINE vs UPGRADED | All of the above; research pipeline (RES, BT) | Promotion gate decisions |
| Ten views | Every record above | Phase I acceptance |

No dependency points from intelligence into the RiskEngine, execution or the Guardian.

## 5. Risk impact assessment

| Risk | Impact | Control |
|---|---|---|
| More parameters and patterns → overfitting, a false edge | HIGH | Every variant is a trial (MI-071, RES-021); only pre-registered patterns trade (MI-122); BASELINE comparison on the untouched holdout (MI-196); new R-33 |
| Repainting from Fibonacci or pattern pivots | HIGH | Confirmed swings only; provisional levels give WAIT (MI-110, MI-120); future-truncation tests (MI-014) |
| Double counting (Fibonacci + OB + FVG, HTF evidence) | HIGH | All G3; derived records count once (MI-113/114, MI-190) |
| A second authority or order path | CRITICAL | Lifecycle constructs nothing; exits and trailing go through `evaluate_*()` (MI-160, MI-180); review check 45 |
| Trailing failure or race | HIGH | One in-flight modification, read-back, minimum step, last confirmed SL shown, GRD-020 (MI-172); new R-34 |
| Forced trading | HIGH | No inactivity inputs (MI-155); prefer WAIT (MI-156) |
| AUTO_ALL read as approved | CRITICAL | Intent only; D-01 PENDING (MI-162); review check 47 |
| Partial exits impossible at minimum lot | MEDIUM | MI-174; A-70 |
| Larger build, later delivery | MEDIUM | Two extra milestone parts (M6c, M6d); the V2.1 baseline stays usable |

No `P-xx` value changes, no safety rule is removed or loosened, and `TRADING_RISK_SPEC.md` is not
edited.

## 6. Implementation sequence (Phases A–J → builder parts)

| Phase | Content | Built in | Evidence |
|---|---|---|---|
| A | Architecture review and specification | This file + MI Part II | PASS (specification) |
| B | Fibonacci engine | M6c | MI-110..118 tests |
| C | Chart pattern engine | M6c | MI-120..123 tests |
| D | Price action and liquidity upgrades | M6c | MI-130, MI-140 tests |
| E | Setup fields, categories, ranking | M6d | MI-150..157 tests |
| F | Lifecycle and authorization record | M6d (pure), M9a (wired) | MI-160..162 tests |
| G | Trailing and exit evaluation | M6d (pure), M9a (wired) | MI-170..185 tests |
| H | MTF roles and market-condition gates | M6d | MI-190..192 tests |
| I | Ten dashboard views | M9a | MI-195 tests |
| J | BASELINE vs UPGRADED, forward test, readiness | M6e, M9b, M10 | MI-196..198 reports |

Milestone parts after this upgrade: M6a, M6b (unchanged), **M6c** V2.2 analysis modules, **M6d** V2.2
setups and management, **M6e** strategy research (was M6c), **M6f** conditional selector (was M6d).

## Appendix A — Source command (verbatim, as supplied by the user on 2026-11-10)

```text
# **MASTER UPGRADE COMMAND**

# **GOLDBOT V2.1 → V2.2**

# **AUTONOMOUS XAUUSD INTELLIGENCE & EXECUTION SYSTEM**

You are upgrading an existing GoldBot V2.1 project.

Your task is to transform the existing architecture into a more advanced, autonomous, evidence-based XAUUSD trading intelligence system.

IMPORTANT: This is an ADDITIVE UPGRADE, not a complete rewrite.

First inspect the entire existing project.

Read all relevant files, including:

* CLAUDE.md  
* README.md  
* MARKET\_INTELLIGENCE\_SPEC.md  
* TRADING\_RISK\_SPEC.md  
* STRATEGY\_RESEARCH\_SPEC.md  
* BACKTESTING\_SPEC.md  
* SYSTEM\_ARCHITECTURE.md  
* EXECUTION\_SAFETY\_SPEC.md  
* GUARDIAN\_SAFETY\_SPEC.md  
* CENT\_ACCOUNT\_VALIDATION.md  
* DATA\_ARCHITECTURE.md  
* API\_SPEC.md  
* MCP\_SECURITY\_SPEC.md  
* REQUIREMENTS\_TRACEABILITY.md  
* All milestone and adversarial review prompts.

Existing architecture contains:

* 10 Market Intelligence modules.  
* 6 strategy families.  
* Evidence Aggregation.  
* Decision Engine.  
* Signal Validator.  
* RiskEngine.  
* Execution Engine.  
* Guardian EA.  
* Backtesting.  
* Adaptive Strategy Selection.  
* Dashboard.  
* MT5 integration.  
* SQLite and Parquet data architecture.

Preserve all existing functionality.

Do not delete existing requirements.

Do not weaken any existing safety restrictions.

Do not independently change P-01 through P-37 or any other approved risk parameter.

Do not allow AI, LLM, MCP, strategies or intelligence modules to modify risk limits.

Create a versioned V2.2 upgrade with migration and rollback support.

Before implementation, produce:

1. Existing architecture inventory.  
2. Missing functionality inventory.  
3. Proposed V2.2 architecture.  
4. Dependency analysis.  
5. Risk impact assessment.  
6. Implementation sequence.

Then implement incrementally.

Create:

FIBONACCI\_INTELLIGENCE\_ENGINE

Implement automatic Fibonacci calculations using objectively confirmed impulse swings.

RETRACEMENT LEVELS:

0.236  
0.382  
0.500  
0.618  
0.650  
0.705  
0.786  
0.886

PRIMARY GOLDEN ZONE:

0.618–0.705

OTE ZONE:

0.618–0.786

REFERENCE LEVEL:

0.705

EXTENSION LEVELS:

1.000  
1.272  
1.414  
1.618  
2.000  
2.618

Features:

* Automatic swing high/low detection.  
* Confirmed impulse leg identification.  
* Bullish Fibonacci.  
* Bearish Fibonacci.  
* Multi-timeframe Fibonacci.  
* Fibonacci cluster detection.  
* Golden Zone overlap detection.  
* OTE overlap detection.  
* Fibonacci \+ Order Block confluence.  
* Fibonacci \+ FVG confluence.  
* Fibonacci \+ Liquidity Sweep confluence.  
* Fibonacci \+ CHOCH/MSS confluence.  
* Premium/Discount integration.  
* Fibonacci invalidation.  
* Zone freshness and mitigation.  
* Extension-based target candidates.

Use ATR-normalized proximity instead of fixed universal price distances.

Never assume that a Fibonacci level is inherently profitable.

Prevent repainting and historical lookahead.

Only confirmed swings can authorize confirmed signals.

Create:

CHART\_PATTERN\_INTELLIGENCE\_ENGINE

Detect classical price-chart patterns objectively.

A. REVERSAL PATTERNS

* Head and Shoulders.  
* Inverse Head and Shoulders.  
* Double Top.  
* Double Bottom.  
* Triple Top.  
* Triple Bottom.  
* Rounding Top.  
* Rounding Bottom.  
* Broadening Top.  
* Broadening Bottom.

B. CONTINUATION PATTERNS

* Bullish Flag.  
* Bearish Flag.  
* Bullish Pennant.  
* Bearish Pennant.  
* Ascending Triangle.  
* Descending Triangle.  
* Symmetrical Triangle.  
* Bullish Rectangle.  
* Bearish Rectangle.  
* Rising Channel.  
* Falling Channel.  
* Horizontal Channel.  
* Cup and Handle.  
* Inverse Cup and Handle.

C. WEDGE PATTERNS

* Rising Wedge.  
* Falling Wedge.

D. BREAKOUT PATTERNS

* Breakout and Retest.  
* Support Break and Retest.  
* Resistance Break and Retest.  
* False Breakout.  
* Failed Breakdown.  
* Compression Breakout.  
* Range Expansion.

For every pattern implement:

* Geometric detection rules.  
* Minimum formation length.  
* Maximum formation length.  
* Pivot validation.  
* Boundary slope calculation.  
* Pattern symmetry.  
* Breakout confirmation.  
* Retest confirmation.  
* Invalidation.  
* ATR-normalized tolerance.  
* Pattern quality score.  
* Formation timestamp.  
* Confirmation timestamp.  
* Historical outcome tracking.

IMPORTANT:

A pattern must not generate a trade merely because its shape appears.

Require a closed-candle breakout or other objectively defined confirmation.

Do not use future candles to identify historical patterns.

Create:

ADVANCED\_PRICE\_ACTION\_ENGINE

Analyse:

* Candle body strength.  
* Upper and lower wick ratios.  
* Rejection strength.  
* Closing position.  
* Momentum expansion.  
* Momentum exhaustion.  
* Consecutive directional candles.  
* Inside bar.  
* Outside bar.  
* Compression.  
* Expansion.  
* Failed continuation.  
* Failed breakout.  
* Impulse and retracement quality.  
* Support/resistance reaction.  
* Microstructure shifts.

Integrate with the existing candlestick and candle behaviour engines.

Do not duplicate existing calculations.

Upgrade the existing Liquidity Intelligence Engine.

Detect:

* Buy-side liquidity.  
* Sell-side liquidity.  
* Equal highs.  
* Equal lows.  
* Internal liquidity.  
* External liquidity.  
* Liquidity pools.  
* Liquidity sweeps.  
* Stop-run behaviour.  
* Inducement.  
* Failed liquidity grabs.  
* Sweep and reclaim.  
* Post-sweep displacement.  
* Liquidity target mapping.

Distinguish genuine confirmed sweeps from ordinary wick penetrations.

Create:

HIGH\_PROBABILITY\_SETUP\_ENGINE

Its responsibility is to identify, rank and explain the best available trade opportunities.

It must evaluate the existing strategies:

1. Trend Following.  
2. Trend Pullback.  
3. Reversal.  
4. Early Reversal Scalping.  
5. Liquidity Sweep.  
6. Breakout and Retest.

For each candidate, evaluate:

A. TREND EVIDENCE

* H4 directional bias.  
* H1 directional bias.  
* M15 structure.  
* M5 confirmation.  
* M1 entry conditions.

B. SMC EVIDENCE

* BOS.  
* CHOCH.  
* MSS.  
* Order Block.  
* FVG.  
* Liquidity Sweep.  
* Displacement.  
* Premium/Discount.

C. FIBONACCI EVIDENCE

* Golden Zone.  
* OTE.  
* Fibonacci cluster.  
* Extension target.  
* Confirmed impulse quality.

D. CHART PATTERN EVIDENCE

* Pattern identity.  
* Pattern maturity.  
* Breakout confirmation.  
* Retest quality.  
* Invalidation distance.

E. CANDLE EVIDENCE

* Engulfing.  
* Pin Bar.  
* Rejection.  
* Momentum.  
* Displacement.  
* Closing strength.

F. MARKET CONDITION EVIDENCE

* Spread.  
* Volatility.  
* Session.  
* News.  
* Tick activity.  
* Execution latency.  
* Market regime.

Every setup must have:

* Unique setup ID.  
* Strategy ID.  
* Direction.  
* Entry zone.  
* Stop-loss reference.  
* Target candidates.  
* Invalidation level.  
* Supporting evidence.  
* Conflicting evidence.  
* Evidence timestamps.  
* Expected execution cost.  
* Reward-to-risk.  
* Setup quality score.  
* Rejection reasons.

Do not treat correlated indicators as independent confirmation.

For example, RSI, MACD and momentum measurements may represent related evidence.

Use correlation groups to avoid artificial score inflation.

Create a deterministic:

TRADE\_AUTHORIZATION\_ENGINE

The system must distinguish:

1. OBSERVING  
2. DEVELOPING\_SETUP  
3. HIGH\_QUALITY\_SETUP  
4. CONFIRMED\_SETUP  
5. RISK\_APPROVED  
6. EXECUTION\_AUTHORIZED  
7. REJECTED  
8. INVALIDATED

A setup must never jump directly from OBSERVING to EXECUTION\_AUTHORIZED.

AUTONOMOUS ENTRY REQUIREMENTS:

* Strategy is individually validated.  
* Market data is valid and fresh.  
* Setup is confirmed using closed-candle evidence.  
* Directional evidence is sufficiently aligned.  
* Required independent evidence groups are satisfied.  
* No unresolved critical contradiction exists.  
* Spread is within approved limits.  
* News restrictions are satisfied.  
* Session restrictions are satisfied.  
* SL is objectively defined.  
* Target and reward-to-risk satisfy the strategy's pre-registered rules.  
* Position size is feasible within the existing risk budget.  
* RiskEngine approves.  
* Signal remains valid at execution time.

The bot should prefer WAIT or NO\_TRADE over a weak opportunity.

Create configurable quality thresholds, validated through historical out-of-sample testing.

Do not hardcode an arbitrary 90% or 95% winning probability.

Confidence is not a guaranteed win probability.

Never trade simply to increase trade frequency.

Never force a trade because the account has been inactive.

Upgrade the existing strategy selector.

Allow the system to identify the current market regime and choose among individually validated strategies.

Examples:

TRENDING MARKET:

* Trend Following.  
* Trend Pullback.

RANGING MARKET:

* Validated range reversal.  
* Confirmed liquidity sweep.

VOLATILE MARKET:

* Reduce exposure through existing risk rules.  
* Reject unsuitable setups.

REVERSAL CONDITIONS:

* Reversal Strategy.  
* Early Reversal Scalping after confirmation.

BREAKOUT CONDITIONS:

* Breakout and Retest.

Requirements:

* Strategy-specific performance records.  
* Strategy version control.  
* Regime-specific validation.  
* No unvalidated strategy activation.  
* No switching based solely on recent losses or profits.  
* No strategy switching that bypasses existing promotion rules.

Create:

INTELLIGENT\_TRAILING\_STOP\_ENGINE

Support three independently testable trailing methods.

A. ATR-BASED TRAILING

Use configurable ATR multipliers.

The distance must adapt to current volatility.

B. STRUCTURE-BASED TRAILING

For BUY:

* Trail below confirmed higher lows.  
* Use validated bullish structure.  
* Respect broker stop and freeze levels.

For SELL:

* Trail above confirmed lower highs.  
* Use validated bearish structure.  
* Respect broker stop and freeze levels.

C. R-BASED TRAILING

Track trade progress in initial risk units.

Allow configurable milestones such as:

* Break-even eligibility at \+1R.  
* Partial protection at \+1.5R.  
* Progressive trailing at \+2R.  
* Further trailing based on confirmed structure.

These are research defaults, not universal optimums.

D. INTELLIGENT TRAILING SELECTION

Select a prevalidated trailing method based on:

* Market regime.  
* Strategy.  
* Volatility.  
* Trend strength.  
* Structure.  
* Available broker distance.

MANDATORY SAFETY RULES:

* Never widen an existing stop loss.  
* Never remove a protective stop.  
* Never increase initial risk.  
* Never modify SL without checking broker constraints.  
* Verify broker confirmation after every modification.  
* Reconcile actual broker SL with internal SL state.  
* Reject duplicate modifications.  
* Preserve an audit record.  
* Handle partial fills and reconnects.  
* Respect freeze level and stops level.  
* If trailing fails, retain the last broker-confirmed protective SL.  
* If the broker-confirmed SL cannot be verified, invoke the existing safety intervention.

Never move SL to breakeven merely because price briefly touches \+1R if transaction costs mean the trade would still close at a net loss.

Do not use aggressive trailing that unnecessarily closes valid trades.

Backtest each trailing method independently and compare net expectancy.

Create:

AUTONOMOUS\_TRADE\_MANAGEMENT\_ENGINE

The bot must independently manage authorized open positions.

Responsibilities:

* Position monitoring.  
* SL monitoring.  
* TP monitoring.  
* Trailing SL updates.  
* Structure-based exit.  
* Reversal warning.  
* Confirmed opposite structure.  
* Partial exit if pre-registered.  
* Time-based exit.  
* Session-based exit.  
* Execution failure recovery.  
* Position reconciliation.  
* Emergency protection.

The engine must distinguish:

* Temporary retracement.  
* Normal volatility.  
* Genuine structure invalidation.  
* Confirmed opposite reversal.  
* Execution failure.

Do not close a position merely because one opposite candle appears.

Every exit must have a recorded reason.

Open positions must continue to receive risk management even when new entries are disabled.

Support:

D1: Major market context.  
H4: External structure.  
H1: Directional bias.  
M30: Intermediate structure.  
M15: Main setup.  
M5: Confirmation.  
M1: Precision entry.

Use only the timeframes required by each validated strategy.

Detect:

* Higher-timeframe trend alignment.  
* Lower-timeframe reversal.  
* Conflicting structure.  
* Multi-timeframe Fibonacci overlap.  
* Multi-timeframe SMC overlap.  
* Entry timeframe exhaustion.

Higher timeframe evidence must not be counted repeatedly as independent evidence.

Implement:

* Economic calendar integration.  
* High-impact news classification.  
* News data freshness.  
* Configurable blackout periods.  
* Session detection.  
* Spread anomaly detection.  
* Volatility anomaly detection.  
* Stale tick detection.  
* Execution latency monitoring.  
* Abnormal market condition detection.

If required news data is unavailable or stale, apply the existing fail-closed rules.

Do not assume a news event's market direction.

Develop an exit evaluation layer that considers:

* Confirmed structure invalidation.  
* Opposite MSS/CHOCH.  
* Liquidity target reached.  
* Fibonacci extension target reached.  
* Opposing OB/FVG.  
* Momentum exhaustion.  
* Volatility expansion.  
* Session deadline.  
* Existing SL/TP.  
* Strategy-specific exit rules.

Never allow exit intelligence to weaken existing RiskEngine protection.

Never widen SL to avoid a losing trade.

Add the following screens:

1. Fibonacci Intelligence.  
2. Chart Pattern Scanner.  
3. High-Probability Setup Scanner.  
4. Live Market Regime.  
5. Multi-Timeframe Confluence.  
6. Trade Authorization Explanation.  
7. Trailing SL Monitor.  
8. Autonomous Position Management.  
9. Strategy Performance.  
10. Signal Rejection Analytics.

Display:

* Current setup.  
* BUY/SELL candidate.  
* Setup quality.  
* Evidence breakdown.  
* Conflicting evidence.  
* Entry zone.  
* SL.  
* TP.  
* Current R.  
* Trailing method.  
* Last broker-confirmed SL.  
* Strategy.  
* Risk authorization.  
* Rejection reasons.

Every displayed score must be explainable.

The desired final operating mode is:

AUTO\_ALL

The bot should discover setups, validate them, request RiskEngine authorization and automatically execute eligible trades without requiring manual confirmation for each individual entry.

However:

* Preserve existing RISK-060 through RISK-067.  
* Preserve P-37 user approval requirements.  
* Preserve the eight-week demo promotion gate where applicable.  
* Preserve automatic demotion triggers.  
* Preserve the independent Guardian EA.  
* Preserve emergency stop entries.  
* Preserve cancel pending orders.  
* Preserve emergency liquidation.  
* MCP and LLM must never directly execute trades.  
* No AI-generated order can bypass RiskEngine.

AUTO\_ALL must remain unavailable until all existing promotion conditions are satisfied.

For an Exness Standard Cent account, explicitly respect CENT\_ACCOUNT\_VALIDATION.md.

Do not assume a Standard Cent demo account exists.

Do not claim Standard demo testing validates Cent execution economics.

Every new engine must have isolated tests.

Compare:

BASELINE:  
Existing V2.1 strategies without the new modules.

UPGRADED:  
V2.2 with Fibonacci, chart patterns and new intelligence.

Evaluate:

* Net expectancy.  
* Profit factor.  
* Win rate.  
* Maximum drawdown.  
* Recovery factor.  
* Average R.  
* Median R.  
* Trade frequency.  
* Average holding time.  
* Spread costs.  
* Commission.  
* Slippage.  
* Missed opportunities.  
* False positive rate.  
* False negative rate.  
* Strategy-specific performance.  
* Regime-specific performance.  
* Trailing SL contribution.  
* Minimum lot rejection rate.

Use chronological datasets.

Implement:

* In-sample.  
* Validation.  
* Untouched holdout.  
* Walk-forward testing.  
* Monte Carlo analysis.  
* Parameter sensitivity.  
* Cost stress testing.  
* Historical event replay.  
* Future-truncation tests.  
* Lookahead-bias tests.  
* Repainting tests.

Optimize for robust out-of-sample net expectancy and controlled drawdown, not maximum historical profit.

Do not optimize parameters on the final holdout dataset.

The target deployment is an Exness MT5 Standard Cent account.

Discover the actual account and symbol properties.

Never assume:

* Symbol name.  
* Contract size.  
* Minimum volume.  
* Volume step.  
* Tick value.  
* Tick size.  
* Commission.  
* Spread.  
* Stops level.  
* Freeze level.  
* Margin requirement.  
* USC conversion.

Use actual MT5 account and symbol data.

Use order\_calc\_profit and order\_calc\_margin for feasibility calculations.

Reject any trade whose minimum executable volume exceeds the approved risk budget.

Never increase lot size to compensate for a small account.

Do not relax SL or risk limits to make trades feasible.

If the account cannot safely execute a strategy at minimum volume, report CAPITAL-INFEASIBLE.

Implement in phases:

PHASE A:  
Architecture review and specification changes.

PHASE B:  
Fibonacci Engine.

PHASE C:  
Chart Pattern Engine.

PHASE D:  
Advanced Price Action and Liquidity upgrades.

PHASE E:  
High-Probability Setup Engine.

PHASE F:  
Trade Authorization Engine.

PHASE G:  
Trailing SL Engine.

PHASE H:  
Autonomous Trade Management.

PHASE I:  
Dashboard integration.

PHASE J:  
Backtesting, adversarial review and release validation.

For each phase:

1. Write the specification.  
2. Implement source code.  
3. Write unit tests.  
4. Run integration tests.  
5. Run regression tests.  
6. Run adversarial review.  
7. Update requirements traceability.  
8. Produce evidence.  
9. Mark PASS, FAIL or INCONCLUSIVE.

Do not mark a feature complete merely because its code exists.

Do not claim profitability without out-of-sample and forward-test evidence.

Do not enable live automatic execution simply because the upgrade compiles.

FINAL OBJECTIVE:

Build an autonomous XAUUSD trading system that:

* Understands market structure.  
* Recognizes chart patterns.  
* Uses Fibonacci intelligently.  
* Detects liquidity events.  
* Identifies high-quality setups.  
* Rejects weak and conflicting signals.  
* Selects validated strategies.  
* Calculates risk safely.  
* Executes only authorized trades.  
* Manages positions independently.  
* Uses intelligent trailing SL.  
* Protects account equity.  
* Explains every trading decision.  
* Knows when NOT to trade.

The highest priority is long-term survival, robust positive expectancy and controlled drawdown.

NO PROFIT GUARANTEE.  
NO FORCED TRADES.  
NO UNVERIFIED CLAIMS.  
NO RISK BYPASS.

Begin by auditing the existing project. Do not start by rewriting everything.
```
