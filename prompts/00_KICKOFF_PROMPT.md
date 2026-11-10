# 00 — KICKOFF PROMPT · Milestone M0: Architecture and specification

> **How to use:** create an empty Git repo, copy the whole V2 pack into its root
> (`CLAUDE.md`, `prompts/`, `specifications/`, `quality/`), open it in VS Code, start Claude Code,
> switch to **plan mode**, and paste everything below the line, followed by the part name (M0a, M0b
> or M0c, §0).

---

You are the **lead architect** for GoldBot in this session (milestone **M0**, part M0a, M0b or M0c). `CLAUDE.md` is
binding. **Write no application code, no MQL5, no tests that execute trading logic, and make no MT5
connection in M0.** M0 turns the V2 specification pack into a repo-ready engineering baseline. Builder
sessions (`prompts/01_MILESTONE_PROMPTS.md`) implement it later.

## 0. M0 runs as three sessions

M0 is too large for one context window. Run it as three fresh sessions. Each starts with this
prompt plus its part name, and each ends by updating `docs/STATUS.md` and stopping.

| Part | Does | Ends when |
|---|---|---|
| **M0a** | §1–§4 | the contradiction report, the tooling list, the re-verification results, the §4 answers and the D-01..D-12 register (answers or `STILL PENDING`) are recorded in `docs/STATUS.md` |
| **M0b** | the §5 rows marked **b** | those files exist and every schema validates (`check-jsonschema`) |
| **M0c** | the §5 rows marked **c**, then §6–§7 | every §5 file exists and the spec-mode review verdict is recorded in `docs/STATUS.md` |

M0b and M0c read `CLAUDE.md`, `docs/STATUS.md` and only the specs their deliverables cite. They
never re-ask a question that M0a recorded.

## 1. Read everything first

Read every file in `specifications/`, `quality/` and `prompts/`, plus `CLAUDE.md`, completely,
except `quality/REQUIREMENTS_TRACEABILITY.md` (about 35k tokens): read its header, then look rows up
by requirement ID when you need them.
Then state in ≤ 10 lines: the system boundary, the five most safety-critical requirements, and any
contradiction you found between files. If you find a contradiction, **stop and report it before
writing anything.**

## 2. Check the installed tooling

List which ECC agents/commands, Karpathy guidelines and Apple/HIG design skills are actually
installed, and which you will use in M0 (planner/architect + an adversarial reviewer). Do not claim
a skill ran unless it did.

## 3. Re-verify external facts (no invention)

For each item in `quality/ASSUMPTIONS_AND_UNKNOWNS.md` marked `REPORTED` or `VERIFIED-DOC`, try to
re-check it against the official source listed in `quality/SOURCES.md` (Exness, MQL5, MCP, Python).
Record each result as VERIFIED (URL + access date), CHANGED (old → new value), or STILL
UNVERIFIED. Items that need the live account stay `BLOCKED` until M2. Never fill a gap with a guess.

## 4. Decisions: present them, never make them

**Already decided by the user (do not re-ask; build to these):** local Windows computer, no cloud
or remote access (ADR-013); local dashboard as the only notification channel (OBS-020); three
separate emergency controls with no combined button (EMG-010, UI-030); automatic position closing;
SL/TP management within strategy rules (RISK-034); strategy switching only through a prevalidated
selector (RES-061); news trading only for news-validated strategies (RISK-018); no overnight or
weekend holding (EXE-080); automatic recovery only for `AUTO`-class failures (RISK-052/053);
MCP never executes orders (MCP-010); sanitised minimum data to AI services (PRV-020..026).

**Pending decisions D-01..D-12** (`quality/ASSUMPTIONS_AND_UNKNOWNS.md` §5): present each one with
its options and the technical and operational consequences already written in the specs (for D-01
use `TRADING_RISK_SPEC.md` §9). Record the user's answer, or record `STILL PENDING`. **Do not
recommend a choice as if it were approved, and do not fill a missing answer.** M1–M6 can proceed
with fixture values, and M7/M9 demo work runs as fixture demo (RISK-066). LIVE entries stay blocked
until the relevant decisions are approved (RISK-005, RISK-065).

**Ask in one batch, then wait:**
1. Dashboard technology: React SPA in a desktop browser window (ADR-005 default) or Flutter desktop?
2. Approve or change the `PROPOSED` engineering parameters in `TRADING_RISK_SPEC.md` §2 (P-06,
   P-09..P-27, P-29, P-30, P-33, P-34). This is separate from the D-decisions.
3. Approve the research acceptance thresholds A1–A10, the applicability rules (RES-023..026) and the
   promotion gate RISK-063, and the market-intelligence defaults MI-042/MI-043 (minimum confluence
   and correlation groups)?
4. LLM: keep disabled (P-28 = 0), or name a provider + monthly cap (with the PRV-023 disclosure)?
5. MCP: build the optional server in M8 (disabled until consented), and which admin actions, if any?
6. Is the Exness account registered in a country where automatic swap-free status applies [S3]?
   Any conditions shown in your Personal Area?
7. Known holidays/early closes for the coming months, for `config/session_exceptions.yaml`
   (EXE-080), or should M2 create an empty file that you maintain?
8. Phase 0 status: legality of offshore leveraged trading and of the funding channel where you live,
   and Exness age eligibility. (Building, backtesting and demo can proceed without it; LIVE cannot.)
9. Any of D-01..D-12 you want to decide now?

## 5. Deliverables (create these files)

| Part | File | Content |
|---|---|---|
| b | `docs/adr/001…013-*.md` | One ADR per row in `SYSTEM_ARCHITECTURE.md` §6 (context, options, decision, consequences, reversal cost) |
| b | `schemas/*.schema.json` | Every schema listed in `DATA_ARCHITECTURE.md` §3, with `schema_version`, money as decimal strings + currency, `env` on every record |
| b | `config/risk_limits.example.yaml` + `config/schema/risk_limits.schema.json` | P-01…P-37 with units, status (`USER_DECISION_REQUIRED` / `PROPOSED` / `BROKER_VERIFICATION_REQUIRED`), fixture values in a separate `fixtures:` block, the allowed-direction field, an optional `profile_name` label with no behaviour (MI-061), and `approved_by_user` / `approved_on` / `reason` fields (RISK-092) left **empty** unless the user approved in this session |
| b | `config/session_exceptions.example.yaml` | Schema and an empty example for holidays and early closes (EXE-080) |
| b | `config/app.example.yaml` | Non-risk settings (paths, ports, symbol selection placeholder, NTP servers, magic numbers), plus `fixture_demo: false` and an empty `fixture_demo_mode` (RISK-066) |
| c | `docs/UI_SPEC.md` | `prompts/UI_DESIGN_BRIEF.md` expanded into exact components, states, copy and tokens |
| c | `docs/STRATEGY_CANDIDATES.md` | 2–3 **proposals for the user to choose from**, drawn from the MI-050 strategy families (RES-073; decisions D-07..D-11 stay with the user), each with its class (RES-023), operating envelope (RES-070), news status (RES-071), session-end exit (RES-072) and expected A10 rejection rate argued in advance |
| c | `docs/TEST_PLAN.md` | Every requirement ID mapped to a test type and milestone, generated by a script from the columns of `quality/REQUIREMENTS_TRACEABILITY.md` (not copied by hand); concrete test names; the `[HUMAN]` steps of `GUARDIAN_SAFETY_SPEC.md` §13; coverage targets (≥ 95% branch on `core/`, 100% on `risk_engine.py`/`sizing.py`, ≥ 80% overall) |
| c | `docs/RUNBOOK.md` | Install, start/stop order, daily checks, emergency procedures, outage behaviour, Windows update policy, power and sleep settings for trading sessions, backup/restore test, secret rotation and compromise response (SEC-007), Guardian folder ACL setup and verification (GRD-008), Guardian attach instructions (input values equal to or tighter than the approved P-xx), Guardian re-arm (GRD-016), session-exception maintenance (EXE-080), failed session-end close procedure (EXE-084) |
| c | `docs/DEFINITION_OF_DONE.md` | A shared checklist plus one block per milestone copied from the acceptance criteria in `prompts/01_MILESTONE_PROMPTS.md` |
| c | `docs/PHASE0_CLEARANCE.md` | A checklist for the user (no documents stored), ending with `STATUS: NOT CLEARED` |
| c | `docs/BACKLOG.md` | Deferred items from `SYSTEM_ARCHITECTURE.md` §8, each with the gate it must pass |
| a | `docs/STATUS.md` | Milestone table M0–M10 (status, review verdict, date); open BLOCKED items; the decision register D-01..D-12 with each answer or `STILL PENDING`; the answers to §4 questions |
| c | `quality/REQUIREMENTS_TRACEABILITY.md` | Keep statuses truthful: nothing becomes `VERIFIED` in M0; mark any requirement you find needs broker data `BROKER_VERIFICATION_REQUIRED`, and any that cannot be finalised without a D-decision `USER_DECISION_REQUIRED` |

## 6. Adversarial review of the baseline

Run `prompts/02_ADVERSARIAL_REVIEW_PROMPT.md` in **spec mode** with a fresh subagent (ECC
architect/code-reviewer if installed). Give it only the files, not this conversation. Fix the
blockers. List any rejected findings with a reason.

## 7. Finish

Report: files created; the user's decisions; items still BLOCKED (with exactly what is needed);
contradictions found and resolved; and a section titled **"HOW COULD THIS SYSTEM FAIL?"**. Then ask
the user to approve M0. Set `docs/STATUS.md` M0 = `DONE (pending approval)`. M1 may start only after
approval.

**M0 acceptance criteria:** each part met its end condition (§0); every file in §5 exists; every schema validates (`check-jsonschema`); no
`P-xx` value differs from `TRADING_RISK_SPEC.md` unless the user changed it and the change is logged;
no USER_DECISION_REQUIRED item is marked approved without the user's explicit statement in this
session;
the spec-mode adversarial review verdict is APPROVE or APPROVE WITH FIXES (all fixes applied); no
requirement in the traceability matrix is left without a planned verification method.
