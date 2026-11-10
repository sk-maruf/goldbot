# UI DESIGN BRIEF V2 — "Watercolor Glass", readability first

> The seed for `docs/UI_SPEC.md` (written in M0, built in M4/M9). Use the installed Apple/HIG
> designer skill and `frontend-design`. HIG principles: **clarity, deference, depth**. The art
> defers to the data. V2 keeps the V1 aesthetic and adds the safety and status layer it was missing.
> **Readability always wins over aesthetics** (UI-001).
>
> **Visual direction superseded (user decision, 2026-11-10; `docs/STATUS.md`,
> `quality/V1_V2_CHANGELOG.md` CH-89).** The look now follows `Inspiration.jpg`: near-black green
> background, lime primary accent, cyan/teal secondary, glass panels with thin luminous borders,
> outline icons, dark theme first. This replaces the watercolor washes in §1 and the colour values
> in §7. Every numbered rule (UI-001..UI-032) still applies: data panels ≥ 85% opaque, the blur
> budget, AA contrast, never colour alone, original art only, and no pulsing or animation unless it
> is a real safety state. The brand lime is never the `HEALTHY` or profit colour token.

## 1. The idea

A calm, premium desktop trading desk with a responsive layout. Soft watercolor washes (mist
lavender, sea-glass teal, warm peach, a hint of gold) sit far behind frosted-glass navigation. All
numbers live on clean, near-opaque panels. Nothing glows, pulses or animates unless it is a real
safety state.

## 2. Hard rules (preserved from V1, numbered)

- **UI-001 Layering.** Watercolor appears only in the shell background, empty states and login.
  Data surfaces use ≥ 85% opaque panels.
- **UI-002 Blur budget.** Heavy blur only on the nav rail, top bar, modals and sheets. At most 3
  `backdrop-filter` layers on screen. Never blur behind charts or scrolling tables.
- **UI-003 Contrast.** WCAG 2.2 AA [S26]: 4.5:1 text; 3:1 icons, chart lines and control borders;
  focus indicators per SC 2.4.7/2.4.13 [S26]. Measured against the **worst-case** backdrop patch.
- **UI-004 Never colour alone.** Every state has a text label + icon. P/L shows a sign (+/−) and
  ▲/▼.
- **UI-005 Numbers.** Tabular numerals. **Every monetary value shows its currency** (e.g.
  `−24.30 USC`). USD-equivalent is secondary and labelled `≈ $`. Signs are never rounded away.
- **UI-006 Accessibility fallbacks.** `prefers-reduced-transparency` / `prefers-contrast: more` →
  solid surfaces; `prefers-reduced-motion` → no non-essential motion; full keyboard operation.
- **UI-007 Performance.** 60 fps on a mid-range laptop. The backdrop is a baked static image
  (≤ 400 KB per theme). Blur is auto-disabled on dropped frames.
- **UI-008 Original art only.** Procedural washes (SVG `feTurbulence` + `feDisplacementMap`, then
  baked) or commissioned art. No copied or unlicensed images.

## 3. Status truthfulness (new in V2)

- **UI-010 Never green when unknown.** A status is shown as healthy only when its health is
  `HEALTHY` (OBS-001). `UNKNOWN` has its own neutral-grey hatched style with a "?" icon and the text
  "Unknown — not verified". Missing data, timeouts, and the WebSocket going silent for > 5 s
  (API-051) all show UNKNOWN, never the last good value.
- **UI-011 Freshness labels** on every live number: `REAL-TIME` (tick age ≤ 2 s), `DELAYED`
  (2 s – P-15), `STALE` (> P-15 in an open session), `MARKET CLOSED`. STALE values turn grey,
  stop animating and show their age.
- **UI-012 Source labels.** Position and order lists show **Broker-confirmed** and **Local ledger**
  side by side, with a reconciliation badge: `Reconciled 3 s ago` / **`UNRECONCILED`** (last
  reconciliation older than 2 × P-24, failed, or running after a reconnect) / `Mismatch (T7)`.
  Trading controls that open risk are disabled while UNRECONCILED.
- **UI-013 Requested ≠ done.** Emergency and command results show their lifecycle state
  (`REQUESTED`, `AUTHORIZED`, `SUBMITTED`, `CONFIRMED`, `PARTIAL`, `FAILED — DEADLINE`,
  `BLOCKED — MARKET CLOSED`, `RECONCILED`), never a bare check mark.
- **UI-014 No guarantee language.** Intervention thresholds are labelled "intervention at", never
  "max loss" or "protected" (RISK-041).
- **UI-015 Stop-loss truthfulness.** A position is described as having a stop-loss only when its SL
  was **broker-confirmed by read-back**, and the text shows the confirmation time: "Broker-side SL at
  4,046.00 (confirmed 10:02:14). A stop-loss does not guarantee the exit price." If the SL has not
  been read back, or broker data is unavailable: "Stop-loss status: **UNKNOWN**". The words
  "protected" or "safe" are never used for positions.
- **UI-016 Required status vocabulary.** Market data `STALE`; reconciliation `UNRECONCILED`; Guardian
  `UNKNOWN` (no heartbeat / unreadable) or `FAILED` (integrity, ACL or duplicate-instance failure,
  T22); stop-loss `UNKNOWN`; exposure `UNRESOLVED EXPOSURE` (EXE-084). Each has its own style; none is
  ever green.

## 4. Required information (by screen region)

**Top bar (always visible):** environment banner (UI-020), MT5 terminal status, broker connection
(+ ping), Guardian status (+ heartbeat age), market-data freshness, last successful reconciliation
time, aggregate health, entry-authorization chip (`MANUAL APPROVAL` / `AUTO — ALL` /
`AUTO — APPROVED STRATEGIES` / `NOT DECIDED — ENTRIES BLOCKED` / `FIXTURE DEMO — <mode>`, with a "narrowed" note while a RISK-067 rule applies), trading-state chip
(ACTIVE/ENTRY_STOP/SUSPENDED, with the recovery class of the active trigger), next session-close
countdown (P-33), emergency controls (UI-030), and the CRITICAL alerts banner (the dashboard is the
only notification channel, OBS-020/023; approval notifications come from it, OBS-024).

- **UI-020 Environment banner.** Full width, solid, never translucent, never dismissible. It shows
  three parts: **env** (`LIVE` red / `DEMO` blue / `BACKTEST` violet / `REPLAY` slate) ·
  **account class** (`CENT` or `STANDARD`, from live discovery) · **symbol and currency**
  (`XAUUSDc · USC`). If the account class is UNKNOWN, the banner says so in the unknown style.
- **UI-021 Account & risk panel:** balance, equity, realized P/L today, floating P/L (each with
  currency); risk utilisation per limit (`0.42% / 1.00% daily — intervention at 1.00%`); effective
  exposure (notional and effective leverage vs P-09); margin utilisation vs P-10; margin level vs
  P-11; daily-loss and drawdown intervention states; consecutive-loss counter;
  min-volume rejection rate (CENT-030).
- **UI-022 Strategy panel:** strategy@version, state (ACTIVE/WATCH/PAUSED), degradation warnings
  (RES-040) with the reason.
- **UI-023 Orders panel:** pending order status (normally none, P-06 = 0) and in-flight intents with
  lifecycle state (EXE §2).

## 5. State catalogue (each needs a designed visual, copy, and the actions available)

| State | Visual | Copy example | User actions |
|---|---|---|---|
| Disconnected (terminal or broker) | Solid amber bar | "Broker connection lost 00:42 ago. No new trades. GoldBot and the Guardian cannot act until it returns. Last broker-confirmed SL: 4,046.00 at 10:02:14" (or "Stop-loss status: UNKNOWN") | View runbook |
| Stale data | Grey numbers + STALE tag | "Prices 14 s old — entries blocked" | — |
| Market closed | Neutral tag | "Gold market closed — reopens Sun 22:05 server time" (from live sessions) | — |
| UNRECONCILED | Amber badge on positions | "Positions not reconciled since 10:01:50. Entries stopped until reconciliation is clean." | View diff |
| Session close approaching | Countdown chip, amber in the last 15 min | "Gold session closes 20:58 server time. New entries stopped. Positions close by 20:28." | — |
| UNRESOLVED EXPOSURE | Critical bar, persistent | "Position 0.01 lot still open after the close deadline. Close attempts continue. Stop-loss status: confirmed 4,046.00 / UNKNOWN." | Emergency Liquidation / runbook |
| Order rejected | Inline row error | "Entry rejected: 10021 no quotes. Not retried." | Dismiss |
| ENTRY_STOP | Amber state bar | "New entries stopped: daily loss intervention (T2). Exits still active." | Clear (per rule) |
| SUSPENDED | Red state bar | "Trading suspended: drawdown intervention (T4). Manual recovery required." | Start recovery checklist |
| Emergency in progress | Red bar + lifecycle list | "Liquidation REQUESTED 10:02:11 · SUBMITTED · awaiting broker confirmation" | — |
| Emergency failed | Critical bar | "Close FAILED — 60 s deadline reached after 5 attempts. Position still open. Last broker-confirmed SL: 4,046.00 at 10:02:14" (or UNKNOWN) | New Emergency Liquidation run / runbook |
| Guardian unknown/stale | Unknown style | "Guardian heartbeat not seen for 25 s — entries stopped" | Runbook |
| Guardian FAILED | Critical style | "Guardian message integrity failed (T22). Manual recovery required." | Recovery checklist |
| Automatic recovery pending | Neutral bar with timer | "Clock offset recovered. Entries resume in 3:12 if all health checks keep passing." | Keep stopped |
| Unknown health | Hatched grey | "Status unknown — not verified" | — |

## 6. Safety-critical controls

- **UI-030 Emergency controls (user decision: three separate controls, no combined button).**
  Always visible, solid surfaces, keyboard accessible, each with a **distinct visual identity**
  (icon, label and colour treatment; not distinguished by colour alone), its own confirmation, its
  own lifecycle display (UI-013) and its own audit record:
  - **Stop Entries**: amber outline, "pause" icon, one confirmation;
  - **Cancel Pending Orders**: amber filled, "remove list" icon, two-step confirmation listing the
    orders;
  - **Emergency Liquidation**: red filled, "exit" icon, placed apart from the other two; two-step
    confirmation + re-authentication (TOTP); the dialog lists positions and volumes, offers "include
    foreign positions" (unticked), and states: "Requests closes. Fills are not guaranteed."
  When Emergency Liquidation sets Stop Entries first (EXE §8), the UI shows that as a separate entry
  in the lifecycle list.
- **UI-031 Approval card:** direction, entry, SL, TP, volume, modelled loss (currency + % equity +
  ≈ USD), R:R, spread now, freshness, strategy@version, deterministic rationale (LLM-005), a
  countdown ring to expiry (P-23), and hold-to-confirm (≥ 800 ms) or a dialog. On expiry the card
  is greyed out and cannot be approved. A new card raises the approval notification (OBS-024).
- **UI-032 Entry authorization settings.** Shows the three modes with the consequences from
  TRADING_RISK_SPEC §9. While D-01 is undecided, it shows "Not decided — entries blocked" and
  nothing is pre-selected. In fixture demo it shows "Fixture demo — <mode> (test setting, not a
  decision)" (RISK-066). It lists any narrowing rules the user decided (RISK-067) and when each
  applies next. Enabling an automatic mode, or auto-approving a strategy, needs a typed
  phrase + TOTP and is possible only when the promotion gate is met; the screen shows which gate
  criteria are satisfied.

## 7. Starter tokens (V1 values kept; new status tokens added)

```jsonc
{
  "color": {
    "wash": { "lavender": "#CFC6F2", "seaglass": "#A9DCD3", "peach": "#F6CDB4", "gold": "#E8D29A" },
    "light": { "bg": "#F6F4F1", "surface-glass": "rgba(255,255,255,0.55)", "surface-solid": "rgba(255,255,255,0.90)",
               "border-hairline": "rgba(20,24,40,0.10)", "text-primary": "#141828", "text-secondary": "#4A5068" },
    "dark":  { "bg": "#0F1220", "surface-glass": "rgba(24,28,46,0.55)", "surface-solid": "rgba(22,26,42,0.92)",
               "border-hairline": "rgba(255,255,255,0.10)", "text-primary": "#EEF0F8", "text-secondary": "#A7ADC4" },
    // Contrast checked against the worst-case solid surface over each wash (see quality/V2_VALIDATION_CHECKLIST.md §3)
    "semantic-light": { "profit": "#0B7A61", "loss": "#C2413A", "warning": "#8F5F0A", "critical": "#B42318",
                        "unknown": "#4F5B67",
                        "env-live": "#B42318", "env-demo": "#2F6FDB", "env-backtest": "#6B5BD6", "env-replay": "#5C6B7A" },
    "semantic-dark":  { "profit": "#3CCB9F", "loss": "#FF8A80", "warning": "#F2B544", "critical": "#FF8A80",
                        "unknown": "#B4BCC8" }
  },
  "blur": { "sm": 8, "md": 20, "lg": 32 },
  "radius": { "sm": 8, "md": 14, "lg": 22 },
  "space": [4, 8, 12, 16, 24, 32, 48],
  "type": { "family-ui": "Inter, system-ui, sans-serif", "family-num": "'JetBrains Mono', ui-monospace",
            "size": { "caption": 12, "body": 14, "data": 15, "title": 20, "display": 32 } },
  "motion": { "fast": 120, "base": 200, "slow": 320, "easing": "cubic-bezier(0.2,0,0,1)" }
}
```
SF Pro may be used only on Apple platforms (licence). Inter is the cross-platform default.

## 8. Screens

1. **Overview** (top bar + UI-021/022/023 panels + open position card).
2. **Market:** Lightweight Charts on a solid surface; bid/ask; spread sparkline; session timeline
   from live sessions; blackout markers.
3. **Approvals:** queue + history.
4. **Positions & History:** broker vs ledger (UI-012); closed trades with tier PT2/PT3 labels.
5. **Risk:** every P-xx with utilisation; triggers T1–T27 with status, recovery class and any cooldown; pending-decision parameters shown as "Not decided"; tighten-only controls.
6. **Research:** registry; reports with tier labels (BT-001); DSR/PBO/CI with plain-language tooltips.
7. **System:** component health table (OBSERVABILITY §3); clocks (NTP offset, server offset); Guardian
   details; emergency action history.
8. **Audit:** searchable, chain-verified log.
9. **Settings:** mode switch and narrowing rules (RISK-067), consents (LLM/MCP), alerts and the
   approval-notification switch (OBS-024), theme, accessibility overrides.
10. **Narrow layout (≤ 600 px):** top bar condensed into two rows; Overview, Approvals and emergency
    controls only.
11. **Intelligence** (built in M9a; `MARKET_INTELLIGENCE_SPEC.md` MI-081/082): active strategies with
    state, regime labels and last decision; rejected signals with reason codes and counts; a decision
    explanation drawer (MI-080); per-module health on the System screen; SMC zones and liquidity
    levels labelled "inferred from price"; confidence shown as a score, never as a probability.
    V2.2 adds ten views inside this area (MI-195): Fibonacci, Chart Pattern Scanner, Setup Scanner,
    Regime, Multi-Timeframe Confluence, Trade Authorization Explanation, Trailing SL Monitor,
    Position Management, Strategy Performance (tier-labelled) and Signal Rejection Analytics. The
    trailing view always shows the last broker-confirmed SL, and a failed modification is shown as
    failed, never as applied.

## 9. Deliverables before component code (M4 gate)

Moodboard (3 procedural backdrops, light/dark); `tokens.json` + automated contrast report against
the worst-case backdrop; static mockups of Overview, Approvals and Risk at 1440 px and 390 px, light
and dark, **including the Disconnected, UNRECONCILED, SUSPENDED, UNRESOLVED EXPOSURE and Emergency-in-progress
states**; a component inventory with every state from §5. The user approves these before
components are built.
