# PHASE 0 CLEARANCE — Your checklist before any live-money trading

> M0c deliverable (kickoff §5). Created 2026-11-13.
> **Only you may tick these boxes and change the status line.** Claude Code and every other tool
> must never tick a box, fill in a date or change the status line on your behalf (CLAUDE.md §3.17,
> §3.22). A statement in chat is not a tick in this file.

## Why this exists

`env=LIVE` refuses to start until this file says `STATUS: CLEARED` (CLAUDE.md §3.17, EXE-070), every
USER_DECISION_REQUIRED parameter is approved (RISK-005), and the M10 release-readiness verdict for
the pilot is GO. Building, backtesting and demo trading can go ahead without Phase 0; live trading
cannot. M10 cannot start until this file is cleared (`prompts/01_MILESTONE_PROMPTS.md`, M10
dependencies).

## Rules for this file

- **No documents, no personal data.** Do not attach, paste or link identity documents, contracts,
  tax papers, bank or payment details, account numbers, passwords, your name or your address. Each
  item is a yes/no that you answer for yourself. GoldBot stores only the attestation (yes/no and a
  date), never evidence (PRIVACY_POLICY §3, SEC-003).
- **No advice.** This project gives no legal, tax or financial advice and makes no legal claim
  (A-50, PRIVACY_POLICY status note). Where an item says "check", you decide how; a qualified local
  adviser is the route A-50 names.
- Tick a box by changing `[ ]` to `[x]` only when the statement is true for you today.

## Statement recorded on 2026-11-13

On 2026-11-13 you stated in chat that **legality, the funding channel and your age eligibility are
confirmed** (`docs/STATUS.md` §9, question 8). That statement is recorded here as background.
**It does not clear Phase 0.** Each box below must still be ticked by you, and the status line
changed by you, before M10.

## A. Legal and eligibility

- [ ] A1. Trading leveraged CFDs (including gold) with an offshore broker, through an automated
  program, is legal for a resident of the country or countries where you live (A-50).
- [ ] A2. The way you deposit money to the broker and withdraw it (the funding and withdrawal
  channel) is legal where you live, including any foreign-exchange rules that apply (A-50).
- [ ] A3. You meet the broker's minimum age and eligibility rules for opening and operating this
  account. (A-17 reports an age of 18 or more from the client agreement; this project has not
  verified it. Check the current client agreement.)
- [ ] A4. The account is yours, opened in your own name, and only you operate it.
- [ ] A5. You know how gains and losses from this trading are treated for tax where you live, and
  what you must report. (Tax awareness only; no tax figures are stored here.)

## B. Broker terms

- [ ] B1. The broker's current terms allow automated trading on this account type: Expert Advisors in
  the MT5 terminal and orders sent through the MetaTrader5 Python package (STATUS §6: A-17 and the
  client agreement were not re-verified in M0).
- [ ] B2. The broker's terms do not forbid running an automated system on your own computer for
  your own account.
- [ ] B3. You have checked the swap-free conditions for your account in the Personal Area and know
  what they are (A-09, CENT-007). M2 verifies the swap values from MT5; your statement does not
  override MT5 data.
- [ ] B4. You have read what the broker's terms say about margin calls and stop-out, and about
  whether a loss can exceed your deposit. This project has not verified those terms.

## C. Risk acknowledgements

- [ ] C1. A stop-loss does not guarantee the exit price. Gaps, slippage, rejected orders and closed
  markets can fill a stop at a worse price, or not at all until the market reopens (RISK-040/041).
- [ ] C2. The daily (P-02, 1.00%), weekly (P-03, 2.00%) and drawdown (P-04, 5.00%) levels are
  **intervention thresholds**: they trigger protective actions. Losses can go beyond them through
  gaps, slippage, rejected closes, closed markets, outages or a broker stop-out (TRADING_RISK_SPEC
  §8). For illustration at 10,000 USC equity, the drawdown intervention triggers at about 500 USC
  (≈ $5); the loss can be larger.
- [ ] C3. When the computer, MT5 or the broker connection is unavailable, neither GoldBot nor the
  Guardian can act. Only stop-losses already confirmed at the broker remain (GRD-030).
- [ ] C4. Emergency Liquidation and the session-end close are requests, not certainties; a position
  can stay open after them (UNRESOLVED EXPOSURE, EXE-084).
- [ ] C5. The live pilot may lose money. No profit is expected or promised. At about $100, even a
  strong validated edge is illustrated at about $2 a month (CENT_ACCOUNT_VALIDATION §7). "No edge
  found" is a valid outcome (RES-020).
- [ ] C6. The money you deposit for the pilot is money you can afford to lose in full.
- [ ] C7. Results from the Standard demo do not show cent-account economics; the live pilot is the
  first place they are seen (CENT-040).
- [ ] C8. The dashboard on this computer is the only alert channel. Nothing reaches you by phone,
  email or message (OBS-020).

## D. Privacy and records

- [ ] D1. You have checked which data-protection law applies to records kept on your own computer
  (A-51, OPEN-PRV-1). Nothing in this project claims compliance with any law.
- [ ] D2. You have checked how long trading records must or should be kept where you live, and you
  accept the 7-year default or will set a shorter period (A-52, OPEN-PRV-2, PRIVACY_POLICY §4).
- [ ] D3. You accept the local-first design: telemetry off, LLM disabled (P-28 = 0), MCP only with
  per-client consent, NTP queries to time.google.com and time.cloudflare.com (PRIVACY_POLICY §5).

## E. Your own conduct

- [ ] E1. You will enter every credential into the Windows Credential Manager yourself and never
  paste one into chat, a file or a screenshot (SEC-001).
- [ ] E2. You will keep `config/session_exceptions.yaml` up to date from the broker's announcements
  (EXE-080, `docs/RUNBOOK.md` §13).
- [ ] E3. You will be present and attending the system when the first live order is placed (M10).
- [ ] E4. You have read `docs/RUNBOOK.md`, including the emergency procedures (§9–§11) and how to
  close a position by hand in MT5 (§10).

## Sign-off (you only)

When every box above is ticked:

1. Fill in the date below.
2. Replace the last line of this file, `STATUS: NOT CLEARED`, with `STATUS: CLEARED`. Keep it as the
   last line. Do not delete the checklist.
3. Tell Claude Code in chat that you cleared Phase 0, so `docs/STATUS.md` can record it.

If any statement stops being true later (for example the law or the broker's terms change), change
the last line back to `STATUS: NOT CLEARED` and stop live trading.

Date cleared (YYYY-MM-DD):

STATUS: NOT CLEARED
