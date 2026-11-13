# STATUS — GoldBot

> Read this first in every session (GOV-001). Updated at the end of every milestone part.
> Last update: 2026-11-10, end of M0a. Nothing is built, connected to a broker, or `VERIFIED`.

## 1. Milestones

A part may start only when every dependency is `DONE` with an `APPROVE` review (GOV-001;
dependency order in `prompts/01_MILESTONE_PROMPTS.md`). The M0 review runs once, in M0c (kickoff §6).

| Part | Status | Review verdict | Date |
| --- | --- | --- | --- |
| M0a Read, contradictions, tooling, re-verification, decisions | DONE | at M0c | 2026-11-10 |
| M0b ADRs, schemas, config examples | DONE | at M0c (part review APPROVE WITH FIXES, fixes applied) | 2026-11-13 |
| M0c UI spec, candidates, test plan, runbook, DoD, Phase 0, backlog, review | NOT STARTED | | |
| S0 Feasibility spike (advisory, gates nothing) | NOT STARTED | n/a | |
| M1 Foundation | NOT STARTED | | |
| M2a Read-only MT5 and discovery · M2b 24 h soak | NOT STARTED | | |
| M3 Decimal and RiskEngine | NOT STARTED | | |
| M4 Dashboard (read-only) | NOT STARTED | | |
| M5 Data and backtester | NOT STARTED | | |
| M6a · M6b · M6c · M6d · M6e · M6f (conditional) | NOT STARTED | | |
| M7a Execution on FakeBroker · M7b Guardian · M7c demo soak | NOT STARTED | | |
| M8 Security, privacy, MCP | NOT STARTED | | |
| M9a Integration · M9b forward test | NOT STARTED | | |
| M10 Cent pilot readiness | NOT STARTED | | |

## 2. Standing authorization (user, 2026-11-10)

The user said in chat: the prompts are for building an autonomous trading bot; work in auto mode
with full access to this folder; take the dashboard look from the inspiration image and improvise.
The user then approved the M0 plan that states the following.

- **Granted:** no stop for approval between M0a, M0b and M0c; file edits, git commits and shell
  commands inside `C:\GoldBot` without asking; the contradiction fixes in §4; pack defaults for
  unanswered kickoff questions, each marked `DEFAULT — not confirmed by user`.
- **Not granted, and not grantable by a general instruction** (CLAUDE.md §3.17, §3.22, GOV-001/002):
  choosing D-01..D-12 or any risk value; any live or real-money order; use of a trading password;
  skipping a milestone review. One stop remains at the end of M0 for the user's approval (kickoff §7).

## 3. M0a §1 summary

- **System boundary:** one local Windows computer running the MT5 terminal, the Guardian EA, the
  Python engine, the loopback API and the dashboard. The only outside party on the order path is the
  Exness trade server. LLM and MCP are optional and never on that path.
- **Five most safety-critical requirements:** RISK-001 (only the RiskEngine authorises); RISK-013
  (volume rounds down, a minimum lot over budget is skipped); RISK-031 with EXE-031 (every stop-loss
  broker-confirmed by read-back); EXE-002 with EXE-013 (no resubmission while an operation is
  UNKNOWN); EXE-004 (fail closed on stale data, failed queries, unclean reconciliation or an
  unhealthy Guardian).
- **Contradictions:** five found, all fixed with the user's approval (§4).

## 4. Contradiction report

All fixes are logged in `quality/V1_V2_CHANGELOG.md` §7. No `P-xx` value changed.

| # | Conflict | Outcome |
| --- | --- | --- |
| X1 | Emergency-action lifecycle states: SYSTEM_ARCHITECTURE §2 vs EXECUTION_SAFETY_SPEC §8 | FIXED (CH-83): §2 uses the §8 states |
| X2 | `op_id` vs `intent_id` for the idempotency ID | FIXED (CH-84): `op_id` everywhere |
| X3 | CRITICAL trigger set: OBS-011 vs TRADING_RISK_SPEC §7 | FIXED (CH-85): OBS-011 is the stricter union; §7 untouched |
| X4 | SEC-022 off-box audit export vs PRIVACY_POLICY §5 (off by default) | FIXED (CH-86): local export; TM-13 residual restated |
| X5 | TIME-030 "P-20 cadence" vs GRD-011 (Guardian heartbeat 5 s) | FIXED (CH-87): wording only |
| — | Seven stale references and labels | FIXED (CH-88) |

**OPEN, for the user (not edited because it touches the Guardian check):**

- `prompts/03_RELEASE_READINESS_PROMPT.md` §3 says Guardian inputs equal to or tighter than
  P-02/P-04/P-05. GRD-013, the README and M10 say P-02/P-04/P-05/P-32. Add P-32 to the 03 prompt?

**Observations carried to the M0c review ("How could this system fail?"), no edit made:**

- EXE-020: the comment tag is the first 10 base32 characters of a UUIDv7, which is its millisecond
  timestamp plus 2 bits, so it carries almost no random bits.
- GRD-050: the emergency lease is 30 s, an emergency run can last 60 s (P-25), and renewal is unstated.
- `C1–C4` names data classes, strategy classes and (as C1–C5) clocks.
- `OUTSIDE_ENVELOPE` (MI-041) and `OUTSIDE_STRATEGY_ENVELOPE` (RISK-017) are near-duplicate codes.
- RES-040 says its degradation defaults are "user-approved in M0", but kickoff question 3 omits them.
- The traceability matrix has no generator script in the repo; rows quoting changed text were edited
  by hand (DATA-002, OBS-010, OBS-011, SEC-022, TIME-030, CENT-005, PRV-010).

## 5. Tooling found in this session (kickoff §2)

- ECC: installed (`/ecc:plan`, `/ecc:code-review`, `ecc:security-review`, `ecc:tdd-workflow`; agents
  `ecc:planner`, `ecc:architect`, `ecc:code-reviewer`, `ecc:security-reviewer`, `ecc:tdd-guide`,
  `ecc:build-error-resolver`, `ecc:e2e-runner`). A-54 holds for this session.
- Karpathy guidelines: installed (`andrej-karpathy-skills:karpathy-guidelines`).
- Design: no skill named `frontend-design` and none named Apple/HIG. Substitutes for M0c and M4:
  `ecc:liquid-glass-design` and `ecc:frontend-design-direction`. `DEFAULT — not confirmed by user`.
- MT5 MCP server `mt5`: only read tools are exposed; `.claude/settings.json` denies the order tools.
  Not used in M0.
- Used in M0a: Claude Code plan mode; gstack `/browse` for §3. No reviewer ran in M0a.

## 6. Re-verification of external facts (kickoff §3), 2026-11-10

**Result: nothing was re-verified.** The gstack headless browser was refused by every source:
`exness.com` and `get.exness.help` returned a bot check (HTTP 403), and `mql5.com/en/docs` returned
HTTP 404. No workaround was attempted. No MT5 connection was made.

| Item | Source | Outcome |
| --- | --- | --- |
| A-02, A-03, A-15 | S4 | STILL UNVERIFIED (stays `REPORTED`; live check in M2) |
| A-14 | S5 | STILL UNVERIFIED (stays `REPORTED`; observed in M7) |
| A-17 | Exness client agreement (no URL in SOURCES) | STILL UNVERIFIED (user confirms in Phase 0) |
| A-10, A-11, A-13, A-16 | S2 | Not re-checked; stays `VERIFIED-DOC` as of 2026-11-08 |
| A-12 | S3 | Not re-checked; stays `VERIFIED-DOC` as of 2026-11-08 |
| A-22 | S10 | Not re-checked; stays `VERIFIED-DOC`, interpretation `BLOCKED` until M2 |

Live values override every one of these in M2 (CENT-001).

## 7. Open BLOCKED and OPEN items

Unchanged from `quality/ASSUMPTIONS_AND_UNKNOWNS.md`; listed with what each needs.

- **BLOCKED until M2 (read-only account):** A-05, A-06, A-07, A-32 (`symbol_info()` on the cent
  account); A-22 (TIME-005 measurement); A-09 swap fields.
- **BLOCKED until M7 (Standard demo):** A-08 commission from first deals; A-30 comment preservation;
  A-31 SL on entry; A-41 P-14 from demo slippage; A-42 EXE-060 thresholds; A-40 needs at least two
  weeks of spread data (M2–M7).
- **OPEN, user:** A-50 legality (Phase 0 checklist sign-off before M10); A-51, A-52 privacy law
  and record retention. A-46 and A-47 were approved 2026-11-13; A-09 waits for M2 verification.
- **Unknown by design:** A-55 whether any edge exists; A-67 and A-70 minimum-lot feasibility (S0).

## 8. Decision register D-01..D-12

Decided by the user in chat on 2026-11-13 (dialog answers); Claude Code chose none. Approval
records are in `config/risk_limits.yaml` (RISK-092). Values equal the fixture column, so the
golden vectors of TRADING_RISK_SPEC §11 need no recomputation.

| ID | Decision | Answer |
| --- | --- | --- |
| D-01 | Entry authorization mode (P-37) | DECIDED 2026-11-13: `AUTO_ALL` |
| D-02 | Risk per trade, strategy budget | DECIDED 2026-11-13: P-01 0.25%, P-32 0.25% |
| D-03 | Daily, weekly, drawdown interventions | DECIDED 2026-11-13: P-02 1.00%, P-03 2.00%, P-04 5.00% |
| D-04 | Aggregate open risk, positions | DECIDED 2026-11-13: P-31 0.25% (one full-risk position at a time); P-05 follows the strategy within P-31 |
| D-05 | Daily profit-target behaviour (P-35) | DECIDED 2026-11-13: none |
| D-06 | Loss streak limits, reduction | DECIDED 2026-11-13: P-07 3, P-08 5, P-36 none |
| D-07 | Trading style | DECIDED 2026-11-13: research both scalping and intraday; the edge verdict picks |
| D-08 | Initial strategy selection | DECIDED 2026-11-13: research candidate A (opening-range breakout and retest) first, then B, then C |
| D-09 | One strategy or several | DECIDED 2026-11-13: several strategies, sharing the P-31 budget |
| D-10 | Rule-based, ML or hybrid | DECIDED 2026-11-13: rule-based only (no model in the signal path) |
| D-11 | Research, AI permissions | DECIDED 2026-11-13: the system may research and report new strategies (never deploys without approval); LLM disabled (P-28 = 0); no AI in signals |
| D-12 | Adaptive selection | DECIDED 2026-11-13: prevalidated selector (C4, built and validated in M6f) |

Further answers 2026-11-13: a leverage or margin breach keeps rejecting the trade (no size-down);
A10 counts every capital and cost rejection (CH-92); Guardian inputs max open positions 1 and
emergency-SL loss budget 0.20%; max volume per position is computed in M7b from broker data.

The user first chose Hybrid for D-10 and then, asked about the conflict with D-11, chose
rule-based only. With P-31 = P-01 = 0.25%, several strategies cannot hold positions at the same
time; at most one full-risk position is open.

## 9. Kickoff §4 questions (answered 2026-11-13)

| # | Question | Answer |
| --- | --- | --- |
| 1 | Dashboard technology | React + TypeScript SPA on loopback, confirmed (ADR-005 Accepted); dark and light themes |
| 2 | `PROPOSED` engineering parameters | APPROVED as proposed (A-46); P-14 and P-13 component A wait for broker data |
| 3 | Research thresholds A1–A10 and related defaults | APPROVED as proposed (A-47) |
| 4 | LLM | Disabled completely; P-28 = 0 |
| 5 | MCP server in M8 | Yes: the 9 read tools and the 3 admin actions (each admin action still approved per invocation, MCP-030) |
| 6 | Swap-free | User states the account is swap-free; M2 verifies from MT5 (A-09) |
| 7 | Holidays and early closes | Empty example (M0b); M2 creates the file the user maintains |
| 8 | Phase 0 | User states legality, funding channel and age are confirmed; `PHASE0_CLEARANCE.md` stays `NOT CLEARED` until the user signs the checklist before M10 |
| 9 | D-decisions | See §8 |
| — | NTP servers | time.google.com, time.cloudflare.com (PRIVACY_POLICY §5, CH-91) |
| — | A-71 reason codes | Names approved (CH-90) |

## 10. UI direction (user decision, 2026-11-10)

Source: `Inspiration.jpg` in the repo root. Logged as CH-89; noted at the top of
`prompts/UI_DESIGN_BRIEF.md`. Applied in `docs/UI_SPEC.md` (M0c) and at the M4 design gate.

- **Taken:** near-black green background; lime primary accent; cyan/teal secondary; glass panels
  with thin luminous borders; left icon rail with outline icons; top bar with account summary;
  tabbed chart header; candlestick chart with moving averages, volume and indicator panes; dense
  tables with status dots and pill buttons; tabular numerals; dark theme first.
- **Not taken:** order book and depth panel (MT5 has none for this CFD; MI-021 forbids order-flow
  claims); wallet, staking, DeFi, NFT and "Connect Wallet" items; any copied logo or asset (UI-008).
- **Unchanged:** every numbered rule UI-001..UI-032. Data panels stay at least 85% opaque, at most
  three blur layers, AA contrast, never colour alone, no pulsing or animation unless it is a real
  safety state, `env` banner colours, three separate emergency controls. The brand lime is never
  the `HEALTHY` or profit token.
- **Answered 2026-11-13:** dark and light themes, dark first.

## 11. M0b record (2026-11-13)

**Delivered:** `docs/adr/001..013` (ADR-005 `Proposed`, pack default, not confirmed by user; ADR-012
`Pending user decision (D-01)`); 54 schemas in `schemas/` and `schemas/mcp/` (29 records from
DATA_ARCHITECTURE §3, `common.schema.json`, 12 MCP tools × input/output);
`config/risk_limits.example.yaml` + `config/schema/risk_limits.schema.json`,
`config/session_exceptions.example.yaml` (empty), `config/app.example.yaml` (`fixture_demo: false`,
no symbol, no magic numbers, no secrets, LLM and MCP off). No `P-xx` value, D-01..D-12 decision or
spec rule changed; every parameter has `approved_by_user: false`.

**Checks run (all pass):**

- `uvx check-jsonschema --check-metaschema schemas/*.json schemas/mcp/*.json
  config/schema/risk_limits.schema.json` → ok.
- `uvx check-jsonschema --schemafile config/schema/risk_limits.schema.json
  config/risk_limits.example.yaml` → ok.
- Independent assert script (not written by the authors): 13 ADRs with the five sections; every §3
  name and MCP tool has a schema; `schema_version` and `env` present (Guardian IPC files carry no
  `env` by GRD-010); no money, price or volume typed as a number; no secret-like field; every `$ref`
  resolves; emergency states equal EXECUTION_SAFETY_SPEC §8; the 37 parameters' names, statuses and
  numeric fixtures equal TRADING_RISK_SPEC §2; `TRADING_RISK_SPEC.md` differs from `main` only in T8.
- Negative tests: the risk-limits schema rejects a relabelled status, a renamed parameter and an
  approval with no value; ReconciliationResult rejects `clean: true` with an UNKNOWN op or a raised
  trigger; RiskApprovedAction rejects a risk-increasing approval with no modelled loss or entry
  price; OrderIntent rejects TIGHTEN_SL without SL or ticket; PositionState rejects a confirmed SL
  with no value.

**Independent review** (fresh `ecc:architect`, wrote nothing): APPROVE WITH FIXES. Fixed: B1 the
risk-limits schema binds name, status and UI direction to each `P-xx` id and requires a value once a
USER_DECISION_REQUIRED parameter is approved; B2 risk-increasing approvals require a modelled loss
(RISK-011) and an entry price; B3 a clean reconciliation cannot carry UNKNOWN ops, unresolved
mismatches or triggers; NB1 confirmed SL has a value; NB2 `raised_triggers` is a list; NB3 → A-71;
NB4 per-action required fields; NB7 MCP inputs do not require `schema_version`; NB9 no preset NTP
servers; NB10 ADR-005 status. Deferred to the M0c spec review (non-blocking): NB5 privacy-mode
money in MCP outputs, NB6 structured values in `get_risk_status`, NB8 schemas for `app.yaml` and
`session_exceptions.yaml`, NB11 `expires_mono` across restarts, NB12 per-command payload schemas
(before M4), NB13 confidence as a JSON number in hashes.

**Spec ambiguities raised by the authors and the reviewer (for M0c; none fixed here):** RISK-091
vs API_SPEC §4 MODE_CHANGE/TIGHTEN_LIMIT; P-14 has no fixture yet EXE-020 needs a deviation; P-13
component A null inside `min(A, B, C)`; whether reductions and emergency closes carry a
RiskApprovedAction; `fixture_demo_mode: null` in fixture demo; editable `fixtures` block; Guardian
files carry no `env` in a shared `Files\goldbot\` (Guardian topic, user question); EXE §2 state
machine reused for closes; GRD-010 field named `schema` vs DATA-010 `schema_version`; GRD-016 clean
reconciliation flag absent from the heartbeat; ADR-007 manual blackout schedule undefined; MCP-015
128-char limit vs a 1,000-char journal note; P-32 fixture "= P-01".

## 12. Next (resume point, updated 2026-11-13)

M0c drafts are committed (`07bb8b9`): `docs/UI_SPEC.md`, `docs/STRATEGY_CANDIDATES.md`,
`docs/TEST_PLAN.md` (generated by `tools/gen_test_plan.py`; `--check` and `--self-test` pass),
`docs/RUNBOOK.md`, `docs/DEFINITION_OF_DONE.md`, `docs/PHASE0_CLEARANCE.md` (`STATUS: NOT CLEARED`),
`docs/BACKLOG.md`; traceability statuses updated (0 VERIFIED; 6 rows → BROKER_VERIFICATION_REQUIRED;
D-01..D-12 DECIDED).

To finish M0c: run the M0 spec-mode adversarial review (`prompts/02_ADVERSARIAL_REVIEW_PROMPT.md`)
with two fresh reviewers (A–D, G, H 26–34/38/39 and E, F, I, H 35–37), fix BLOCKER/HIGH findings,
record the verdict here, mark M0c DONE, commit. Then S0 (`prompts/00b_FEASIBILITY_SPIKE_PROMPT.md`;
needs bars from a Standard demo terminal read-only, or a user CSV — ask the user which), then M1.

Known follow-ups: add `.gitattributes` (`* text=auto eol=lf`) in M1 so `gen_test_plan.py --check`
survives CRLF checkouts; UI_SPEC §11 OPEN-01..14 (API response schemas, alerts routes, login
routes, privacy mode) feed M4/M8 planning.
