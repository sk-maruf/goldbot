# V2_VALIDATION_CHECKLIST — Cross-file audit results

> Audit date: 2026-11-08. Scope: every Markdown file in this pack. Method: automated checks (§2)
> plus a manual read of every file against the V2 command and the V1 audit findings (§4–§5).
> Items that cannot be resolved without the live broker account are **BLOCKED** and are not counted
> as resolved.

## 1. Method

1. Requirement-ID integrity: every ID referenced anywhere is defined exactly once.
2. Range checks for `P-xx`, `T#`, `GV`, `CGV`, `S#`, `TM`, `A-xx`, `CH`, `R` references.
3. File-reference resolution.
4. Markdown table integrity (column counts outside code fences).
5. Phrase scan for guarantee/cap/max-loss/"high win rate" language, with every hit reviewed in
   context.
6. Colour-contrast computation for every token against the worst-case backdrop.
7. Manual review against the V2 command's §3–§11 and the V1 audit findings.

## 2. Automated check results (final run)

| Check | Result |
|---|---|
| Requirement IDs | 293 defined, 293 referenced, **0 undefined** (4 found and fixed during the audit: CENT-020, RES-001, RES-002, RES-020) |
| Range references | 0 out of range after the tier rename (see §6, F-01) |
| File references | 0 missing |
| Table integrity | 0 column mismatches |
| Phrase scan | 31 hits. All are prohibitions, negations, verified broker facts (S2 news leverage cap), or unrelated uses ("capped at 128 characters"). One misleading input name fixed (F-02) |
| Traceability | Every defined ID appears in `REQUIREMENTS_TRACEABILITY.md`, with 207 marked CRITICAL. The table is generated from the spec text, so it cannot drift from it at generation time. Builders must regenerate it if specs change |

## 3. Contrast results (WCAG 2.2 AA: text ≥ 4.5:1) [S26]

Worst case = `surface-solid` over the darkest wash.

| Token | Light | Dark |
|---|---|---|
| text-primary | 16.83 | 12.80 |
| text-secondary | 7.60 | 6.53 |
| profit | 5.05 | 7.10 |
| loss | 4.88 | 6.38 |
| warning | 5.26 | 7.95 |
| critical | 6.28 | 6.38 |
| unknown (new) | 6.63 | 7.60 |
| Banners, white on env colour | live 6.57 · demo 4.75 · backtest 5.13 · replay 5.47 | — |

All pass. Design note: dark `critical` and `loss` share a colour, so the two are distinguished by
label and icon (UI-004).

## 4. Issue → fix map

### 4.1 Findings from the V1 review (earlier in this project)

| # | V1 finding | Status | Where fixed |
|---|---|---|---|
| V1-1 | The master prompt forbade coding while being meant to build the bot | RESOLVED | M0 (spec) + M1–M10 builder prompts |
| V1-2 | No UI specification | RESOLVED | UI_DESIGN_BRIEF V2; M4 design gate |
| V1-3 | "Demo first" impossible on Standard Cent [S1] | RESOLVED | CENT §8; CENT-040; M7 on Standard demo; M10 gate |
| V1-4 | Over-engineered for $100 | RESOLVED | SYSTEM §6/§8; backlog |
| V1-5 | Strategy selector not validated | RESOLVED | RES-060/061 |
| V1-6 | LLM role undefined | RESOLVED | LLM-001..005 |
| V1-7 | Mid-price backtests hide costs | RESOLVED | BACKTESTING_SPEC |
| V1-8 | Coding agent lacked OS/data/time/tests/DoD | RESOLVED | SYSTEM §7; TIME spec; M0 deliverables |
| V1-9 | Security gaps (auth, approvals, injection, audit) | RESOLVED (spec level) | SECURITY_THREAT_MODEL; API_SPEC |
| V1-10 | Leverage left to chance | RESOLVED | EXP-001..009 (+ the user sets leverage manually) |
| V1-11 | Legal risk ignored | RESOLVED as a gate; **legality itself UNRESOLVED** (user) | Phase 0; A-50 |
| V1-12 | "Powerful" / profit framing | RESOLVED | SYSTEM §1; README; RES-050 |

### 4.2 The V2 command's required corrections

| Item | Status | Evidence |
|---|---|---|
| A1 single RiskEngine authority | RESOLVED | RISK-001/002/003 |
| A2 all risk-increasing ops through it | RESOLVED | RISK-002; GV-21/22 |
| A3 Decimal | RESOLVED | RISK-020..023 |
| A4 conversion boundary (`Decimal(str(x))` style) | RESOLVED: V2 uses `Decimal(repr(x))`, which equals `str(x)` for floats in Python 3 and is the shortest round-trip form | RISK-020 |
| A5 tick/step/precision/money rounding | RESOLVED | RISK-022 |
| A6 volume down to step | RESOLVED | RISK-013 |
| A7 skip when min volume exceeds risk | RESOLVED | RISK-013; CENT-030 |
| A8 broker-confirmed SL | RESOLVED, with a **BLOCKED** part (SL-on-entry support A-31) | RISK-031; EXE-030/031 |
| A9 fail-closed list | RESOLVED | EXE-004; T7–T13 |
| A10 never assume a fill | RESOLVED | EXE-001 |
| B effective exposure and margin | RESOLVED | EXP-001..009 |
| C three emergency states with lifecycles | RESOLVED | EXECUTION_SAFETY_SPEC §8 |
| D Guardian independence spec | RESOLVED | GUARDIAN_SAFETY_SPEC |
| E clock architecture; MT5 time functions explained | RESOLVED; tick-time interpretation **BLOCKED** until M2 (A-22) | TIME_AND_CLOCK_SPEC |
| F execution realism and tier separation | RESOLVED; priors are ASSUMPTIONS until M7 | BACKTESTING_SPEC |
| G thresholds with purpose, limits, sample size, multiple testing; registry; purge/embargo; degradation; selector rule | RESOLVED | STRATEGY_RESEARCH_SPEC |
| H cent validation file; golden tests; illustrative labels; rejection reporting | RESOLVED; actual cent specs **BLOCKED** (A-05..A-08) | CENT_ACCOUNT_VALIDATION |
| I interventions ≠ guarantees | RESOLVED | RISK-040..042; banned-phrase review check |
| §4 security (credentials, API, threat model) | RESOLVED (spec) | SECURITY_THREAT_MODEL; API_SPEC |
| §4 privacy | RESOLVED (engineering); legal applicability **UNRESOLVED** (A-51/52) | PRIVACY_POLICY |
| §5 MCP | RESOLVED | MCP_SECURITY_SPEC |
| §6 UI/UX status layer | RESOLVED | UI_DESIGN_BRIEF §3–§6; OBS-001 |
| §7 milestone order M0–M10 with all 9 fields | RESOLVED | 01_MILESTONE_PROMPTS (M0 in 00_KICKOFF) |
| §8 file structure | RESOLVED + 2 added files (TIME_AND_CLOCK_SPEC, SOURCES) | README tree |
| §10 changelog + traceability | RESOLVED | V1_V2_CHANGELOG; REQUIREMENTS_TRACEABILITY |

## 5. Cross-file audit checklist (V2 command §11)

| Check | Result | Evidence |
|---|---|---|
| Contradictory risk limits | PASS: all numbers live in TRADING_RISK_SPEC §2; other files cite `P-xx` | grep of 0.25/1/2/5%, 1:200, 10 s, 60 s matched P-register values |
| Inconsistent account currency assumptions | PASS | CENT §1; RISK-023; CGV-02 |
| Incorrect cent lot calculations | PASS for the illustrative profile; real values BLOCKED (A-05/06) | §3.1 worked example; CGV-01/05/06 recomputed |
| Invalid MT5 API assumptions | PASS: function list checked against S9; no `TimeTradeServer` in Python; `order_calc_margin` ignoring positions handled | A-20..A-34 |
| Unsafe execution paths | PASS | RISK-001 type rule; EXE-011; review check A1 |
| Missing Guardian failure scenarios | PASS | GRD §2, §10, §12 |
| Incorrect timestamp handling | PASS (design); measurement BLOCKED in M2 | TIME-001..056 |
| Unrealistic backtesting assumptions | PASS: priors labelled; PROXY/PLACEHOLDER flags | BT-010, BT-022..029 |
| Unsupported statistical claims | PASS: §4 sample-size worked example; verdict INCONCLUSIVE exists | RES §4, §11 |
| Incomplete privacy controls | PASS (engineering) / OPEN (law) | PRV-*; A-51/52 |
| MCP privilege escalation | PASS | MCP-010/011; API-040 |
| Missing authorization checks | PASS | API-040 matrix; API-013 re-auth list |
| Inconsistent UI status definitions | PASS: terminology from SYSTEM §2 used in UI §5 and OBS §3 | UI-010..014 |
| Missing milestone dependencies | PASS | dependency graph in 01; GOV-001 |
| Missing acceptance criteria | PASS: every milestone has acceptance + failure conditions; every requirement has a traced criterion | 01; traceability |

## 6. Defects found and fixed during this audit

| # | Defect | Fix |
|---|---|---|
| F-01 | Performance tiers named T0–T3 collided with trading-state triggers T1–T19 (e.g. "T2" meant both demo results and the daily-loss trigger) | Tiers renamed **PT0–PT3** in all files |
| F-02 | Guardian input called "per-position max loss %" read like a guarantee | Renamed "emergency-SL loss %" |
| F-03 | 4 requirement IDs referenced but not defined | Defined: CENT-020, RES-001/002/020 |
| F-04 | `RISK-030` used for both the SL rule and manual recovery | Manual recovery is RISK-050; SL rule is RISK-030 |
| F-05 | CGV-05 threshold miscalculated ($2.43) | Recomputed: (25 − 3) / 10 = $2.20 |
| F-06 | Cross-references to BT-040 / RES-031 pointed to the wrong items | Re-pointed to BACKTESTING §7 and threshold A9 |
| F-07 | A pipe character inside a table cell broke a row | Rewritten |
| F-08 | The V1 claim that the 5% drawdown "caps pilot loss at about $5" | Rewritten as an intervention trigger with an explicit overshoot warning (M10, 03 prompt §6) |

## 7. Unresolved and BLOCKED (not counted as resolved)

- **BLOCKED until live data (M2/M7):** A-05..A-08 cent specs and commission; A-09 swap/swap-free;
  A-22 tick-time interpretation; A-29 common-path access; A-30 comment preservation; A-31 SL-on-entry;
  A-32 filling modes; A-40..A-42 spread cap, deviation, execution-quality thresholds.
- **Unreachable official sources this session:** S4 (Standard Cent article) and S5 (HMR article). The
  claims that depend on them are `REPORTED`.
- **OPEN (user):** A-46/A-47 parameter and threshold approval; A-50 legality (Phase 0); A-51/52
  privacy law and record retention; Q9 swap-free conditions.
- **Unknown by design:** A-55 whether any edge exists.

## 8. Evidence-based self-assessment (first V2 audit — superseded by §9.7)

Scale 1–10, where 10 = a specification a careful team could implement without guessing. Nothing
has been implemented, so no score reflects working software.

| Dimension | Score | Why not higher |
|---|---|---|
| Trading & quantitative research | 8 | Candidates are only sketched; thresholds are judgement calls (stated as such) |
| Risk management | 8 | Complete and consistent, but every number is unvalidated against the live account |
| MT5 integration | 7 | API facts verified; four behaviours still BLOCKED (A-22, A-30, A-31, A-32) |
| Standard Cent compatibility | 7 | Strong discovery process; actual cent specs unknown; Exness cent article unreachable |
| Execution realism | 7.5 | Model complete; latency/slippage/reject priors are assumptions until M7 |
| Guardian safety | 7.5 | Well bounded; HMAC hand-built in MQL5; file IPC adds moving parts; same-user malware residual |
| Security | 7.5 | Solid single-host model; residual host-compromise risk accepted rather than mitigated |
| Privacy | 7 | Engineering controls complete; applicable law unassessed |
| MCP architecture | 8 | Minimal, read-only, stdio; the network option is deliberately unbuilt |
| UI/UX | 7.5 | Truthfulness rules and contrast verified; no mockups exist yet |
| Software architecture | 8 | Clear boundaries and ADRs; two-process + Guardian complexity is the main cost |
| Testing | 7.5 | Test obligations defined per requirement; concrete test names are generated, not hand-written |
| Documentation | 8 | Automated checks pass; the pack is long, and traceability acceptance text is templated |
| Development readiness | 7 | M0–M1 can start now; M2+ depend on live data and user decisions |

## 9. Final V2 correction audit (2026-11-08, in place)

Scope: every Markdown file in this folder, after the targeted corrections listed in
`V1_V2_CHANGELOG.md` §3. Backup of the pre-correction state: the read-only sibling folder
`goldbot-prompt-pack-v2_BACKUP_pre-final-correction_2026-11-08/` (27 files, SHA-256 manifest kept).
**No V3 directory was created, and no file was renamed or removed.**

### 9.1 Automated checks (final run)

| Check | Result |
|---|---|
| Requirement IDs | 345 defined, 345 referenced, **0 undefined**, 0 undefined range endpoints |
| Range references | P-01..37, T1..27, GV-01..38, CGV-01..09, S1..39, TM-01..22, A-xx, CH-01..60, R-01..29, D-01..12: all in range. The only out-of-range token is "T0" in §6 F-01 of this file, which describes the old tier name |
| File references | 0 missing |
| Tables | 0 column mismatches (indented tables inside list items were checked by eye) |
| Phrase scan | 45 hits, all prohibitions, negations, broker facts, unrelated uses ("capped at 128 characters") or historical descriptions in this file. Every use of "protected"/"protects" is a prohibition or a conditional |
| Stale-term scan | No remaining `SEMI`/`AUTO` entry modes, `Panic` control or route, VPS/VPN options, HMAC key file or desktop/email notification defaults. The only mentions are explanations of what was removed (GRD-008, SYSTEM §2 "Emergency controls", the changelog and this checklist) |
| Traceability | Regenerated: 345 requirements (256 CRITICAL); statuses `IMPLEMENTATION_REQUIRED` 330, `BROKER_VERIFICATION_REQUIRED` 11, `DOCUMENTED` 4, `VERIFIED` 0; 12 decision items `USER_DECISION_REQUIRED` |

### 9.2 User decisions (§3 of the correction request) → where implemented

| Decision | Status | Where |
|---|---|---|
| 3.1 Entry authorization undecided; three modes; automatic closing | RESOLVED (documented, not chosen) | TRADING_RISK_SPEC §9, P-37, D-01, RISK-064/065, UI-032, API `/v1/mode` |
| 3.2 SL/TP management; position count by strategy and aggregate risk; prevalidated switching | RESOLVED | RISK-002/015/016/034, P-05/P-31/P-32, RES-061 |
| 3.3 Separate emergency operations with own rules; attempted ≠ confirmed | RESOLVED | EXECUTION_SAFETY_SPEC §8, EMG-001/010/020/030 |
| 3.4 Recovery classification matrix; manual for the listed failures | RESOLVED | TRADING_RISK_SPEC §7 (T1–T27), RISK-050..053, P-34 |
| 3.5 Per-strategy session envelope | RESOLVED | RES-070, RISK-017 |
| 3.6 News only for news-validated strategies; safe policy for bad data | RESOLVED | RISK-018, RES-071, TIME-042/043 |
| 3.7 No overnight/weekend holding with failure handling | RESOLVED | EXE-080..086, GRD-028, BT-034, P-19/P-33 |
| 3.8 Local Windows only; AI/MCP independence | RESOLVED | SYSTEM §7, ADR-013, LLM-006, API-002, SEC-011 |
| 3.9 MCP non-trading admin actions with full controls; no execution | RESOLVED | MCP §3, §4.1, MCP-016, MCP-020..030 |
| 3.10 AI data sharing | RESOLVED | PRV-020..026 |
| 3.11 Dashboard-only notifications | RESOLVED | OBS-020/023 |
| 3.12 Three distinct dashboard controls, no combined button | RESOLVED | UI-030, EMG-010, API routes |

### 9.3 Critical corrections (§4) → fix map

| # | Issue | Status | Evidence |
|---|---|---|---|
| 4.1 | Guardian emergency SL could exceed its budget | RESOLVED | GRD-020 (budget-first, `OrderCalcProfit` [S38], never widened, close policy, escalation); GRD-002 inputs; tests in GRD §12 |
| 4.2 | Keyring vs `guardian.key` contradiction | RESOLVED | GRD-008 decision table (no secret; integrity + ACL; lifecycle rows; residual risk); ADR-011; SEC-001 scope statement |
| 4.3 | Idempotency and duplicate submission | RESOLVED | EXE-002, EXE §2 state machine, EXE-013..015; MT5 has no native key [S35] |
| 4.4 | Directional SL/TP rounding | RESOLVED | RISK-022 (OFF_TICK default), RISK-025 (opt-in procedure), GV-31/32 |
| 4.5 | PBO / sensitivity / rule-based contradiction | RESOLVED | RES-023..027 with classes C1–C4 and the applicability matrix |
| 4.6 | Deposit compared with current balance | RESOLVED | CENT-002/016, CGV-07/09 |
| 4.7 | Emergency retry deadline | RESOLVED | P-25 (worst case 40 s ≤ 60 s), EMG-020, `FAILED_DEADLINE` |
| 4.8 | MCP client identity | RESOLVED, with stated limits | MCP-021..024, MCP-022 same-user limits, TM-03 residual |
| 4.9 | Salt and deletion lifecycle | RESOLVED (engineering); legal applicability OPEN | PRV-012..014, PRV-030; A-51/52 |
| 4.10 | UI safety messaging | RESOLVED | UI-015/016, state catalogue, OBS health rows, FAILED state |

### 9.4 §5 additional improvements and §7 invariants

§5 A (risk engine items) → RISK-005/010/015/016/017, EXP-001..009, T2–T6, CENT-030; B → EXE-080..086;
C → BT-020..035; D → CENT-001..020; E → RES-060/061; F → LLM-006, PRV-026.

| §7 invariant | Enforcing requirement(s) |
|---|---|
| 1–4 No martingale / grid / averaging down / size increase to recover | TRADING_RISK_SPEC §10; RISK-013; P-36 "never an increase"; CLAUDE §3.13 |
| 5 No duplicate submission after ambiguous responses | EXE-002, EXE-013..015 |
| 6 No order without RiskEngine approval | RISK-001 |
| 7 No trading on stale/invalid data | EXE-004, TIME-020..022, GV-09 |
| 8 No silent SL/TP distance changes | RISK-022/025/034 |
| 9 No Guardian action beyond approved risk | GRD-020, GRD-013 |
| 10 No autonomous risk-limit changes | RISK-090..092 |
| 11 No MCP order execution | MCP-010/011 |
| 12 No credentials in code or ordinary config | SEC-001, DATA config row, GRD-008 |
| 13 Liquidation not assumed | EMG-001, UI-013 |
| 14 SL does not guarantee maximum loss | RISK-040, UI-015 |
| 15 No automatic recovery from critical failures | RISK-053 |
| 16 No overnight/weekend holding | EXE-080..086 |
| 17 No trading with incomplete reconciliation | EXE-004, T7/T8/T20, UI-012 |
| 18 No external AI dependency for safety | LLM-006 |

### 9.5 Defects found and fixed during this pass

| # | Defect | Fix |
|---|---|---|
| F-09 | New assumption rows were written with 6 columns in a 7-column table | Rewritten with a Source column |
| F-10 | Stale ranges after the extensions (T1–T19, P-01…P-30, GV-01..30) in 5 files | Updated to T1–T27, P-01…P-37, GV-01..38 |
| F-11 | HC-4 did not cover a latched Guardian, so automatic recovery could proceed while the Guardian still required re-arm | HC-4 now requires the Guardian kill flag to be clear |
| F-12 | Leftover HMAC references (architecture B3, data stores, privacy classes) contradicted GRD-008 | Replaced with integrity + ACL wording |
| F-13 | Kickoff still asked for 10 ADRs and "SPECIFIED" statuses | 13 ADRs; new status vocabulary |
| F-14 | Two decision items had no linked requirements | Linked manually (D-05, D-06, D-08, D-09) |

### 9.6 Remaining blockers before development

- **None block M0–M1.** M2 onward needs read-only access to the actual account.
- **Broker verification (M2/M7):** A-05..A-09, A-22, A-29..A-32, A-40..A-42, A-56, A-61, A-62.
- **User decisions:** D-01..D-12 (block DEMO/LIVE entries, not development); M0 questions 1–9.
- **External:** Phase 0 legality and eligibility (A-50); privacy law and record retention (A-51/52);
  Exness help pages S4/S5 were unreachable twice, so those claims remain REPORTED.

### 9.7 Evidence-based scores after the final correction (specification quality; nothing is built)

| Area | Score | Evidence and limits |
|---|---|---|
| Trading research | 8 | Classes, applicability and N/A rules remove the contradiction; strategies remain undecided by design |
| Risk management | 8.5 | Single register with decision statuses, aggregate risk, recovery matrix; every value still unapproved |
| Execution safety | 8.5 | Explicit state machine, deadline-bounded emergencies, no-overnight handling; comment preservation and SL-on-entry still BLOCKED |
| Guardian EA | 8 | Budget-first SL, no-secret channel, user re-arm, backstop; same-user malware residual; several MQL5 behaviours (A-61/62) unverified |
| Standard Cent compatibility | 7.5 | MT5-only class derivation, balance-operation corroboration; actual specs unknown; two Exness pages unreachable |
| MT5 integration | 7.5 | New facts verified (S35–S38); four platform behaviours still BLOCKED |
| Security | 8 | Honest keyring scope, compromise response, local-only; host compromise accepted, not mitigated |
| Privacy | 7.5 | Salt lifecycle, audit-safe deletion, AI sharing rules; law unassessed |
| MCP | 8 | Per-client scopes, human-approved admin actions, stated identity limits |
| UI/UX | 8 | Truthful SL and status vocabulary, three distinct controls; still no mockups |
| Architecture | 8.5 | Preserved V2 structure; 3 new ADRs; local-only boundary clarified |
| Testing | 7.5 | Test obligations expanded (GV-31..38, CGV-09, chaos, Guardian); test names are still generated templates |
| Development readiness | 7.5 | M0–M6 can proceed on fixtures; DEMO/LIVE correctly blocked by pending decisions |

**Recommendation: CONDITIONAL GO** for M0 onward (documentation baseline, build, backtest, demo once
D-01 and the risk values are decided). **NO-GO for live money** until Phase 0 is cleared, D-01..D-06 are
approved, the broker-verification items affecting money handling are resolved, and the M10
release-readiness verdict is GO.

## V2.1 patch note (2026-11-08)

This audit describes V2. The V2.1 patch (`V1_V2_CHANGELOG.md` §4) adds RISK-066, RISK-067, OBS-024,
GV-39..41, A-64..66, R-30, CH-61..67, review checks 38–39 and `prompts/00b_FEASIBILITY_SPIKE_PROMPT.md`.
Each new requirement ID has a row in `REQUIREMENTS_TRACEABILITY.md`. The automated checks in §2 were
not re-run as a full audit. The patch was checked for: every edit applied exactly once, every new ID
defined once and traced, and no new table column mismatch.

## V2.1 intelligence merge note (2026-11-08)

The intelligence merge (`V1_V2_CHANGELOG.md` §5) adds `specifications/MARKET_INTELLIGENCE_SPEC.md`
(MI-001..MI-093), invariant 23, milestone parts M6a–M6d, A-67/68, R-31/32, CH-68..73 and review
checks 40–43. Checked for this merge: every edit applied exactly once (scripted, one match
required per edit); every MI ID defined once and traced in `REQUIREMENTS_TRACEABILITY.md`; every
MI ID referenced anywhere is defined; every file reference to the new spec resolves; no table
column mismatch in an edited file; the P-01..P-37 register is byte-identical to the pre-merge
pack; Appendix A equals the supplied brief. The full §2 audit was not re-run.

Readiness fixes (2026-11-08, CH-74/75): `.claude/settings.json` blocks the MT5 MCP order tools;
MI-015 defines DEGRADED; M6 TIME references corrected. The same scripted checks were re-run.

V2.2 upgrade (2026-11-10, CH-76..82): MI-100..MI-199, the Phase A review, parts M6a–M6f, A-69/70,
R-33/34 and review checks 44–47. The same scripted checks were re-run; the full §2 audit was not.
