# RISK_REGISTER — Project risks (not trading-limit parameters)

> L = likelihood, I = impact (L/M/H). Owner: **U** = user, **B** = builder agent (Claude Code),
> **R** = reviewer session. Review at every milestone end (02 prompt) and in M10.

| ID | Risk | L | I | Rating | Indicator / trigger | Response | Owner | Linked |
|---|---|---|---|---|---|---|---|---|
| R-01 | Offshore leveraged trading or its funding is unlawful where the user lives | M | H | CRITICAL | Phase 0 not cleared | Live blocked in code; build/backtest/demo continue | U | A-50, CLAUDE §3.17 |
| R-02 | No strategy shows an edge after costs | H | M | CRITICAL | M6 verdicts FAIL/INCONCLUSIVE | Accept; stay in research/demo; this is a valid result | U/B | RES-020 |
| R-03 | Min-lot makes strategies capital-infeasible | H | M | CRITICAL | A10 > 50% | Measure it early (S0 feasibility spike); report it; pick tighter-stop designs or accept NO-GO; never raise risk silently | U | CENT-031 |
| R-04 | Broker changes specs, hours or margin rules | M | H | CRITICAL | Spec hash change; session export change | T10 ENTRY_STOP; CENT-020 re-validation | B/U | CENT-018/020 |
| R-05 | No cent demo, so cent behaviour is first seen live | H | M | CRITICAL | — | Read-only discovery in M2; minimum-lot pilot under the decided entry mode (manual approval recommended for the first 4 weeks); release gate | U | CENT-040 |
| R-06 | Host/terminal/broker outage with an open position | M | H | CRITICAL | Heartbeats stale; disconnection | Neither GoldBot nor the Guardian can act; only broker-confirmed SLs remain. No-overnight rule limits exposure time; keep the PC awake; honest UI copy (UI-015) | U | GRD-030 |
| R-07 | Gap or slippage exceeds the modelled loss | M | M | HIGH | Overshoot metric (RISK-042) | P-26 allowance; blackouts; weekend rules; report overshoot | B | RISK-040 |
| R-08 | Overfitting despite the protocol | M | H | CRITICAL | Forward test outside band | DSR/PBO, holdout one-shot, degradation demotion | B/R | RES-* |
| R-09 | The builder agent drifts from the spec or weakens tests | M | H | CRITICAL | Review findings | GOV-001/002; independent 02 reviews; traceability evidence | R | GOV-* |
| R-10 | Builder agent invents broker facts | M | H | CRITICAL | Unlabelled numbers | GOV-003; ASSUMPTIONS file; review check D13 | R | GOV-003 |
| R-11 | The user raises risk after losses | M | H | CRITICAL | Config edits after drawdown | Loosening needs file edit + restart + audit; the release prompt re-checks | U | RISK-090 |
| R-12 | Host malware or credential theft | L | H | MEDIUM | AV alerts | SEC-010; investor password for reads; accepted residual TM-07 | U | TM-06/07 |
| R-13 | Dependency compromise | L | H | MEDIUM | Audit failures | Lockfiles, audits, minimal deps | B | SEC-012 |
| R-14 | MetaTrader5 package or terminal API changes | M | M | HIGH | Import/version errors | Pin the version; `mt5` tests on each upgrade | B | A-20 |
| R-15 | Swap-free status conditions (fees or restrictions) | M | L | MEDIUM | Personal Area terms | User checks (kickoff question 6); cost model updated | U | A-09 |
| R-16 | Engine and Guardian conflict (double action) | L | M | MEDIUM | Duplicate modifications/closes in logs | Leases + check-then-act (GRD-050..052) | B | GRD-050 |
| R-17 | Approval fatigue or a mistaken approval | M | M | HIGH | Fast approvals; rejected-after-approve trades | Full card numbers; expiry; hold-to-confirm; no external channels | U | UI-031 |
| R-18 | Cost of LLM or other paid services exceeds any plausible profit | H | L | MEDIUM | Monthly cost vs P/L | LLM off by default; P-28 cap; local host only | U | LLM-004 |
| R-19 | MCP client leaks data to its model provider | M | M | HIGH | MCP enabled | Off by default; privacy mode; consent; no trading tools; admin actions approved per invocation | U | MCP-030/040 |
| R-20 | Time-zone/DST misinterpretation | L | M | MEDIUM | TIME-005/051 alarms | Five-clock design; live measurement | B | TIME-* |
| R-21 | Data quality problems in the tick history | M | M | HIGH | QA report | Quarantine; DEGRADED labelling; PROXY flags | B | BT-012/013 |
| R-22 | Scope creep (ML, multi-asset, Telegram) before v1 is safe | M | M | HIGH | New features in PRs | Backlog with gates; review check G25 | R | SYSTEM §8 |
| R-23 | A position cannot be closed before the session end (rejects, halt, early close not in the calendar) | M | H | CRITICAL | Close deadline reached with an open position | Pre-close entry restriction; close deadline with margin (P-33); Guardian backstop (GRD-028); T26 + UNRESOLVED EXPOSURE; exceptions file | B/U | EXE-080..086 |
| R-24 | Pending decisions are never made, so LIVE stays blocked | M | M | HIGH | D-01..D-12 still PENDING at M10 | Present the decisions at M0 and M9; M1–M6 proceed on fixtures and M7/M9 demo runs as fixture demo; the LIVE blocking is intended | U | RISK-005, RISK-066 |
| R-25 | Automatic recovery flaps (stop/resume loops) or resumes on a hidden fault | L | H | MEDIUM | Repeated AUTO resumptions in the audit | Cooldowns, continuous health checks, daily cap → MANUAL (RISK-052); RISK-053 list never auto-recovers | B | RISK-052/053 |
| R-26 | Same-user malware forges Guardian files or impersonates an MCP client | L | H | MEDIUM | Integrity/ACL alarms; unexpected MCP calls | Accepted residual (TM-07/10/03); ACL check; per-invocation approval for MCP admin actions; host hygiene | U | GRD-008, MCP-022 |
| R-27 | Off-tick rejection, strategy envelopes and the no-overnight rule leave too few trades for a verdict | H | M | CRITICAL | A1/A2 INCONCLUSIVE | Report honestly (RES-026); do not loosen rules to get trades | U | RES-024..026 |
| R-28 | Guardian emergency SL cannot be placed within budget, so the Guardian must close instead | M | M | HIGH | GRD-020 step 5 events | Budget check with OrderCalcProfit; close policy; T25/T18 escalation | B | GRD-020 |
| R-29 | The computer sleeps, reboots or loses power during a session | M | H | CRITICAL | Heartbeats stop; T12 | Power/sleep settings; Windows update active hours; no-overnight rule; runbook | U | SEC-010, EXE-086 |
| R-30 | Fixture demo runs against a real account, or its values are mistaken for approved settings | L | H | HIGH | `params=FIXTURE` on a non-demo account; fixture values cited as approved | MT5 `trade_mode` check at start and on reconnect; refusal with `env=LIVE`; banner on every screen; GV-39/40; review check 38 | B/R | RISK-066 |
| R-31 | The intelligence layer adds many parameters and trials, so overfitting, lookahead bugs or double counting produce a false edge | H | H | CRITICAL | Future-truncation failures; large DSR trial counts; forward test outside the band | MI-013/014 tests; correlation groups and the derived-record rule; every weight set counts as a trial; ablation report; M6a–M6f built in parts with reviews | B/R | MI-013, MI-043, MI-071 |
| R-32 | SMC or "liquidity" labels are read as real institutional order flow, or a confidence score as a win probability | M | M | HIGH | UI, report or log wording | MI-021/082 labels; review check 43 | B/R | MI-011, MI-021 |
| R-33 | The V2.2 additions (two modules, 33 patterns, three trailing methods, many thresholds) multiply trials, so a false edge or a late build becomes likelier | H | H | CRITICAL | Large trial counts; UPGRADED better only in sample | MI-071 trial counting; only pre-registered patterns trade (MI-122); MI-196 BASELINE comparison on the untouched holdout; review check 47 | B/R | MI-071, MI-122, MI-196 |
| R-34 | A trailing or exit modification fails, races or is duplicated, so the SL is unknown or looser than believed | M | H | CRITICAL | Modification rejects; read-back mismatch | One in-flight modification per position, read-back, minimum step, last broker-confirmed SL shown, GRD-020 (MI-172); review check 46 | B | MI-172, EXE-030 |

**Rating rule:** L and I mapped L = 1, M = 2, H = 3; product ≥ 6 = CRITICAL, 4 = HIGH, 2–3 = MEDIUM,
1 = LOW. The critical risks as of the final V2 correction are those rated CRITICAL above.
