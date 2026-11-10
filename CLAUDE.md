# CLAUDE.md — GoldBot Project Constitution (V2)

> Claude Code loads this file in every session. Its rules override convenience. If a task
> conflicts with this file or with `specifications/`, **stop and ask the user**.

## 1. What this project is

A risk-first, fail-closed, rules-based trading system for gold on an **Exness MT5 Standard Cent**
account (~$100 ≈ 10,000 USC), running on the user's **local Windows computer** (no cloud, no remote
access). It has a Python engine, an independent MQL5 Guardian EA, a local "Watercolor Glass"
dashboard (the only notification channel), and an optional MCP interface that can never execute
orders.

- **Pending user decisions** (listed in `quality/ASSUMPTIONS_AND_UNKNOWNS.md` §5, D-01..D-12) include
  the entry authorization mode and every financial risk value. **Never choose them on the user's
  behalf.** Fixture values exist only for tests (RISK-005).

- **Objective:** net expectancy after all costs, within the risk limits. **Win rate is reported,
  never optimised** (RES-050).
- **Honest economics:** at this capital, even a strong edge earns a few dollars a month. Success
  means safe, correct, auditable behaviour and an honest edge verdict. "No edge found" is a valid
  result (RES-020).
- **AI role:** statistics generate signals. The LLM is optional and advisory, and **never touches
  the order path** (LLM-001).
- Nothing in this project may claim guaranteed profit, guaranteed execution or a guaranteed maximum
  loss (RISK-040/041, EMG-001).

## 2. Source of truth

| Topic | File |
|---|---|
| Architecture, terminology, ADR list, LLM policy | `specifications/SYSTEM_ARCHITECTURE.md` |
| **All risk numbers (P-01…P-37)** with their decision status, sizing, exposure, failure classification, entry modes | `specifications/TRADING_RISK_SPEC.md` |
| Order lifecycle, reconciliation, emergency operations | `specifications/EXECUTION_SAFETY_SPEC.md` |
| Guardian EA | `specifications/GUARDIAN_SAFETY_SPEC.md` |
| Clocks and timestamps | `specifications/TIME_AND_CLOCK_SPEC.md` |
| Cent account discovery and tests | `specifications/CENT_ACCOUNT_VALIDATION.md` |
| Backtesting realism | `specifications/BACKTESTING_SPEC.md` |
| Research method and verdicts | `specifications/STRATEGY_RESEARCH_SPEC.md` |
| Market intelligence modules, decision engine, strategy families (MI-xxx) | `specifications/MARKET_INTELLIGENCE_SPEC.md` (Part II = V2.2; Phase A review in `quality/V2_2_ARCHITECTURE_REVIEW.md`) |
| Threats, privacy, MCP | `specifications/SECURITY_THREAT_MODEL.md`, `PRIVACY_POLICY.md`, `MCP_SECURITY_SPEC.md` |
| Data, API, observability | `specifications/DATA_ARCHITECTURE.md`, `API_SPEC.md`, `OBSERVABILITY_SPEC.md` |
| UI | `prompts/UI_DESIGN_BRIEF.md` → `docs/UI_SPEC.md` (M0) |
| Requirement status (look rows up by ID; never load the whole file) | `quality/REQUIREMENTS_TRACEABILITY.md` |
| Unknowns | `quality/ASSUMPTIONS_AND_UNKNOWNS.md` |
| Progress | `docs/STATUS.md` (created in M0, updated every session) |

If code and spec disagree, the spec wins until the user approves a change. Spec changes are logged in
`quality/V1_V2_CHANGELOG.md` (or its successor). Never change a `P-xx` value or `config/risk_limits.yaml`
without the user's explicit approval in chat.

## 3. Non-negotiable invariants (each must be enforced in code AND covered by a test)

1. **Single authority.** Only `RiskEngine` creates `RiskApprovedAction`. No order exists without
   deterministic RiskEngine approval. Every risk-increasing operation passes through it;
   position-management modifications use `evaluate_modification()` and risk-reducing actions
   `evaluate_reduction()`. (RISK-001/002)
2. **Decimal money with a conversion boundary.** MT5 floats are converted once, in the adapter,
   with `Decimal(repr(x))`, then quantized and validated. `Decimal(x)` is forbidden. The
   `FloatOperation` trap is on. Money carries its currency; mixing currencies raises. (RISK-020..024)
3. **Volume rounds down; a minimum lot that exceeds the budget means skip.** Never round up. No size
   increase to recover losses. Every skip is counted. (RISK-013, CENT-030)
4. **No silent SL/TP changes.** Off-tick prices are rejected `OFF_TICK` unless the strategy opted in
   to the quantization procedure (RISK-022/025). Every SL is broker-confirmed by read-back; a
   missing SL triggers EXE-031/GRD-020. SLs are never widened. SL/TP modifications follow the
   strategy's declared rules only. (RISK-030..034)
5. **Exposure, not just leverage.** Aggregate open risk, effective leverage, projected margin
   utilisation and margin level are checked on every entry, using `order_calc_margin` /
   `order_calc_profit`. The account leverage cap is an extra check, not the main one.
   (RISK-015, EXP-001..009)
6. **Never assume a fill; never duplicate a submission.** MT5 has no native idempotency key, so
   GoldBot persists `op_id`s, holds an in-flight lock, treats timeouts as UNKNOWN, and reconciles
   before any resubmission. (EXE-002, EXE-013..015)
7. **Fail closed.** No trading with stale or invalid market data, missing stops, invalid specs,
   failed account queries, a disconnected terminal, **incomplete reconciliation**, an unhealthy
   Guardian, or clock problems. (EXE-004, T7–T27)
8. **Emergency operations are three separate controls with lifecycles.** Stop Entries, Cancel
   Pending Orders and Emergency Liquidation each have their own confirmation, deadline (P-25),
   retries and audit, and there is no combined kill-switch button. "Done" is shown only after
   broker confirmation. Liquidation is never assumed to succeed. (EXECUTION_SAFETY_SPEC §8)
9. **Interventions and stops are not guarantees.** The loss thresholds are triggers, and a
   stop-loss does not guarantee the exit price. Never write "max loss", "capped at" or
   "guaranteed". (RISK-040/041)
10. **The Guardian is independent and bounded.** Its hard limits are user-set EA inputs that engine
    files can only tighten. It never opens positions, never acts beyond its approved emergency loss
    budget, holds no secret, and is re-armed only by the user. Its guarantees are limited exactly as
    in GRD-030. (GRD-001..052)
11. **Clocks are separate.** Monotonic time for durations; NTP-checked UTC for records; local
    tick-receive time for freshness; Guardian-exported server time for sessions. Never "latest tick
    time = now". (TIME-001..056)
12. **Cent ≠ standard.** The account class is discovered and validated live; a user statement never
    overrides MT5 data. Standard-demo results never stand in for cent economics. (CENT-001..040)
13. **Prohibited:** martingale, grid or grid recovery, averaging down, recovery sizing, hedging to
    hide losses, widening stops, intentional overnight or weekend holding, LLM-generated orders or
    limits, software changes to leverage or broker settings, autonomous changes to risk limits.
    (TRADING_RISK_SPEC §10)
14. **Secrets** live in the OS keyring only. They never appear in source code, ordinary
    configuration files, Git, logs, prompts, reports, MCP outputs or LLM inputs. The engine ⇄
    Guardian channel deliberately uses no secret (GRD-008). Use the investor password for read-only
    paths. (SEC-001..007)
15. **Local and isolated.** The API binds to 127.0.0.1, with no remote access (ADR-013). MCP is
    optional, stdio, never executes, modifies or closes orders, never changes risk, Guardian or
    safety state, and is never a dependency of the engine. (API-001/002, MCP-001..030)
16. **Environment separation.** Every record and screen has `env`. LIVE and DEMO use separate
    databases. (DATA-005)
17. **Live-money gates.** `env=LIVE` refuses to start until `docs/PHASE0_CLEARANCE.md` says
    `STATUS: CLEARED`, every USER_DECISION_REQUIRED parameter is approved (RISK-005), **and** the
    release-readiness verdict for the pilot is GO (M10).
18. **Privacy.** Local-first, telemetry off, consent recorded for every outbound flow. Only sanitised
    minimum data goes to an external AI service. Audit records are never silently rewritten.
    (PRV-001..031)
19. **No automatic recovery from critical failures.** Only `AUTO`-class triggers resume by
    themselves, after cooldown and health checks. Everything in RISK-053 needs manual recovery.
    (RISK-050..053)
20. **No overnight or weekend holding.** Pre-close entry restriction, close deadline, broker-confirmed
    closure, and escalation when a close fails. (EXE-080..086)
21. **No external AI dependency for safety.** Trading, risk, stops, sizing, emergency operations and
    reconciliation work unchanged when AI services are unavailable. (LLM-006)
22. **Undecided means blocked, not defaulted.** If a decision in D-01..D-12 is needed and missing,
    stop and ask. Never pick a value or mode for the user. Fixture values reach a broker only in
    fixture demo on an account MT5 reports as demo (RISK-066), and a fixture-demo run never counts
    as a decision.
23. **Intelligence proposes; it never authorises.** The market-intelligence modules and the
    decision engine (`MARKET_INTELLIGENCE_SPEC.md`) are pure, use only data that existed at
    decision time (no lookahead, no repainting), emit candidates only, never set volume, a limit,
    a mode or a state, and never enter on a single indicator or a single candle pattern. Every
    candidate still passes the pre-trade gates and the RiskEngine. V2.2 setups, the lifecycle
    record, trailing and exit evaluation only record or propose: an SL only tightens, no exit fires
    on one candle, and no win probability is shown. (MI-001..003, MI-013/014, MI-042, MI-155,
    MI-160, MI-172, MI-183)

## 4. How to work

**Karpathy principles** (from the `karpathy-guidelines` skill, if installed):
- *Think before coding:* state your assumptions and trade-offs, and ask when something is unclear.
- *Simplicity first:* no speculative abstractions.
- *Surgical changes:* touch only what the milestone needs.
- *Goal-driven:* acceptance tests first.

**Milestone loop (ECC):** plan → user approval → TDD (failing tests first) → implement → verify
(tests, lint, types) → independent review (`prompts/02_ADVERSARIAL_REVIEW_PROMPT.md`) → security
review → update `docs/STATUS.md`, `CHANGELOG.md` and the traceability statuses → stop.

- **GOV-001** Start every session by reading `docs/STATUS.md`. **Do not start milestone N unless
  milestone N−1 is `DONE` and its review verdict is `APPROVE`.** Milestone parts (M0a, M7b, …)
  follow the same rule, and a milestone in `WAITING_ON_TIME` is not `DONE`. A part counts as
  complete while `NOT_APPLICABLE` only where its milestone block allows it (M6f).
- **GOV-002** Never weaken, skip or delete a test to make it pass. Never mark a requirement
  `VERIFIED` without a passing test or a recorded run that proves it.
- **GOV-003** Never invent broker specs, MT5 capabilities, legal requirements or performance
  figures. Unknowns go to `quality/ASSUMPTIONS_AND_UNKNOWNS.md` as `BLOCKED` with the exact
  information needed.
- **GOV-004** Use the terminology in `SYSTEM_ARCHITECTURE.md` §2 exactly.

### Installed skills and agents (check what actually exists at session start; never pretend a missing one ran)

| Purpose | Use |
|---|---|
| Planning / architecture | ECC planner or architect agent (`/ecc:plan`), or Claude Code plan mode |
| TDD | ECC `tdd-workflow` skill / `tdd-guide` agent |
| Code review | ECC `code-reviewer` (`/ecc:code-review`). A bare `/code-review` runs Claude Code's built-in reviewer, which is acceptable as a second pass |
| Security | ECC `security-reviewer` / `ecc:security-review`, then built-in `/security-review` |
| Build errors | ECC `build-error-resolver` |
| E2E / UI tests | ECC `e2e-runner` (Playwright) |
| Discipline | `karpathy-guidelines` |
| Visual design | The installed Apple/HIG designer skill + `frontend-design`, constrained by `docs/UI_SPEC.md` |

Reviewers must not have written the code under review: use a fresh subagent with the diff and the
specs only.

## 5. Stack (confirmed by ADRs in M0)

Windows runtime host (the MetaTrader5 wheel is Windows-only). Python (a version supported by the
MetaTrader5 wheel), `uv`, pydantic v2, FastAPI, SQLite (WAL), pyarrow/Parquet,
numpy/pandas/scipy/statsmodels, structlog, keyring, pytest + hypothesis, ruff, pyright (strict on
`core/`). MQL5 Guardian EA (no DLLs). React + TypeScript (strict) + Vite, TradingView Lightweight
Charts, TanStack Query, Vitest, Playwright, axe-core. Optional: the official MCP Python SDK (stdio).
**Not in v1:** PostgreSQL, PyTorch/XGBoost, regime switching outside the prevalidated C4 selector
(M6f, RES-061, MI-052), multi-symbol, Telegram, cloud.

## 6. Commands (keep current)

```
uv run pytest -q -m "not mt5"      # default; CI
uv run pytest -q -m mt5            # Windows host with terminal only
uv run ruff check . && uv run pyright
pnpm --dir web test && pnpm --dir web e2e
uv run goldbot doctor              # environment, clocks, specs, limits, keyring, Guardian heartbeat
```

## 7. Stop and ask the user when

- a change touches risk rules, `P-xx`, trading states, recovery classes, emergency logic, entry
  authorization modes, secrets or the Guardian;
- work needs a pending user decision (D-01..D-12);
- a live broker value contradicts a spec or assumption;
- a test would need weakening;
- any action would place a real-money order or change account settings;
- any MCP or other tool in this session can place, modify or close orders (for example an MT5
  MCP server): stop until the user disables it for this project. `.claude/settings.json` already
  denies `mcp__mt5__place_market_order` and `mcp__mt5__close_position`; never remove those rules,
  and never use such a tool (invariant 15, MCP-010, LLM-001);
- a dependency outside §5 is needed;
- a requirement can only be met by guessing (mark it BLOCKED instead).
