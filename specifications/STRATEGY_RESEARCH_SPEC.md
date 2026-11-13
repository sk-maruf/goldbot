# STRATEGY_RESEARCH_SPEC — Hypotheses, validation and honest verdicts

> Status: **SPECIFICATION.** Corrects V1 audit item **G**. No threshold in this file "proves" an
> edge. Thresholds are filters that reject most false positives at an affordable cost in false
> negatives. Every threshold below states why it exists and where it fails.

## 1. Workflow

1. **RES-001 Hypothesis:** plain-language economic reason, the market behaviour it exploits, the
   regime where it should work, and how it fails. An LLM may *draft* a hypothesis (LLM-002). Drafting
   is free; every hypothesis **tested** on data counts as a trial (RES-021).
2. **RES-002 Pre-registration:** `research/prereg/<strategy>@<version>.md` is committed to git
   **before** any out-of-sample run. It holds rules, parameter grid, splits, acceptance criteria
   (§5), and the exact metrics to report. The commit hash is recorded.
3. **Development** on the training split only.
4. **Validation** with walk-forward out-of-sample windows (§2).
5. **Holdout** test: one shot, only for candidates that passed step 4.
6. **RES-020 Verdict:** `PASS`, `FAIL`, `INCONCLUSIVE` or `CAPITAL-INFEASIBLE` (CENT-031), with
   a written report.

## 2. Data separation

- **RES-005 Chronological splits.** The oldest data is used for training, then validation folds,
  then a final **holdout** (the most recent ≥ 6 months, or ≥ 20% of the data, whichever is larger).
  The holdout is never used for selection. When it is accessed, the registry records it
  (`holdout_touched=true`, timestamp, git hash). A second access requires a new strategy version
  and a new holdout window.
- **RES-006 Walk-forward.** Rolling windows (default: 12-month train, 3-month test, step 3 months)
  inside the non-holdout period. Parameters are chosen only on each train window.
- **RES-007 Purging and embargo** [S29]. When a trade's holding period or a label's horizon
  overlaps a fold boundary, overlapping training samples are **purged**. An **embargo** equal to
  the maximum holding period (minimum 1 trading day) is dropped after each test fold. Required for
  any ML model or for any strategy whose features use forward-looking labels. For simple rule-based
  strategies, the requirement reduces to "no trade straddles a fold boundary".

## 3. Experiment registry and versioning

- **RES-010 Registry** (SQLite table `experiments` + CLI). One row per run, failures included:
  `run_id`, `strategy`, `version` (semver), `code_hash`, `data_hash`, `config`, `param_set`, `seed`,
  `split`, `tier` (PT0/PT1), metrics, `status` (`completed` / `failed` / `aborted`),
  `holdout_touched`, `notes`. Rows are append-only (hash-chained like the audit log).
- **RES-011 Versioning.** Any change to rules, features, parameter grid or cost model creates a
  new **minor** version. A new idea creates a new strategy. A version that passed the gate is
  frozen. Its code hash must match whatever runs in the engine (startup check).
- **RES-012** Nothing may be deleted from the registry. Abandoned ideas stay visible.

## 4. Sample-size uncertainty (read before §5)

*Plain idea:* a strategy's average result per trade (its **expectancy**, measured in R = units of
the risk taken) is estimated from a limited number of trades. Fewer trades means a wider band of
plausible true values.

*Formula:* the standard error of mean R is `SE = σ_R / √n`, where σ_R is the standard deviation of
per-trade R.

*Worked example (illustrative):* σ_R = 1.1, n = 200 → SE = 1.1 / 14.14 = **0.078R**. The 95%
interval is ± 1.96 × 0.078 = **± 0.15R**.
*Interpretation:* a measured +0.10R after 200 trades is statistically indistinguishable from zero.

*Trades needed* to detect a true +0.10R edge (one-sided α = 5%, power 80%):
`n = ((1.645 + 0.842) × σ_R / μ)² = (2.487 × 1.1 / 0.10)² = (27.36)² ≈ 749 trades`.
*Interpretation:* at ~40 trades per month, that is about 19 months of trading. This is why V2 treats
200 trades as a **minimum for evaluation**, not as proof, and why "INCONCLUSIVE" is a common,
honest verdict.

## 5. Acceptance thresholds — purpose, limits, applicability

All thresholds are fixed in the pre-registration file before out-of-sample data is seen. Defaults
below are PROPOSED for user approval in M0.

| # | Threshold (default) | Plain meaning | Why it exists | Limitations | Appropriate for | Sample-size note |
|---|---|---|---|---|---|---|
| A1 | ≥ 200 trades across walk-forward OOS windows | Enough trades to say anything at all | Below this, almost any result is noise | Doesn't make results significant (§4) | All | 200 trades → ±0.15R band at σ = 1.1 |
| A2 | Net expectancy > 0 **and** lower bound of the one-sided 90% bootstrap CI > 0 (PT1) | The average trade makes money after all costs, with some confidence | Directly targets the objective (net expectancy) | Assumes the future resembles the sample; bootstrap ignores regime change | All | With n = 200 this requires roughly μ > 0.10R |
| A3 | Profit factor after costs ≥ 1.15 | Gross wins ÷ gross losses | Simple; catches strategies living on a few huge wins | Unstable for small samples and fat tails; can look good while expectancy is tiny | Frequent-trading strategies; weak for strategies with < 50 trades/yr | PF CI is wide below ~100 trades |
| A4 | Positive expectancy in ≥ 60% of walk-forward windows | Works in most periods, not just one | Detects strategies whose total comes from one lucky period | Few windows (e.g. 8) make 60% coarse | All | With 8 windows, 5/8 = 62.5% passes |
| A5 | DSR probability ≥ 0.95 [S27] | Probability the Sharpe ratio beats zero after accounting for how many variants were tried, and for skew/fat tails | Corrects the "best of many tries" bias | Needs an honest trial count (RES-021); assumes a known number of independent trials | All | Sensitive to the trial count and to non-normal returns |
| A6 | PBO ≤ 0.20 via CSCV, 16 blocks [S28] | Chance that the in-sample best configuration underperforms the median out of sample | Measures overfitting of parameter selection directly | Needs ≥ 2 evaluated configurations (≥ 10 recommended); undefined when exactly one configuration was ever evaluated | Classes C2–C4 (§5.1) | Fewer blocks → noisier estimate |
| A7 | Monte Carlo 95th-percentile max drawdown ≤ P-04 at planned risk | Bad-luck ordering of the same trades would not hit the drawdown intervention | Survivability, not profit | Reshuffling assumes independent trades; use block bootstrap if autocorrelated | All | Needs ≥ 100 trades to be informative |
| A8 | Each parameter ±20% keeps ≥ 70% of base expectancy | Not balanced on a knife-edge | Fragile optimum = probable overfit | Arbitrary ±20%; coupled parameters need joint perturbation | Every strategy with at least one numeric constant, including "fixed" rules (C1–C4) | — |
| A9 | Expectancy > 0 under "spread × 1.5 + stop slippage × 2" (BT §5) | Edge survives realistic cost shocks | Cent accounts lose thin edges to costs [S32] | Stress size is a judgement | All | — |
| A10 | Capital-feasibility rejection rate ≤ 50% (CENT-030/031: minimum lot, leverage, margin, stop-out distance, aggregate risk and spread rejections all count; user decision 2026-11-13) | Most signals can actually be traded at this capital | Otherwise the live strategy differs from the tested one | Depends on equity path | All on cent | — |

- **RES-021 Multiple testing.** Every configuration evaluated on any out-of-sample window counts
  as a trial. DSR uses the registry's count of trials for that strategy family (correlated variants
  count individually; this is conservative). PBO covers selection within a grid. The holdout
  one-shot rule (RES-005) protects the final estimate.
- **RES-022 No threshold shopping.** Changing a threshold after seeing out-of-sample results
  creates a new pre-registration and a new version, and the earlier result is kept.

### 5.1 Strategy classes and criterion applicability (resolves the PBO / sensitivity contradiction)

V2 said PBO is "meaningless for a single fixed rule" while also requiring A1–A10 for every PASS,
and it scoped parameter sensitivity to "parametric" strategies without defining that term. The
corrected rules:

- **RES-023 Strategy class is decided from the experiment registry, not by the developer.**

| Class | Objective definition (from the registry) | Correct methodology |
|---|---|---|
| C1 Pre-specified rule | Exactly **one** configuration was ever evaluated on any non-training data, and its numeric constants were fixed in the pre-registration before any data was examined | Walk-forward without re-fitting; DSR with trial count = registry count for the whole strategy family (other C1 ideas tested count too); sensitivity (A8) on every numeric constant; PBO is N/A |
| C2 Tuned rule | ≥ 2 configurations evaluated (any grid, any manual retry) | Parameters chosen on each train window only; PBO via CSCV over the full evaluated grid; DSR with the full trial count; A8 around the chosen point |
| C3 ML-assisted / hybrid (not used: D-10, 2026-11-13, rule-based only) | Any fitted model | Purging and embargo (RES-007); nested walk-forward (model selection inside each train window); feature-importance stability across windows; PBO over model and hyperparameter choices; DSR; A8 on hyperparameters; frozen model hash in the strategy version |
| C4 Strategy selector | A rule choosing among strategies (RES-061) | Treated as one strategy: every candidate × selection-rule combination counts as a trial; PBO and DSR over those combinations; walk-forward of the selector, never of its components alone |

- **RES-024 Per-criterion results.** Each criterion A1–A10 is reported as exactly one of:
  `PASS` · `FAIL` · `N/A` · `INCONCLUSIVE`.

| Criterion | C1 | C2 | C3 | C4 |
|---|---|---|---|---|
| A1 trade count | applicable | applicable | applicable | applicable |
| A2 net expectancy + CI | applicable | applicable | applicable | applicable |
| A3 profit factor | applicable | applicable | applicable | applicable |
| A4 walk-forward consistency | applicable | applicable | applicable | applicable |
| A5 DSR | applicable | applicable | applicable | applicable |
| A6 PBO | **N/A** (justification: one evaluated configuration, proven by the registry) | applicable | applicable | applicable |
| A7 Monte Carlo drawdown | applicable | applicable | applicable | applicable |
| A8 sensitivity | applicable if any numeric constant exists; **N/A** only if the rule has no numeric constant at all | applicable | applicable | applicable |
| A9 cost stress | applicable | applicable | applicable | applicable |
| A10 capital feasibility | applicable | applicable | applicable | applicable |

- **RES-025 N/A rules (no bypass).** `N/A` is allowed **only** where the matrix above shows it,
  with a written technical justification **and** registry evidence (e.g. "one configuration;
  registry rows R-…"). If the registry shows a second configuration was ever evaluated, the
  strategy is C2 and A6 becomes applicable retroactively. An applicable criterion marked N/A
  makes the verdict FAIL. The adversarial review (02 prompt) checks every N/A.
- **RES-026 INCONCLUSIVE.** A criterion is `INCONCLUSIVE` when it cannot be judged with the
  available sample (e.g. A1 below 200 trades, the A2 interval straddling zero, or A7 with fewer than
  100 trades). INCONCLUSIVE is never converted to PASS by adding assumptions.
- **RES-027 Out-of-sample limitations.** Out-of-sample success shows that the rule did not fail on
  one more period. It does not prove the future will resemble that period. Regime shifts, changes in
  broker conditions (spreads, margin, sessions) and capital changes (min-lot feasibility) can break
  a validated strategy. That is why RES-040 monitors degradation after deployment.

## 6. Win rate is not an objective

- **RES-050** Win rate is reported, never optimised, and never used as an acceptance criterion. A
  strategy with a win rate > 70% receives a mandatory **tail-risk review**: payoff ratio; largest
  loss in R; behaviour under gaps; dependence on rare large losses. *Reason:* high win rates usually
  mean small targets and wide stops. That profile is fragile to stop slippage, and on this account
  it is most often blocked by the minimum-lot rule (wide stops).

## 7. Regime-specific reporting

- **RES-030** Report performance by regime: volatility tercile (14-day ATR relative to its 1-year
  distribution), trend state (sign of the 20-day return and the ratio |20-day return| / (ATR ×
  √20)), and session (Asia, London, New York). These are **descriptive only**. A regime label can
  drive strategy switching only through a prevalidated selector (RES-061). The Market Regime
  Detection Engine implements exactly these labels (MI-035).
- **RES-031** A strategy whose expectancy is positive in only one regime must state that dependence
  in its verdict, together with A9's stress result.

## 8. Degradation detection and demotion

- **RES-040 Strategy states:** `ACTIVE` → `WATCH` → `PAUSED` (research-only, no signals) →
  `RETIRED`.

| Transition | Trigger (defaults, approved by the user as proposed 2026-11-13, A-47) |
|---|---|
| ACTIVE → WATCH | Rolling 30-trade mean R below the lower edge of the BT §6 band; or a CUSUM alarm on R (reference = backtest mean − 0.5σ, threshold h = 5σ); or an EXE-060 breach |
| WATCH → PAUSED | WATCH persists for 20 more trades; or drawdown attributable to the strategy ≥ 50% of P-04 |
| WATCH → ACTIVE | Rolling mean returns inside the band for 30 trades (user acknowledgement) |
| PAUSED → ACTIVE | Only after re-validation on new data with a new pre-registration (new version) |
| Any → RETIRED | User decision |

- **RES-041** Demotion is automatic. Promotion is never automatic.
- **RES-042** Any strategy state change while an automatic entry mode is active demotes entry
  authorization to human approval (RISK-062). Under `AUTO_APPROVED_STRATEGIES`, the strategy also
  loses its `auto_approved` flag.

## 9. Strategy selection (user decision: switching only through a prevalidated mechanism)

- **RES-060** Only strategies with verdict `PASS` may trade. The system **must not select, switch
  or re-weight strategies because one recently performed better**. Recent outperformance is mostly
  noise (§4).
- **RES-061 Prevalidated selector.** Switching between PASS strategies is allowed **only** through a
  selector that is itself registered and validated as a C4 strategy (§5.1): its inputs are fixed in
  advance (e.g. session, volatility tercile, spread state) and **never** a strategy's own recent P/L
  alone; it has its own pre-registration and version; and it must PASS on its own. Until a selector
  has PASSed, each strategy runs only within its own envelope, with no switching. D-12 (decided
  2026-11-13): the user chose the prevalidated selector; it is built and validated in M6f.

## 10. Strategy operating envelope, news validation and candidates

- **RES-070 Operating envelope.** Every strategy's versioned specification declares: eligible
  sessions; excluded windows; maximum spread (≤ P-13); volatility band; minimum liquidity proxy
  (tick rate per minute); broker-session compatibility (it must close before P-33, because
  overnight holding is prohibited); whether it is news-validated (RES-071); and whether it allows
  price quantization (RISK-025). The RiskEngine enforces the envelope (RISK-017). The intended
  preference is to trade in all eligible sessions, but no strategy trades simply because the market
  is open.
- **RES-071 News validation.** A strategy may trade inside the P-18 blackout only if its
  pre-registration includes a news hypothesis and it passes, on news-window trades alone: A1–A10
  using event data with verified timestamps (TIME-043); a relevance classification (which events
  apply); execution stress with spreads and slippage measured in past news windows (at least
  spread × 3, stop slippage × 3); and a separate verdict. Otherwise it is "not news-validated" and
  RISK-018 applies.
- **RES-072 Intraday only.** Because overnight and weekend holding is prohibited, backtests force a
  close at the P-33 deadline (BT-034), and a strategy whose edge depends on holding past it fails
  A9. Swing styles are therefore incompatible with the current invariants (decision D-07 note).
- **RES-073 Candidate proposals (decided 2026-11-13).** M0 **proposes** 2–3 simple candidates for the
  user to choose from, drawn from the strategy families in `MARKET_INTELLIGENCE_SPEC.md` MI-050
  (e.g. a London or New York session breakout/retest, including opening-range variants; a
  volatility-scaled H1 trend-following rule with a session-end exit; a liquidity-sweep reversal). Each states its
  class, envelope, stop-distance distribution and expected A10 rejection rate **before** testing.
  The choices of style, initial strategy, number of strategies and rule-based vs ML vs hybrid were
  decided by the user on 2026-11-13 (D-07..D-11; D-08: candidate A first, then B, then C; D-10:
  rule-based only). Order-flow strategies are out of scope: retail MT5 tick data has no
  reliable traded volume on CFDs [ASSUMPTION; verify `volume`/`flags` fields in M2].

## 11. Verdict definitions

- **PASS**: every **applicable** criterion (RES-024) is `PASS` on walk-forward; every `N/A` meets
  RES-025; and the holdout result lies within the walk-forward 95% band.
- **FAIL**: any applicable criterion is `FAIL`, or any applicable criterion was marked `N/A`.
- **INCONCLUSIVE**: no FAIL, but at least one applicable criterion is `INCONCLUSIVE`. The system
  stays in research/demo.
- **CAPITAL-INFEASIBLE**: A10 is `FAIL`. Reported separately because it depends on capital, not on
  the market.
- "No candidate passed" is a successful outcome of M6 (RES-020).
