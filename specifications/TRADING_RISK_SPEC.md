# TRADING_RISK_SPEC — RiskEngine, sizing, exposure, interventions, autonomy

> Status: **SPECIFICATION** (final V2 correction, 2026-11-08). This file is the **single source of
> truth for every risk number**
> (§2). Other files refer to parameters by ID (`P-xx`) and must not restate different values.
> Any change to a `P-xx` default requires the user's explicit approval and an entry in
> `quality/V1_V2_CHANGELOG.md`.

## 1. Authority and scope

- **RISK-001 Single authority.** `RiskEngine` is the only component that can produce a
  `RiskApprovedAction`. The execution layer accepts no other type for **entries, volume
  increases, SL moves away from price, TP changes that extend exposure time, or any pending
  order placement**. This is enforced in the type system: the constructor is private to
  `core/risk_engine.py`, and a test confirms that no other module can create the object.
- **RISK-002 Action classes.**
  - *Risk-increasing*: open position, add volume, place pending order, widen SL. These need a full `evaluate()`.
  - *Risk-reducing*: close or partial-close, tighten SL toward price, cancel pending order.
    These need `evaluate_reduction()`, which only checks that the action does reduce risk and
    is well-formed. They are permitted in every trading state, including SUSPENDED.
  - *Position-management modification*: TP changes and strategy-defined SL tightening. These need
    `evaluate_modification()`, which checks strategy rules, OFF_TICK (RISK-022), stops/freeze
    levels and compatibility with the session-close deadline (P-33), and records old and new values
    (RISK-034). Widening an SL is risk-increasing **and prohibited** (§10).
  - Unknown action types are rejected.
- **RISK-003 Determinism.** `evaluate()` is a pure function of `(proposal, account_snapshot,
  symbol_spec, market_snapshot, limits, limit_state, trading_state, clock_snapshot)`. It reads
  no clock and no global state. The same inputs always give the same `RiskDecision`.
- **RISK-004 Re-evaluation.** Whenever an entry needs human approval (§9), the RiskEngine runs
  again at approval time with fresh snapshots. An approval never carries a stale decision forward.

## 2. Parameter register

**Parameter status values:** `USER_DECISION_REQUIRED` (the user must choose; a recommended range
is shown, never an approved value) · `PROPOSED` (engineering default; approved or changed by the
user in M0) · `BROKER_VERIFICATION_REQUIRED` (set from live measurements).
**Fixture values** exist only so that tests and BACKTEST/REPLAY runs can execute. They are **not
approved settings** (RISK-005).

The "UI may" column is the only runtime direction allowed. **Loosening** any parameter
requires editing `config/risk_limits.yaml`, restarting, and a logged confirmation (RISK-090).

| ID | Parameter | Status | Recommended range / default | Fixture (tests only) | Unit / basis | UI may | Rationale |
|---|---|---|---|---|---|---|---|
| P-01 | `risk_per_trade` | USER_DECISION_REQUIRED | 0.10–0.50 (V1 proposal 0.25) | 0.25 | % of current equity | tighten | Higher values reach the drawdown intervention after fewer losses; lower values make more trades capital-infeasible (CENT-030). |
| P-02 | `daily_loss_intervention` | USER_DECISION_REQUIRED | 0.5–2.0 (V1 proposal 1.00) | 1.00 | % of equity at day start (00:00 UTC) | tighten | Intervention threshold, not a guarantee (RISK-040). |
| P-03 | `weekly_loss_intervention` | USER_DECISION_REQUIRED | 1.0–4.0 (V1 proposal 2.00) | 2.00 | % of equity at week start (Mon 00:00 UTC) | tighten | Part of the financial-risk set awaiting approval. |
| P-04 | `max_drawdown_intervention` | USER_DECISION_REQUIRED | 3–10 (V1 proposal 5.00) | 5.00 | % below equity high-water mark | tighten | A trigger, not a cap. |
| P-05 | `max_open_positions` | USER_DECISION_REQUIRED | Set per strategy, bounded by P-31; no fixed number is imposed | 1 | count | tighten | The user decided that the count follows the strategy and aggregate risk (decision D-04). |
| P-06 | `max_pending_orders` | PROPOSED | 0 until a strategy specification requires pending orders | 0 | count | tighten | Keeps the order lifecycle simple. Raising it needs a strategy spec + user approval. |
| P-07 | `consecutive_losses_entry_stop` | USER_DECISION_REQUIRED | 2–5 (V1 proposal 3) | 3 | closed trades with net P/L < 0 | tighten | Counting rule: net < 0 increments, net > 0 resets, net = 0 no change. |
| P-08 | `consecutive_losses_suspend` | USER_DECISION_REQUIRED | P-07 + 1 … P-07 + 3 (V2 proposal 5) | 5 | as above | tighten | Escalation to SUSPENDED. |
| P-09 | `max_effective_leverage` | PROPOSED | 1.0 | 1.0 | aggregate notional ÷ equity (×) | tighten | EXP-003. |
| P-10 | `max_margin_utilisation` | PROPOSED | 10 | 10 | projected used margin ÷ equity, % | tighten | EXP-004. |
| P-11 | `min_projected_margin_level` | PROPOSED | 1000 | 1000 | equity ÷ projected used margin × 100, % | tighten | EXP-005. Keeps far from broker stop-out. |
| P-12 | `account_leverage_cap` | PROPOSED | 200 | 200 | `account_info().leverage` (1:N) | tighten | An **additional** constraint only (EXP-007). |
| P-13 | `max_spread` | PROPOSED (A: BROKER_VERIFICATION_REQUIRED) | min(A, B, C): A = absolute cap from live spread data; B = 2.0 × rolling 20-day median spread for the same session hour; C = 10% of SL distance. A strategy may set stricter values (RISK-017) | B and C only | price | tighten | Relative to observed conditions. |
| P-14 | `max_entry_deviation` | BROKER_VERIFICATION_REQUIRED | Set in M7 from demo slippage data | — | points (order `deviation`) | tighten | Never guessed. |
| P-15 | `tick_staleness_limit` | PROPOSED | 10 | 10 | seconds since last *locally received* tick change, during an open session | tighten | TIME-020. |
| P-16 | `clock_offset_limits` | PROPOSED | warn 500 / entry-stop 1000 | same | ms, local UTC vs NTP | tighten | TIME-010. |
| P-17 | `server_offset_tolerance` | PROPOSED | 5 | 5 | seconds between consecutive server-offset estimates | tighten | TIME-030. |
| P-18 | `news_blackout` | PROPOSED | −30 min / +15 min around high-impact USD events; applies to every strategy **not** validated for news (RISK-018) | same | minutes | widen only | Exness caps leverage on new gold positions during news [VERIFIED S2]; window conservative [ASSUMPTION]. |
| P-19 | `pre_close_entry_restriction` | PROPOSED | No new entries within 60 min before the daily break or any session end; 120 min before the last session of the week or a known early close; none in the first 30 min after an open | same | minutes | widen only | Supports the no-overnight rule (EXE-080). Session times from the live export [VERIFIED S2 as cross-check]. |
| P-20 | `engine_heartbeat_interval` | PROPOSED | 2 | 2 | s (engine → Guardian file) | — | GRD-010. |
| P-21 | `guardian_staleness` | PROPOSED | engine considers the Guardian stale after 20 s; the Guardian considers the engine stale after 15 s | same | s | tighten | GRD-011/012. |
| P-22 | `missing_stop_response` | PROPOSED | engine must confirm SL within 3 s of fill; Guardian acts at 10 s | same | s | tighten | GRD-020. |
| P-23 | `approval_expiry` | PROPOSED | 60 s or price drift > `max(3 × spread, 0.05 × SL distance)` | same | s / price | tighten | Used only when an entry needs human approval. |
| P-24 | `reconciliation` | PROPOSED | every 5 s; unexplained mismatch → ENTRY_STOP; unresolved > 60 s → SUSPENDED | same | s | tighten | T7/T8. |
| P-25 | `emergency_operation_timing` | PROPOSED | per-attempt timeout **5 s**; retry back-off **1, 2, 4, 8 s**; max **5** attempts; **global deadline 60 s** per emergency run. Worst case 5 × 5 + (1 + 2 + 4 + 8) = 40 s ≤ 60 s. No attempt starts if the remaining deadline < per-attempt timeout | same | s | tighten | EMG-020. |
| P-26 | `stop_slippage_allowance` | PROPOSED | 1.0 × P-13 component B median spread, added to modelled loss at SL | same | account currency | tighten | RISK-012. |
| P-27 | `min_reward_risk` | PROPOSED | 1.0; strategies may require more | 1.0 | TP distance ÷ SL distance (net of round-trip spread) | tighten | — |
| P-28 | `llm_monthly_spend_cap` | USER_DECISION_REQUIRED | 0 = LLM disabled | 0 | USD | tighten | LLM-004. |
| P-29 | `max_signal_age` | PROPOSED | 2 | 2 | s between signal creation and RiskEngine evaluation | tighten | Prevents trading on stale signals. |
| P-30 | `foreign_activity_policy` | PROPOSED | ENTRY_STOP and alert; foreign positions are closed only if the user ticks "include foreign positions" in Emergency Liquidation | same | — | — | EXP-009, EMG-030. |
| P-31 | `max_aggregate_open_risk` | USER_DECISION_REQUIRED | ≤ 2 × P-01 recommended while positions are correlated (one symbol) | 0.25 | % of equity, sum of modelled loss-to-SL over open positions + proposed | tighten | RISK-015. |
| P-32 | `strategy_risk_budget` | USER_DECISION_REQUIRED | Per strategy, ≤ P-01 | = P-01 | % of equity per trade | tighten | RISK-016. |
| P-33 | `session_close_deadline` | PROPOSED | All positions confirmed closed **30 min** before the daily break or any session end; **60 min** before the last session of the week or a known early close. Each deadline must leave ≥ 3 × the P-25 global deadline before the session end | same | minutes | widen only | EXE-080..086. |
| P-34 | `auto_recovery` | PROPOSED | Cooldown per trigger class in §7 (default 5 min); health checks must pass continuously for the cooldown; ≤ 3 automatic resumptions per trigger per UTC day, then MANUAL | same | min / count | tighten | RISK-052. |
| P-35 | `daily_profit_target_behaviour` | USER_DECISION_REQUIRED | Options: none / stop entries after target / reduce risk after target. **No behaviour exists until decided** | none | % of equity | — | Decision D-05. |
| P-36 | `consecutive_loss_risk_reduction` | USER_DECISION_REQUIRED | Options: none / multiply P-01 by a factor < 1 after N losses until a win. **Never an increase** | none | factor | tighten | Decision D-06. |
| P-37 | `entry_authorization_mode` | USER_DECISION_REQUIRED | `MANUAL_APPROVAL` / `AUTO_ALL` / `AUTO_APPROVED_STRATEGIES` (§9) | MANUAL_APPROVAL | enum | — | Decision D-01. No default for LIVE or non-fixture DEMO (RISK-065); fixture demo sets the mode per run (RISK-066). |

- **RISK-005 Pending-parameter gate.** The engine refuses to start in `LIVE`, and in `DEMO` outside
  fixture demo (RISK-066), while any `USER_DECISION_REQUIRED` parameter lacks
  `approved_by_user: true` and an approval date in `config/risk_limits.yaml`. BACKTEST and REPLAY
  runs may use fixture values, but every report then carries the banner "FIXTURE PARAMETERS — NOT
  APPROVED SETTINGS".
- **RISK-066 Fixture demo.** A `DEMO` run may use the fixture values of unapproved parameters,
  including P-37, only while all of these hold. They are checked at start and after every
  reconnect:
  1. MT5 reports a demo account: `account_info().trade_mode == ACCOUNT_TRADE_MODE_DEMO`, read live
     (A-64). Configuration or a user statement never counts (as in CENT-002). Any other value →
     refuse to start, or T15 (SUSPENDED) if it is detected while running.
  2. `env=DEMO` and `fixture_demo: true` in `config/app.yaml`. `fixture_demo: true` with
     `env=LIVE` → refuse to start.
  3. Every record carries `params=FIXTURE`, and every screen and report carries the banner
     "FIXTURE PARAMETERS — NOT APPROVED SETTINGS".
  4. The user sets the entry authorization mode for the run in `fixture_demo_mode`, and every
     record carries it. Any of the three modes may be used, so M7 and M9 can exercise each one; the
     RISK-061 promotion requirement does not apply. Every other rule applies unchanged: the
     RiskEngine, trading states and recovery classes, demotion (RISK-062), the Guardian, the
     emergency controls and the no-overnight rule.

  A fixture-demo run never approves a parameter or a mode (RISK-092) and never satisfies a LIVE
  gate. Its forward-test results count toward the RISK-063 promotion gate only if every value the
  user later approves is equal to or tighter than the fixture value in effect during the run;
  otherwise the forward test restarts under the approved values.

## 3. Risk budget and sizing

**RISK-010 Budget.**
`budget = quantize_down(equity × P-01 / 100, account_currency_minor_unit)`.
Equity comes from the current `account_info()` snapshot, converted at the boundary (RISK-020).

**RISK-011 Modelled loss per 1.00 lot at the stop.**
`loss_per_lot = |order_calc_profit(side, symbol, 1.00, entry_price, sl_price)|` [VERIFIED S11:
returns account currency or `None`]. `entry_price` is the executable side (ask for BUY, bid
for SELL). A `None` result means **reject** (fail closed).

**RISK-012 Slippage allowance.** `slip_per_lot = P-26 converted to account currency per 1.00 lot`,
computed with `order_calc_profit` over a price distance equal to the allowance.

**RISK-013 Volume.**
```
raw      = budget / (loss_per_lot + slip_per_lot)
volume   = floor(raw / volume_step) × volume_step      # ALWAYS round down
if volume < volume_min:      REJECT  reason=MIN_VOLUME_EXCEEDS_BUDGET   (never round up)
if volume > volume_max:      volume = floor(volume_max / volume_step) × volume_step
check:   |order_calc_profit(side, symbol, volume, entry, sl)| + volume × slip_per_lot ≤ budget
         else REJECT reason=BUDGET_CHECK_FAILED
```
Every `MIN_VOLUME_EXCEEDS_BUDGET` rejection is counted per strategy (CENT-030).

**RISK-015 Aggregate open risk.** `Σ modelled loss-to-SL (incl. P-26) over all open positions +
the proposed one ≤ P-31 × equity`. Otherwise reject `AGGREGATE_RISK`. Positions without a
broker-confirmed SL count at their **full notional loss to zero**, which makes any new entry fail
(fail closed).

**RISK-016 Strategy risk budget.** Each strategy's per-trade budget is `P-32 ≤ P-01`. The
RiskEngine uses the smaller of the two.

**RISK-017 Strategy operating envelope.** Every strategy declares (`STRATEGY_RESEARCH_SPEC.md`
RES-070): eligible sessions, excluded windows, maximum spread, volatility band, minimum liquidity
proxy (tick rate), broker-session compatibility, and whether it is news-validated. A signal outside
the envelope is rejected `OUTSIDE_STRATEGY_ENVELOPE`. An open market alone is never a reason to
trade.

**RISK-018 News policy.** A strategy **not** validated for news (RES-071) cannot enter inside the
P-18 blackout. A news-validated strategy may enter only when the calendar data is VALID (TIME-043):
fresh, timezone-verified, relevance-classified. Its own spread and volatility limits still apply.
If calendar data is stale, unavailable or ambiguous, every strategy is treated as not
news-validated, and the unknown-calendar policy of TIME-042 applies.

**RISK-014 Formula cross-check.** Independently compute
`loss_formula = volume × |entry − sl| / tick_size × tick_value_loss`
(`SYMBOL_TRADE_TICK_VALUE_LOSS`; plain `tick_value` if the loss variant is unavailable
[VERIFIED S13 definitions]). If the formula and `order_calc_profit` disagree by more than one
`tick_value × volume`, **reject** with `CALC_MISMATCH` and raise an alert. This catches
cent/standard confusion (CENT-010).

### 3.1 Worked example — ILLUSTRATIVE (not verified against the live account)

Profile `ILL-CENT` (assumed values, see `CENT_ACCOUNT_VALIDATION.md` §4): account currency
USC; tick_size 0.01; tick_value 1.00 USC per tick per 1.00 lot; volume_min 0.01; volume_step
0.01. Equity 10,000.00 USC. BUY at ask 4,070.00, SL 4,045.00 (a $25.00 stop). P-26 slippage
allowance $0.30. **P-01 uses its fixture value 0.25%, not an approved setting.**

1. Budget = 10,000.00 × 0.25 / 100 = **25.00 USC**.
2. Ticks to the stop = 25.00 / 0.01 = 2,500. `loss_per_lot` = 2,500 × 1.00 = **2,500.00 USC**.
3. Slippage ticks = 0.30 / 0.01 = 30. `slip_per_lot` = 30 × 1.00 = **30.00 USC**.
4. raw = 25.00 / (2,500.00 + 30.00) = **0.00988** lots.
5. Floor to step 0.01 → **0.00** < volume_min 0.01 → **REJECT `MIN_VOLUME_EXCEEDS_BUDGET`**.

*Interpretation:* at exactly a $25 stop, the slippage allowance pushes the minimum lot over
budget. V1 said "$25 stop → 0.01 lot". V2 includes stop slippage, so the widest feasible stop
at minimum size is (25.00 − 0.30 USC)/(0.01 × 100 USC per $1) ≈ **$24.70** under this profile.
With SL at 4,046.00 ($24.00): loss at 0.01 lot = 24.00 + 0.30 = 24.30 USC ≤ 25.00 → **0.01 lot
approved**.

## 4. Decimal arithmetic and the conversion boundary

- **RISK-020 Boundary.** Every float from MT5 is converted exactly once, in `mt5_adapter`, by
  `to_decimal(x, kind)`:
  1. reject `None`, NaN, ±Inf and non-numeric values → `ConversionError` (fail closed);
  2. `d = Decimal(repr(x))`, the shortest round-trip string. **`Decimal(x)` is forbidden**
     because it converts the binary float exactly (e.g. `Decimal(1.1)` =
     1.1000000000000000888…) [VERIFIED S19]. Lint rule plus test;
  3. quantize by `kind`: prices to `symbol.digits`; volumes to the decimals of `volume_step`;
     money to the account currency minor unit (0.01);
  4. validate: price is a multiple of `tick_size` (else `OFF_TICK` rejection for order prices;
     market quotes keep their value with a data-quality warning); volume is a multiple of
     `volume_step`.
- **RISK-021 Decimal context.** Use a module-level context with `prec=28` and the
  `FloatOperation` trap **enabled** [VERIFIED S19], so any accidental float mixing raises.
- **RISK-022 Rounding and price rules.** Strategy SL/TP distances are never changed silently.

| Quantity | Rule | Mode |
|---|---|---|
| Trade volume | down to `volume_step` | `ROUND_DOWN` (always toward smaller exposure) |
| Risk budget | down to minor unit | `ROUND_DOWN` |
| Modelled loss | up to minor unit | `ROUND_UP` (conservative) |
| SL / TP / order prices | **no rounding by default**: a price that is not an exact multiple of `tick_size` is **rejected `OFF_TICK`** | — |
| Displayed amounts | to minor unit | `ROUND_HALF_EVEN`, display only |

- **RISK-025 Opt-in price quantization.** A strategy may declare `allow_price_quantization: true`
  in its versioned specification. Only then does the engine run this sequence, and if any step
  fails the signal is rejected:
  1. quantize SL and TP to `tick_size`, choosing for each the direction that does **not** increase
     the loss at SL;
  2. recalculate the modelled loss (RISK-011..014) and the budget check;
  3. recalculate reward-to-risk against P-27 and the strategy's own minimum;
  4. re-validate stops/freeze levels (RISK-032);
  5. re-validate the strategy signal with the quantized prices (the strategy's own `accepts()` check);
  6. record the original prices, the quantized prices and the delta in the risk decision;
  7. after the fill, verify the broker-side SL/TP by read-back (RISK-031).

- **RISK-023 Money type.** `Money(amount: Decimal, currency: Literal["USC","USD", …])`.
  Arithmetic across currencies raises `CurrencyMismatchError`. USC↔USD conversion is only
  allowed through `convert_display(money, rate_source="ACCOUNT_DEFINITION")`, and is never
  used inside the RiskEngine (CENT-011).
- **RISK-024 Values sent back to MT5** (prices, volumes) are converted from `Decimal` to
  `float(str(d))` at the adapter, after the quantization above, and only there.

## 5. Stop-loss rules

- **RISK-030 SL required.** Every risk-increasing action carries an SL. An `OrderIntent`
  without an SL cannot be constructed (type test) and is rejected again by the adapter (defence
  in depth).
- **RISK-031 Broker-confirmed SL.** The SL is attached in the same `order_send` request where the
  symbol's execution mode permits it. Fill confirmation must read the position back and verify
  `sl == intended_sl` (within one tick). If the broker does not accept SL-on-entry for this
  symbol/mode [BLOCKED: verify in M2/M7], the engine places the SL immediately with
  `TRADE_ACTION_SLTP` and P-22 applies.
- **RISK-032 Distance rules.** `|entry − sl| ≥ max(stops_level × point, freeze_level × point) +
  current spread` [VERIFIED S13 definitions]. Otherwise reject `SL_TOO_CLOSE`.
- **RISK-033 Never widen.** No SL modification may move away from price. The position manager
  may only tighten or move to break-even, as defined by the strategy.
- **RISK-034 Managed SL/TP modifications.** The bot may modify SL (tighten only) and TP
  automatically, but only by rules declared in the strategy's versioned specification. Each
  modification goes through `evaluate_modification()` (RISK-002). It must not move a TP beyond
  what can be reached before the session-close deadline (P-33). It is sent as `TRADE_ACTION_SLTP`,
  verified by read-back, and audited with a reason code and old/new values. A modification the
  broker rejects leaves the previous broker-confirmed values in force, and the UI shows those.

## 6. Effective exposure and margin (corrects V1's reliance on account leverage)

- **EXP-001 Inputs** from each account snapshot: balance, equity, margin (used), margin_free,
  margin_level, `margin_so_mode`, `margin_so_call`, `margin_so_so`, leverage. All values pass the
  conversion boundary.
- **EXP-002 Notional per position (account currency).** Use the broker's own calculation:
  `notional = |order_calc_profit(BUY, symbol, volume, P, 2P)|`, i.e. the P/L of a move from P to
  2P, which equals volume × contract × P in account currency. Cross-check with
  `volume × P / tick_size × tick_value`; disagreement > 0.5% → `CALC_MISMATCH`.
- **EXP-003 Effective leverage.** `eff_lev = Σ notional(open positions + proposed) / equity`
  must be ≤ P-09. *Illustrative:* 0.01 lot at $4,070 under `ILL-CENT` ≈ 4,070 USC notional ÷
  10,000 USC = 0.41×.
- **EXP-004 Margin utilisation.** `required = order_calc_margin(type, symbol, volume, price)`
  [VERIFIED S12: account currency; **ignores existing positions**]. Therefore
  `projected_used = account.margin + required`, and `projected_used / equity × 100 ≤ P-10`.
- **EXP-005 Projected margin level.** `equity / projected_used × 100 ≥ P-11`. Also require
  `margin_free − required > 0`.
- **EXP-006 Stop-out distance.** Report the price move that would bring the margin level to
  `margin_so_so`. Reject if it is smaller than 3 × the SL distance.
- **EXP-007 Account leverage cap.** `account_info().leverage > P-12` → ENTRY_STOP (retained from
  V1 as an *additional* control). Because Exness may apply different margin during news
  [VERIFIED S2: 1:200 cap on new gold positions] and around breaks [REPORTED S5], margin is
  always taken from `order_calc_margin` at decision time, never derived from the leverage number.
- **EXP-008 Concentration.** v1 trades one symbol, so symbol exposure equals account exposure.
  The number of positions is bounded by P-05 and P-31, both pending user decision. The checks are
  written per symbol and per account. Positions on one symbol are treated as fully correlated in
  P-31.
- **EXP-009 Ownership.** Positions/orders whose magic number is not the engine's (`MAGIC_ENGINE`)
  or the Guardian's are *foreign*. Policy P-30. Foreign exposure still counts toward EXP-003..005.

## 7. Trading states, failure classification and recovery

States, in order: `ACTIVE` < `ENTRY_STOP` < `SUSPENDED`. The effective state is the **highest**
state demanded by any active trigger. Every trigger, resumption and clear is audited.

**Health-check bundle** (used in the *Health checks* column): HC-1 terminal connected and trading
allowed; HC-2 tick fresh (P-15) in an open session; HC-3 clean reconciliation with no UNKNOWN
intents or positions; HC-4 Guardian HEALTHY with valid message integrity **and its kill flag clear** (a Guardian latch that needs re-arm, GRD-016, keeps HC-4 failing until the user re-arms it); HC-5 clock within P-16;
HC-6 spec hash unchanged; HC-7 config valid and hash unchanged; HC-8 audit chain verifies; HC-9
every open position has a broker-confirmed SL; HC-10 no emergency action in progress or unresolved.

**Recovery classes:** `AUTO` = resumes automatically after the cooldown when the listed checks
pass continuously (RISK-052); `ACK` = needs a one-step user acknowledgement (TOTP) plus all checks;
`MANUAL` = needs full manual recovery approval (RISK-050).

| # | Trigger | Severity | State | Emergency actions requested | Recovery class | Cooldown (P-34) | Health checks |
|---|---|---|---|---|---|---|---|
| T1 | Manual entry stop (UI/CLI/`STOP` file) | INFO | ENTRY_STOP | none | MANUAL clear by the user (TOTP) | — | HC-1..10 |
| T2 | Daily loss ≥ P-02 (equity vs day start, incl. floating) | HIGH | ENTRY_STOP | CANCEL_PENDING + EMERGENCY_LIQUIDATE | ACK, not before the next UTC day | next UTC day | HC-1..10 |
| T3 | Weekly loss ≥ P-03 | HIGH | SUSPENDED | CANCEL_PENDING + EMERGENCY_LIQUIDATE | MANUAL | — | HC-1..10 |
| T4 | Drawdown ≥ P-04 from equity HWM | CRITICAL | SUSPENDED | CANCEL_PENDING + EMERGENCY_LIQUIDATE | MANUAL | — | HC-1..10 |
| T5 | Consecutive losses ≥ P-07 | MEDIUM | ENTRY_STOP | none | AUTO at the next UTC day (counter persists; resets only on a winning trade) | next UTC day | HC-1..10 |
| T6 | Consecutive losses ≥ P-08 | HIGH | SUSPENDED | none | MANUAL | — | HC-1..10 |
| T7 | Reconciliation mismatch that the reconciler cannot explain from deal history (EXE-051) | CRITICAL | ENTRY_STOP | none | MANUAL | — | HC-3 + all |
| T8 | T7 unresolved > 60 s (P-24) | CRITICAL | SUSPENDED | none | MANUAL | — | HC-1..10 |
| T9 | Guardian heartbeat stale (no integrity failure) | HIGH | ENTRY_STOP | none | AUTO | Guardian HEALTHY for 60 s | HC-1..10 |
| T10 | Symbol spec hash changed | HIGH | ENTRY_STOP | none | MANUAL (CENT-020 re-validation) | — | HC-6 + all |
| T11 | Clock offset > P-16 entry-stop level, or NTP unreachable > 10 min | MEDIUM | ENTRY_STOP | none | AUTO | offset < warn level for 5 min | HC-1..10 |
| T12 | Terminal disconnected / trading not allowed / account query failed | HIGH | ENTRY_STOP | none | AUTO only if reconciliation after reconnect is clean **and** no intent or position state became unknown; otherwise escalate to T20 | 5 min connected | HC-1..10 |
| T13 | Account leverage > P-12 | MEDIUM | ENTRY_STOP | none | AUTO when compliant on re-read | 5 min | HC-1..10 |
| T14 | Foreign position/order detected | HIGH | ENTRY_STOP | none | MANUAL | — | HC-1..10 |
| T15 | Account class ≠ configured class, or env/config mismatch | CRITICAL | SUSPENDED | none | MANUAL | — | HC-1..10 |
| T16 | Configuration invalid, corrupted, or `risk_limits.yaml` hash changed while running | CRITICAL | SUSPENDED | none | MANUAL (restart required) | — | HC-7 + all |
| T17 | Manual EMERGENCY_LIQUIDATE requested | HIGH | SUSPENDED | as requested | MANUAL | — | HC-1..10 |
| T18 | Guardian takeover reported (GRD-040) | CRITICAL | SUSPENDED | per Guardian | MANUAL (+ Guardian input re-arm, GRD-016) | — | HC-1..10 |
| T19 | Emergency action FAILED / deadline exceeded (unresolved liquidation) | CRITICAL | SUSPENDED | — | MANUAL | — | HC-10 + all |
| T20 | Unknown order execution state or unknown open-position state (EXE §2 `UNKNOWN` not resolved within the P-25 global deadline) | CRITICAL | SUSPENDED | none (no blind action) | MANUAL | — | HC-3 + all |
| T21 | RiskEngine integrity failure (startup self-test or golden-vector check fails; unexpected exception in `evaluate`) | CRITICAL | SUSPENDED | none | MANUAL | — | HC-1..10 |
| T22 | Guardian message integrity/authentication failure (GRD-031) | CRITICAL | SUSPENDED | none | MANUAL | — | HC-4 + all |
| T23 | Audit-chain verification failure (SEC-022) | CRITICAL | SUSPENDED | none | MANUAL | — | HC-8 + all |
| T24 | Suspected credential compromise (secret-scan hit, unexpected login, keyring entry changed, user report) | CRITICAL | SUSPENDED | none | MANUAL (+ secret rotation, SEC-007) | — | HC-1..10 |
| T25 | Broker-side protection uncertainty: an open position whose SL is not broker-confirmed after P-22, or whose SL cannot be read | CRITICAL | SUSPENDED | EXE-031 response | MANUAL | — | HC-9 + all |
| T26 | Session-end close failure: a position still open at the P-33 deadline (EXE-084) | CRITICAL | SUSPENDED | EMERGENCY_LIQUIDATE continues while the market is open | MANUAL | — | HC-1..10 |
| T27 | Unexpected broker session change (live session export differs from the cached schedule) | HIGH | ENTRY_STOP | none | AUTO after the new schedule is loaded and all deadlines are recomputed | 5 min | HC-1..10 |

- **RISK-050 Manual recovery approval.** A checklist in the UI: the cause is shown and
  acknowledged; HC-1..10 pass; for T24 the secrets have been rotated; for T16 the process was
  restarted with a valid config. Then a typed phrase + TOTP. The result is ACTIVE, with any
  **automatic entry permission paused**: entries resume only under human approval until the user
  explicitly re-confirms the configured automatic mode (RISK-061).
- **RISK-051 Exits during states.** Protective exits, SL tightening, strategy-defined exits and
  session-end closes continue in every state. A state never leaves a position unmanaged.
- **RISK-052 Automatic recovery rules.** Only triggers classed `AUTO` may resume automatically.
  Conditions: the cooldown has elapsed; every listed health check has passed continuously for the
  cooldown; **no `MANUAL`-class trigger is active**; and the per-trigger daily limit in P-34 has
  not been reached (otherwise the trigger becomes `MANUAL`). Every automatic resumption is audited
  and shown in the dashboard. It never re-enables an automatic entry mode that RISK-062 demoted.
- **RISK-053 Prohibited automatic recovery.** Automatic resumption is prohibited while any of these
  is unresolved: reconciliation failure (T7/T8); unknown order or position state (T20); RiskEngine
  integrity failure (T21); Guardian authentication/integrity failure (T22); invalid or corrupted
  configuration (T16); compromised credentials (T24); unresolved emergency liquidation (T19);
  broker-side protection uncertainty (T25); audit integrity failure (T23).

## 8. Loss and drawdown interventions are not guarantees

- **RISK-040** P-02, P-03 and P-04 are **intervention thresholds**. Realised losses **can exceed
  them**. Reasons include: price gaps through SL (weekend, news); stop slippage; rejected or
  requoted close orders (retcodes 10004, 10006, 10018, 10021, 10031 [VERIFIED S14]); the market
  being closed when the threshold is crossed; the terminal, host or broker connection being down;
  broker stop-out at `margin_so_so`; and the threshold check running on a polling interval. A
  stop-loss likewise does **not** guarantee the exit price or a maximum loss.
- **RISK-041** No UI, report, README or prompt may describe these thresholds as a "maximum
  loss", "guaranteed protection" or a "cap". The adversarial review checks for these phrases.
- **RISK-042 Reporting.** Every intervention reports the threshold, the equity at trigger, the
  equity when protective actions were confirmed, and the overshoot.

## 9. Entry authorization (operating mode) — USER DECISION PENDING (D-01, P-37)

The user has **not** chosen how new entries are authorised. The system supports three modes, and
no mode is selected on the user's behalf.

| Mode | Behaviour | Technical consequences | Operational consequences |
|---|---|---|---|
| `MANUAL_APPROVAL` | Every entry is proposed; the user approves each in the dashboard (API-031) | Needs the approval UI, approval tokens, expiry (P-23) and re-evaluation (RISK-004). Fills are delayed by human latency, so the backtest must model approval delay as extra latency | The user must be present. Signals in the user's absence expire unused. Lowest automation risk. Forward results include approval behaviour |
| `AUTO_ALL` | Every entry that passes the RiskEngine is sent automatically | No approval path in the loop. Requires the promotion gate (RISK-063) and the demotion triggers (RISK-062). Execution-quality monitoring (EXE-060) becomes critical | Trades happen while the user is away. Errors repeat faster. Needs the strongest evidence before LIVE |
| `AUTO_APPROVED_STRATEGIES` | Automatic entry only for strategies the user has individually marked `auto_approved` (each must have passed RISK-063 on its own); other strategies' entries need manual approval | Per-strategy permission flag, versioned (RES-011): a new strategy version loses `auto_approved` | A middle path: mature strategies run unattended; new ones stay supervised |

- **RISK-060** The selected mode persists in SQLite and every change is audited.
- **RISK-061 Enabling an automatic mode** (`AUTO_ALL`, or `auto_approved` for a strategy)
  outside fixture demo (RISK-066) requires: the promotion gate passed (RISK-063) for each strategy concerned; trading state ACTIVE;
  a typed phrase + TOTP; an audit entry. On `env=LIVE`, also: the M10 pilot report and a GO from
  `prompts/03_RELEASE_READINESS_PROMPT.md`.
- **RISK-062 Automatic demotion to human approval** happens on: any trigger T2–T27; strategy
  demotion (RES-040); two consecutive rejected orders; execution-quality breach (EXE-060). It takes
  effect within one engine cycle. Open positions keep being managed and closed by their rules.
  Demotion is a safety fallback, not a choice of mode, and only the user can re-enable automation.
- **RISK-063 Promotion gate (PROPOSED defaults, user-approved in M0):** demo forward test ≥ 8 weeks
  **and** ≥ 50 closed trades; forward expectancy inside the 95% bootstrap band of the PT1 backtest
  (`BACKTESTING_SPEC.md` §6); zero unhandled execution errors; no reconciliation mismatch
  unresolved > 60 s; zero Guardian takeovers. *Limitation:* 50 trades is a small sample. The gate
  detects gross failure; it does not prove an edge (`STRATEGY_RESEARCH_SPEC.md` §4).
- **RISK-064** No mode can bypass the RiskEngine. A mode change never cancels management or
  automatic closing of open positions. **Position closing is always automatic**, according to the
  strategy's exit rules, the risk rules and the session-close deadline (EXE-080).
- **RISK-065 Fail closed while undecided.** In `LIVE`, and in `DEMO` outside fixture demo, the
  engine generates no entries until P-37 is approved (RISK-005). In fixture demo the mode comes from
  `fixture_demo_mode` (RISK-066). BACKTEST and REPLAY must state which mode they simulate.
- **RISK-067 Schedule narrowing (optional, part of D-01).** The user may also decide that automatic
  entry is narrowed by time or conditions: for example automatic only in chosen sessions, or human
  approval inside news windows or above a volatility level. A narrowing rule can only move an entry
  from automatic to human approval, never the reverse, and it never bypasses RISK-061. Rules are
  versioned in `config/risk_limits.yaml`, evaluated deterministically from the clock and market
  snapshots (RISK-003), audited when they fire, and shown on the entry-authorization chip (UI-032).
  No rule exists until the user decides one.

## 10. Prohibited behaviour (V1 list preserved; V2 additions marked +)

Martingale; grid or grid recovery; averaging down; loss-recovery sizing or any size increase to
recover losses; hedging to hide losses; widening a stop; LLM-generated orders or limits; automatic
or autonomous loosening of any limit; changing account leverage or any broker setting from
software. **+** Resubmitting an order after an ambiguous execution response before
reconciliation proves it did not execute (EXE-002); **+** silent SL/TP distance changes (RISK-022);
**+** Guardian actions beyond the approved loss budget (GRD-020); **+** intentional overnight or
weekend holding (EXE-080); **+** order execution through MCP (MCP-010); **+** any external AI
service as a dependency of order authorization, risk, sizing, stop calculation, emergency operations
or reconciliation (LLM-006).

## 11. Golden test vector catalogue

Vectors run against two fixture profiles: `ILL-CENT` and `ILL-STD` (illustrative, defined in
`CENT_ACCOUNT_VALIDATION.md` §4). In M2–M3 they run again against `VER-CENT` / `VER-STD`
(recorded from live accounts). Expected values are recomputed **only** with user approval.
**All vectors use the fixture column of §2** (e.g. P-01 0.25%, P-02 1%, P-04 5%, P-05 1, P-07 3,
P-08 5, P-31 0.25%). These are test values, not approved settings. When the user approves different
values, the vectors are recomputed and the change is logged.

| GV | Scenario | Expected |
|---|---|---|
| GV-01 | Normal BUY, $24 stop, ILL-CENT, equity 10,000 USC | APPROVE 0.01 |
| GV-02 | $25 stop with slippage allowance | REJECT MIN_VOLUME_EXCEEDS_BUDGET |
| GV-03 | $12 stop | APPROVE 0.02 (raw 0.0203 → floor) |
| GV-04 | $85 stop (≈1× ATR) | REJECT MIN_VOLUME_EXCEEDS_BUDGET |
| GV-05 | ILL-STD, equity 100.00 USD, $24 stop (USD account: 0.01 lot ≈ 1 USD per $1) | budget 0.25 USD; loss 24.30 USD → REJECT MIN_VOLUME_EXCEEDS_BUDGET |
| GV-06 | Money(USC) + Money(USD) | CurrencyMismatchError |
| GV-07 | `order_calc_profit` returns None | REJECT CALC_UNAVAILABLE |
| GV-08 | Formula vs calc differ by 100× | REJECT CALC_MISMATCH + alert |
| GV-09 | Tick age 11 s in open session | REJECT STALE_TICK (gate) |
| GV-10 | Spread above P-13 | REJECT SPREAD_TOO_WIDE |
| GV-11 | Strategy not news-validated, inside the P-18 blackout | REJECT BLACKOUT |
| GV-12 | Daily loss at the fixture 1.00% | ENTRY_STOP + emergency requests |
| GV-13 | Drawdown at the fixture 5.00% | SUSPENDED + emergency requests |
| GV-14 | 3rd consecutive loss | ENTRY_STOP until next UTC day |
| GV-15 | 5th consecutive loss | SUSPENDED |
| GV-16 | Leverage 1:2000 reported | ENTRY_STOP (T13) |
| GV-17 | Effective leverage would be 1.2× | REJECT EFFECTIVE_LEVERAGE |
| GV-18 | Projected margin level 800% | REJECT MARGIN_LEVEL |
| GV-19 | SL inside stops level | REJECT SL_TOO_CLOSE |
| GV-20 | Intent without SL | Cannot construct; adapter also rejects |
| GV-21 | SL widen request | REJECT (risk-increasing, prohibited) |
| GV-22 | SL tighten request in SUSPENDED | APPROVE (risk-reducing) |
| GV-23 | Second position while one is open (fixture P-05 = 1) | REJECT MAX_POSITIONS |
| GV-24 | Spec hash differs from snapshot | ENTRY_STOP (T10) |
| GV-25 | Float passed into Money | FloatOperation raised |
| GV-26 | `Decimal(x)` used in adapter | lint failure (static test) |
| GV-27 | Signal age 3 s | REJECT SIGNAL_STALE |
| GV-28 | Entry inside the P-19 pre-close window, or a planned exit later than the P-33 deadline | REJECT PRE_CLOSE / OVERNIGHT_HOLD |
| GV-29 | Foreign position present | ENTRY_STOP (T14) |
| GV-30 | Equity query fails | ENTRY_STOP (T12); no decision made |
| GV-31 | SL price not a multiple of `tick_size`, strategy without opt-in | REJECT OFF_TICK (no silent rounding) |
| GV-32 | Same, strategy with `allow_price_quantization` | Quantized away from extra loss; risk and R:R recalculated; original and quantized prices recorded |
| GV-33 | `env=DEMO` start with a USER_DECISION_REQUIRED parameter unapproved and `fixture_demo: false` | Engine refuses to start (RISK-005) |
| GV-34 | Signal outside the strategy's eligible sessions | REJECT OUTSIDE_STRATEGY_ENVELOPE |
| GV-35 | News-validated strategy, calendar stale | REJECT NEWS_DATA_INVALID (treated as not validated) |
| GV-36 | Aggregate open risk would exceed fixture P-31 | REJECT AGGREGATE_RISK |
| GV-37 | Open position without broker-confirmed SL, new entry proposed | REJECT AGGREGATE_RISK (RISK-015 counts full loss) and T25 |
| GV-38 | TP modification beyond what can be reached before P-33 | REJECT MODIFICATION_PAST_CLOSE |
| GV-39 | `fixture_demo: true`, but MT5 `trade_mode` is REAL or CONTEST | Engine refuses to start (RISK-066) |
| GV-40 | `env=LIVE` with `fixture_demo: true` | Engine refuses to start (RISK-066) |
| GV-41 | `AUTO_ALL` with the narrowing rule "human approval outside the London session"; signal outside it | Routed to human approval; nothing sent automatically (RISK-067) |

## 12. Configuration change control

- **RISK-090** `config/risk_limits.yaml` is validated against its schema at startup, hashed, and
  the hash is written to the audit log. The UI may only *tighten* (§2). Loosening requires: file
  edit → restart → typed confirmation. A diff is shown and logged.
- **RISK-091** No component other than the user's file edit can change `P-xx`. Nothing from the
  LLM, MCP, API command, Guardian or strategy can (enforced by tests that try each path).
- **RISK-092 Approval record.** Each USER_DECISION_REQUIRED parameter in `risk_limits.yaml` carries
  `approved_by_user`, `approved_on` and a free-text `reason`. The values and the approval are copied
  into `docs/STATUS.md`. An approval is never inferred from a fixture value or a recommendation.
