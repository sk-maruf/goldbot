# DEFINITION OF DONE — GoldBot

> A milestone part is `DONE` only when the shared checklist (§1) **and** its own block (§3) are
> complete. The criteria in §3 are copied verbatim from `prompts/00_KICKOFF_PROMPT.md` §0 and §7,
> `prompts/00b_FEASIBILITY_SPIKE_PROMPT.md` and `prompts/01_MILESTONE_PROMPTS.md` (extracted by
> script in M0c, 2026-11-13, and split on `;` into checklist items with the words unchanged). If a
> prompt and this file disagree, the prompt wins and this file is corrected.

## 1. Shared checklist (every milestone part)

- [ ] **GOV-001** The session started by reading `docs/STATUS.md`; every dependency is `DONE` with an `APPROVE` review (a part in `WAITING_ON_TIME` is not `DONE`).
- [ ] Plan mode: files, tests first (by requirement ID), assumptions and BLOCKED items listed, and the plan approved by the user before code.
- [ ] **Tests first (TDD):** the required tests of the block were written and seen failing before the implementation. Test names follow `docs/TEST_PLAN.md`.
- [ ] Every **Required test** of the block passes, and no **Failure condition** of the block occurred.
- [ ] Tests, lint and types green: `uv run pytest -q -m "not mt5"` (plus `uv run pytest -q -m mt5` where the part needs the Windows host), `uv run ruff check . && uv run pyright`, and `pnpm --dir web test && pnpm --dir web e2e` when `web/` changed.
- [ ] The coverage targets of `docs/TEST_PLAN.md` §1 that apply to the code touched are met.
- [ ] **GOV-002** No test was weakened, skipped or deleted to pass. No requirement is `VERIFIED` without a passing test or a recorded run (commit + run reference in `docs/STATUS.md`). A `[HUMAN]` test passes only with its evidence.
- [ ] **GOV-003/004** Unknowns are recorded `BLOCKED` in `quality/ASSUMPTIONS_AND_UNKNOWNS.md` with the exact information needed; terminology follows `SYSTEM_ARCHITECTURE.md` §2.
- [ ] **Independent review** with `prompts/02_ADVERSARIAL_REVIEW_PROMPT.md` by a fresh subagent that wrote none of the code: verdict `APPROVE` recorded in `docs/STATUS.md`.
- [ ] **Security review:** ECC `security-reviewer` / `ecc:security-review`, then the built-in `/security-review`; every finding tracked to closure.
- [ ] `docs/STATUS.md`, `CHANGELOG.md` and the traceability statuses updated with evidence; `python tools/gen_test_plan.py --check` passes.
- [ ] The report lists the skills that actually ran, spec deviations, and "HOW COULD THIS FAIL?" for the part (01 prompt, preamble step 7).
- [ ] Commit tagged (`mN-done`, or `m7a-done` for a part) only after the `APPROVE` verdict. Then stop.

A part whose acceptance needs elapsed time ends its session `WAITING_ON_TIME` in `docs/STATUS.md`
(what runs, when it started, the exact end condition); it is not `DONE` until a later session
checks that condition. A milestone with parts is `DONE` only when every part is (only M6f may be
`NOT_APPLICABLE`). The 01 prompt states acceptance criteria per milestone; for M2, M7 and M9 they
are checked in the last part, and the earlier parts finish on the shared checklist.

## 2. User decisions of 2026-11-13 that change scope

Source: `docs/STATUS.md` §8–§10. Claude Code chose none of them. Each note is repeated in the block
it affects.

| Decision | Effect | Blocks |
| --- | --- | --- |
| D-01 `AUTO_ALL` | The entry mode to integrate, test and pilot; M10 still recommends `MANUAL_APPROVAL` for the first 4 weeks and the user decides | M3, M9a, M10 |
| D-02..D-06 values | Equal to the fixture column; tests keep fixture parameters (RISK-005) | M3, M7a |
| D-07 scalping and intraday | Both researched; the edge verdict picks | M6e |
| D-08 initial strategy | **PENDING**: M6e uses the M0 candidates until decided | M6e |
| D-09 several strategies | They share P-31 = 0.25%: at most one full-risk position open | M6e, M9a |
| D-10 rule-based only | No ML or other model in the signal path | M6e, M9a |
| D-11 research yes; LLM disabled (P-28 = 0) | M8 builds no LLM integration beyond the disabled payload builder; no AI in signals | M6e, M8 |
| D-12 prevalidated C4 selector | M6f is built if at least two strategies PASS in M6e | M6f |
| Q1 dark and light themes | Both themes in M4, dark first | M4 |
| Q5 MCP | In scope for M8: 9 read tools + 3 admin actions, each approved per invocation (MCP-030) | M8 |

## 3. Blocks per milestone part

### M0a

**Part (verbatim):** Does §1–§4.

**Acceptance (kickoff §0 "Ends when", verbatim):**

- [ ] the contradiction report, the tooling list, the re-verification results, the §4 answers and the D-01..D-12 register (answers or `STILL PENDING`) are recorded in `docs/STATUS.md`

### M0b

**Part (verbatim):** Does the §5 rows marked **b**.

**Acceptance (kickoff §0 "Ends when", verbatim):**

- [ ] those files exist and every schema validates (`check-jsonschema`)

### M0c

**Part (verbatim):** Does the §5 rows marked **c**, then §6–§7.

**Acceptance (kickoff §0 "Ends when", verbatim):**

- [ ] every §5 file exists and the spec-mode review verdict is recorded in `docs/STATUS.md`

**M0 as a whole (kickoff §7, verbatim), checked at the end of M0c:**

- [ ] each part met its end condition (§0)
- [ ] every file in §5 exists
- [ ] every schema validates (`check-jsonschema`)
- [ ] no `P-xx` value differs from `TRADING_RISK_SPEC.md` unless the user changed it and the change is logged
- [ ] no USER_DECISION_REQUIRED item is marked approved without the user's explicit statement in this session
- [ ] the spec-mode adversarial review verdict is APPROVE or APPROVE WITH FIXES (all fixes applied)
- [ ] no requirement in the traceability matrix is left without a planned verification method.

### S0 — Feasibility spike (advisory, gates nothing)

**Acceptance (00b "Done when", verbatim):**

- [ ] every candidate has all five numbers at all three risk levels, or a stated reason why a number could not be computed.

### M1 — Project foundation and development environment

**Acceptance (01 prompt, verbatim):**

- [ ] CI green on both OSes
- [ ] ≥ 95% branch coverage on `core/money.py` and `core/convert.py`
- [ ] `goldbot doctor` passes on the dev machine
- [ ] no secrets in the repo (gitleaks clean).

### M2a — Read-only MT5 and discovery

**Part (verbatim):** **M2a** builds and tests everything below.

("Everything below" is the M2 Scope / deliverables list in the 01 prompt.) Done = the shared checklist with every M2 **Required test** passing; the M2 acceptance is checked in M2b.

**2026-11-13 decisions:** The user states the account is swap-free; M2 verifies it from MT5 (A-09; STATUS §9 Q6). M2 creates `config/session_exceptions.yaml`, which the user maintains (STATUS §9 Q7).

### M2b — 24 h soak and acceptance check

**Part (verbatim):** **M2b** is the 24 h observer-heartbeat soak (`WAITING_ON_TIME`), followed by the acceptance check.

**Acceptance (01 prompt, M2, verbatim):**

- [ ] `VERIFIED_SPECS.md` contains all CENT-004 fields for the chosen symbol(s)
- [ ] TIME-005 result recorded with median and IQR
- [ ] every CENT-010..018 check PASS or explicitly BLOCKED with a reason
- [ ] the observer Guardian heartbeat has run continuously for 24 h with zero integrity failures.

### M3 — Deterministic financial calculations and RiskEngine

**Acceptance (01 prompt, verbatim):**

- [ ] 100% branch coverage on `risk_engine.py`, `sizing.py`, `exposure.py`, `trading_state.py`
- [ ] mutation-testing spot check (e.g. `mutmut` on `sizing.py`) with no surviving mutants in the rounding/rejection branches
- [ ] worked example `TRADING_RISK_SPEC` §3.1 reproduced exactly.

**2026-11-13 decisions:** D-01..D-06 decided (`AUTO_ALL`; P-01 0.25%, P-32 0.25%, P-02 1.00%, P-03 2.00%, P-04 5.00%, P-31 0.25%, P-07 3, P-08 5, P-35 and P-36 none). The values equal the fixture column, so the golden vectors need no recomputation (STATUS §8). The M3 tests still use fixture parameters only. P-14 and P-13 component A still wait for broker data (STATUS §9 Q2).

### M4 — Dashboard and monitoring interface (read-only)

**Acceptance (01 prompt, verbatim):**

- [ ] the user approved the design gate
- [ ] all tests green
- [ ] 60 fps profile attached
- [ ] ≤ 3 blur layers verified by test.

**2026-11-13 decisions:** React + TypeScript SPA on loopback with **dark and light themes, dark first** (ADR-005 Accepted; STATUS §9 Q1 and §10). The design gate starts from the Inspiration direction (STATUS §10).

### M5 — Historical data and realistic backtesting

**Acceptance (01 prompt, verbatim):**

- [ ] all tests green
- [ ] reports always show the tier label
- [ ] a PT0 number never appears outside its appendix (test).

### M6a — Intelligence foundation

**Part (verbatim):** first the architecture impact report `docs/intelligence/ARCHITECTURE_IMPACT.md` (MI-090), then **wait for user approval**. Then the `Evidence` contract (MI-010..012), bar and timeframe utilities (MI-016), the future-truncation harness (MI-013/014), data-quality and module-health handling (MI-015/018), and the Candle Behavior, Candlestick (MI-031/032), Liquidity and Smart Money Concepts (MI-030) modules, each documented in `docs/intelligence/<module>.md` (MI-012).

**Acceptance (01 prompt, M6, verbatim):**

- [ ] all tests green
- [ ] ≥ 95% branch coverage on `src/goldbot/intelligence/`
- [ ] zero future-truncation differences
- [ ] every MARKET_INTELLIGENCE_SPEC §4 concept documented (MI-012).

### M6b — Intelligence completion

**Part (verbatim):** the Trend, Market Regime (MI-035), Multi-Timeframe Confluence (MI-034), Live Market Perception (MI-020 module 7, MI-021) and Early Reversal (MI-033) modules; the decision engine (MI-040..047); `DecisionRecord` persistence for the backtester and the research store (MI-045).

**Acceptance (01 prompt, M6, verbatim):**

- [ ] all tests green
- [ ] ≥ 95% branch coverage on `src/goldbot/intelligence/`
- [ ] zero future-truncation differences
- [ ] every MARKET_INTELLIGENCE_SPEC §4 concept documented (MI-012).

### M6c — V2.2 analysis modules (Phases B–D)

**Part (verbatim):** the Fibonacci (MI-110..118) and Chart Pattern (MI-120..123) modules, the module 4 price-action extension (MI-130) and the module 8 liquidity upgrade (MI-140), each with `docs/intelligence/<module>.md` (MI-012). First update `docs/intelligence/ARCHITECTURE_IMPACT.md` for V2.2 against the real repository (MI-090) and **wait for user approval**.

**Acceptance (01 prompt, M6, verbatim):**

- [ ] the same coverage and truncation bars for the V2.2 code
- [ ] every Part II concept documented
- [ ] `docs/STATUS.md` records each phase's spec IDs, tests, review, traceability and a PASS / FAIL / INCONCLUSIVE verdict (MI-199).

### M6d — V2.2 setups and management (Phases E–H, pure parts)

**Part (verbatim):** setup fields, evidence categories and display ranking (MI-150..157); the lifecycle record (MI-160..162); the trailing methods, net-of-cost break-even and partial-exit feasibility (MI-170..174); exit evaluation (MI-180..185); timeframe roles and market-condition gates (MI-190..192); the additive migrations with down-migrations (MI-101). Nothing here sends an order: live wiring is M9a.

**Acceptance (01 prompt, M6, verbatim):**

- [ ] the same coverage and truncation bars for the V2.2 code
- [ ] every Part II concept documented
- [ ] `docs/STATUS.md` records each phase's spec IDs, tests, review, traceability and a PASS / FAIL / INCONCLUSIVE verdict (MI-199).

### M6e — Strategy research

**Part (verbatim):** the scope below, applied to the strategy families the user selected in D-08 (MI-050, MI-053 for scalping), each implemented on the intelligence layer behind the one `Strategy` interface. While D-08 is pending, the M0 candidates (RES-073) are used. V2.2: the BASELINE versus UPGRADED comparison (MI-196, MI-197), the trailing-method backtests (MI-175) and the pattern outcome statistics (MI-123).

**Acceptance (01 prompt, M6, verbatim):**

- [ ] each candidate has a committed pre-registration that predates its OOS run (git timestamps)
- [ ] each has a verdict
- [ ] the A10 rejection rate is reported
- [ ] the MI-196 BASELINE versus UPGRADED report exists for every UPGRADED family. **"No candidate passed" is an acceptable, successful outcome.**

**2026-11-13 decisions:** D-07: research both scalping and intraday; the edge verdict picks. D-10: **rule-based only**, no model in the signal path. D-11: the system may research and report new strategies but never deploys one without the user's approval; no AI in signals. D-09: several strategies share the P-31 budget. **D-08 is still pending**: the M0 candidates (RES-073) are used until the user decides.

### M6f — Strategy selector (conditional)

**Part (verbatim):** only if the user chose a selector in D-12 **and** at least two strategies PASS in M6e: a C4 selector (MI-052, RES-061) with its own pre-registration, version and verdict. Otherwise record `M6f NOT_APPLICABLE (<reason>)` in `docs/STATUS.md`. M6 is `DONE` when M6a–M6e are `DONE` with APPROVE and M6f is `DONE` or `NOT_APPLICABLE`. If the condition becomes true later, M6f runs then, and no selector trades before its PASS.

**Acceptance (01 prompt, M6, verbatim):**

- [ ] the selector has a verdict, or the part is `NOT_APPLICABLE` with its reason.

**2026-11-13 decisions:** D-12 decided: a prevalidated selector (C4). M6f is therefore built when at least two strategies PASS in M6e; otherwise it is recorded `NOT_APPLICABLE (<reason>)`.

M6 is `DONE` when M6a–M6e are `DONE` with APPROVE and M6f is `DONE` or `NOT_APPLICABLE` (01 prompt).

### M7a — Engine execution against FakeBroker

**Part (verbatim):** order lifecycle, request construction, retcodes, SL verification, partial fills, reconciler, emergency controller, restart sequence, the `op_id` state machine, the failure classification and recovery engine, session-end closing and the three dashboard emergency controls, with every chaos test FakeBroker can drive.

Done = the shared checklist with every **Required test** this part can run passing; the M7 acceptance is checked in M7c.

**2026-11-13 decisions:** Whether a run is fixture demo follows RISK-005/RISK-066: P-14 and P-13 component A are not approved yet (broker data), and P-14 and the EXE-060 thresholds are set in M7 with the user's approval.

### M7b — Guardian EA

**Part (verbatim):** the full Guardian on top of the M2 observer, built and tested with the loop in GUARDIAN_SAFETY_SPEC §13, including its `[HUMAN]` steps.

Done = the shared checklist with every **Required test** this part can run passing; the M7 acceptance is checked in M7c.

### M7c — Standard-demo soak

**Part (verbatim):** (after M7a and M7b): the demo measurements below, the 20 round trips, the demo chaos and Guardian scenarios, and the 5 demo trading days (`WAITING_ON_TIME` while they run).

**Acceptance (01 prompt, M7, verbatim):**

- [ ] all chaos and Guardian scenarios pass with evidence
- [ ] zero unexplained reconciliation mismatches over 5 demo trading days
- [ ] measured distributions recorded in `docs/VERIFIED_SPECS.md`.

### M8 — Security, privacy and MCP integration

**Acceptance (01 prompt, verbatim):**

- [ ] ECC `security-reviewer` and `/security-review` have no unresolved HIGH findings
- [ ] the threat-register residual risks are reviewed and accepted by the user in writing.

**2026-11-13 decisions:** LLM **disabled completely** (D-11, P-28 = 0; STATUS §9 Q4): M8 builds the LLM payload builder only as the block requires it, disabled by default, and no further LLM integration. MCP is **in scope**: stdio, the 9 read tools and the 3 admin actions, each admin action approved per invocation (MCP-030; STATUS §9 Q5).

### M9a — Integration

**Part (verbatim):** **M9a** integration: the approval flow and its notifications, the modes and any narrowing rules, the degradation monitor, the intelligence layer in the live path with its Intelligence screen (MI-081), the V2.2 lifecycle record, trailing and exit evaluation wired through the existing position manager and RiskEngine (MI-160, MI-172, MI-180) and the ten V2.2 views (MI-195), REPLAY parity and the required tests.

Done = the shared checklist with the M9 **Required tests** passing; the M9 acceptance is checked in M9b.

**2026-11-13 decisions:** D-01 decided: `AUTO_ALL`. M9a integrates and tests that mode; the fixture-demo test of all three modes applies only while D-01 is pending. With P-31 = P-01 = 0.25%, at most one full-risk position is open at a time even with several strategies (STATUS §8). Rule-based only (D-10).

### M9b — Forward test

**Part (verbatim):** **M9b** the forward test (`WAITING_ON_TIME` until ≥ 8 weeks and ≥ 50 trades), then the forward-test report, the OBS §5 targets and the system-mode adversarial review.

**Acceptance (01 prompt, M9, verbatim):**

- [ ] `docs/research/forward_test_report.md` states, with numbers and tier labels, whether the promotion gate (RISK-063) passed
- [ ] OBS §5 targets met
- [ ] the adversarial review verdict is APPROVE.

### M10 — Standard Cent pilot readiness assessment

**Acceptance (01 prompt, verbatim):**

- [ ] the user's written GO in chat, recorded in `docs/STATUS.md`, **before** any live order.

**Dependencies (01 prompt, verbatim):** M9 APPROVE; `docs/PHASE0_CLEARANCE.md` = `STATUS: CLEARED`; every USER_DECISION_REQUIRED parameter approved (RISK-005) and D-01 decided. If any is missing, **stop** and write the reason in `docs/STATUS.md`.

**2026-11-13 decisions:** D-01 = `AUTO_ALL`. The readiness review still *recommends* `MANUAL_APPROVAL` for the first 4 weeks of the pilot, and the user decides (block text). `docs/PHASE0_CLEARANCE.md` stays `NOT CLEARED` until the user signs it (STATUS §9 Q8).
