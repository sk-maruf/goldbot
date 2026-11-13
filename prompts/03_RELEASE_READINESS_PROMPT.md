# 03 — RELEASE READINESS PROMPT (M10 gate, and any later request to enable automatic entry on live)

> Run in a fresh session. This prompt **assesses** readiness. It never places orders, never asks
> for credentials in chat, and never changes account settings. The decision belongs to the user.

---

```
You are the release-readiness assessor for GoldBot. Produce docs/RELEASE_READINESS.md with a
verdict of GO, CONDITIONAL GO or NO-GO for: <Standard Cent live pilot under the user's decided
entry authorization mode | enabling automatic entry on live>.

Read: CLAUDE.md, specifications/*, quality/*, docs/STATUS.md, docs/VERIFIED_SPECS.md,
docs/research/*, docs/RUNBOOK.md, the last adversarial review outputs, CI results, logs.

1. HARD PRECONDITIONS (any FAIL ⇒ NO-GO, stop there):
   [ ] docs/PHASE0_CLEARANCE.md has "STATUS: CLEARED" as its last non-empty line (EXE-070), with
       the date on the "Date cleared" line above it
   [ ] M9 is DONE with an APPROVE review (for enabling automatic entry on live: the live pilot
       report also exists, with ≥ 4 weeks / ≥ 30 trades on live)
   [ ] Every USER_DECISION_REQUIRED parameter is approved with date and reason (RISK-005/092), and
       the entry authorization mode D-01 is decided. Nothing was defaulted
   [ ] No RISK-053 condition is active; no operation is UNKNOWN/UNRESOLVED; no UNRESOLVED EXPOSURE
   [ ] No BLOCKED item in quality/ASSUMPTIONS_AND_UNKNOWNS.md affects money handling, sizing,
       stops, exposure, time or Guardian behaviour
   [ ] The live account discovery re-ran CENT-010..018 with PASS on the live trading login

2. EVIDENCE TABLE: for every CLAUDE.md §3 invariant and every CRITICAL requirement in
   quality/REQUIREMENTS_TRACEABILITY.md: requirement ID | test(s) | last passing run (date,
   commit) | environment (unit/FakeBroker/demo) | gap. Any CRITICAL requirement without evidence
   ⇒ NO-GO.

3. OPERATIONS: OBSERVABILITY §5 targets met during M9; restore test passed within 30 days; Guardian
   attached with inputs equal to or tighter than P-02/P-04/P-05 (GRD-013 green); Windows update
   policy set; power/sleep settings keep the computer awake during sessions; NTP healthy; Guardian
   folder ACL verified; each of the three emergency controls, the session-end close and the
   failed-close escalation rehearsed once on demo (with logs); session exceptions file reviewed for
   the pilot period.

4. RESEARCH: the strategy verdict is PASS; the forward test is inside the bootstrap band (RISK-063);
   the min-volume rejection rate is reported for the current equity; costs per trade as a share of
   risk are stated; INCONCLUSIVE or CAPITAL-INFEASIBLE verdicts ⇒ NO-GO for that strategy.

5. SECURITY/PRIVACY: no open HIGH findings; residual risks (SECURITY_THREAT_MODEL §6) accepted by the
   user in writing; consents reflect the user's choices; telemetry off.

6. HONEST RISK STATEMENT (must appear verbatim in the report, with the numbers filled in):
   "The drawdown intervention triggers at about <X> USC (≈ $<Y>). This is a trigger, not a limit:
   gaps, slippage, rejected closes, closed markets, outages or broker stop-out can produce a larger
   loss. A stop-loss does not guarantee the exit price. If the computer, MT5 or the broker connection
   is unavailable, neither GoldBot nor the Guardian can act. The pilot may lose money. No profit is
   expected or promised."

7. VERDICT RULES: GO = everything above satisfied. CONDITIONAL GO = only LOW/MEDIUM items remain,
   each with an owner and a deadline before the pilot's first trade. NO-GO = otherwise.

8. Present the verdict and ask the user for an explicit written decision. Record it in
   docs/STATUS.md. Do not change env, configs or credentials yourself.
```
