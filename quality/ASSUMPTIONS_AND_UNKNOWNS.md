# ASSUMPTIONS_AND_UNKNOWNS

> Every fact the system depends on, with its evidence level. **Types:**
> `VERIFIED` (official source retrieved, `quality/SOURCES.md`) · `VERIFIED-DOC, LIVE CHECK` (documented,
> but the live account still overrides it) · `REPORTED` (source unreachable in this session; claim
> carried from V1 research) · `ASSUMPTION` (engineering judgement) · `BLOCKED` (cannot be resolved
> without live account data or measurement; says exactly what is needed) · `OPEN` (a user decision or
> an external check).
> Builders update this file as items resolve (GOV-003). Nothing is promoted to VERIFIED without
> evidence.

## 1. Broker and account (Exness)

| ID | Statement | Type | Source | Resolution (what is needed) | When | Impact if wrong |
|---|---|---|---|---|---|---|
| A-01 | Standard Cent has no demo account | VERIFIED | S1 | — | — | Demo plan already accounts for it |
| A-02 | Standard Cent account currency is USC; 100 USC = 1 USD | REPORTED | S4 | `account_info().currency` + deposit attestation (CENT-016) | M2 | Sizing off by 100× (mitigated by CENT-012) |
| A-03 | A cent lot = 0.01 standard lot | REPORTED | S4 | Never used directly; `order_calc_profit` (CENT-010) | M2 | None if CENT-010 is used as specified |
| A-04 | Cent gold symbol is named `XAUUSDc` | ASSUMPTION | — | Symbol discovery (CENT-003) | M2 | None (discovered) |
| A-05 | Contract size, tick size, tick value of the cent gold symbol | **BLOCKED** | — | `symbol_info()` on the cent account (read-only) | M2 | Sizing; all ILL-CENT values are illustrative until then |
| A-06 | `volume_min`, `volume_step`, `volume_max` of the cent symbol | **BLOCKED** | — | `symbol_info()` | M2 | Feasibility and rejection rate |
| A-07 | Stops level and freeze level | **BLOCKED** | — | `symbol_info()` | M2 | SL validity (RISK-032) |
| A-08 | Commission on Standard Cent gold | **BLOCKED** | — | `history_deals_get` commission/fee on first deals (CENT-006) | M7 (demo, Standard) / M10 (cent) | Backtest costs (placeholder until then) |
| A-09 | Swap values and whether the account is swap-free | **BLOCKED** (user states swap-free, 2026-11-13; M2 verifies from MT5) | S3 says automatic swap-free applies to accounts registered in Islamic countries | `symbol_info()` swap fields + the user checks the Personal Area for conditions (OPEN, kickoff question 6) | M0/M2 | Cost model; overnight holds |
| A-10 | Triple swap on Wednesday for metals | VERIFIED-DOC, LIVE CHECK | S2, S3 | `swap_rollover3days` | M2 | Minor |
| A-11 | Gold trading hours Sun 22:05 – Fri 20:58, daily break 20:58–22:01, server time GMT+0 | VERIFIED-DOC, LIVE CHECK | S2 | Guardian session export (CENT-005) | M2 | Blackouts (P-19) |
| A-12 | Swap charged at 21:00 GMT+0 (summer) / 22:00 (winter) | VERIFIED-DOC, LIVE CHECK | S3 | Session export + deals | M2/M7 | Rollover timing in the backtester |
| A-13 | Leverage on new gold positions is capped at 1:200 during news releases | VERIFIED-DOC | S2 | — | — | Margin estimates during news (EXP-007 uses `order_calc_margin`) |
| A-14 | Higher margin requirements apply around news and market breaks | REPORTED | S5 | Observe `order_calc_margin` around breaks on demo | M7 | Margin headroom |
| A-15 | Very high ("unlimited") leverage option and a low stop-out level | REPORTED | S4 | `account_info().leverage`, `margin_so_so` | M2 | EXP-006/007 |
| A-16 | Server time zone stays GMT+0 | VERIFIED-DOC, LIVE CHECK | S2 | TIME-030/031 measurement | M2 | Session/day boundaries |
| A-17 | Exness client eligibility requires age ≥ 18 | REPORTED (V1 research quoting the client agreement) | — | User confirms in Phase 0 | Phase 0 | Account eligibility |

## 2. MT5 platform

| ID | Statement | Type | Source | Resolution | When | Impact |
|---|---|---|---|---|---|---|
| A-20 | MetaTrader5 Python package: Windows x86-64 only; CPython 3.6–3.14; v5.0.6231 | VERIFIED | S18 | Re-check at M1 | M1 | Host choice |
| A-21 | The Python package has no `TimeTradeServer` equivalent | VERIFIED | S9 | — | — | Guardian exports server time (TIME-030) |
| A-22 | Python tick times are "UTC without the shift" (ambiguous) | VERIFIED-DOC, **BLOCKED** for interpretation | S10 | TIME-005 measurement | M2 | Bar building, sessions |
| A-23 | `order_calc_margin` ignores existing orders/positions | VERIFIED | S12 | — | — | EXP-004 adds existing margin |
| A-24 | `order_calc_profit` returns account currency, or `None` on failure | VERIFIED | S11 | — | — | — |
| A-25 | `TimeTradeServer` and `TimeGMT` depend on the local clock | VERIFIED | S7, S8 | — | — | TIME-010/032 |
| A-26 | MQL5 has SHA-256 but no native HMAC or asymmetric signatures | VERIFIED | S17 | The channel uses SHA-256 integrity + seq + ACL with no secret (GRD-008, final correction) | M2 | GRD-008 |
| A-27 | `FileMove` with `FILE_REWRITE` + `FILE_COMMON` replaces the target | VERIFIED | S16 | Test in M2 | M2 | Atomic IPC |
| A-28 | `os.replace` on the same NTFS volume is atomic for readers | ASSUMPTION | standard Windows behaviour | Stress test with concurrent reads | M2 | Torn reads (GRD-007 retries mitigate) |
| A-29 | Python `terminal_info()` exposes the common data path | ASSUMPTION | S15 (MQL5 property) | Check in M2; fallback: Guardian writes its path to a known local file | M2 | IPC location |
| A-30 | The broker preserves the order `comment` field | **BLOCKED** | — | Demo test (EXE-021) | M7 | Idempotency (fallback defined) |
| A-31 | SL can be attached in the market-order request for this symbol | **BLOCKED** | — | Demo test (RISK-031) | M7 | Missing-stop window |
| A-32 | Allowed filling modes for the gold symbol | **BLOCKED** | S13 definition | `symbol_info().filling_mode` | M2 | Retcode 10030 |
| A-33 | MQL5 calendar event times are in trade-server time | ASSUMPTION | — | Compare 3 events with a public calendar (TIME-042) | M7 | Blackout timing |
| A-34 | CFD tick volume is unreliable for order-flow strategies | ASSUMPTION | — | Inspect `volume`/`flags` in M2 | M2 | Strategy scope only; MI-021 labels tick activity `TICK_ACTIVITY_PROXY` |
| A-56 | Balance operations (`DEAL_TYPE_BALANCE`) appear in Python `history_deals_get` results | ASSUMPTION | S37 (deal types VERIFIED) | Check in M2 on the read-only account | M2 | CENT-016 corroboration only |
| A-57 | MT5 trade requests have no client idempotency or request-ID field | VERIFIED | S35 | — | — | EXE-002 provides its own `op_id` mechanism |
| A-58 | MQL5 `OrderCalcProfit` returns account-currency profit, or false on failure | VERIFIED | S38 | — | — | GRD-020 budget check |
| A-59 | MT5 session data is a weekday template; holidays and early closes are not available by date | VERIFIED | S36 | The user maintains `config/session_exceptions.yaml` from broker announcements (OPEN) | M2 | EXE-080/085 |
| A-60 | MQL5 has no Credential Manager API (it would need DLL imports) | ASSUMPTION | MQL5 reference (no such function found) | Re-check in M2; the design does not depend on it (GRD-008) | M2 | None |
| A-61 | Changing an EA input re-initialises the EA (`OnDeinit`/`OnInit`), which the `rearm_counter` relies on | ASSUMPTION | standard MT5 behaviour | Demo test | M7 | GRD-016 |
| A-62 | A Windows ACL on the common `goldbot` folder can restrict it to one account without breaking terminal access | ASSUMPTION | — | Demo test with `icacls` | M2 | GRD-008 |
| A-63 | An MCP stdio server cannot verify which program launched it | ASSUMPTION | design consequence of S20/S21 | — | — | MCP-022 states the limit |
| A-64 | `account_info().trade_mode` reports `ACCOUNT_TRADE_MODE_DEMO` on the Exness Standard demo and a different value on real accounts | ASSUMPTION | MQL5 `ENUM_ACCOUNT_TRADE_MODE` | Read it on the Standard demo and on the cent account (read-only) | M2 | RISK-066 fixture-demo gate |
| A-65 | `metaeditor64.exe /compile:<file> /log:<file>` compiles headlessly and writes the error and warning counts to the log | ASSUMPTION | — | Run it on the M2 observer build | M2 | GUARDIAN_SAFETY_SPEC §13 build loop |

## 3. Parameters needing measurement

| ID | Item | Type | Resolution | When |
|---|---|---|---|---|
| A-40 | P-13 component A (absolute spread cap) | **BLOCKED** | ≥ 2 weeks of live/demo spread data by session hour | M2–M7 |
| A-41 | P-14 entry deviation | **BLOCKED** | Demo slippage distribution | M7 |
| A-42 | EXE-060 execution-quality thresholds | **BLOCKED** | Demo measurements + user approval | M7 |
| A-43 | Latency/slippage/reject priors in BT-023/024/028 | ASSUMPTION | Replaced by M7 empirical distributions | M7 |
| A-44 | Commission placeholder (0.5 × median spread per lot round trip) | ASSUMPTION | Replaced by A-08 | M7/M10 |
| A-45 | News blackout −30/+15 min (P-18) | ASSUMPTION (conservative) | Review after M9 with blackout-window performance | M9 |
| A-46 | `PROPOSED` engineering parameters (P-06, P-09..P-27, P-29, P-30, P-33, P-34) | APPROVED by the user 2026-11-13 as proposed (P-14 and P-13 component A stay BROKER_VERIFICATION_REQUIRED) | M0 question 2 | M0 |
| A-47 | Research thresholds A1–A10, applicability rules RES-023..026, promotion gate RISK-063, the RES-040 strategy-state transition defaults, and the market-intelligence defaults MI-042/MI-043 (minimum confluence, correlation groups) | APPROVED by the user 2026-11-13 as proposed | M0 question 3 | M0 |

## 4. External, legal, privacy, tooling

| ID | Statement | Type | Resolution | When |
|---|---|---|---|---|
| A-50 | Legality of offshore leveraged CFD trading and funding transfers for the user's residence (Bangladesh and/or Nepal) | **OPEN (user, Phase 0)** | User checks with a qualified local adviser. The pack makes no legal claim | before M10 |
| A-51 | Applicable data-protection law (OPEN-PRV-1) | OPEN | User | before M10 |
| A-52 | Record-retention rules for trading records (OPEN-PRV-2) | OPEN | User | before M10 |
| A-53 | MCP spec version 2026-07-28 is current | VERIFIED (at access date) | Re-check in M8 | M8 |
| A-54 | ECC command names (`/ecc:plan`, `/ecc:code-review`, …) match the installed version | ASSUMPTION | Session-start check (CLAUDE.md §4) | every session |
| A-55 | A tradeable edge exists for a simple gold strategy at this capital after costs | **UNKNOWN by design** | M6 verdicts | M6 |
| A-66 | A dashboard served on `127.0.0.1` may use the browser Notification API (loopback counts as a secure context) | ASSUMPTION | Test in the chosen desktop browser | M9 |
| A-67 | M1/M5 scalping (MI-053) can be traded at the cent minimum lot after spread: P-13 component C (spread ≤ 10% of the SL distance) and A10 leave enough trades | **UNKNOWN by design** | S0 feasibility spike, then the M6e A10 result | S0/M6e |
| A-68 | The SMC and candlestick rules in `MARKET_INTELLIGENCE_SPEC.md` §4 are engineering definitions; there is no single industry-standard definition, so results apply only to the rules as written | ASSUMPTION | None needed; every rule is documented and versioned (MI-012) | M6a |
| A-69 | The Fibonacci anchoring rules and the 33 chart-pattern geometries in `MARKET_INTELLIGENCE_SPEC.md` Part II are engineering definitions with research defaults; results apply only to the rules as written | ASSUMPTION | None needed; every rule is documented and versioned (MI-012) | M6c |
| A-70 | At the cent minimum lot the stops level, freeze level and spread leave room for trailing and break-even modifications at the MI-172 minimum step; partial exits are infeasible at the minimum volume | **UNKNOWN** | Measure stops and freeze levels and spread in S0 and M2 discovery; MI-174 records `PARTIAL_INFEASIBLE`; the MI-175 backtests use the measured values | S0/M6e |
| A-71 | TRADING_RISK_SPEC.md names no RiskEngine reason code for rejections by EXP-004, EXP-005, EXP-006, P-27, a trading state other than ACTIVE, or an unknown action type (RISK-002); `schemas/risk_decision.schema.json` has a closed enum and cannot record them (found in the M0b review) | RESOLVED 2026-11-13: the user approved `MARGIN_UTILISATION`, `FREE_MARGIN`, `STOP_OUT_DISTANCE`, `REWARD_RISK_BELOW_MIN`, `STATE_NOT_ACTIVE`, `UNKNOWN_ACTION` (CH-90) | User approves the code names as a spec change (TRADING_RISK_SPEC §11); no code is invented | M3 |
| A-72 | Whether `account_info().trade_allowed` reveals an investor (read-only) login: on the Exness demo server it stayed `True` after the user stated they re-logged with the investor password (S0, 2026-11-13) | **UNKNOWN** | Verify in M2 with a known investor login (and a known trading login) before any code relies on this flag for SEC read-only paths; until then a user statement is required and recorded | M2 |
| A-73 | FakeBroker behaviours taken from MT5 documentation, not from a spec (marked `# belief (GOV-003)` in `adapters/fake_broker.py`): order_check success retcode 0; history query dates read in server time; partial market fill recorded as ORDER_STATE_PARTIAL; last_error codes (-10005 timeout, -2 invalid params) and reset per call; SL/TP side checked against bid (BUY) / ask (SELL); market request without price accepted | **UNKNOWN** | Verify each against the real terminal in M2 (demo, read-only where possible); fix the fake where it differs | M2 |
| A-74 | FakeBroker does not simulate pending orders / TRADE_ACTION_REMOVE, freeze level (A-07), requotes/deviation, or terminal disconnects; scripted replies bypass validation | **OPEN** | Add before the M7 CANCEL_PENDING and chaos tests rely on them | M7 |
| A-75 | `goldbot doctor --offline` skips the NTP check and can exit 0, while RUNBOOK §3 step 14 says it passes with no failures. Assumed: an offline run never satisfies step 14 (SKIPPED is never PASS). Also: the DATA-005 env header form is the table `goldbot_meta(key='env')`; `fixture_demo: true` with env BACKTEST/REPLAY is not refused (the spec names LIVE only) | **ASSUMED** | User to confirm the RUNBOOK reading; spec owner to confirm the header form and the BACKTEST/REPLAY rule | M2 |

## 5. User decision register (D-01..D-12) — all decided 2026-11-13

Pending decisions are **never** filled in by Claude Code (CLAUDE.md §3.22). Until each is decided,
tests and fixture-demo runs (RISK-066) use labelled fixture values (TRADING_RISK_SPEC §2), and LIVE
entries stay blocked (RISK-005, RISK-065). Options and consequences are in the referenced sections.

| ID | Decision | Options | Consequences documented in | Blocks | Status |
|---|---|---|---|---|---|
| D-01 | Entry authorization mode (P-37). The user stated AUTO_ALL as the intended final mode on 2026-11-10; that is intent, not an approval (MI-162, RISK-092) | `MANUAL_APPROVAL` · `AUTO_ALL` · `AUTO_APPROVED_STRATEGIES`; optionally narrowed by schedule or conditions (RISK-067) | TRADING_RISK_SPEC §9 | LIVE entries; M9 scope; M10 | DECIDED 2026-11-13: `AUTO_ALL` |
| D-02 | Risk per trade (P-01) and strategy budgets (P-32) | Recommended 0.10–0.50% | TRADING_RISK_SPEC §2, CENT §6–7 | LIVE | DECIDED 2026-11-13: P-01 0.25%, P-32 0.25% |
| D-03 | Daily loss (P-02), weekly loss (P-03) and maximum drawdown (P-04) interventions | Ranges in §2 | TRADING_RISK_SPEC §2, §8 | LIVE; Guardian inputs | DECIDED 2026-11-13: P-02 1.00%, P-03 2.00%, P-04 5.00% |
| D-04 | Maximum aggregate open risk (P-31) and maximum simultaneous positions (P-05), unless set by a validated strategy within P-31 | Ranges in §2 | TRADING_RISK_SPEC RISK-015, EXP-008 | LIVE | DECIDED 2026-11-13: P-31 0.25% (one full-risk position at a time); P-05 follows the strategy within P-31 |
| D-05 | Daily profit-target behaviour (P-35) | none / stop entries / reduce risk | TRADING_RISK_SPEC §2 | Nothing (no behaviour until decided) | DECIDED 2026-11-13: none |
| D-06 | Consecutive-loss limits (P-07, P-08) and automatic risk reduction (P-36) | Ranges and options in §2; never an increase | TRADING_RISK_SPEC §2, §7 | LIVE | DECIDED 2026-11-13: P-07 3, P-08 5, P-36 none |
| D-07 | Trading style: scalping, intraday or swing | Swing **conflicts** with the confirmed no-overnight rule (RES-072) and would require changing that decision | STRATEGY_RESEARCH_SPEC RES-072/073; MARKET_INTELLIGENCE_SPEC MI-053 (scalping) | Strategy selection | DECIDED 2026-11-13: research both scalping and intraday; the edge verdict picks |
| D-08 | Initial strategy selection | From M0 proposals (RES-073), drawn from the MI-050 strategy families | STRATEGY_RESEARCH_SPEC §10 | M6 focus | DECIDED 2026-11-13: research candidate A (opening-range breakout and retest) first, then B, then C |
| D-09 | One strategy or several | Several requires P-31 sizing and, for switching, a prevalidated selector (RES-061) | STRATEGY_RESEARCH_SPEC §9 | M6/M9 | DECIDED 2026-11-13: several strategies, sharing the P-31 budget |
| D-10 | Rule-based, ML-assisted or hybrid | ML/hybrid = class C3 with purging, embargo and nested walk-forward (RES-023) | STRATEGY_RESEARCH_SPEC §5.1 | M6 scope | DECIDED 2026-11-13: rule-based only (no model in the signal path) |
| D-11 | May the system research new strategies? AI signal-generation permissions | An external AI service in the signal path conflicts with LLM-001/LLM-006; only a locally run, versioned, validated model (C3) is compatible | SYSTEM_ARCHITECTURE §9; STRATEGY_RESEARCH_SPEC §5.1 | M6/M8 | DECIDED 2026-11-13: the system may research and report new strategies (never deploys without approval); LLM disabled (P-28 = 0); no AI in signals |
| D-12 | Adaptive strategy-selection preferences | none / prevalidated selector (C4; MI-052, built in M6f) | STRATEGY_RESEARCH_SPEC RES-061 | Selector work | DECIDED 2026-11-13: prevalidated selector (C4, built and validated in M6f) |

**Verification tasks (not decisions):** Exness account confirmation, Standard Cent confirmation,
actual MT5 symbol, account currency and the Windows MT5 environment are all verified live in M2
(CENT-002..018). None of them is assumed.
