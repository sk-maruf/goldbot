# GoldBot Prompt Pack V2

A planning and prompt pack for building a risk-first, fail-closed gold trading system on an
Exness MT5 Standard Cent account, running on your local Windows computer, with Claude Code in VS Code.
**Final V2 correction: 2026-11-08** (the pre-correction backup sits next to this folder as
`goldbot-prompt-pack-v2_BACKUP_pre-final-correction_2026-11-08/`). It contains **specifications and
instructions only**. Nothing here has been built, connected to a broker, or run.

**V2.1 patch (2026-11-08):** fixture demo, M0/M2/M7/M9 split into sessions, a Guardian build and
test loop, approval notifications, optional schedule narrowing of automatic entry, and a
feasibility spike before M1. Every change is listed in `quality/V1_V2_CHANGELOG.md` §4.

**V2.1 intelligence merge (2026-11-08):** your "Advanced Intelligence Upgrade" brief is merged as
`specifications/MARKET_INTELLIGENCE_SPEC.md` (MI-001..MI-093; the brief itself is kept word for word
in its Appendix A). It is built as milestone parts M6a–M6f, wired into the live path and the
dashboard in M9a, and protected by invariant 23. No `P-xx` value changed and no safety rule was
loosened (`quality/V1_V2_CHANGELOG.md` §5).

**V2.2 upgrade (2026-11-10):** your master upgrade command is added as Part II of the intelligence
spec (MI-100..MI-199): Fibonacci and chart-pattern modules, price-action and liquidity upgrades,
setup fields, an authorization lifecycle record, trailing stops and exit evaluation, timeframe roles,
ten dashboard views and a BASELINE-versus-UPGRADED evaluation. Phase A (the architecture review) is
`quality/V2_2_ARCHITECTURE_REVIEW.md`. Two parts are inserted, so M6 is now M6a–M6f (the old M6c
research is M6e, the old M6d selector is M6f). AUTO_ALL is recorded as your intended final mode, not
as an approval: D-01 stays yours to decide after the gates. No `P-xx` value changed and no safety
rule was loosened (`quality/V1_V2_CHANGELOG.md` §6).

## What's in it

```
goldbot-prompt-pack-v2/
├── README.md                     ← you are here
├── .claude/settings.json         ← (added) blocks MT5 MCP order tools for Claude Code in this project
├── CLAUDE.md                     ← constitution Claude Code loads every session (23 invariants)
├── prompts/
│   ├── 00_KICKOFF_PROMPT.md      ← M0: architecture + specification baseline (no code)
│   ├── 00b_FEASIBILITY_SPIKE_PROMPT.md ← S0: can any candidate fit the minimum lot? (after M0)
│   ├── 01_MILESTONE_PROMPTS.md   ← M1–M10 builder prompts with tests, criteria, failure conditions
│   ├── 02_ADVERSARIAL_REVIEW_PROMPT.md   ← independent review after every milestone
│   ├── 03_RELEASE_READINESS_PROMPT.md   ← GO / CONDITIONAL GO / NO-GO for the live cent pilot
│   └── UI_DESIGN_BRIEF.md        ← Watercolor Glass V2, with status truthfulness rules
├── specifications/
│   ├── SYSTEM_ARCHITECTURE.md    ← components, trust boundaries, canonical terms, ADRs, LLM policy
│   ├── TRADING_RISK_SPEC.md      ← THE parameter register P-01…P-37 (with decision status), sizing, exposure, failure classification, entry modes
│   ├── EXECUTION_SAFETY_SPEC.md  ← order lifecycle, retcodes, reconciliation, emergency ops
│   ├── GUARDIAN_SAFETY_SPEC.md   ← independent MQL5 safety component and its limits
│   ├── TIME_AND_CLOCK_SPEC.md    ← (added) five clocks, MT5 time functions, freshness
│   ├── CENT_ACCOUNT_VALIDATION.md← live discovery, USC vs USD, cent golden tests
│   ├── BACKTESTING_SPEC.md       ← performance tiers PT0–PT3, tick-level execution realism
│   ├── STRATEGY_RESEARCH_SPEC.md ← thresholds with purpose and limits, degradation, verdicts
│   ├── MARKET_INTELLIGENCE_SPEC.md ← (added) 12 intelligence modules, SMC/candle/Fibonacci/pattern rules, decision engine, trailing and exits, 6 strategy families
│   ├── SECURITY_THREAT_MODEL.md  ← assets, controls, 20-threat register
│   ├── PRIVACY_POLICY.md         ← local-first, classification, retention, LLM exposure
│   ├── MCP_SECURITY_SPEC.md      ← optional, stdio, read-only, 9 tools
│   ├── DATA_ARCHITECTURE.md      ← stores, tables, schemas, retention
│   ├── API_SPEC.md               ← loopback REST/WebSocket, scopes, approvals
│   └── OBSERVABILITY_SPEC.md     ← health model ("unknown is never green"), alerts
└── quality/
    ├── V1_V2_CHANGELOG.md        ← every significant change with its validation method
    ├── REQUIREMENTS_TRACEABILITY.md ← every requirement ID → component, file, test, status
    ├── RISK_REGISTER.md          ← project risks with owners and responses
    ├── V2_2_ARCHITECTURE_REVIEW.md ← (added) V2.2 Phase A review and the master upgrade command
    ├── ASSUMPTIONS_AND_UNKNOWNS.md  ← VERIFIED / REPORTED / ASSUMPTION / BLOCKED items
    ├── V2_VALIDATION_CHECKLIST.md   ← cross-file audit results and the V1-issue → fix map
    └── SOURCES.md                ← (added) every external source with URL, access date, status
```

## How to use it

1. Create an empty Git repo, copy this whole folder's contents into its root, and open it in VS Code.
   Include the hidden `.claude/` folder: its `settings.json` stops Claude Code from using the
   `place_market_order` and `close_position` tools of an MT5 MCP server named `mt5`. If your MT5
   server has another name, add its order tools to that deny list too.
2. In Claude Code, install the tools you plan to use (once):
   - ECC: `/plugin marketplace add https://github.com/affaan-m/ECC`, then `/plugin install ecc@ecc`
   - Karpathy guidelines: `/plugin marketplace add forrestchang/andrej-karpathy-skills`, then
     `/plugin install andrej-karpathy-skills@karpathy-skills`
   - Your Apple/HIG design skill, as installed.
3. **M0:** three fresh sessions (M0a, M0b, M0c; kickoff §0). In each: plan mode, paste
   `prompts/00_KICKOFF_PROMPT.md` plus the part name, answer its questions (you may leave the
   D-decisions pending), and approve.
4. **S0 (recommended):** one session with `prompts/00b_FEASIBILITY_SPIKE_PROMPT.md`, to see whether
   any candidate strategy can be traded at the minimum lot before you build M1–M6.
5. **M1 → M10:** one milestone part per fresh session (M2, M6, M7 and M9 have parts), using the Shared
   preamble plus the milestone block. Waits for elapsed time are tracked as `WAITING_ON_TIME` in
   `docs/STATUS.md`. After each part, run `02_ADVERSARIAL_REVIEW_PROMPT.md` in another fresh
   session. Continue only on APPROVE.
6. **Live pilot:** only after M9 APPROVE, Phase 0 cleared, every pending risk decision approved,
   and a GO from `03_RELEASE_READINESS_PROMPT.md` that you confirm in writing.

## Your decisions so far, and what is still open

**Built in as requirements:** local Windows only; dashboard-only alerts; three separate emergency
controls (Stop Entries, Cancel Pending Orders, Emergency Liquidation); automatic position closing;
SL/TP management within strategy rules; strategy switching only through a prevalidated selector;
news trading only for news-validated strategies; no overnight or weekend positions; automatic
recovery only for low-risk failures; MCP can never trade; only sanitised data goes to AI services.

**Still yours to decide** (D-01..D-12 in `quality/ASSUMPTIONS_AND_UNKNOWNS.md` §5): how entries are
authorised (manual approval, fully automatic, or automatic only for approved strategies, optionally
narrowed by schedule or conditions); risk per
trade; daily, weekly and drawdown intervention levels; aggregate open risk and the position count;
consecutive-loss rules; profit-target behaviour; trading style; which strategy or strategies;
rule-based vs ML; whether the system may research new strategies; AI signal permissions; adaptive
selection. Until you decide, tests use labelled fixture values, LIVE stays blocked, and demo trading
runs only as the labelled *fixture demo* on an account MT5 itself reports as demo (RISK-066).

## Honest expectations

- **"High win ratio" is deliberately not a goal.** The system maximises net expectancy after costs
  within strict limits, and reports win rate without optimising it. High-win-rate designs usually
  hide rare large losses, and on this account their wide stops are mostly blocked by the
  minimum-lot rule (`STRATEGY_RESEARCH_SPEC.md` §6).
- **No "expert master trader" exists in this pack.** What the pack does is make the system honest:
  it tests ideas properly, refuses trades it cannot size safely, and tells you when it does not know.
  "No edge found" is a successful outcome.
- **Money:** at ~$100, a strong edge earns about $2 per month (illustrative, step by step in
  `CENT_ACCOUNT_VALIDATION.md` §7). Treat this as an engineering and learning project.
- **Loss thresholds are triggers, not caps.** Gaps, slippage, rejected closes or outages can produce
  larger losses, and a stop-loss does not guarantee the exit price (`TRADING_RISK_SPEC.md` §8).
- **When your computer, MT5 or the broker connection is down, nothing in GoldBot can act.** Only
  stop-losses already confirmed at the broker remain. Keep the computer awake during trading sessions.

## Things only you can do

- **Phase 0:** check that offshore leveraged trading and the way you fund it are legal where you
  live, and that you meet Exness's age requirement. Building, backtesting and demo trading can go
  ahead without it; live trading cannot.
- Enter credentials into the OS keyring yourself. Never paste them into chat.
- Attach the Guardian EA and type its input limits. They must be equal to or tighter than your
  approved P-02, P-04, P-05 and P-32. Re-arm it by hand after any Guardian intervention (GRD-016).
- Do the `[HUMAN]` Guardian test steps when the builder asks, and give it the evidence
  (`specifications/GUARDIAN_SAFETY_SPEC.md` §13).
- Keep `config/session_exceptions.yaml` up to date with holidays and early closes from Exness
  announcements. MT5 does not provide them by date.
- Make the D-01..D-12 decisions when you are ready, and approve every gate.
