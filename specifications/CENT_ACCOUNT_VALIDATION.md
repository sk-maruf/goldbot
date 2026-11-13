# CENT_ACCOUNT_VALIDATION — Discovering and proving Standard Cent behaviour

> Status: **SPECIFICATION.** Every number in this file is **ILLUSTRATIVE** unless it is marked
> VERIFIED with a source, or recorded from the live account in M2 (profiles `VER-*`).

## 1. Why the cent account needs its own validation

| Do not confuse | Correct handling |
|---|---|
| USD vs USC | The account currency is read from `account_info().currency`. All risk maths use that currency (RISK-023). USD appears only as a labelled display conversion. |
| Standard lot vs cent lot | A cent lot is reported to be 0.01 of a standard lot [REPORTED S4]. The system never applies this rule itself; it uses `symbol_info` and `order_calc_profit` for the actual symbol. |
| Standard symbol vs cent symbol | The cent gold symbol is expected to carry a suffix (e.g. `XAUUSDc`) [ASSUMPTION]. It is discovered, never assumed (CENT-003). |
| Balance vs equity | Risk uses **equity** (balance + floating P/L). Balance is shown, never used for sizing. |
| Displayed amount vs USD-equivalent | Every amount shows its currency. USD-equivalent is labelled "≈ USD". |
| Standard demo vs cent live | A Standard Cent demo does not exist [VERIFIED S1]. Demo results never stand in for cent economics (§8). |

## 2. Discovery procedure (M2, read-only, investor password)

- **CENT-001 Live values win.** Values read from the connected account override any document,
  including this pack. Disagreements are written to `docs/VERIFIED_SPECS.md`, and the affected
  `ASSUMPTIONS_AND_UNKNOWNS.md` items are updated.
- **CENT-002 Account discovery.** Record `account_info()` fields: `login` (stored hashed in
  logs, PRV-011), `server`, `company`, `currency`, `trade_mode` (demo/contest/real), `leverage`,
  `margin_so_mode`, `margin_so_call`, `margin_so_so`, `trade_allowed`, `trade_expert`, `limit_orders`.
  Derive **account class from MT5 data only**: `CENT` if the account currency is `USC` **and** the
  chosen gold symbol passes CENT-010..012 at cent scale; `STANDARD` if the currency is a normal ISO
  currency and the symbol passes at standard scale. Anything else → `UNKNOWN` → SUSPENDED (T15).
  The user's confirmation of the account type (as shown in the Exness Personal Area) is recorded as
  **corroboration only**. If it conflicts with the MT5 data, the MT5 data wins, the class is
  `UNKNOWN`, and a BLOCKED item is raised. A user statement never overrides MT5 information.
- **CENT-003 Symbol discovery.** `symbols_get()` filtered to names containing `XAU`. Then
  `symbol_select(name, True)` for each candidate, and record the full `symbol_info()`. The user
  picks the symbol in the UI from the discovered list. The choice is stored with the spec hash.
  If no candidate has `trade_mode` allowing full trading → BLOCKED.
- **CENT-004 Spec snapshot fields** [definitions VERIFIED S13]: `digits`, `point`,
  `trade_tick_size`, `trade_tick_value`, `trade_tick_value_profit`, `trade_tick_value_loss`,
  `trade_contract_size`, `volume_min`, `volume_max`, `volume_step`, `volume_limit`,
  `trade_stops_level`, `trade_freeze_level`, `trade_mode`, `trade_exemode`, `filling_mode`,
  `order_mode`, `swap_mode`, `swap_long`, `swap_short`, `swap_rollover3days`, `currency_base`,
  `currency_profit`, `currency_margin`, `margin_initial`, `margin_maintenance`. The snapshot is
  stored as canonical JSON, and its SHA-256 is the **spec hash** (T10).
- **CENT-005 Sessions.** The Python package has no session function [VERIFIED S9 function list].
  The Guardian exports `SymbolInfoSessionTrade` results for each weekday into
  `guardian_sessions.json` (`GUARDIAN_SAFETY_SPEC.md` §3 and §11). The engine cross-checks them against
  the published hours [VERIFIED S2: XAU Sunday 22:05 – Friday 20:58, daily break 20:58–22:01,
  server time GMT+0]. A mismatch is logged; the **exported live sessions win**.
- **CENT-006 Commission.** No `symbol_info` field reports commission. It is observed from
  `history_deals_get()` (`commission`, `fee` fields) on the first demo/pilot deals, recorded per
  lot, and fed to the backtester cost model. Until it is observed: [BLOCKED: needs real deal
  records]; the backtester uses a pessimistic placeholder (BT-022).
- **CENT-007 Swap.** Record `swap_mode`, `swap_long`, `swap_short`, `swap_rollover3days`.
  Exness may apply automatic swap-free status to accounts registered in Islamic countries
  [VERIFIED S3]. The system therefore reads swap from the live symbol and never assumes it. If
  swap-free status applies, record any conditions shown in the user's Personal Area [OPEN: user
  to check]. Because overnight holding is prohibited (EXE-080), swap normally appears only after a
  failed session-end close. It is still modelled and reported.

## 3. Validation checks (all must pass before any trading on the account)

| ID | Check | Pass criterion |
|---|---|---|
| CENT-010 | Profit calc | `order_calc_profit(BUY, sym, volume_min, P, P + 1.00)` returns a non-None value. Record it as `value_per_dollar_at_min_lot`. Cross-check with `volume_min × 1.00 / tick_size × tick_value_profit` within one tick value. |
| CENT-011 | Currency consistency | Unit of CENT-010 result = `account_info().currency`. If the account class is CENT, the currency must be `USC`. |
| CENT-012 | Scale plausibility | Under CENT, `value_per_dollar_at_min_lot` must be within ±5% of the value predicted by `contract_size × volume_min × (USC per USD)`. "USC per USD" = 100 [REPORTED S4]; CENT-016 may corroborate it from balance operations. Failure → BLOCKED with both numbers shown. |
| CENT-013 | Margin calc | `order_calc_margin(BUY, sym, volume_min, ask)` non-None, in account currency, and > 0. |
| CENT-014 | Volume grid | `volume_min`, `volume_step` > 0; `volume_min` is a multiple of `volume_step` (Decimal check). |
| CENT-015 | Stops/freeze | Recorded. Converted to price distance = level × `point`. |
| CENT-016 | Account-type evidence (no balance comparison) | **Primary:** account currency and account class from CENT-002/010–012. **Optional corroboration:** read balance operations from `history_deals_get` (deal type `DEAL_TYPE_BALANCE` [VERIFIED S37]; their presence in the Python result is [ASSUMPTION A-56]). If the user supplies a deposit amount in USD, compare it with the **deposit balance operation itself** (≈ amount × 100 USC, ± fees), **never with the current balance**, which changes with profits, losses, withdrawals, bonuses, credits and corrections. A mismatch is reported for the user to review. It never overrides MT5 data and never upgrades the account class. |
| CENT-017 | Tick sanity | 200 consecutive polled ticks: `ask ≥ bid`, spread > 0, `time_msc` non-decreasing (TIME-021). |
| CENT-018 | Repeatability | Checks re-run on every reconnect. A changed spec hash → T10. |

- **CENT-020 Re-validation after a spec change.** The UI shows a field-by-field diff of the old and new
  snapshot. CENT-010..017 re-run against the new spec. The golden vectors re-run on a `VER-*`
  profile rebuilt from it. The user confirms with a typed phrase. Only then is T10 cleared, and the
  new spec hash becomes the reference.

## 4. Fixture profiles

`ILL-*` profiles are **assumed** values used only to write tests before M2. `VER-*` profiles
are recorded from the live accounts in M2 and replace `ILL-*` in CI, with user approval.

| Field | ILL-CENT (assumed) | ILL-STD (assumed) |
|---|---|---|
| account currency | USC | USD |
| symbol | `XAUUSDc` | `XAUUSD` |
| tick_size | 0.01 | 0.01 |
| tick_value (per 1.00 lot) | 1.00 **USC** | 1.00 **USD** |
| implied value of $1 move at 0.01 lot | 1 USC (= $0.01) | 1 USD |
| volume_min / step | 0.01 / 0.01 | 0.01 / 0.01 |
| stops_level / freeze_level (points) | 0 / 0 | 0 / 0 |

> **Trap these profiles are designed to catch:** both have tick_value **1.00**. Only the
> currency differs, and that means a 100× difference in real money. Any code that drops the
> currency passes one profile and fails the other (GV-05, CGV-04).

## 5. Cent-specific golden tests (in addition to GV-01..41)

| CGV | Scenario | Expected |
|---|---|---|
| CGV-01 | Equity 10,000.00 USC, $24 stop, ILL-CENT | 0.01 lot; modelled loss 24.30 USC |
| CGV-02 | Same trade evaluated with ILL-STD specs but USC equity | REJECT CURRENCY_MISMATCH (spec currency ≠ account currency) |
| CGV-03 | Display of a −24.30 USC loss | "−24.30 USC · ≈ −$0.24" (sign kept, USD labelled ≈) |
| CGV-04 | tick_value 1.00 with the currency field missing | REJECT SPEC_INCOMPLETE |
| CGV-05 | volume_min 0.10 (hypothetical spec change), equity 10,000 USC | Loss at 0.10 lot = 10 USC per $1 + 3 USC slippage ≤ 25 → every signal with a stop > $2.20 is rejected; rejection rate reported |
| CGV-06 | Equity 9,000 USC after losses, $24 stop | Budget 22.50 → 0.01 lot loss 24.30 > 22.50 → REJECT MIN_VOLUME_EXCEEDS_BUDGET |
| CGV-07 | User reports a $100 deposit; current balance 9,431 USC after trading; the balance operation shows +10,000 USC | Corroboration consistent (the current balance is ignored); account class still decided by CENT-002/010–012 only |
| CGV-09 | User says "Standard Cent", but MT5 currency is `USD` | Class `UNKNOWN` → T15; MT5 data wins; BLOCKED raised |
| CGV-08 | Swap-free symbol (swap 0) on triple-swap day, position held only because a session-end close failed | Swap cost 0 recorded against the failed close (EXE-084); overnight holding is never planned |

## 6. Minimum-volume rejection reporting

- **CENT-030** For each strategy and period:
  `min_volume_rejection_rate = (# MIN_VOLUME_EXCEEDS_BUDGET) / (# signals that passed every
  pre-trade gate)`. Reported in backtests (`BACKTESTING_SPEC.md` §7), the forward test, live, the dashboard
  (UI-021) and the MCP tool `get_strategy_performance`.
  Also, for A10 (user decision 2026-11-13, CH-92): `capital_feasibility_rejection_rate = (# signals
  rejected with any of `MIN_VOLUME_EXCEEDS_BUDGET`, `EFFECTIVE_LEVERAGE`, `MARGIN_UTILISATION`, `MARGIN_LEVEL`, `FREE_MARGIN`, `STOP_OUT_DISTANCE`, `AGGREGATE_RISK` or `SPREAD_TOO_WIDE`, at a pre-trade gate or in the
  RiskEngine) / (# signals not rejected for a reason unrelated to capital or cost)`. Rejections for
  stale data, blackout, pre-close window or trading state are excluded from both counts.
- **CENT-031** If the capital-feasibility rejection rate exceeds 50% over the evaluation window, the strategy report flags it
  `CAPITAL-INFEASIBLE`. The research verdict must say that the strategy cannot be traded as
  designed at this capital, rather than quietly trading only the surviving subset.
- **CENT-032** CGV-06 shows that the rate rises as equity falls. Reports must show the rate
  against equity, because after a drawdown the system may become unable to trade at all. That
  is correct behaviour, not a bug.

## 7. Economics — ILLUSTRATIVE, step by step

Assumptions (all illustrative): equity 10,000 USC; risk 25 USC per trade (the P-01 **fixture**
value, not an approved setting); a validated
edge of +0.2R per trade after costs; 40 trades per month.

1. Expected gain per trade = 0.2 × 25 USC = **5 USC**.
2. Per month = 5 × 40 = **200 USC**.
3. In USD = 200 / 100 = **≈ $2.00 per month**.
4. *Interpretation:* even an edge that very few retail strategies achieve earns about $2 per
   month. An LLM subscription or any paid service can exceed that. This is why `SYSTEM_ARCHITECTURE.md` §1 defines
   success without reference to profit.
5. *Sample-size caution:* at 40 trades per month, separating +0.2R from 0R needs several hundred
   trades (`STRATEGY_RESEARCH_SPEC.md` §4), i.e. many months of live data.

## 8. What each environment can and cannot validate

| Environment | Validates | Does **not** validate |
|---|---|---|
| BACKTEST (PT1) | Strategy logic, sizing parity, cost sensitivity on recorded cent ticks | Live fills, latency, rejects |
| DEMO, Standard account (PT2) | Connectivity, order lifecycle, retcode handling, reconciliation, Guardian behaviour, approval flow | Cent symbol specs, cent spreads/swap/commission, USC maths, cent fill quality |
| LIVE, Standard Cent pilot (PT3) | Cent economics, real spreads and fills on `XAUUSDc` | Long-run edge (sample too small) |

- **CENT-040** The M10 pilot is the first environment that validates cent economics. It needs
  its own approval gate (`prompts/03_RELEASE_READINESS_PROMPT.md`).
