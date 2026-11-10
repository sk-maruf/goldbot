# STATUS — GoldBot

> Read this first in every session (GOV-001). Updated at the end of every milestone part.
> Last update: 2026-11-10, end of M0a. Nothing is built, connected to a broker, or `VERIFIED`.

## 1. Milestones

A part may start only when every dependency is `DONE` with an `APPROVE` review (GOV-001;
dependency order in `prompts/01_MILESTONE_PROMPTS.md`). The M0 review runs once, in M0c (kickoff §6).

| Part | Status | Review verdict | Date |
| --- | --- | --- | --- |
| M0a Read, contradictions, tooling, re-verification, decisions | DONE | at M0c | 2026-11-10 |
| M0b ADRs, schemas, config examples | NOT STARTED | at M0c | |
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
- **OPEN, user:** A-46 and A-47 (approve `PROPOSED` parameters and research thresholds); A-50
  legality (Phase 0); A-51, A-52 privacy law and record retention; A-09 swap-free conditions.
- **Unknown by design:** A-55 whether any edge exists; A-67 and A-70 minimum-lot feasibility (S0).

## 8. Decision register D-01..D-12

No decision was made in M0a. Claude Code chose none (CLAUDE.md §3.22). Options and consequences are
in `quality/ASSUMPTIONS_AND_UNKNOWNS.md` §5.

| ID | Decision | Status |
| --- | --- | --- |
| D-01 | Entry authorization mode (P-37) | STILL PENDING. Intent AUTO_ALL stated 2026-11-10 (twice); intent is not approval (MI-162, RISK-092) |
| D-02 | Risk per trade (P-01), strategy budgets (P-32) | STILL PENDING |
| D-03 | Daily, weekly and drawdown interventions (P-02, P-03, P-04) | STILL PENDING |
| D-04 | Aggregate open risk (P-31), maximum positions (P-05) | STILL PENDING |
| D-05 | Daily profit-target behaviour (P-35) | STILL PENDING |
| D-06 | Consecutive-loss limits (P-07, P-08), risk reduction (P-36) | STILL PENDING |
| D-07 | Trading style | STILL PENDING |
| D-08 | Initial strategy selection | STILL PENDING (M0c proposes candidates) |
| D-09 | One strategy or several | STILL PENDING |
| D-10 | Rule-based, ML-assisted or hybrid | STILL PENDING |
| D-11 | Research of new strategies; AI signal permissions | STILL PENDING |
| D-12 | Adaptive strategy selection | STILL PENDING |

Until decided: tests and fixture demo use the labelled fixture values; LIVE stays blocked (RISK-005).

## 9. Kickoff §4 questions

The user chose not to be stopped for these. Each line is the pack's own default or the absence of an
answer, and none is an approval.

| # | Question | Recorded |
| --- | --- | --- |
| 1 | Dashboard technology | React SPA (ADR-005). `DEFAULT — not confirmed by user` |
| 2 | `PROPOSED` engineering parameters (P-06, P-09..P-27, P-29, P-30, P-33, P-34) | NOT APPROVED. They stay `PROPOSED` |
| 3 | Research thresholds A1–A10, RES-023..026, RISK-063, MI-042/043 (and RES-040 defaults) | NOT APPROVED. They stay `PROPOSED` |
| 4 | LLM | Disabled. P-28 itself is STILL PENDING |
| 5 | MCP server in M8, and which admin actions | NOT ANSWERED. M8 builds no MCP server until the user chooses it |
| 6 | Swap-free status and conditions | NOT ANSWERED (A-09 stays OPEN) |
| 7 | Holidays and early closes | M0b writes the empty example; M2 creates an empty file the user maintains |
| 8 | Phase 0 (legality, funding channel, age) | NOT ANSWERED. `NOT CLEARED`; LIVE blocked |
| 9 | Any D-decision now | None |

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
- **OPEN, user:** the brief and the M4 tests require a light theme as well. Keep a light theme, or
  dark only? Until answered, both are specified, dark first.

## 11. Next

M0b (kickoff §5 rows marked **b**): ADRs 001–013, `schemas/*.schema.json`,
`config/risk_limits.example.yaml` with its schema, `config/session_exceptions.example.yaml`,
`config/app.example.yaml`. Ends when every schema validates with `check-jsonschema`.
