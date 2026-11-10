# 00b — FEASIBILITY SPIKE (S0): can any candidate fit the minimum lot?

> **When:** after M0 is approved, before M1. One fresh Claude Code session. **Advisory:** it informs
> decisions D-02 and D-07..D-09. It gives no edge verdict and gates nothing. Paste everything below
> the line.

---

You are running a throwaway feasibility check for GoldBot. `CLAUDE.md` is binding.

**Question:** for each candidate in `docs/STRATEGY_CANDIDATES.md`, what share of its signals can be
traded at the minimum lot within the risk budget, after costs? This measures feasibility, not
profit.

**Rules**
- Code lives in `spikes/feasibility/`. `src/goldbot` never imports it, and it uses no login with
  trading rights.
- Data: bars from the Standard demo terminal via `copy_rates_range` (read-only), or a CSV the user
  supplies. Record the source, symbol, timeframe and date range.
- Use no data from the future RES-005 holdout (the most recent ≥ 6 months, or ≥ 20% of the data,
  whichever is larger), so the M6 holdout stays untouched.
- Compute stop distances, spreads and sizing only. Profit, win rate and returns stay uncomputed:
  computing them would be an unregistered trial (RES-021).
- Label every number `PT0 — FEASIBILITY ONLY, NOT A RESULT` (BT-001). Use the fixture parameters
  and the `ILL-CENT` profile (or `VER-CENT` if M2 has run), and say which.

**For each candidate, at P-01 = 0.10 %, 0.25 % and 0.50 %** (the recommended range; none of them is
an approval):
1. the stop-distance distribution of its signals in USD (median, P10, P90);
2. the widest stop the minimum lot allows, per RISK-013 with the P-26 slippage allowance;
3. the share of signals rejected `MIN_VOLUME_EXCEEDS_BUDGET` (the A10 rate, CENT-030);
4. the median round-trip spread as a share of the stop distance, if spread data exists;
5. the number of signals per week that survive.

**Deliverable:** `docs/research/feasibility_spike.md` with that table, the data provenance, and one
plain sentence per candidate: "feasible at ≥ X %", "marginal", or "infeasible at every recommended
risk level". Add the result to `docs/STATUS.md` as input to D-02 and D-07..D-09, with no choice
marked as approved. Then stop.

**Done when:** every candidate has all five numbers at all three risk levels, or a stated reason why
a number could not be computed.
