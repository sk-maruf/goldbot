# V1 → V2 CHANGELOG

> Baseline: V1 pack (`README.md`, `CLAUDE.md`, `prompts/00_KICKOFF_PROMPT.md`,
> `prompts/01_MILESTONE_PROMPTS.md`, `prompts/UI_DESIGN_BRIEF.md`) plus the original master prompt
> (`Bot-trading-build-prompt.md`). V1 is untouched in its own folder.
> **No V1 safety restriction was weakened.** The few changes that could look like a loosening are
> listed in §2 with the reasoning.

## 1. Significant changes

| # | V1 behaviour | Weakness | V2 correction | Reason | Development impact | Validation |
|---|---|---|---|---|---|---|
| CH-01 | 3 prompts + CLAUDE.md; Session 0 had to write all specs | The builder had to invent most of the specs; nothing was traceable | 14 specs, 6 quality files and 5 prompts with requirement IDs | Consistency and traceability | M0 becomes refinement, not invention | Traceability matrix; cross-file audit |
| CH-02 | "No order reaches the broker unless the Risk Engine approved it" | Silent on modifications, pending orders, SL changes | RISK-001/002: every risk-increasing action; separate `evaluate_reduction()` | Modifications can increase risk | Two RiskEngine entry points | GV-21/22; type test |
| CH-03 | "Money is Decimal, never float" | No rule for *how* MT5 floats become Decimal; `Decimal(float)` keeps binary artefacts [S19] | Conversion boundary RISK-020..024: `Decimal(repr(x))`, quantize, `FloatOperation` trap, rounding table | Exactness | Adapter owns conversion | GV-25/26; lint rule |
| CH-04 | Volume floor only | No rounding rule for SL/TP/money | RISK-022 rounding table | Conservative direction everywhere | Small | Property tests |
| CH-05 | Budget compared to loss at SL only; "$25 stop → 0.01 lot" | Ignored stop slippage, so real losses could exceed the budget | P-26 slippage allowance inside the budget; widest stop at min lot ≈ $24.70 (illustrative) | Budget must hold under normal slippage | Fewer feasible trades (honest) | GV-01/02 |
| CH-06 | SL attached at submission | No verification that the broker accepted it | RISK-031 read-back; EXE-031 escalation; GRD-020 backstop | "Never assume" applies to stops too | Extra read per fill | Chaos test "SL removed" |
| CH-07 | Account leverage cap 1:200 as the exposure control | Leverage setting ≠ exposure | EXP-001..009: effective leverage, margin utilisation, projected margin level, stop-out distance, via `order_calc_*`; leverage cap kept as an extra check | V2 cmd §3B | New `core/exposure.py` | GV-16/17/18 |
| CH-08 | One kill switch that "by default flattens" | Mixed three different operations; implied completion | ENTRY_STOP, CANCEL_PENDING, EMERGENCY_LIQUIDATE as separate requests with lifecycles (EXE §8); **Panic** = all three (keeps V1's default flatten) | Requested ≠ done | `emergency_controller` | Chaos tests; UI-013 |
| CH-09 | "5% drawdown shutdown"; M10 "caps pilot loss at about $5" | Implied a guaranteed maximum loss | RISK-040..042: intervention thresholds; overshoot reporting; banned phrases | Honesty; V2 cmd §3I | Copy changes; overshoot metric | Review check F22 |
| CH-10 | "SAFE MODE" (undefined) | Ambiguous triggers and clear rules | Trading states ACTIVE/ENTRY_STOP/SUSPENDED with T1–T19 and explicit clear rules | Determinism | `core/trading_state.py` | Tests per trigger |
| CH-11 | Guardian "reads limits from a file it can open read-only"; ~300 lines | The engine could loosen the Guardian; no failure model | GUARDIAN_SAFETY_SPEC: hard limits as EA inputs; files tighten only; HMAC/seq; ownership; leases; explicit can/cannot table | Independence | Larger EA (≤ 1,000 lines) | GRD tests §12 |
| CH-12 | Guardian built in M7 | Server time and sessions are needed from M2 | Read-only Guardian "observer" in M2; full Guardian in M7 | Dependency order | Earlier MQL5 work | M2 acceptance |
| CH-13 | Server-time offset "measured from latest tick time vs NTP"; clock skew limit 2 s | Tick time is not "now" (quiet/closed market) | TIME_AND_CLOCK_SPEC: five clocks; Guardian exports `TimeTradeServer`/`TimeGMT`; NTP limits 0.5 s warn / 1 s entry stop (tightened) | V2 cmd §3E | Clock module + Guardian export | TIME tests §9 |
| CH-14 | Stale if tick > 10 s (tick time) | Wrong clock | TIME-020..023: local receive monotonic; quiet vs dead feed | Correctness | Small | TIME-022 test |
| CH-15 | Backtester: bid/ask fills + slippage | No tiers, no latency/rejects/partials, ambiguous SL fills | BACKTESTING_SPEC: performance tiers PT0–PT3; BT-020..032; parity tests; stress set | V2 cmd §3F | Bigger M5 | BT tests |
| CH-16 | Fixed thresholds (200 trades, PF 1.15, DSR 0.95, PBO 0.2, MC, ±20%) | Presented as proof; no limits or sample-size context | Each threshold with purpose/limits/applicability (§5); added CI lower bound (A2), capital feasibility (A10), purge/embargo, registry, versioning, degradation, selector ban | V2 cmd §3G | M6 scope | Reference-value tests |
| CH-17 | Cent maths in prose; "$25 stop → 0.01 lot" | Unlabelled numbers could be mistaken for verified specs | CENT_ACCOUNT_VALIDATION: discovery, checks CENT-010..018, ILL vs VER profiles, CGV tests, rejection reporting | V2 cmd §3H | M2/M3 work | CGV tests |
| CH-18 | Standard demo + capped pilot | Demo's role not bounded | CENT §8 table: what each environment validates; CENT-040 | Avoid false confidence | — | Release readiness |
| CH-19 | 8 security bullets | No structured threat model | SECURITY_THREAT_MODEL with 20 threats, likelihood/impact/residual | V2 cmd §4 | M8 | Security test list |
| CH-20 | None | No privacy design | PRIVACY_POLICY (classification, retention, consent, LLM exposure, backups) | V2 cmd §4 | M8 workflows | Privacy tests |
| CH-21 | None | No MCP design | MCP_SECURITY_SPEC: optional, stdio, read-only, 9 tools | V2 cmd §5 | M8 (optional) | MCP-060 |
| CH-22 | Approvals: HMAC over sha256(proposal) + nonce, expiry | No scopes, no re-auth rules | API_SPEC scopes, route matrix, re-auth list, WebSocket auth (approval design preserved) | Authorization gaps | M4/M8 | API-040 matrix |
| CH-23 | Health shown in UI | No rule against false green | OBSERVABILITY_SPEC + UI-010: unknown never green | V2 cmd §6 | Health model | UNKNOWN tests |
| CH-24 | Watercolor Glass brief | Missing broker/Guardian/reconciliation/freshness/exposure/emergency status | UI brief V2 §3–§6, state catalogue, unknown token (V1 aesthetic and tokens kept) | V2 cmd §6 | M4/M9 | Playwright/axe |
| CH-25 | M1..M10 (M8 approvals, M9 autonomy) | Order differed from the requested structure; security late | M0..M10 per V2 cmd §7; security baseline in M1/M4; approvals + autonomy in M9 | Dependency clarity | Re-sequenced | GOV-001 gate |
| CH-26 | Review prompt inside milestones file | No release gate | `02_ADVERSARIAL_REVIEW_PROMPT.md`, `03_RELEASE_READINESS_PROMPT.md` | Independent gates | — | — |
| CH-27 | Pending orders unspecified | Lifecycle complexity | P-06 = 0 (market orders only in v1) | Simplicity | — | GV |
| CH-28 | "3 consecutive losses → cool-down" | Undefined counting and reset | P-07 (defined), P-08 escalation to SUSPENDED | Precision | — | GV-14/15 |
| CH-29 | Blackout "aligned with Exness HMR windows" (exact window unverified) | Unverifiable number | P-18 −30/+15 min, labelled ASSUMPTION, widen-only | No invented facts | — | A-45 review |
| CH-30 | Unclean restart behaviour unspecified | Could resume AUTO after a crash | EXE-070/071: start in ENTRY_STOP; mode forced to SEMI | Fail closed | — | Restart chaos test |
| CH-31 | Win rate not addressed | User goal "high win ratio" invites fragile designs | RES-050: win rate reported, not optimised; tail-risk review > 70% | Honest objective | — | Review check F22 |
| CH-32 | Sources inline / unverifiable | Some claims unverifiable | `quality/SOURCES.md` with fetch status; claim labels | V2 cmd §9 | — | Audit |
| CH-33 | Swap assumed to exist | Account may be swap-free [S3] | CENT-007, A-09, CGV-08 | New fact | — | M2 |
| CH-34 | MCP absent, LLM role brief | — | LLM policy LLM-001..005 consolidated | Clarity | — | Static tests |
| CH-35 | Leverage cap only | Margin math | EXP-004 uses `order_calc_margin` **plus** existing margin (the function ignores positions [S12]) | Correctness | — | GV-18 |

## 2. Changes that could look like a loosening (reviewed: none weakens safety)

1. **Kill-switch default.** V1: one kill switch that flattens by default. V2: the "Panic" control
   keeps exactly that behaviour, and the separate "Stop entries" control is an *additional*
   lighter option. Automatic triggers T2 (daily loss) and T3/T4 still request liquidation, as V1's
   Guardian did.
2. **Guardian does not liquidate merely because the engine is stale** (GRD-015). V1 never specified
   that it would. Positions keep broker-side SLs, and the Guardian still enforces SL presence and
   equity thresholds.
3. **Guardian size target ≤ 1,000 lines** instead of ~300. More code, but it adds integrity and
   duplicate-prevention features. No limit becomes looser.
4. **Pilot deposit ~$100 (not ≤ $10).** Already changed in V1's final version for feasibility. V2
   only fixes the wording that called the 5% drawdown a cap.
5. **News blackout explicit −30/+15 min.** V1 named an unverified Exness window. V2's window is a
   labelled assumption, and it can only be widened at runtime.
6. **Fixture demo (V2.1, RISK-066).** DEMO may now start with fixture values. This loosens RISK-005
   for play money only: the account must be one MT5 itself reports as demo, `env=LIVE` refuses
   fixture values, every record and screen is labelled, and nothing from fixture demo counts as an
   approval. It removes a deadlock: M7 and M9 needed demo trades that the V2 gate forbade. The user
   chose this on 2026-11-08.

Tightened in V2: clock-offset entry stop (2 s → 1 s); spread cap (single → min of three);
consecutive-loss escalation; P-06 = 0 pending orders; slippage inside the risk budget; unclean
restart forces SEMI + ENTRY_STOP.

## 3. Final V2 correction (2026-11-08) — in place, no V3

Applied directly to the V2 files after a read-only backup was taken
(`goldbot-prompt-pack-v2_BACKUP_pre-final-correction_2026-11-08/`, beside this folder). Format as in
§1: V2 behaviour → weakness → correction → reason → impact → validation.

| # | V2 behaviour | Weakness | Correction | Reason | Development impact | Validation |
|---|---|---|---|---|---|---|
| CH-36 | Default SEMI, with AUTO behind a gate | Chose the entry mode for the user | Three modes (`MANUAL_APPROVAL`, `AUTO_ALL`, `AUTO_APPROVED_STRATEGIES`) documented with consequences; P-37 and D-01 pending; DEMO/LIVE entries blocked until decided (RISK-005/065) | User decision 3.1 | Mode logic for 3 modes; M9 tests all three if undecided | GV-33; review check 26 |
| CH-37 | P-01..P-08 presented as defaults | Financial risk values looked approved | Parameter statuses (`USER_DECISION_REQUIRED` / `PROPOSED` / `BROKER_VERIFICATION_REQUIRED`), recommended ranges, separate fixture column, approval fields (RISK-092) | User §6 | Config schema gains status/approval fields | M0 acceptance; review check 26 |
| CH-38 | P-05 = 1 fixed | Arbitrary count | P-05 per strategy, bounded by new aggregate open risk P-31 (RISK-015) and strategy budget P-32 (RISK-016) | User 3.2 | New gate in core | GV-36/37 |
| CH-39 | Neutral modifications disallowed; TP rules unspecified | No TP management | `evaluate_modification()`; SL tighten-only and TP per strategy rules, audited, verified by read-back (RISK-034); widening still prohibited | User 3.2 (V1 no-widen kept) | Third RiskEngine entry point | GV-21, GV-38 |
| CH-40 | Selector backlog only | Switching impossible even when validated | Switching allowed only through a C4-validated selector; never on recent P/L (RES-061) | User 3.2/§5E | Selector is optional research work | RES-061 tests |
| CH-41 | One "Panic" button + T17 | Combined kill switch | Removed: three separate controls with distinct identity, confirmation, lifecycle and audit; `/panic` route removed (EMG-010, UI-030, API) | User 3.3/3.12 | UI and API simplified | Review check 29 |
| CH-42 | P-25: 5 attempts, back-off to 16 s, 10 s per attempt, no global deadline | Worst case 81 s, unbounded overall | Per-attempt 5 s, back-off 1–8 s, max 5, **global deadline 60 s**, worst case 40 s; `FAILED_DEADLINE` final state (EMG-020) | User 4.7 | Simple scheduler | Chaos test "deadline" |
| CH-43 | T-table with clear rules, some auto-clearing (e.g. T7 after 3 clean runs) | Auto-resumption possible after critical failures | Failure classification matrix: severity, recovery class AUTO/ACK/MANUAL, cooldown, health checks (T1–T27); RISK-052/053; new triggers T20–T27 | User 3.4 | Recovery engine | Property test (M3) |
| CH-44 | Global P-19 blackouts; GV-28 swap rule | Overnight holding possible | No overnight or weekend holding: pre-close restriction, close deadline P-33, cancellation, broker-confirmed closure, failed-close escalation T26, weekend and calendar-unknown rules, holiday exceptions file (EXE-080..086); Guardian backstop GRD-028; BT-034 | User 3.7, §5B | New module; backtest forced close | Chaos tests; GV-28 |
| CH-45 | Global news blackout | Not strategy-specific | News trading only for news-validated strategies (RES-071) with valid, timezone-verified, relevance-classified data (TIME-043); unknown-calendar policy | User 3.6 | Calendar validity checks | GV-11/35 |
| CH-46 | Global session rules only | Could trade just because the market is open | Strategy operating envelope (RES-070, RISK-017) | User 3.5 | Envelope declared per strategy | GV-34 |
| CH-47 | GRD-020 moved the emergency SL "outward" to satisfy stops/freeze levels | Could exceed the approved loss budget | Budget-first procedure with `OrderCalcProfit` [S38]; never widened; close policy if no compliant SL; UNRESOLVED exposure escalation | User 4.1 | Guardian logic | Guardian tests §12 |
| CH-48 | HMAC key in keyring **and** `guardian.key` file, fingerprint as EA input | Contradicted keyring-only rule; no real protection against same-user processes | No shared secret: SHA-256 integrity + seq + instance + folder ACL; duplicate-engine detection; documented lifecycle and residual risk (GRD-008, ADR-011) | User 4.2 | Simpler; MQL5 HMAC code removed | ACL/duplicate tests |
| CH-49 | Guardian kill flag cleared by an engine file request | A faulty engine could clear it | Engine-stale latch auto-clears; every other reason needs the user's `rearm_counter` input change (GRD-016) | Guardian independence | Runbook step | Re-arm test |
| CH-50 | Order lifecycle diagram | Persistence, timeout semantics and resubmission rules were implicit | Explicit state machine with PERSISTED/SUBMITTED/ACKNOWLEDGED/RECONCILING/UNRESOLVED; persistent `op_id`; in-flight lock; MT5 has no native idempotency key [S35] (EXE-002, EXE-013..015) | User 4.3 | Durable writes before sends | Duplicate-prevention chaos tests |
| CH-51 | SL/TP rounded directionally to tick | Silent distance changes | Default `OFF_TICK` rejection; opt-in quantization with recalculation, re-validation, recording and read-back (RISK-022/025) | User 4.4 | Strategy spec flag | GV-31/32 |
| CH-52 | PBO "meaningless for a fixed rule" yet required for PASS | Contradiction; N/A undefined | Strategy classes C1–C4 decided from the registry; per-criterion PASS/FAIL/N/A/INCONCLUSIVE; N/A only where the matrix allows, with evidence; per-class methodology; OOS limitations (RES-023..027) | User 4.5 | Report format | Review check 34 |
| CH-53 | CENT-016 compared deposit with current balance; user confirmation part of class derivation | Wrong comparison; user statement could decide | Account class from MT5 data only; user statement = corroboration; optional comparison against the balance operation itself (CENT-002/016, CGV-07/09) | User 4.6 | Simpler check | CGV-07/09 |
| CH-54 | Single shared `mcp:read` token; "per-client" via a name | Identity not provable | Per-client tokens with honest same-user limits; revocation; unauthorized-client handling; approved non-trading admin actions with per-invocation dashboard approval (MCP-016, MCP-020..030, §4.1) | User 3.9/4.8 | MCP admin routes | MCP-060 |
| CH-55 | `local_salt` undefined; audit "re-anchored" | Salt lifecycle and deletion vs hash chain unclear | Salt lifecycle (PRV-012); deletion by content-table removal + crypto-shredding + explicit audit event, never rewriting (PRV-013/014); per-generation backup keys; AI/MCP retention disclosure | User 4.9 | Privacy jobs | Privacy tests |
| CH-56 | UI copy "protected only by broker-side stop-losses"; "Partially synchronized" | Claimed protection without confirmation | UI-015/016: SL shown only when broker-confirmed, else UNKNOWN; STALE, UNRECONCILED, Guardian UNKNOWN/FAILED, UNRESOLVED EXPOSURE; health state FAILED | User 4.10 | Copy and states | Review check 36 |
| CH-57 | Windows VM/VPS options; VPN remote access; email/Telegram options | Conflicted with local deployment and dashboard-only alerts | Local Windows only; no remote access; dashboard-only alerts with missed-alert protection (ADR-013, API-002, SEC-011, OBS-020/023) | User 3.8/3.11 | Removes options | Review check 37 |
| CH-58 | AI sharing rules were partial | Missing never-share list, disclosure, failure behaviour | PRV-020/023..026; LLM-006 (no AI dependency for safety, tested with providers blocked) | User 3.10, §5F | Payload builder checks | Privacy/LLM tests |
| CH-59 | Credential compromise not specified | — | SEC-007 response; T24 | User 3.4 | Runbook | — |
| CH-60 | Backtests ignored historical specs and approval delay | Optimistic results | BT-033 historical specs, BT-034 forced session-end close, BT-035 approval delay | User §5C | Backtester | BT tests |

**Safety-restriction check for this correction:** nothing was loosened. Removing the Panic button is a
user decision; the three operations it combined are all still available, and automatic triggers
still request them in order. The kill-flag clearing rule became stricter. SL widening remains
prohibited. Every former auto-clearing trigger that the user listed as critical is now MANUAL.

## 4. V2.1 patch (2026-11-08): build-readiness review

Applied after an external build-readiness review. The pre-patch pack is the original
`goldbot-prompt-pack-v2.zip`. No `P-xx` value changed.

| # | V2 behaviour | Weakness | Correction | Reason | Development impact | Validation |
|---|---|---|---|---|---|---|
| CH-61 | DEMO refused to start while any decision was pending (RISK-005/065) | M7 and M9 needed demo trades, and M9 said "test all three modes on demo if D-01 is pending": a deadlock | Fixture demo (RISK-066): MT5-reported demo account only, `fixture_demo: true`, FIXTURE labels, mode set per run, never counts as approval; forward results count for RISK-063 only if the approved values are equal or tighter | User decision 2026-11-08 | Gate logic in core; `trade_mode` read in the adapter | GV-33/39/40; review check 38 |
| CH-62 | M0 read every file in one session, including the ~35k-token traceability matrix | Context-window overflow and drift during M0 | M0 split into M0a/M0b/M0c with end conditions; the traceability matrix is looked up by ID; TEST_PLAN generated by script | Context load | Three M0 sessions | M0 acceptance |
| CH-63 | "One milestone per session", while M2, M7 and M9 need hours to weeks of elapsed time; M7 bundled execution, Guardian and the demo soak | Sessions could not finish, and there was no status for waiting | Parts (M2a/b, M7a/b/c, M9a/b) and the `WAITING_ON_TIME` status; GOV-001 covers parts | Session size | More, smaller sessions | `docs/STATUS.md` milestone table |
| CH-64 | No MQL5 build or test procedure; human-only Guardian steps unmarked | The builder could not compile or test the Guardian, and human steps had no evidence rule | GUARDIAN_SAFETY_SPEC §13: `.mqh` core, MetaEditor command-line compile with a 0-error/0-warning gate, an MQL5 test script, `[HUMAN]` steps with required evidence; the GRD-006 test moved to M2 to match A-28 | Buildability | `goldbot mql5-build` command | Review check 39 |
| CH-65 | Dashboard-only alerts; Windows notifications off by default | Manual-approval proposals (60 s expiry) expired unseen | OBS-024: approval notifications with a chime, on by default, no amount, account or price in the text; the dashboard must be open | Semi-automatic usability | Notification API in the web app | M9 E2E test |
| CH-66 | Modes were global or per strategy only | No way to say "automatic only in chosen sessions" | RISK-067: optional narrowing rules (part of D-01) that only move entries toward human approval | Mode-switch scope | Rule evaluation in `core/autonomy.py` | GV-41 |
| CH-67 | Strategy feasibility first measured in M6 | Five milestones of infrastructure before learning whether any candidate fits the minimum lot | `prompts/00b_FEASIBILITY_SPIKE_PROMPT.md` (S0): stop distances against the minimum-lot budget, no P/L, holdout untouched | De-risking | One session after M0 | Spike report |

**Safety-restriction check for this patch:** one loosening, CH-61, for demo accounts only (§2 item 6).
Everything else adds structure or tightens.

## 5. V2.1 intelligence merge (2026-11-08)

Merges the user's brief "GoldBot V2.1 — Advanced Intelligence Upgrade" into the pack. No `P-xx` value
changed.

| # | V2.1 behaviour | Weakness | Correction | Reason | Development impact | Validation |
|---|---|---|---|---|---|---|
| CH-68 | The signal layer was "features → strategy" with no specification | The builder would have invented indicator, SMC and candle logic with no rules, timestamps or tests | `specifications/MARKET_INTELLIGENCE_SPEC.md`: ten modules with single concept ownership, objective SMC and candle rules, the Evidence contract, no-lookahead rules, the decision engine, six strategy families, explainability; the brief is kept verbatim in Appendix A and mapped item by item in its §11 | User request | New package `src/goldbot/intelligence/` | MI-092 tests; review checks 40–43 |
| CH-69 | M6 was one session (research only) | Too large once the intelligence layer is added | M6 split into M6a, M6b, M6c and a conditional M6d (`NOT_APPLICABLE` allowed for M6d only; GOV-001 updated) | Session size | Four smaller sessions | `docs/STATUS.md` milestone table |
| CH-70 | 22 invariants | Nothing stopped the signal layer from sizing trades, looking ahead or trading on one pattern | Invariant 23 "Intelligence proposes; it never authorises" | Brief §9, §12 | One more invariant in the M10 evidence table | Static, property and unit tests (MI-001/003/014/042) |
| CH-71 | Selector and regime switching "not in v1" (CLAUDE.md §5, SYSTEM_ARCHITECTURE §8) | Brief §8 asks for adaptive selection | Allowed only as the existing RES-061 C4 selector, built in M6d if the user chooses it in D-12 and two strategies PASS; never on recent P/L | Brief §8 | Conditional part | RES-061 tests; review check 43 |
| CH-72 | No storage, schema, health or screen for signal reasoning | Brief §7 and §11 could not be traced | `decision_records` table and `Evidence`/`DecisionRecord` schemas; module health row; Intelligence screen in M9a; MI-072 report metrics; review checks 40–43; R-31/32; A-67/68; optional `profile_name` label (MI-061) | Brief §7, §9, §11 | M0b schemas; M9a UI | Traceability rows MI-001..093 |
| CH-73 | RES-073 examples included a mean-reversion rule | Examples did not match the brief's strategy families | Examples drawn from MI-050 (a liquidity-sweep reversal replaces the mean-reversion example) | Consistency | None | — |
| CH-74 | Nothing stopped a Claude Code session from using an order-capable MCP tool present in the user's environment | A builder session could place or close a trade outside the RiskEngine | `.claude/settings.json` denies `mcp__mt5__place_market_order` and `mcp__mt5__close_position`; CLAUDE.md §7 stops work while any order-capable tool is available | Readiness review 2026-11-08 | Copy the hidden `.claude/` folder with the pack | Session-start tool check (CLAUDE.md §4) |
| CH-75 | `data_quality = DEGRADED` was listed but never defined; M6 cited TIME §5 for bar building | A builder would guess; BT-013's "with and without DEGRADED months" report was impossible | MI-015 defines OK / DEGRADED / INSUFFICIENT (DEGRADED blocks entries in LIVE and DEMO, and is flagged in BACKTEST/REPLAY); OBSERVABILITY health row aligned; M6 now cites TIME §2 and §5–7 | Readiness review 2026-11-08 | None | MI-015 unit tests |

**Safety-restriction check for this merge:** no loosening. CH-71 adds scope only through the
existing RES-061 rule. Where the brief was looser than the pack (win rate "not solely" optimised,
"dynamic" stops, FVG entries, risk profiles), the stricter pack rule applies (MI §11).

## 6. V2.2 upgrade (2026-11-10)

Adds the user's "MASTER UPGRADE COMMAND — GoldBot V2.1 → V2.2" (kept word for word in
`quality/V2_2_ARCHITECTURE_REVIEW.md` Appendix A). No `P-xx` value changed and `TRADING_RISK_SPEC.md`
was not edited. Rows in §5 keep the old part names (M6c research, M6d selector).

| # | V2.1 behaviour | Weakness | Correction | Reason | Development impact | Validation |
|---|---|---|---|---|---|---|
| CH-76 | No Phase A review for the upgrade | Builder would start coding without an inventory | `quality/V2_2_ARCHITECTURE_REVIEW.md`: inventory, gaps, architecture, dependencies, risk impact, sequence | Command Phase A | Read before M6c | Review (02 prompt) |
| CH-77 | No Fibonacci or chart-pattern logic | Command §1–2 missing | Modules 11 and 12, MI-110..123; MI-020 now has twelve modules; MI-043 groups extended | Command | New M6c part | MI-110..123 tests |
| CH-78 | Price action and liquidity lacked stop runs, failed grabs, reclaim, compression, expansion | Command §3–4 missing | Extensions of modules 4 and 8 (MI-130, MI-140), no new engine | Command; single ownership (MI-020) | M6c | MI-130/140 tests |
| CH-79 | Candidates had no setup fields, lifecycle or trailing or exit logic | Command §5–9 missing | MI-150..185 as extensions of the decision engine, a lifecycle record and a pure exit-evaluation layer; no second scorer or authority | Command; RISK-001; invariant 23 extended | New M6d part; M9a wiring | MI-150..185 tests |
| CH-80 | No timeframe roles, anomaly gates, ten views or BASELINE comparison | Command §10–13, §15 missing | MI-190..197 | Command | M6d, M9a, M6e | Tests and reports |
| CH-81 | M6 had parts M6a–M6d | Two V2.2 parts must precede research | New M6c and M6d; old M6c → M6e, old M6d → M6f in every current file | Build order | Part names changed | Grep: no stale part references |
| CH-82 | Desired final mode not recorded | — | AUTO_ALL recorded as intent only; D-01 stays PENDING (MI-162) | RISK-092 | None | Review check 47 |

**Safety-restriction check for this upgrade:** no loosening. Where the command was looser than the
pack (win probabilities, partial exits at the minimum lot, strategy selection by score, AUTO_ALL),
the stricter rule applies (`quality/V2_2_ARCHITECTURE_REVIEW.md` §0).

## 7. M0a contradiction fixes and UI direction (2026-11-10)

Found by the kickoff §1 cross-file read in M0a. The user approved them in chat on 2026-11-10 (plan
approval). No `P-xx` value changed.

| # | Earlier text | Weakness | Correction | Reason | Development impact | Validation |
|---|---|---|---|---|---|---|
| CH-83 | SYSTEM_ARCHITECTURE §2 gave the emergency-action lifecycle as `REQUESTED → SUBMITTED → CONFIRMED / PARTIAL / FAILED / TIMED_OUT / BLOCKED_MARKET_CLOSED` | Disagreed with EXECUTION_SAFETY_SPEC §8 and UI-013 | §2 now uses the §8 states: `AUTHORIZED`, `FAILED_DEADLINE`, and the mandatory `RECONCILED` step | GOV-004: one vocabulary | The `EmergencyAction` schema has one state list | grep: no `TIMED_OUT` in `specifications/` |
| CH-84 | The idempotency ID was `op_id` in EXE-002/014, MI-172 and `order_intents`, but `intent_id` in DATA-002, EXE-020, OBS-010 and `positions_ledger` | Two names for one ID | `op_id` everywhere | One name in schemas and logs | `OrderIntent` and `PositionState` schemas use `op_id` | grep: no `intent_id` in `specifications/` |
| CH-85 | OBS-011 listed the CRITICAL triggers as T2–T4, T8, T15–T19 | Stale since T20–T27 were added; disagreed with the severity column of TRADING_RISK_SPEC §7 | OBS-011 = every trigger §7 marks CRITICAL, plus T2, T3, T17 and the non-trigger events (the stricter union). §7 itself is unchanged | CRITICAL alerts must cover T7 and T20–T26 | Alert mapping reads §7 | Test: every §7 CRITICAL trigger logs at CRITICAL |
| CH-86 | SEC-022 said the daily audit export "goes off-box" | PRIVACY_POLICY §5 has off-box backups off by default (ADR-013); TM-13's residual relied on the export | The export is local and encrypted, and off-box only when the user enabled it; TM-13 states its residual for both cases | Honest residual risk | None | Review |
| CH-87 | TIME-030 had the Guardian exporting clocks at "P-20 cadence" | P-20 is the engine's 2 s interval; the Guardian heartbeat is every 5 s (GRD-011) | TIME-030 cites the Guardian heartbeat (5 s, GRD-011) | Consistency; no Guardian behaviour changes | None | Review |
| CH-88 | Stale references and labels in seven files | Wrong section numbers; a label and a status that do not exist | Kickoff §3 `VERIFY-DOC` → `VERIFIED-DOC`; A-09 and R-15 "Q9" → kickoff question 6; CENT-005 → GUARDIAN_SAFETY_SPEC §3 and §11; PRV-010 → DATA_ARCHITECTURE §2; ASSUMPTIONS §5 title date; T8 "unresolved > 60 s (P-24)"; 02 prompt "PT tiers"; 01 preamble `TEST_REQUIRED` (no `IMPLEMENTED` status exists) | Accuracy | None | Review |
| CH-89 | UI brief: "Watercolor Glass" washes, "nothing glows" | The user supplied `Inspiration.jpg` and asked for its palette, glass look and icons | Visual direction: near-black green, lime primary, cyan/teal secondary, luminous-border glass panels, dark theme first. Every numbered UI rule (UI-001..UI-032) is unchanged | User decision 2026-11-10 | `docs/UI_SPEC.md` (M0c) and the M4 design gate use the new direction | M4 contrast report and design gate |

The traceability rows that quote the changed text (DATA-002, OBS-010, OBS-011, SEC-022, TIME-030,
CENT-005, PRV-010) were updated by hand. No requirement ID was added or removed.

**Safety-restriction check for these fixes:** no loosening. CH-85 widens what counts as CRITICAL.
CH-86 removes a claimed mitigation that the default configuration never had, and raises the stated
residual risk to match.

## 8. User decisions and follow-ups (2026-11-13)

The user answered D-01..D-07 and D-09..D-12 and the open kickoff questions in chat on 2026-11-13.
Values are recorded in `config/risk_limits.yaml` and `docs/STATUS.md` §8; no spec value changed.

| # | Earlier text | Weakness | Correction | Reason | Development impact | Validation |
| --- | --- | --- | --- | --- | --- | --- |
| CH-90 | EXP-004, EXP-005 (free margin), EXP-006, P-27, RISK-002 (unknown action) and the ACTIVE-state requirement had no reason code | A rejection by them could not be recorded (A-71, M0b review) | Codes `MARGIN_UTILISATION`, `FREE_MARGIN`, `STOP_OUT_DISTANCE`, `REWARD_RISK_BELOW_MIN`, `UNKNOWN_ACTION`, `STATE_NOT_ACTIVE` | User approved the names 2026-11-13 | `risk_decision` schema enum | M3 tests per code |
| CH-91 | PRIVACY_POLICY §5 did not list the NTP flow that TIME-010 needs | An unlisted outbound flow | Row added: time.google.com and time.cloudflare.com, user choice 2026-11-13 | Every outbound flow is listed and consented (PRV-018) | `config/app.yaml` servers | `goldbot doctor` clock check |
| CH-92 | A10 counted only `MIN_VOLUME_EXCEEDS_BUDGET` (CENT-030/031) | A strategy could pass A10 while most signals fail the leverage, margin or spread rules (M0c strategy review) | A10 uses a capital-feasibility rejection rate over all capital and cost rejection codes; the min-volume rate is still reported | User decision 2026-11-13 | Backtest and report code compute both rates | M6 report tests |

The user also decided on 2026-11-13: a leverage or margin breach keeps rejecting the trade (no size-down); Guardian inputs max open positions 1 and emergency-SL loss budget 0.20%; D-08 research order candidate A, then B, then C (`docs/STRATEGY_CANDIDATES.md`).

**Safety-restriction check:** no loosening. CH-92 makes A10 stricter. CH-90 names rejections that already existed; CH-91 lists a flow that was required but undocumented.
