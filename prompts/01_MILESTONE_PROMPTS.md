# 01 — MILESTONE BUILDER PROMPTS (M1–M10)

> **How to use:** one milestone **part** per fresh Claude Code session (or `/clear`). M2, M6, M7 and M9
> have parts (listed in their blocks); every other milestone is a single part. Paste the **Shared
> preamble**, then that milestone's block and the part name. After each part, run
> `prompts/02_ADVERSARIAL_REVIEW_PROMPT.md` in another fresh session. Tag the commit
> (`git tag mN-done`, or `m7a-done` for a part) only after an APPROVE verdict.
>
> **Waiting for elapsed time.** When a part's acceptance needs time to pass (the M2 24 h soak, the
> M7 demo days, the M9 forward test), its session ends with `WAITING_ON_TIME` in `docs/STATUS.md`:
> what is running, when it started, and the exact condition that ends the wait. A later session
> checks that condition and either finishes the part or leaves it waiting.

## Dependency order and gates

```
M0 Spec ─► M1 Foundation ─► M2 Read-only MT5 + discovery ─► M3 Decimal + RiskEngine
                │                                                │
                └──────────► M4 Dashboard (read-only) ◄──────────┘
M3 ─► M5 Data + backtester ─► M6 Market intelligence + strategy research (M6a–M6f)
M2 + M3 + M4 ─► M7 Execution + Guardian (Standard demo)
M4 + M7 ─► M8 Security, privacy, MCP
M6 + M7 + M8 ─► M9 Integration, entry-authorization modes, adversarial tests, demo forward test
M9 + Phase 0 ─► M10 Standard Cent pilot readiness (separate approval: 03_RELEASE_READINESS_PROMPT.md)
```
S0 (`prompts/00b_FEASIBILITY_SPIKE_PROMPT.md`) runs after M0 and before M1. It is advisory and gates
nothing.

A milestone may start only when **every** dependency is `DONE` with an `APPROVE` review in
`docs/STATUS.md` (GOV-001); a milestone with parts is `DONE` only when every part is (only M6f may instead be
`NOT_APPLICABLE`, as its block defines). Baseline security (loopback bind, auth, secrets) is built where it is
first needed (M1/M4). M8 hardens and verifies it.

---

## Shared preamble (paste first, every time)

```
You are the builder for GoldBot milestone <MN>. CLAUDE.md is binding.
1. Read docs/STATUS.md. If any dependency of <MN> (see the dependency order in
   prompts/01_MILESTONE_PROMPTS.md) is not DONE with an APPROVE review, STOP and tell me.
   If <MN> is WAITING_ON_TIME, check its end condition first, then finish it or report that it
   is still waiting.
2. Read the spec files listed for <MN> completely, plus quality/ASSUMPTIONS_AND_UNKNOWNS.md.
   Look requirement rows up in quality/REQUIREMENTS_TRACEABILITY.md by ID; do not load the whole
   file.
3. Plan mode: list the files to create or change, the tests you will write first (by requirement
   ID), assumptions, and BLOCKED items. Wait for my approval.
4. TDD: the required tests fail first, then you implement until they pass. Never weaken a test.
5. Use the installed skills per CLAUDE.md §4 and report which ones actually ran.
6. Never fabricate data, specs or results. Unknowns → ASSUMPTIONS_AND_UNKNOWNS.md as BLOCKED.
7. Finish with: test/lint/type results; changed files; requirement IDs moved to TEST_REQUIRED or
   VERIFIED in quality/REQUIREMENTS_TRACEABILITY.md (with the evidence); spec deviations;
   docs/STATUS.md and CHANGELOG.md updated; "HOW COULD THIS FAIL?" for this milestone. Then stop.
```

---

## M1 — Project foundation and development environment

**Objective:** a tested skeleton in which the core safety primitives exist before any MT5 code.
**Specs:** SYSTEM_ARCHITECTURE, TRADING_RISK_SPEC §4, DATA_ARCHITECTURE, SECURITY_THREAT_MODEL §2–3, PRIVACY_POLICY §2, TIME_AND_CLOCK_SPEC §3–4.
**Dependencies:** M0.
**Scope / deliverables:**
- Repo layout `src/goldbot/{core,intelligence,engine,adapters,api,research,llm,mcp}`, `mql5/`, `web/`,
  `schemas/`, `config/`, `tests/{unit,property,golden,integration,chaos,e2e,security}`; `uv`,
  lockfiles, ruff, pyright, pytest + hypothesis, pre-commit (ruff, gitleaks), CI (Windows + Linux,
  `-m "not mt5"`).
- `core/money.py` (`Money`, `CurrencyMismatchError`); `core/convert.py` (`to_decimal`, RISK-020) with
  the decimal context and the `FloatOperation` trap (RISK-021); rounding helpers (RISK-022).
- Pydantic models ↔ JSON schemas sync test (DATA-011). Config loader with schema validation and
  hashing (RISK-090).
- `BrokerPort` protocol + `FakeBroker` (deterministic; recorded fixtures; session simulation;
  configurable retcodes).
- Clock abstraction: injectable UTC and monotonic clocks; NTP probe (TIME-010/011/015).
- Structured logging with redaction (SEC-004, OBS-010); keyring wrapper (SEC-001); hash-chained
  audit log (SEC-022); `goldbot doctor`.
- `env` guard: separate DB per env (DATA-005); Phase-0 guard for LIVE (CLAUDE.md §3.17).

**Required tests:** RISK-020..024 (incl. a lint rule banning `Decimal(<float>)`), GV-06, GV-25, GV-26;
redaction property test; audit-chain tamper test; schema sync; wall-clock jump test (TIME-015);
naive-datetime ban; LIVE-without-clearance refusal; env/DB mismatch refusal.
**Acceptance criteria:** CI green on both OSes; ≥ 95% branch coverage on `core/money.py` and
`core/convert.py`; `goldbot doctor` passes on the dev machine; no secrets in the repo (gitleaks
clean).
**Failure conditions:** any float reaches `Money`; any secret appears in test output; CI green only
on one OS.
**Security implications:** establishes secret handling and log redaction. Every later milestone
inherits them.
**Out of scope:** MT5 calls, strategies, UI, MQL5.

---

## M2 — Read-only MT5 connectivity and account discovery

**Objective:** prove what the account and symbol really are, using only read-only access.
**Specs:** CENT_ACCOUNT_VALIDATION §2–5, TIME_AND_CLOCK_SPEC (all), EXECUTION_SAFETY_SPEC §1 (EXE-003/004), OBSERVABILITY §3.
**Dependencies:** M1. **Host:** the Windows runtime host, with the **investor password** (SEC-002).
**Parts:** **M2a** builds and tests everything below. **M2b** is the 24 h observer-heartbeat soak
(`WAITING_ON_TIME`), followed by the acceptance check.
**Scope / deliverables:**
- `adapters/mt5_broker.py` read side: initialise/login, single worker thread (EXE-003), reconnect
  with back-off, health states.
- Account discovery (CENT-002), symbol discovery with user selection (CENT-003), spec snapshot +
  hash (CENT-004), checks CENT-010..018, deposit attestation UI stub (CLI prompt is acceptable here).
- Tick polling, freshness, out-of-order handling (TIME-020..022); NTP checks (TIME-010);
  tick-timestamp interpretation test (TIME-005).
- **A minimal read-only Guardian "observer" build** (no trading code): heartbeat + clock export
  (TIME-030) + sessions export (CENT-005). This is needed now, because server time and sessions come
  from it. Atomic file write, SHA-256 integrity digests, `seq`/instance checks and the folder ACL
  set-up and verification are included (GRD-006..008). No shared secret is used. It is built and
  tested with the loop in GUARDIAN_SAFETY_SPEC §13.
- Session calendar: weekday template from the Guardian export, plus `config/session_exceptions.yaml`
  (EXE-080), with the "calendar UNKNOWN" behaviour (EXE-085).
- `docs/VERIFIED_SPECS.md`: every recorded value with its source call and timestamp; fixtures
  `VER-CENT` (if the cent account is available read-only) and `VER-STD` (Standard demo) under
  `tests/fixtures/` (no secrets, login hashed).
- Update `quality/ASSUMPTIONS_AND_UNKNOWNS.md`: each item resolved, changed or still BLOCKED.

**Required tests:** disconnect within 5 s → DISCONNECTED and no crash; a spec-hash change → T10;
CENT-010 cross-check; CGV-04; quiet-market vs dead-feed simulation (TIME-022); a server-offset
change (TIME-051); identical SHA-256 digests in Python and MQL5 on NIST vectors and on canonical
JSON fixtures; replayed or corrupted heartbeat rejected (GRD-007); folder ACL tamper → T22; a second
engine instance detected; account class decided from MT5 data even when the user statement
disagrees (CGV-09); no password in any log (grep test).
**Acceptance criteria:** `VERIFIED_SPECS.md` contains all CENT-004 fields for the chosen symbol(s);
TIME-005 result recorded with median and IQR; every CENT-010..018 check PASS or explicitly BLOCKED
with a reason; the observer Guardian heartbeat has run continuously for 24 h with zero integrity
failures.
**Failure conditions:** account class undeterminable; `order_calc_profit` unavailable; CENT-012
plausibility fails (→ BLOCKED; stop and ask).
**Security implications:** first contact with real credentials. Investor password only; keyring
only; verify redaction against real outputs.
**Out of scope:** any order or modification (the investor password cannot trade; keep it that way).

---

## M3 — Deterministic financial calculations and RiskEngine

**Objective:** a pure, exhaustively tested RiskEngine.
**Specs:** TRADING_RISK_SPEC (all), CENT_ACCOUNT_VALIDATION §4–6, EXECUTION_SAFETY_SPEC §5 (rules only).
**Dependencies:** M1, M2 (fixtures).
**Scope / deliverables:** `core/sizing.py` (RISK-010..014); `core/exposure.py` (EXP-001..009, with
broker-calc inputs passed in so the core stays pure); `core/risk_engine.py` (`evaluate`,
`evaluate_reduction`, `evaluate_modification`, all pre-trade gates incl. aggregate open risk,
strategy budgets, strategy envelope and news policy (RISK-015..018), OFF_TICK and opt-in
quantization (RISK-022/025), reason codes, the pending-parameter gate RISK-005 with the fixture-demo conditions RISK-066); `core/limit_state.py` (UTC day/week
boundaries, HWM, consecutive-loss counter, rebuild from deals, TIME-056); `core/trading_state.py`
(T1–T27 with severity, recovery class, cooldown and health-check rules; RISK-050..053);
`core/autonomy.py` (the three entry authorization modes, fixture demo and narrowing rules,
RISK-060..067, state logic only);
min-volume rejection counters (CENT-030).
**Required tests:** all GV-01..41 and CGV-01..09 against the `ILL-*` **and** `VER-*` profiles, using
fixture parameters only;
hypothesis properties (volume never < `volume_min`, always a multiple of `volume_step`, modelled loss
≤ budget for every approval, currency mismatch always rejects, no float anywhere); a test that only
`risk_engine.py` can construct `RiskApprovedAction`; each T-trigger raises the right state and
clears only by its recovery class; no RISK-053 condition can ever be cleared automatically
(property test over random trigger sequences); GV-12/13 produce emergency *requests* (not
completions); no code path selects an entry mode or a P-xx value when it is unapproved.
**Acceptance criteria:** 100% branch coverage on `risk_engine.py`, `sizing.py`, `exposure.py`,
`trading_state.py`; mutation-testing spot check (e.g. `mutmut` on `sizing.py`) with no surviving
mutants in the rounding/rejection branches; worked example `TRADING_RISK_SPEC` §3.1 reproduced
exactly.
**Failure conditions:** any `VER-*` result differs from its `ILL-*` expectation without an approved
explanation; any path to `RiskApprovedAction` outside the RiskEngine.
**Security implications:** limits are read-only at runtime; there is a test for every attempted
loosening path (RISK-091).
**Out of scope:** I/O, MT5 calls, threading.

---

## M4 — Dashboard and monitoring interface (read-only)

**Objective:** an honest, accessible view of everything, before any trading exists.
**Specs:** prompts/UI_DESIGN_BRIEF.md → docs/UI_SPEC.md, API_SPEC §1–3, §6–7, OBSERVABILITY_SPEC, PRIVACY_POLICY §2.
**Dependencies:** M1, M2, M3. **Skills:** Apple/HIG designer + `frontend-design`; ECC `e2e-runner`.
**Scope / deliverables:**
- **Design gate first:** the UI brief §9 deliverables (moodboard, tokens + contrast report, mockups
  including the failure states). **Wait for user approval** before writing components.
- API: loopback bind + Host allowlist (API-001/002), login with password + TOTP (API-010/011), CSRF
  (API-012), scopes `ui:read` only, read routes, WebSocket stream (API-050/051), problem-JSON errors.
- Web: top bar (UI-020 + statuses), Overview, Market, Positions (broker vs ledger), Risk, System,
  Audit; the state catalogue (UI §5) driven by FakeBroker scenarios; emergency controls visible but
  disabled (labelled "available from M7").

**Required tests:** axe-core (zero serious/critical); automated contrast check of every token against
the worst-case backdrop; reduced-transparency / contrast / motion emulation; **UNKNOWN never renders
green** (a test per component with missing data, timeouts and a silent WebSocket); stale/closed
labels; visual snapshots at 1440 px and 390 px, light and dark; non-loopback bind refusal; 401
without a session; CSRF rejection; Host-header spoof rejection.
**Acceptance criteria:** the user approved the design gate; all tests green; 60 fps profile attached;
≤ 3 blur layers verified by test.
**Failure conditions:** any status inferred from stale data; any monetary value without currency.
**Security implications:** first network-facing surface. Loopback, auth, CSRF and Host checks are
mandatory now, not in M8.
**Out of scope:** commands, approvals, MCP.

---

## M5 — Historical data and realistic backtesting

**Objective:** a PT1 tick simulator that shares the live core.
**Specs:** BACKTESTING_SPEC (all), CENT_ACCOUNT_VALIDATION §6, TIME_AND_CLOCK_SPEC §5.
**Dependencies:** M3 (and M2 for data access).
**Scope / deliverables:** tick ingestion → Parquet + manifest (BT-010/011); QA report + quarantine
(BT-012/013); event-driven simulator BT-020..032 using `goldbot.core`; cost model with
PLACEHOLDER/PROXY labels; latency, slippage and reject priors as config; bar builder for signals
only; stress harness (BT §5); report generator (BT §7).
**Required tests:** hand-computed micro-scenarios (≤ 10 ticks) with exact USC P/L; gap through SL
fills at the gap price (BT-025); stops-level rejection (BT-027); closed-session rejection (BT-030);
triple swap applied on `swap_rollover3days`; determinism (BT-040); GV/CGV vectors pass through the
backtest path (BT-050); QA detects injected faults.
**Acceptance criteria:** all tests green; reports always show the tier label; a PT0 number never
appears outside its appendix (test).
**Failure conditions:** fills at mid; SL filled at the SL price through a gap; candle data used for
fills.
**Security implications:** the research process holds no trading credentials (B8).
**Out of scope:** strategy selection, live execution.

---

## M6 — Market intelligence and strategy research

**Objective:** the market-intelligence layer built incrementally on the shared core, then honest
verdicts on the strategies built from it.
**Specs:** MARKET_INTELLIGENCE_SPEC (all), STRATEGY_RESEARCH_SPEC (all), BACKTESTING_SPEC §3–7,
CENT_ACCOUNT_VALIDATION §6–7, TIME_AND_CLOCK_SPEC §2 and §5–7, DATA_ARCHITECTURE §2–3.
**Dependencies:** M5.
**Parts (one session each, a review after each, in the MI-091 order):**
- **M6a Intelligence foundation:** first the architecture impact report
  `docs/intelligence/ARCHITECTURE_IMPACT.md` (MI-090), then **wait for user approval**. Then the
  `Evidence` contract (MI-010..012), bar and timeframe utilities (MI-016), the future-truncation
  harness (MI-013/014), data-quality and module-health handling (MI-015/018), and the Candle Behavior,
  Candlestick (MI-031/032), Liquidity and Smart Money Concepts (MI-030) modules, each documented in
  `docs/intelligence/<module>.md` (MI-012).
- **M6b Intelligence completion:** the Trend, Market Regime (MI-035), Multi-Timeframe Confluence
  (MI-034), Live Market Perception (MI-020 module 7, MI-021) and Early Reversal (MI-033) modules; the decision engine
  (MI-040..047); `DecisionRecord` persistence for the backtester and the research store (MI-045).
- **M6c V2.2 analysis modules (Phases B–D):** the Fibonacci (MI-110..118) and Chart Pattern
  (MI-120..123) modules, the module 4 price-action extension (MI-130) and the module 8 liquidity
  upgrade (MI-140), each with `docs/intelligence/<module>.md` (MI-012). First update
  `docs/intelligence/ARCHITECTURE_IMPACT.md` for V2.2 against the real repository (MI-090) and
  **wait for user approval**.
- **M6d V2.2 setups and management (Phases E–H, pure parts):** setup fields, evidence categories
  and display ranking (MI-150..157); the lifecycle record (MI-160..162); the trailing methods,
  net-of-cost break-even and partial-exit feasibility (MI-170..174); exit evaluation
  (MI-180..185); timeframe roles and market-condition gates (MI-190..192); the additive migrations
  with down-migrations (MI-101). Nothing here sends an order: live wiring is M9a.
- **M6e Strategy research:** the scope below, applied to the strategy families the user selected in
  D-08 (MI-050, MI-053 for scalping), each implemented on the intelligence layer behind the one
  `Strategy` interface. While D-08 is pending, the M0 candidates (RES-073) are used. V2.2: the BASELINE
  versus UPGRADED comparison (MI-196, MI-197), the trailing-method backtests (MI-175) and the
  pattern outcome statistics (MI-123).
- **M6f Strategy selector (conditional):** only if the user chose a selector in D-12 **and** at least
  two strategies PASS in M6e: a C4 selector (MI-052, RES-061) with its own pre-registration, version
  and verdict. Otherwise record `M6f NOT_APPLICABLE (<reason>)` in `docs/STATUS.md`. M6 is `DONE`
  when M6a–M6e are `DONE` with APPROVE and M6f is `DONE` or `NOT_APPLICABLE`. If the condition
  becomes true later, M6f runs then, and no selector trades before its PASS.

**Scope / deliverables (M6e):** experiment registry (RES-010..012); walk-forward runner with
purge/embargo (RES-005..007); DSR, PBO (CSCV), bootstrap CIs, Monte Carlo, parameter-stability grid;
candidates behind one `Strategy` interface; pre-registration committed before each OOS run (RES-002),
including the strategy's intelligence parameters, weights and thresholds (MI-012, MI-071); a report
per candidate with plain-language metric explanations and the MI-072 metrics; verdicts per STRATEGY_RESEARCH_SPEC §11.
**Required tests:**
- M6a/M6b: the MI-092 list: unit tests on hand-labelled synthetic bars for every MARKET_INTELLIGENCE_SPEC §4 rule (positive,
  negative and boundary cases); the MI-014 future-truncation property test for every module and the
  decision engine; determinism (MI-017); an Evidence-hash regression on a recorded dataset; the
  MI-001 static import test; confidence never reaches sizing (MI-003); one correlation group alone
  never produces a candidate (MI-042); derived records are counted once (MI-044); opposite
  candidates never hedge (MI-047); a module fault gives `NO_TRADE` (MI-015/018).
- M6c: hand-labelled synthetic fixtures for every Fibonacci rule and every MI-121 table row
  (positive, negative, boundary); future-truncation tests for modules 11 and 12; provisional levels
  and `FORMING` patterns never support a candidate (MI-110, MI-122); a Fibonacci zone overlapping an
  OB or FVG contributes once (MI-114); a wick penetration is never sweep evidence (MI-140).
- M6d: the score breakdown sums to the score (MI-153); a static test that no input depends on time
  since the last trade (MI-155); a property test that no lifecycle sequence skips a state and that
  the lifecycle cannot construct `RiskApprovedAction` (MI-160); trailing candidates are never looser
  than the current SL and respect the stops level and minimum step (MI-172); break-even includes
  costs and needs a closed bar (MI-173); `PARTIAL_INFEASIBLE` at the minimum lot (MI-174); one
  opposite candle never yields an exit, and every exit has a reason code (MI-183, MI-185); the
  anomaly gates only block (MI-192); a V2.1 strategy version gives byte-identical decision records
  after the migration, and the down-migration runs (MI-101).
- M6e: DSR/PBO implementations reproduce reference values (cite the paper values used); on a
  synthetic random walk the pipeline finds no edge (guards against a broken validator); registry
  trial counts equal the actual runs, including every evaluated weight set (MI-071); the
  holdout-touch is recorded and a second touch is refused; every backtest trade has a complete
  MI-080 explanation; group-contribution correlations are reported (MI-043).
- M6f: every candidate × selection-rule combination counts as a trial; no selector input is a
  strategy's own P/L (RES-061).
**Acceptance criteria:**
- M6a/M6b: all tests green; ≥ 95% branch coverage on `src/goldbot/intelligence/`; zero
  future-truncation differences; every MARKET_INTELLIGENCE_SPEC §4 concept documented (MI-012).
- M6c/M6d: the same coverage and truncation bars for the V2.2 code; every Part II concept documented;
  `docs/STATUS.md` records each phase's spec IDs, tests, review, traceability and a PASS / FAIL /
  INCONCLUSIVE verdict (MI-199).
- M6e: each candidate has a committed pre-registration that predates its OOS run (git timestamps);
  each has a verdict; the A10 rejection rate is reported; the MI-196 BASELINE versus UPGRADED report
  exists for every UPGRADED family. **"No candidate passed" is an acceptable,
  successful outcome.**
- M6f: the selector has a verdict, or the part is `NOT_APPLICABLE` with its reason.
**Failure conditions:** thresholds or weights changed after OOS results without a new version; PT0
numbers used for a verdict; any lookahead or repainting (a future-truncation difference); any
evidence counted twice; any intelligence output reaching volume, a limit or a mode; a candidate from
a single indicator or a single candle pattern.
**Security implications:** LLM drafting (if enabled) uses PRV-020 payloads only. The intelligence
modules have no I/O, so no credential can reach them.
**Out of scope:** ML signal models (pending D-10); any selector before the M6f condition holds; any
LLM in the signal path; order-flow data (MI-021); live execution (M7); the Intelligence screen and
the ten V2.2 views (M9a); sending any trailing or exit modification (M9a).

---

## M7 — Execution engine and Guardian EA (Standard demo)

**Objective:** a safe order path and an independent safety net, proven on demo.
**Specs:** EXECUTION_SAFETY_SPEC (all), GUARDIAN_SAFETY_SPEC (all), TRADING_RISK_SPEC §5, §7.
**Dependencies:** M2, M3, M4. **Account:** Exness **Standard demo**, trading password in the keyring,
`env=DEMO`.
Until the user approves the risk parameters, runs are fixture demo (RISK-066).
**Parts (one session each, a review after each):**
- **M7a Engine execution against FakeBroker:** order lifecycle, request construction, retcodes, SL
  verification, partial fills, reconciler, emergency controller, restart sequence, the `op_id`
  state machine, the failure classification and recovery engine, session-end closing and the three
  dashboard emergency controls, with every chaos test FakeBroker can drive.
- **M7b Guardian EA:** the full Guardian on top of the M2 observer, built and tested with the loop
  in GUARDIAN_SAFETY_SPEC §13, including its `[HUMAN]` steps.
- **M7c Standard-demo soak** (after M7a and M7b): the demo measurements below, the 20 round trips,
  the demo chaos and Guardian scenarios, and the 5 demo trading days (`WAITING_ON_TIME` while they
  run).

**Scope / deliverables:** order lifecycle (EXE §2), request construction (EXE-020..022), retcode
classes (EXE §4), SL verification (EXE-030/031), partial fills (EXE-040/041), reconciler (EXE-050..052),
emergency controller with lifecycles (EXE §8), restart sequence (EXE-070..072), execution-quality
metrics (EXE-060), the order-submission state machine with persistent `op_id`s and in-flight lock
(EXE-002, EXE-013..015), the failure classification and recovery engine (TRADING_RISK_SPEC §7,
RISK-050..053), and session-end closing (EXE-080..086). Full Guardian (GRD-001..052, incl. the
budget-bounded emergency SL GRD-020, re-arm GRD-016 and session-end backstop GRD-028) on top of the
M2 observer. The three dashboard emergency controls are enabled (UI-030), with lifecycle display
(UI-013).
- Measure and record on demo: comment preservation (EXE-021), SL-on-entry support (RISK-031),
  latency/slippage/reject distributions (feed BT-023/024/028), and set P-14 and the EXE-060
  thresholds (user approval).

**Required tests:** the chaos list in EXECUTION_SAFETY_SPEC §11 and the Guardian tests in
GUARDIAN_SAFETY_SPEC §12, on demo with logs; 20 automated minimum-size demo round trips, each
reconciled; duplicate-prevention test (a `None` result after a real send); a market-closed emergency
→ `BLOCKED_MARKET_CLOSED`; an emergency run that cannot finish ends `FAILED_DEADLINE` within 60 s;
a forced session-end close in FakeBroker with every close rejected (T26, UNRESOLVED EXPOSURE); each
`AUTO`-class trigger resumes only after cooldown + checks, and each RISK-053 condition blocks
automatic resumption; the UI never shows CONFIRMED before broker read-back.
**Acceptance criteria:** all chaos and Guardian scenarios pass with evidence; zero unexplained
reconciliation mismatches over 5 demo trading days; measured distributions recorded in
`docs/VERIFIED_SPECS.md`.
**Failure conditions:** any duplicate order; any resubmission while an operation is UNKNOWN; any
Guardian SL whose `OrderCalcProfit` loss exceeds its budget; any position without a broker-confirmed
SL for longer than P-22 that did not trigger T25; any position held past a session end without T26;
any "done" shown without confirmation.
**Security implications:** the trading password is loaded only by the engine; the Guardian channel
holds no secret, and its folder ACL is verified; the Guardian runs with no DLLs.
**Out of scope:** the entry-approval UI and automatic entry modes (M9); live accounts.

---

## M8 — Security, privacy and MCP integration

**Objective:** verified security controls, privacy workflows, and the optional MCP server (read tools + approved non-trading admin actions; never order execution).
**Specs:** SECURITY_THREAT_MODEL, PRIVACY_POLICY, MCP_SECURITY_SPEC, API_SPEC (all).
**Dependencies:** M4, M7.
**Scope / deliverables:** a route × scope authorization matrix and tests (API-040); command routes
with re-auth rules (API-013/020/021) wired to the engine; approval-token implementation
(API-030..033) (UI use comes in M9); consent registry (PRV-004/018); export/delete workflows
(PRV-014/015/016); salt lifecycle and crypto-shredding (PRV-012/013); retention jobs (§4);
per-generation encrypted backups + automated restore test (PRV-030/031); LLM payload builder with
allowlist, sanitisation, provider disclosure and unavailable-provider behaviour (PRV-020..026,
LLM-004/006), disabled by default; credential-compromise response (SEC-007); the MCP server (stdio,
9 read tools, per-client tokens MCP-021..024, and only the admin actions the user chose, each with
per-invocation dashboard approval, MCP §4.1) if the user chose it in M0.
**Required tests:** the full security test list in SECURITY_THREAT_MODEL §7; the MCP tests in
MCP-060; privacy tests (no C3 identifiers or C4 values in LLM payloads or MCP outputs; delete-all
removes everything it lists; the restore test passes); a REPLAY run is identical with MCP on and off.
**Acceptance criteria:** ECC `security-reviewer` and `/security-review` have no unresolved HIGH
findings; the threat-register residual risks are reviewed and accepted by the user in writing.
**Failure conditions:** any scope escalation; any secret in an output; MCP reachable over the
network.
**Security implications:** this is the security milestone. Every finding is tracked to closure.
**Out of scope:** network MCP transport, external alert channels.

---

## M9 — Integration, adversarial testing and demo validation

**Objective:** the whole system working together on demo, under whichever entry authorization
mode(s) the user has decided (D-01), and compared against backtest. If D-01 is still pending, test
all three modes on demo as fixture-demo runs (RISK-066, one `fixture_demo_mode` per run) and report
each separately. That tests the modes; it chooses none.
**Specs:** TRADING_RISK_SPEC §9, BACKTESTING_SPEC §4/6, STRATEGY_RESEARCH_SPEC §8, OBSERVABILITY §5, UI brief §6 and §8, MARKET_INTELLIGENCE_SPEC §5, §9 and §18–22.
**Dependencies:** M6 (≥ 1 strategy PASS; otherwise run M9 for plumbing only and say so), M7, M8.
**Parts:** **M9a** integration: the approval flow and its notifications, the modes and any narrowing
rules, the degradation monitor, the intelligence layer in the live path with its Intelligence
screen (MI-081), the V2.2 lifecycle record, trailing and exit evaluation wired through the existing
position manager and RiskEngine (MI-160, MI-172, MI-180) and the ten V2.2 views (MI-195), REPLAY
parity and the required tests. **M9b** the forward test
(`WAITING_ON_TIME` until ≥ 8 weeks and ≥ 50 trades), then the forward-test report, the OBS §5
targets and the system-mode adversarial review.
**Scope / deliverables:** entry-approval flow end to end with approval notifications (UI-031,
API-031, RISK-004, OBS-024); the three
entry authorization modes with promotion gate, strategy auto-approval flags and demotion triggers
(RISK-060..065), and any narrowing rules the user decided (RISK-067); strategy envelope and news policy enforcement (RISK-017/018); strategy degradation monitor
(RES-040..042); the intelligence layer in the live engine path, with `decision_records` written by
the engine (MI-002, MI-045), the Intelligence screen with the rejected-signals list, and per-module
health (MI-018, MI-081/082); forward test on the Standard demo ≥ 8 weeks and ≥ 50 trades (PT2); recorded-tick
REPLAY parity (BT-041); operational targets (OBS §5); a full adversarial review of the integrated
system (02 prompt, system mode).
**Required tests:** replayed/expired/altered approvals rejected; a proposal raises one notification
whose text has no amount, account or price (OBS-024); GV-41 through the live path; every demotion trigger demotes within
one cycle; a mode switch with an open position keeps it managed; E2E proposal → approve → fill →
SL hit → journal; REPLAY parity within BT-041 tolerances; REPLAY decision records identical to the backtest
decision records for the same ticks (MI-017); every forward-test trade has a complete MI-080
explanation; Intelligence-screen tests for UNKNOWN, stale and missing modules (MI-081); on FakeBroker
and demo, a trailing modification goes through `evaluate_modification()` and read-back, a rejected
modification leaves the last broker-confirmed SL in force and on screen, and a duplicate is refused
(MI-172); every lifecycle event and exit has its reason codes (MI-160, MI-185); the ten views show
UNKNOWN rather than stale values (MI-195).
**Acceptance criteria:** `docs/research/forward_test_report.md` states, with numbers and tier labels,
whether the promotion gate (RISK-063) passed; OBS §5 targets met; the adversarial review verdict is
APPROVE.
**Failure conditions:** forward results outside the bootstrap band (automatic entry stays disabled
on demo, and the strategy goes to WATCH); any operational target missed.
**Security implications:** the approval flow is now live on demo. Monitor for the TM-11/12/20
scenarios.
**Out of scope:** any live account.

---

## M10 — Standard Cent pilot readiness assessment

**Objective:** decide, with evidence, whether a small live pilot may start. **This milestone does not
start the pilot by itself.**
**Specs:** CENT_ACCOUNT_VALIDATION §8 (CENT-040), TRADING_RISK_SPEC §8–9, all quality files.
**Dependencies:** M9 APPROVE; `docs/PHASE0_CLEARANCE.md` = `STATUS: CLEARED`; every
USER_DECISION_REQUIRED parameter approved (RISK-005) and D-01 decided. If any is missing, **stop**
and write the reason in `docs/STATUS.md`.
**Scope / deliverables:** run `prompts/03_RELEASE_READINESS_PROMPT.md`. It produces
`docs/RELEASE_READINESS.md` with a GO / CONDITIONAL GO / NO-GO verdict. On a user-approved GO:
- pilot config: `env=LIVE`, cent symbol from VER-CENT, the planned ~$100 deposit (**not** less: at
  $10, a 0.25% budget makes almost every trade infeasible), minimum lot, a pilot stop after 30
  trades or 4 weeks pending review. **Entry authorization for the pilot:** whatever the user decided
  in D-01. The readiness review *recommends* `MANUAL_APPROVAL` for the first 4 weeks, because cent
  execution has never been observed before; the user decides;
- re-run CENT-010..018 against the live trading login;
- the first live order happens with the user present and the system attended.

The drawdown intervention (P-04, at its approved value) triggers at that % of equity; at the
fixture 5% that would be about $5. **Losses can exceed this** (RISK-040).
The pilot report compares PT3 against PT1/PT2 (spreads, swap, slippage, rejection rate) and ends with
the user's decision to continue, adjust or stop.
**Required tests:** every CLAUDE.md §3 invariant mapped to its passing test and last run date
(evidence table); the restore test passed within 30 days; the Guardian attached with inputs equal to
or tighter than the approved P-02/P-04/P-05/P-32, and a close deadline consistent with P-33
(GRD-013 check green); a session-end close and a failed-close escalation rehearsed on demo with logs.
**Acceptance criteria:** the user's written GO in chat, recorded in `docs/STATUS.md`, **before** any
live order.
**Failure conditions:** any BLOCKED item that affects money handling is still open → NO-GO.
**Security implications:** the trading password for the live account is entered by the user into the
keyring. It never appears in chat.
**Out of scope:** enabling automatic entry on live if the pilot ran with human approval (that needs
a later readiness review using pilot evidence, RISK-061).
