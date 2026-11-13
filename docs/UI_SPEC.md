# UI_SPEC — GoldBot dashboard

> Status: **SPECIFICATION (M0c draft, for the M0 review and the M4 design gate).** Nothing here is
> built. Source: `prompts/UI_DESIGN_BRIEF.md` (rules UI-001..UI-032), expanded into exact
> components, states, copy and tokens. Visual direction: `Inspiration.jpg` (user decision
> 2026-11-10, CH-89; `docs/STATUS.md` §10). Themes: dark and light, dark first (user decision
> 2026-11-13; ADR-005). Where this file and a specification disagree, the specification wins
> (CLAUDE.md §2). Every gap in the API or the specs is marked **OPEN** and listed in §11.

## 1. Purpose, scope and precedence

### 1.1 Purpose

The dashboard is GoldBot's only notification channel (OBS-020) and the only place where the user
sees health, reconciliation, positions, proposals, limits and the three emergency controls. Its job
is to be **truthful first**: it never shows an unknown status as healthy (OBS-001, UI-010), never
shows a requested action as done (UI-013), and never describes a threshold or a stop-loss as a
guarantee (RISK-040/041, GRD-030).

### 1.2 Scope by milestone

| Milestone | What this spec covers there |
| --- | --- |
| M4 (read-only) | Shell, top bar, Overview, Market, Positions, Risk, System, Audit, Alerts; every state in §6; emergency controls **visible but disabled** with the label `Available from M7`; no commands, no approvals, no MCP (M4 "Out of scope") |
| M7 | Commands enabled: Stop Entries, Cancel Pending Orders, Emergency Liquidation, clear state (RISK-050), mode change, tighten limit |
| M8 | Consents, MCP client registration, MCP admin-request approvals |
| M9a | Approvals end to end with notifications (UI-031, OBS-024); Intelligence area (MI-081, MI-195) |

### 1.3 Precedence (highest first)

1. `CLAUDE.md` invariants and the `specifications/` files.
2. The numbered UI rules UI-001..UI-032 in `prompts/UI_DESIGN_BRIEF.md`. **UI-001: readability
   always wins over aesthetics.** Data surfaces are at least 85% opaque.
3. This document (tokens, components, copy, acceptance checks).
4. `Inspiration.jpg` as an aesthetic reference only.
5. Design skills (`ecc:design-system`, `ecc:liquid-glass-design`, `ecc:frontend-design-direction`).
   A skill never overrides 1–3.

### 1.4 Taken and not taken from `Inspiration.jpg` (STATUS §10)

| Taken | Not taken |
| --- | --- |
| Near-black green background; lime primary accent; cyan/teal secondary | Order book and depth panel (MT5 has none for this CFD; MI-021 forbids order-flow claims) |
| Glass panels with thin luminous borders | Wallet, staking, DeFi, NFT, "Connect Wallet", any crypto or exchange item |
| Left icon rail with outline icons; top bar with account summary | Any copied logo, glyph, illustration or asset (UI-008) |
| Tabbed chart header; candlesticks with moving averages, volume and an indicator pane | "Trade history" tape of anonymous prints (no such data source) |
| Dense tables with status dots (plus text) and pill buttons; tabular numerals | Lime used as a "good" or "profit" colour (STATUS §10) |

## 2. Design tokens

All tokens live in `web/src/design/tokens.json` (generated into CSS custom properties). Component
code uses tokens only; a lint rule rejects raw hex values outside the token file (UIT-05).

### 2.1 Colour tokens — dark theme (default)

| Token | Value | Use |
| --- | --- | --- |
| `bg.canvas` | `#070D0A` | App background behind everything |
| `bg.backdrop` | baked static image, range `#050A07`..`#1C3326` | Shell background only (UI-001, UI-007); lightest patch `#1C3326` is the contrast worst case |
| `surface.panel` | `rgba(15, 29, 22, 0.92)` (`#0F1D16` at 92%) | Data panels, tables, cards; **no** backdrop blur |
| `surface.raised` | `rgba(21, 39, 30, 0.94)` | Row hover, selected tab, popovers |
| `surface.topbar` | `rgba(12, 24, 18, 0.90)` | Top bar (blur layer 1) |
| `surface.rail` | `rgba(10, 20, 15, 0.80)` | Icon rail (blur layer 2); carries labels and icons only, no live numbers |
| `surface.modal` | `rgba(16, 31, 24, 0.96)` | Dialogs and sheets (blur layer 3) |
| `surface.solid` | `#0E1A14` | Emergency strip, banners' inner content, reduced-transparency fallback |
| `surface.chart` | `#0A130E` | Chart canvas (solid; never blurred, UI-002) |
| `border.hairline` | `rgba(160, 255, 200, 0.10)` | Panel and table dividers (decorative) |
| `border.luminous` | `rgba(184, 242, 58, 0.22)` | 1 px top edge of glass panels (decorative, §2.8) |
| `border.control` | `#5E7A6B` | Input, checkbox and outline-button borders (3:1) |
| `focus.ring` | `#7FE7FF` | Focus outline, 2 px, offset 2 px |
| `text.primary` | `#E8F2EC` | Values, headings |
| `text.secondary` | `#AFC2B6` | Labels, column headers |
| `text.tertiary` | `#8FA699` | Captions, timestamps (still ≥ 4.5:1) |
| `text.disabled` | `#6B8277` | Disabled controls only (exempt from 1.4.3, always paired with a reason text) |
| `brand.lime` | `#B8F23A` | Brand accent: primary button fill, active rail marker, selected tab underline, `MA fast` line |
| `brand.lime-ink` | `#B8F23A` | Lime used as text or stroke |
| `brand.on-lime` | `#0A1405` | Text on `brand.lime` fill |
| `accent.cyan` | `#4FD3E6` | Secondary accent: links, `MA slow` line, selected chart timeframe |
| `status.healthy` | `#6BDB94` | `HEALTHY` only |
| `status.warning` | `#F5B83D` | `ENTRY_STOP`, `UNRECONCILED`, `DELAYED`, session close < 15 min, Stop Entries identity |
| `status.degraded` | `#FFA066` | `DEGRADED` |
| `status.critical` | `#FF7A73` | `UNHEALTHY`, `FAILED`, `SUSPENDED`, `UNRESOLVED EXPOSURE`, CRITICAL alerts (as text) |
| `status.unknown` | `#A9B6AF` + hatch | `UNKNOWN`, `STALE` values; hatch = 45° stripes `rgba(255,255,255,0.06)` 1 px every 6 px |
| `pl.profit` | `#34D6A6` | Positive P/L (always with `+` and ▲) |
| `pl.loss` | `#FF8F84` | Negative P/L (always with `−` and ▼) |
| `bar.critical` / `bar.on-critical` | `#7F1D1D` / `#FFFFFF` | Critical state bars and the CRITICAL alert banner |
| `bar.warning` / `bar.on-warning` | `#4A3508` / `#FFE7B0` | Warning state bars; FIXTURE banner |
| `bar.unknown` / `bar.on-unknown` | `#26302C` / `#E1E8E4` | Unknown state bars (with hatch) |
| `btn.liquidate` / `btn.on-liquidate` | `#C42B1C` / `#FFFFFF` | Emergency Liquidation fill |
| `btn.cancel` / `btn.on-cancel` | `#F5B83D` / `#1A1200` | Cancel Pending Orders fill |
| `chart.up` / `chart.down` | `#3CC9A6` / `#F0757E` | Candle bodies (up = hollow outline, down = filled; shape differs, not only colour) |
| `chart.ma-fast` / `chart.ma-slow` | `#B8F23A` / `#4FD3E6` | Moving averages (legend names them) |
| `chart.grid` | `rgba(175, 194, 182, 0.08)` | Grid lines (decorative) |

### 2.2 Colour tokens — light theme

| Token | Value | Note |
| --- | --- | --- |
| `bg.canvas` | `#EEF3EF` | |
| `bg.backdrop` | baked static image, range `#C6D4CA`..`#F7FAF8` | Darkest patch `#C6D4CA` is the worst case |
| `surface.panel` | `rgba(255, 255, 255, 0.92)` | |
| `surface.raised` | `rgba(255, 255, 255, 0.96)` | |
| `surface.topbar` | `rgba(250, 252, 251, 0.90)` | |
| `surface.rail` | `rgba(244, 248, 245, 0.82)` | |
| `surface.modal` | `rgba(255, 255, 255, 0.97)` | |
| `surface.solid` / `surface.chart` | `#FFFFFF` / `#FBFDFC` | |
| `border.hairline` / `border.luminous` | `rgba(14, 26, 19, 0.10)` / `rgba(74, 115, 0, 0.25)` | Decorative |
| `border.control` | `#7A8C81` | |
| `focus.ring` | `#0A5FB4` | |
| `text.primary` / `.secondary` / `.tertiary` / `.disabled` | `#0E1A13` / `#3B4E43` / `#4F6357` / `#8A9A90` | |
| `brand.lime` / `brand.on-lime` | `#B8F23A` / `#0A1405` | Fill only; lime is never text on light |
| `brand.lime-ink` | `#4A7300` | Lime used as text, underline or stroke |
| `accent.cyan` | `#08707F` | |
| `status.healthy` / `.warning` / `.degraded` / `.critical` / `.unknown` | `#1B7A41` / `#8A5A00` / `#A24A12` / `#B42318` / `#53616A` | Unknown hatch: `rgba(0,0,0,0.06)` |
| `pl.profit` / `pl.loss` | `#0B7560` / `#B93A33` | |
| `bar.critical` / `bar.on-critical` | `#B42318` / `#FFFFFF` | |
| `bar.warning` / `bar.on-warning` | `#FCEFC7` / `#5C3D00` | |
| `bar.unknown` / `bar.on-unknown` | `#E3E8E5` / `#2B3530` | |
| `btn.liquidate` / `btn.on-liquidate` | `#B42318` / `#FFFFFF` | |
| `btn.cancel` / `btn.on-cancel` | `#F5B83D` / `#1A1200` | |
| `chart.up` / `chart.down` | `#0E8A6E` / `#C8434C` | |
| `chart.ma-fast` / `chart.ma-slow` | `#5E8F00` / `#0A7C8C` | |
| `chart.grid` | `rgba(14, 26, 19, 0.07)` | |

### 2.3 Environment banner tokens (both themes, solid, UI-020)

| `env` | Background | Text | Contrast |
| --- | --- | --- | --- |
| `LIVE` | `#B3261E` (red) | `#FFFFFF` | 6.54:1 |
| `DEMO` | `#1F5FBF` (blue) | `#FFFFFF` | 6.09:1 |
| `BACKTEST` | `#5B47C9` (violet) | `#FFFFFF` | 6.58:1 |
| `REPLAY` | `#4A5866` (slate) | `#FFFFFF` | 7.29:1 |

### 2.4 Semantic rules

- **Brand lime is never a status or P/L colour.** `brand.lime` and `status.healthy` / `pl.profit`
  are separate tokens with different hues (lime `#B8F23A` vs green `#6BDB94` vs mint `#34D6A6` in
  dark). A test compares the resolved values (UIT-06).
- **Health state → token, icon and label** (OBS §3; display rank OBS-001: `HEALTHY` < `DEGRADED` <
  `UNKNOWN` < `UNHEALTHY` < `FAILED`):

| Health | Token | Icon (outline) | Label |
| --- | --- | --- | --- |
| `HEALTHY` | `status.healthy` | circle-check | `Healthy` |
| `DEGRADED` | `status.degraded` | triangle-minus | `Degraded` |
| `UNKNOWN` | `status.unknown` + hatch | circle-question ("?") | `Unknown — not verified` |
| `UNHEALTHY` | `status.critical` | octagon-x | `Unhealthy` |
| `FAILED` | `status.critical` on `bar.critical` | octagon-x (filled) | `Failed` |
| MCP not configured | `text.tertiary` | circle-off | `Off` |

- **Status chip anatomy:** icon (16 px) + text label + optional age, on a tint of the status token
  (16% in dark, 10% in light) with a 1 px border in the status token. Colour is never the only
  carrier (UI-004).
- `WARNING` is not a health state; it is the display token for the latching and pending conditions
  listed in §2.1 (`ENTRY_STOP`, `UNRECONCILED`, `DELAYED`, session close < 15 min).

### 2.5 Contrast results (computed)

Method: WCAG 2.x relative luminance. Each translucent surface was composited at its opacity over
**both** ends of the backdrop range, and the patch giving the lower contrast with `text.primary` was
used (UI-003 worst case). Composited worst-case surfaces: dark panel `#101F17`, raised `#15281E`,
top bar `#0E1B14`, rail `#0E1A14`, modal `#102019`; light panel `#FAFCFB`, raised `#FDFDFD`, top
bar `#F5F8F6`, rail `#ECF2ED`, modal `#FDFEFD`. Text tokens were checked on panel, raised, top bar,
modal, solid and chart surfaces, and on their own chip tint; UI tokens (3:1) on panel and chart; the
focus ring on every surface (it sits on the surface because of its 2 px offset). 234 pairs, 0
failures. The table lists each token's **lowest** ratio and where it occurred.

| Theme | Token | Lowest ratio | Against | Needs | Result |
| --- | --- | --- | --- | --- | --- |
| dark | `text.primary` | 13.55:1 | raised | 4.5:1 | PASS |
| dark | `text.secondary` | 8.28:1 | raised | 4.5:1 | PASS |
| dark | `text.tertiary` | 5.97:1 | raised | 4.5:1 | PASS |
| dark | `brand.lime-ink` | 11.67:1 | raised | 4.5:1 | PASS |
| dark | `accent.cyan` | 6.75:1 | cyan chip tint | 4.5:1 | PASS |
| dark | `status.healthy` | 6.92:1 | healthy chip tint | 4.5:1 | PASS |
| dark | `status.warning` | 6.88:1 | warning chip tint | 4.5:1 | PASS |
| dark | `status.degraded` | 6.26:1 | degraded chip tint | 4.5:1 | PASS |
| dark | `status.critical` | 5.26:1 | critical chip tint | 4.5:1 | PASS |
| dark | `status.unknown` | 5.96:1 | unknown chip tint | 4.5:1 | PASS |
| dark | `pl.profit` | 6.58:1 | profit chip tint | 4.5:1 | PASS |
| dark | `pl.loss` | 5.85:1 | loss chip tint | 4.5:1 | PASS |
| dark | `border.control` | 3.63:1 | panel | 3.0:1 | PASS |
| dark | `focus.ring` | 10.91:1 | raised | 3.0:1 | PASS |
| dark | `chart.up` / `chart.down` | 8.21:1 / 6.14:1 | panel | 3.0:1 | PASS |
| dark | `chart.ma-fast` / `chart.ma-slow` | 12.84:1 / 9.58:1 | panel | 3.0:1 | PASS |
| dark | `brand.on-lime` on `brand.lime` | 14.17:1 | lime fill | 4.5:1 | PASS |
| dark | `bar.on-critical` / `bar.on-warning` / `bar.on-unknown` | 10.02:1 / 9.60:1 / 9.13:1 | own bar (unknown incl. hatch) | 4.5:1 | PASS |
| dark | `btn.on-liquidate` / `btn.on-cancel` | 5.66:1 / 10.44:1 | own fill | 4.5:1 | PASS |
| light | `text.primary` | 15.73:1 | rail | 4.5:1 | PASS |
| light | `text.secondary` | 7.85:1 | rail | 4.5:1 | PASS |
| light | `text.tertiary` | 6.03:1 | top bar | 4.5:1 | PASS |
| light | `brand.lime-ink` | 5.25:1 | top bar | 4.5:1 | PASS |
| light | `accent.cyan` | 4.87:1 | cyan chip tint | 4.5:1 | PASS |
| light | `status.healthy` | 4.56:1 | healthy chip tint | 4.5:1 | PASS |
| light | `status.warning` | 5.01:1 | warning chip tint | 4.5:1 | PASS |
| light | `status.degraded` | 5.00:1 | degraded chip tint | 4.5:1 | PASS |
| light | `status.critical` | 5.40:1 | critical chip tint | 4.5:1 | PASS |
| light | `status.unknown` | 5.38:1 | unknown chip tint | 4.5:1 | PASS |
| light | `pl.profit` | 4.74:1 | profit chip tint | 4.5:1 | PASS |
| light | `pl.loss` | 4.75:1 | loss chip tint | 4.5:1 | PASS |
| light | `border.control` | 3.46:1 | panel | 3.0:1 | PASS |
| light | `focus.ring` | 5.59:1 | rail | 3.0:1 | PASS |
| light | `chart.up` / `chart.down` | 4.18:1 / 4.67:1 | panel | 3.0:1 | PASS |
| light | `chart.ma-fast` / `chart.ma-slow` | 3.77:1 / 4.77:1 | panel | 3.0:1 | PASS |
| light | `brand.on-lime` on `brand.lime` | 14.17:1 | lime fill | 4.5:1 | PASS |
| light | `bar.on-critical` / `bar.on-warning` / `bar.on-unknown` | 6.57:1 / 8.63:1 / 8.97:1 | own bar (unknown incl. hatch) | 4.5:1 | PASS |
| light | `btn.on-liquidate` / `btn.on-cancel` | 6.57:1 / 10.44:1 | own fill | 4.5:1 | PASS |

Notes: light-theme chips must use the 10% tint; at 16% `status.healthy`, `pl.profit`, `pl.loss` and
`accent.cyan` drop below 4.5:1. `chart.grid`, `border.hairline` and `border.luminous` are
decorative and carry no information. M4 re-runs this computation as an automated test against the
real baked backdrop images (UIT-04); a failure there overrides this table.

### 2.6 Typography

No remote font is loaded (CSP `default-src 'self'`, API-003; local-first). v1 uses system stacks.

| Token | Value |
| --- | --- |
| `font.ui` | `"Segoe UI Variable Text", "Segoe UI", system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif` |
| `font.mono` | `"Cascadia Mono", Consolas, ui-monospace, "SF Mono", Menlo, monospace` (IDs, hashes, op_ids, retcodes) |
| `font.numeric` | `font.ui` with `font-variant-numeric: tabular-nums lining-nums; font-feature-settings: "tnum" 1, "lnum" 1` |

| Role | Size / line height | Weight | Notes |
| --- | --- | --- | --- |
| `type.caption` | 12 / 16 px | 400 | Minimum size anywhere |
| `type.label` | 12 / 16 px | 600 | Panel titles, upper case, letter-spacing 0.04em (as in the inspiration) |
| `type.body` | 14 / 20 px | 400 | |
| `type.data` | 15 / 20 px | 500 | Every number in tables and cards; `font.numeric` |
| `type.title` | 18 / 24 px | 600 | Screen titles |
| `type.price` | 32 / 40 px | 600 | Chart header price; `font.numeric` |

Every element that renders a number (price, volume, money, %, count, age) uses `font.numeric`
(UI-005, UIT-15). Text is resizable to 200% without loss of content (SC 1.4.4).

### 2.7 Spacing, sizing, radii

- **Space scale (px):** `space.1` 4 · `space.2` 8 · `space.3` 12 · `space.4` 16 · `space.5` 24 ·
  `space.6` 32 · `space.7` 48. Panel padding `space.4`; gap between panels `space.3`.
- **Radii (px):** `radius.sm` 6 (chips, inputs) · `radius.md` 10 (buttons) · `radius.lg` 14
  (panels, dialogs) · `radius.pill` 999 (pill buttons, tags).
- **Sizes:** rail width 72 px (icon 24 px; labels as tooltips plus `aria-label`; the expanded rail
  at ≥ 1440 px is 216 px with visible labels); top bar
  height 56 px; env banner height 32 px; table row 36 px; minimum target 24 × 24 px (SC 2.5.8);
  emergency buttons 44 px high, minimum 160 px wide.

### 2.8 Glass, blur budget, elevation

- **Blur layers (UI-002), at most three on screen:** `blur.rail` 20 px on the rail; `blur.topbar`
  20 px on the top bar; `blur.modal` 32 px on one open dialog or sheet. Dialogs never stack: the
  re-authentication step replaces the confirmation step inside the same dialog. Data panels,
  tables and the chart use **no** `backdrop-filter`. A test counts layers (UIT-08).
- **Luminous edge:** panels get `box-shadow: inset 0 1px 0 var(--border-luminous)` plus a 1 px
  `border.hairline`. No glow behind text, no `text-shadow` anywhere.
- **Elevation:** `shadow.panel` `0 1px 2px rgba(0,0,0,0.40)` (dark) / `0 1px 2px rgba(14,26,19,0.08)`
  (light); `shadow.modal` `0 16px 48px rgba(0,0,0,0.55)` / `0 16px 48px rgba(14,26,19,0.18)`.
- **Glow:** only `shadow.glow-lime` `0 0 0 1px rgba(184,242,58,0.35), 0 0 12px rgba(184,242,58,0.18)`
  on the primary button and the active rail marker, and only outside the element, so it never
  lowers the contrast of any text. Status, emergency and P/L elements never glow.
- **Fallbacks (UI-006):** `prefers-reduced-transparency: reduce` or `prefers-contrast: more` → every
  surface uses its solid equivalent (`surface.solid`), blur off, hairlines become `border.control`.
  Frame drops below 50 fps for 2 s → blur off for the session (UI-007).

### 2.9 Motion

| Token | Value | Allowed use |
| --- | --- | --- |
| `motion.fast` | 120 ms, `cubic-bezier(0.2, 0, 0, 1)` | Colour and border transitions on hover and focus |
| `motion.base` | 200 ms, same easing | Dialog and sheet fade/slide in |
| `motion.countdown` | linear, 1 s steps | Approval expiry ring (P-23) and emergency deadline bar (P-25): real safety states |

Nothing pulses, blinks, shimmers or loops. Loading uses a static skeleton, not a shimmer. Live
numbers update in place without flashing. `prefers-reduced-motion: reduce` → all transitions 0 ms
and countdowns show numbers only (the ring is drawn without animation, updated once per second).

### 2.10 Z-index layers

| Layer | z-index |
| --- | --- |
| Content, chart | 0 |
| Chart overlays (staleness overlay, price lines) | 10 |
| Sticky table headers | 20 |
| Rail | 100 |
| Top bar | 110 |
| Env banner and FIXTURE banner | 120 |
| CRITICAL alert banner | 130 |
| Popovers, menus, tooltips | 200 |
| Drawers and sheets | 300 |
| Dialogs | 400 |
| Skip link (when focused) | 1000 |

No layer may cover the env banner or the emergency strip except a dialog, and a dialog never covers
the env banner (dialogs start below it).

### 2.11 Breakpoints

The API is loopback-only (ADR-013), so "phone width" means a narrow window on the host, not a
remote phone.

| Name | Width | Layout |
| --- | --- | --- |
| `bp.phone` | ≤ 600 px (tested at 390) | Rail becomes a bottom tab bar (Overview, Approvals, Alerts, More); top bar condenses to two rows; only Overview, Approvals and the emergency controls (brief §8.10) |
| `bp.tablet` | 601–1023 px | Rail 72 px; one content column |
| `bp.desktop` | 1024–1439 px | Rail 72 px; two content columns |
| `bp.wide` | ≥ 1440 px (tested at 1440) | Rail 216 px with labels; three columns on Overview |

### 2.12 Icons

Original outline icons drawn for GoldBot (UI-008) on a 24 px grid, 1.5 px stroke, round caps,
inline SVG with `aria-hidden="true"` when a text label is present. No icon package is added (an icon
library is a dependency outside CLAUDE.md §5). Required set: overview, chart, approvals, positions,
risk, intelligence, research, system, audit, settings, alert-bell, theme, logout, pause (Stop
Entries), list-x (Cancel Pending Orders), exit-door (Emergency Liquidation), circle-check,
triangle-minus, triangle-alert, octagon-x, circle-question, circle-off, lock, clock, link-chain,
arrow-up-triangle (▲), arrow-down-triangle (▼).

## 3. App shell and layout

### 3.1 Desktop shell (≥ 1024 px)

```text
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│ ENV BANNER  DEMO · CENT · XAUUSDc · USC                                  (solid, 32 px)  │
│ FIXTURE BANNER (only in fixture demo / fixture params)                                   │
├──────┬───────────────────────────────────────────────────────────────────────────────────┤
│ RAIL │ TOP BAR (56 px, glass)                                                            │
│ ◻ Ov │ Equity · Balance · Floating P/L │ Health ▸ │ Trading state │ Entry auth │ Session  │
│ ◻ Mk │ ──────────────────────────────── │ Terminal · Broker · Data · Guardian · Recon     │
│ ◻ Ap │                                   │  [Stop Entries] [Cancel Pending]  ║ [Emergency  │
│ ◻ Po │                                   │                                   ║ Liquidation]│
│ ◻ Rk ├───────────────────────────────────────────────────────────────────────────────────┤
│ ◻ In │ CRITICAL ALERT BANNER (persistent until acknowledged)                             │
│ ◻ Rs ├───────────────────────────────────────────────────────────────────────────────────┤
│ ◻ Sy │ STATE BAR (ENTRY_STOP / SUSPENDED / Disconnected / UNRECONCILED …)                │
│ ◻ Au ├───────────────────────────────────────────────────────────────────────────────────┤
│      │ SCREEN CONTENT (panels at ≥ 85% opacity)                                          │
│ ◻ ⚙  │                                                                                   │
│ 🔔 ◐ ⏻│                                                                                   │
└──────┴───────────────────────────────────────────────────────────────────────────────────┘
```

- **Env banner** is the first element in the DOM after the skip link, full width, never
  translucent, never dismissible, never scrolled away (UI-020).
- **Top bar** has three zones: account summary (left), status chips (centre), emergency strip
  (right, on `surface.solid`). Emergency Liquidation sits apart from the other two with a 24 px gap
  and a vertical divider (UI-030).
- **Rail** (top to bottom): Overview, Market, Approvals (with count badge, text not only colour),
  Positions & History, Risk, Intelligence (M9a; hidden until built), Research, System, Audit;
  bottom group: Settings, Alerts (bell with unacknowledged count), theme toggle, Log out. The active
  item has a 3 px `brand.lime` bar on its left edge and `aria-current="page"`.
- **Order of stacking under the top bar:** CRITICAL alert banner, then the state bar, then content.
  Neither can be scrolled away while active.

### 3.2 Phone shell (≤ 600 px)

```text
┌─────────────────────────────┐
│ ENV  DEMO · CENT · XAUUSDc  │
├─────────────────────────────┤
│ Health ▸ · State · Entry auth│  row 1
│ Equity · Floating · Session  │  row 2
├─────────────────────────────┤
│ CRITICAL / STATE BAR        │
├─────────────────────────────┤
│ content (one column)        │
├─────────────────────────────┤
│ [Stop] [Cancel]  │ [Liquid.] │  emergency strip, fixed above tab bar
├─────────────────────────────┤
│ Overview  Approvals  Alerts ⋯│
└─────────────────────────────┘
```

On phone width the emergency buttons keep their full labels (two lines allowed) and their icons;
they are never collapsed into a menu.

### 3.3 Screens and panels

| # | Screen | Route (SPA) | Panels | Milestone |
| --- | --- | --- | --- | --- |
| 1 | Overview | `/` | Account & risk (UI-021); Strategy (UI-022); Orders & in-flight (UI-023); Open position card(s); Recent alerts; Mini chart | M4 |
| 2 | Market | `/market` | Chart header (tabs, price, freshness); Chart (§8); Bid/ask and spread; Spread sparkline; Session timeline with blackout markers | M4 |
| 3 | Approvals | `/approvals` | Mode notice; Approval queue (cards, UI-031); Approval history | M9a (M4: placeholder with mode notice) |
| 4 | Positions & History | `/positions` | Reconciliation badge; Positions: broker-confirmed vs local ledger (UI-012); Pending orders; Closed trades with tier labels (PT2/PT3) | M4 |
| 5 | Risk | `/risk` | Trading state and active triggers; Parameter table P-01..P-37 with utilisation; Trigger table T1–T27; Recovery checklist (RISK-050); Tighten dialog | M4 read-only; commands M7 |
| 6 | Intelligence | `/intelligence` | Active strategies, regime, last decision; Rejected signals; Decision drawer (MI-080); the ten MI-195 views | M9a |
| 7 | Research | `/research` | Registry; Reports with tier labels (BT-001); DSR/PBO/CI with plain-language tooltips | M4 read-only (data from M5/M6) |
| 8 | System | `/system` | Component health table (OBS §3); Clocks; Guardian details; Metrics (OBS §2); Emergency action history; Module health (MI-018) | M4 |
| 9 | Audit | `/audit` | Audit summary and chain status; event list | M4 |
| 10 | Settings | `/settings` | Entry authorization (UI-032); Notifications (OBS-024); Consents (LLM/MCP); MCP clients and admin requests; Theme; Accessibility overrides; Privacy mode | M4 view; commands M7/M8 |
| 11 | Alerts | `/alerts` | Notification centre (§7.6) | M4 |

## 4. Global state model and shared copy

### 4.1 Data freshness (UI-010, UI-011, API-051)

Every live value carries one freshness label, computed client-side from the WebSocket message
(`as_of_utc`, `freshness`, API-051) and the client's monotonic clock (`performance.now()` elapsed
since receipt; TIME rule: durations use monotonic time).

| Label | Condition | Visual | Copy |
| --- | --- | --- | --- |
| `REAL-TIME` | tick age ≤ 2 s | `text.secondary` label, filled dot | `REAL-TIME` |
| `DELAYED` | 2 s < tick age ≤ P-15 | `status.warning` label | `DELAYED · <n> s` |
| `STALE` | tick age > P-15 with the session open (TIME-022) | value in `status.unknown`, hatch, no animation, age shown | `STALE · <n> s old — entries blocked` |
| `MARKET CLOSED` | session closed per the live session export (EXE-080) | neutral tag | `MARKET CLOSED — reopens <ddd HH:MM> server time` |
| `UNKNOWN` | no message on the channel for > 5 s, or field missing | unknown style, last value **removed**, not greyed | `Unknown — not verified` |

The last good value is never shown as current once UNKNOWN applies (UI-010). STALE values stay
visible in grey with their age because they are known to be old.

### 4.2 Shared component states and exact copy

Every data component implements these states. `<Panel>` is the panel title.

| State | Trigger | Visual | Copy |
| --- | --- | --- | --- |
| Loading | First fetch in flight, no data yet | Static skeleton rows (no shimmer), `aria-busy="true"` | `Loading <panel>…` |
| Empty | Fetch succeeded, zero items | Panel with icon and one line | Per component (§5) |
| Stale | Freshness `STALE` (§4.1) | Grey values, hatch, age | `STALE · <n> s old` |
| Error | REST call returned problem JSON (API-061) | Inline error row on `bar.unknown` | `Could not load <panel>. <title from problem JSON>. Reference <trace_id>.` + `Retry` button |
| Disconnected | WebSocket closed or token refresh failed | Unknown style on every live value in the panel | `Live updates disconnected. Values hidden until the stream returns. Reconnecting…` |
| Unknown | Stream silent > 5 s, a field missing, or a health computation timed out (OBS-002) | Unknown style, "?" icon | `Unknown — not verified` |
| Not yet available | Feature belongs to a later milestone | Neutral text, control disabled | `Available from M<n>` |

Retries of REST reads use exponential back-off (1, 2, 4, 8 s, cap 30 s) and never more than the
API-062 read limit. Error copy never includes a stack trace, SQL or path (API-061).

### 4.3 Time display

Records are UTC (DATA-003); sessions are in broker server time (TIME, Guardian export). Every time
shown on screen carries its zone: `10:02:14 UTC`, `20:58 server time`, or, if the user picks local
display in Settings, `11:02:14 local`. Ages are relative (`3 s ago`) with the absolute time in the
tooltip and in the accessible name.

## 5. Component catalogue

Data-source notes: routes and channels are from API_SPEC §4 and §6; field names are from the record
schemas in `schemas/` (DATA-011). **API_SPEC defines routes but no response bodies (OPEN-01):** each
component below names the schema it expects; the per-route response schema must be fixed before M4.

### 5.1 Shell and top bar

**C-01 EnvBanner** — Purpose: show `env`, account class, symbol and currency at all times (UI-020).
Source: `GET /v1/account` (`env`, `account_class`, `currency` from `account_snapshot`) and the
selected symbol (CENT-002/005). Every WebSocket message also carries `env` (API-051).

| State | Copy |
| --- | --- |
| Normal | `LIVE · CENT · XAUUSDc · USC` (example; values from live discovery) |
| Account class `UNKNOWN` | `DEMO · ACCOUNT CLASS UNKNOWN — not verified · <symbol> · <currency>` in `bar.unknown` style inside the env colour bar |
| Loading | `<env> · discovering account…` (env is known from the served config before the account loads) |
| `env` mismatch between messages | `ENVIRONMENT MISMATCH — data hidden` and every data panel switches to Unknown (fail closed) |

A11y: `role="banner"` is the page header; the env banner is a `<div role="status" aria-live="off">`
with a visible text label. Not focusable. Never hidden by any layout.

**C-02 FixtureBanner** — Shown when any record carries `params = FIXTURE` (RISK-066 item 3) or a
BACKTEST/REPLAY report uses fixture values (RISK-005). `bar.warning`, full width, under C-01.
Copy: `FIXTURE PARAMETERS — NOT APPROVED SETTINGS` and, in fixture demo, `· Fixture demo —
<fixture_demo_mode> (test setting, not a decision)`.

**C-03 AccountSummary** — Equity, balance, floating P/L, margin level. Source: `GET /v1/account`,
WS `account`. Fields: `equity`, `balance`, `margin_level`, `currency`; floating P/L = OPEN-01
(not a field of `account_snapshot`; needs a position-level or account-level field). Format per §9.3.
States: §4.2; Unknown copy per value: `Equity: Unknown — not verified`.

**C-04 HealthChip (aggregate)** — Worst component state (OBS-001). Source: `GET /v1/health`
(`aggregate`, `components`), WS `health`. Shows `Health: Healthy` only when every required component
is `HEALTHY`; otherwise the worst label and the component name, e.g. `Health: Unknown — Guardian`.
Click opens the health popover listing the 13 components of `health_status.components`
(MT5_TERMINAL … MCP) with state, reason and time of last change.

**C-05 ComponentChips** — Five compact chips: Terminal, Broker (+ ping ms), Market data
(+ freshness), Guardian (+ heartbeat age), Reconciliation (+ last clean run age). Source: WS
`health`. Copy examples: `Terminal: Healthy`, `Broker: Healthy · 84 ms`, `Data: STALE · 14 s`,
`Guardian: Unknown — no heartbeat for 25 s`, `Reconciled 3 s ago`, `UNRECONCILED since 10:01:50 UTC`.
At `bp.tablet` and below only C-04 is shown; the popover holds the rest.

**C-06 EntryAuthChip (UI-032)** — Source: `GET /v1/config/limits` (P-37 value and approval) and
`mode_change` events on WS `risk` (OPEN-01 for the channel payload). Click goes to Settings §7.2.

| Condition | Chip copy | Token |
| --- | --- | --- |
| P-37 = `MANUAL_APPROVAL` | `MANUAL APPROVAL` | neutral |
| P-37 = `AUTO_ALL`, enabled (RISK-061 met) | `AUTO — ALL` | neutral, `brand.lime-ink` icon |
| P-37 = `AUTO_APPROVED_STRATEGIES` | `AUTO — APPROVED STRATEGIES (<n>)` | neutral |
| P-37 not approved | `NOT DECIDED — ENTRIES BLOCKED` | `status.warning` |
| Fixture demo | `FIXTURE DEMO — <mode>` | `bar.warning` |
| Demoted (RISK-062, `mode_change.cause = DEMOTION`) | `<mode> · DEMOTED — APPROVAL REQUIRED (<trigger>)` | `status.warning` |
| Automation paused after recovery or unclean restart (RISK-050, EXE-071) | `<mode> · AUTOMATION PAUSED — approval required until you re-confirm` | `status.warning` |
| Decided automatic mode not yet enabled (RISK-061 gate not met) | `AUTO — ALL · NOT ENABLED — promotion gate not met` (**OPEN-11**: whether entries are blocked or need approval meanwhile) | `status.warning` |
| A narrowing rule applies now (RISK-067) | suffix `· narrowed: <rule name>` | — |
| Unknown | `Entry authorization: Unknown — not verified` | unknown |

User decision D-01 (2026-11-13) is `AUTO_ALL`; the other rows remain for fixture demo, demotion and
any later change by the user.

**C-07 TradingStateChip** — Source: `GET /v1/risk`, WS `risk` (`trading_state_event`:
`to_state`, `trigger`, `recovery_class`, `cooldown_ms`). Copy: `ACTIVE`; `ENTRY_STOP · T2 · ACK`;
`SUSPENDED · T4 · MANUAL`; with several triggers, the highest state plus `+<n> more`. Tokens: ACTIVE
neutral with circle-check outline (never `status.healthy` fill), ENTRY_STOP `status.warning`,
SUSPENDED `status.critical`. Unknown: `Trading state: Unknown — not verified`.

**C-08 SessionCloseChip** — Next session close and the P-33 deadline. Source: OPEN-07 (no session
calendar route; the `SESSION_END_READINESS` component of `/v1/health` gives only health). Copy:
`Session closes 20:58 server time · new entries stop 19:58 · positions close by 20:28`. Amber in
the last 15 min before the P-33 deadline. Calendar unknown (EXE-085): `Session calendar: Unknown —
entries blocked from the earliest plausible close`.

**C-09 EmergencyStrip** — §6. Always rendered, on `surface.solid`, in the top bar (desktop) or
fixed above the tab bar (phone).

**C-10 CriticalAlertBanner** — §7.6. `bar.critical`, persistent until acknowledged (OBS-020),
`role="alert"` on first appearance only.

**C-11 StateBar** — Renders the active rows of the state catalogue (§5.9). One bar per active state,
most severe first, at most three visible plus `+<n> more states`.

### 5.2 Overview panels

**C-20 AccountRiskPanel (UI-021)** — Source: `GET /v1/account`, `GET /v1/risk`, WS `account`,
`risk`. Rows, each with currency or unit:

| Row | Example copy |
| --- | --- |
| Balance | `10,012.40 USC  ≈ $100.12` |
| Equity | `9,987.10 USC  ≈ $99.87` |
| Realized P/L today | `▼ −25.30 USC` |
| Floating P/L | `▲ +3.10 USC` |
| Daily loss utilisation | `0.42% / 1.00% daily — intervention at 1.00%` |
| Weekly loss utilisation | `0.42% / 2.00% weekly — intervention at 2.00%` |
| Drawdown from high-water mark | `0.80% / 5.00% — intervention at 5.00%` |
| Aggregate open risk (P-31) | `0.25% / 0.25% of equity` |
| Effective exposure (P-09) | `Notional 3,950.00 USC · effective leverage 0.40× / 1.0×` |
| Margin utilisation (P-10) | `2.1% / 10%` |
| Projected margin level (P-11) | `4,760% / minimum 1,000%` |
| Consecutive losses (P-07/P-08) | `1 · entry stop at 3 · suspend at 5` |
| Min-volume rejection rate (CENT-030) | `12% of signals skipped (minimum lot over budget)` |

Bars show utilisation with a text value; the bar is decorative (`aria-hidden`), the text is the
value. Empty: not applicable (always populated or Unknown). Unknown per row as §4.2.

**C-21 StrategyPanel (UI-022)** — Source: `GET /v1/strategies/performance`, WS `risk` (OPEN-01:
strategy state field). Row: `strategy@version`, state `ACTIVE` / `WATCH` / `PAUSED` (RES-040),
degradation reason, tier label. Empty: `No strategy is active. Strategies are added through research
and your approval (D-08).`

**C-22 OrdersPanel (UI-023)** — Source: `GET /v1/orders`, WS `commands` (in-flight intents with
their EXE §2 state). Pending orders are normally none (P-06 = 0). Empty: `No pending orders. No
operation in flight.` In-flight row copy: `Entry BUY 0.01 · SUBMITTED 10:02:11 UTC · awaiting
broker confirmation`; `UNKNOWN — reconciling (no resubmission until resolved)`. Never a check mark
before `COMPLETED`.

**C-23 PositionCard** — Source: `GET /v1/positions`, WS `positions` (`position_state`). Shows side,
volume, open price, current price with freshness, floating P/L, SL and TP, ownership
(`ENGINE` / `GUARDIAN` / `FOREIGN`), strategy. **SL line (UI-015, GRD-030):**

- `sl_broker_confirmed = true`: `Broker-side SL at 4,046.00 (confirmed 10:02:14 UTC). A stop-loss
  does not guarantee the exit price.`
- otherwise, or broker data unavailable: `Stop-loss status: UNKNOWN` in unknown style.

Empty: `No open positions.` Words "protected" and "safe" never appear (UI-015).

### 5.3 Market screen

**C-30 ChartHeader** — Tabs (the symbol and its timeframes `M1 M5 M15 M30 H1 H4 D1`, from the
`timeframe` enum), price in `type.price`, change, session high/low, freshness label. Source:
`GET /v1/market/snapshot`, WS `market`. Tabs are a `role="tablist"`; arrow keys move between tabs.

**C-31 PriceChart** — §8.

**C-32 QuotePanel** — Bid, ask, spread (price and points), spread vs P-13 cap. Source: WS
`market`. Copy: `Spread 0.21 · cap 0.40 (min of A, B, C)`; when component A is still unset:
`cap from B and C (A waits for broker data)`.

**C-33 SpreadSparkline** — Last 15 min of spread; source OPEN-03 (no series route). Text summary for
screen readers: `Spread median 0.18, now 0.21`.

**C-34 SessionTimeline** — Today's sessions, P-19 pre-close window, P-33 deadline, news blackout
windows (P-18), from the live export plus `session_exceptions.yaml` (EXE-080). Source OPEN-07.
Every band has a text label; blackout markers say `News blackout 13:00–13:45 UTC`.

### 5.4 Positions & History screen

**C-40 ReconciliationBadge (UI-012)** — Source: WS `positions`, `health` (RECONCILIATION component,
`reconciliation_result`). Copy: `Reconciled 3 s ago` · `UNRECONCILED — last clean run 10:01:50 UTC`
· `UNRECONCILED — running after reconnect` · `Mismatch (T7) — <n> unresolved` · `Never reconciled
since start — Unknown`. While UNRECONCILED, every control that opens risk is disabled with the
reason text `Disabled: positions are not reconciled`.

**C-41 PositionsCompare** — Two columns side by side: **Broker-confirmed** and **Local ledger**,
matched by ticket, with a per-row match result (`Match`, `VOLUME_DIFF`, `SL_DIFF`, `TP_DIFF`,
`MISSING_AT_BROKER`, `MISSING_IN_LEDGER`, `FOREIGN`; EXE-051). Source: `GET /v1/positions`
(OPEN-08: whether both sources are returned). Empty: `No positions at the broker or in the ledger.`
Table semantics: `<table>` with `<th scope>`; mismatch cells have an icon and text.

**C-42 PendingOrdersTable** — `GET /v1/orders`. Empty: `No pending orders (P-06 = 0).`

**C-43 ClosedTradesTable** — `GET /v1/trades?from&to&limit`. Columns: time, side, volume, entry,
exit, net P/L (with commission, fee, swap), exit reason code (MI-185), tier label (PT2 forward
demo, PT3 live). Empty: `No closed trades in this range.` Pagination by `limit`; keyboard operable.

### 5.5 Risk screen

**C-50 ActiveTriggersPanel** — Source: `GET /v1/risk`, WS `risk` (`trading_state_event`). One row
per active trigger: `T#`, name, severity, state demanded, recovery class, cooldown remaining, health
checks HC-1..HC-10 with pass/fail/unknown text. Empty: `No active triggers. Trading state ACTIVE.`

**C-51 ParameterTable** — All P-01..P-37 from `GET /v1/config/limits`: ID, name, value with unit,
status (`USER_DECISION_REQUIRED` / `PROPOSED` / `BROKER_VERIFICATION_REQUIRED`), approval
(`Approved 2026-11-13` or `Not decided`), current utilisation where defined, "UI may" direction
(`tighten`, `widen only`, `—`). Parameters waiting for broker data show `Waits for broker data
(M2/M7)`, never a number. A `Tighten…` button appears only on rows whose direction is `tighten` or
`widen only` (§7.4).

**C-52 TriggerTable** — T1–T27 reference with severity, state, recovery class, cooldown, last fired
time. Static content from TRADING_RISK_SPEC §7 plus last-fired time (OPEN-06).

**C-53 RecoveryChecklist (RISK-050)** — §7.3.

### 5.6 System, Audit, Research

**C-60 HealthTable** — All 13 components (OBS §3) with state, reason, last change, and the
"HEALTHY when" rule as help text. Source: `GET /v1/health`, WS `health`. MCP not configured shows
`Off`.

**C-61 ClockPanel** — NTP offset vs P-16 (`Offset 120 ms · warn 500 · entry stop 1000`), last NTP
success, server-offset estimate and stability (P-17), tick-time drift (TIME-052). Source: `/v1/health`
(CLOCK component; OPEN-01 for the numeric fields).

**C-62 GuardianPanel** — Heartbeat age (both directions, P-20/P-21), integrity digest result, folder
ACL check, `config_status`, limits vs engine (`equal or tighter` / `looser — FAILED`), kill flag
and re-arm counter. When re-arm is required: `Guardian re-arm required. Re-arm it in the EA inputs
in MT5 (GRD-016); GoldBot cannot re-arm it.` Always shows the GRD-030 text: `When MT5, the PC or
the broker connection is unavailable, neither GoldBot nor the Guardian can act. Only stop-loss and
take-profit orders confirmed at the broker before the outage remain, and they do not guarantee the
exit price.`

**C-63 EmergencyHistory** — `GET /v1/emergency/actions`, WS `emergency`. Every run with type,
requester (`USER` / `RISK_ENGINE` / `GUARDIAN`), trigger, lifecycle transitions with times, attempts,
deadline used, result, residual exposure. Empty: `No emergency actions recorded.`

**C-64 MetricsPanel** — OBS §2 metrics. Source OPEN-01 (no metrics route; `/v1/health` only).

**C-65 AuditView** — `GET /v1/audit/summary`: chain status `Audit chain verified 06:00 UTC` /
`Audit chain verification FAILED (T23)`; counts by event type. Search and the event list need a
route (OPEN-05). Content shows hashed identifiers only (PRV-011).

**C-66 ResearchRegistry** — `GET /v1/research/reports`, `/v1/research/reports/{id}`. Every result
carries its tier label (BT-001) and, where applicable, `FIXTURE PARAMETERS — NOT APPROVED
SETTINGS`. DSR, PBO and CI each have a one-sentence plain-language tooltip. Win rate is shown as
`Win rate (reported, not optimised)`. A verdict of no edge is shown as a result, not an error:
`No edge found under the pre-registered tests.` Empty: `No research reports yet.`

### 5.7 Intelligence (M9a)

**C-70 IntelligenceViews** — Active strategies with regime labels and last decision; rejected
signals with reason codes and counts; decision drawer (MI-080); the ten MI-195 views. Routes:
OPEN-09. Rules: SMC zones and liquidity levels labelled `inferred from price` (MI-082); confidence
shown as `Score 0.62` and never as a probability, a percentage chance or "win chance" (MI-011,
MI-154); no win probability anywhere (MI-154); setup quality shows its breakdown (MI-153); the
trailing view always shows `Last broker-confirmed SL` and a failed modification as `Modification
FAILED — SL unchanged at <price>` (MI-172, MI-195); exits never show a single-candle reason
(MI-183). A missing or stale module is Unknown (MI-081).

### 5.8 Settings, alerts, auth

**C-80 EntryAuthorizationSettings** — §7.2. **C-81 NotificationSettings** — §7.6. **C-82
Consents** — §7.7. **C-83 McpClients** and **C-84 McpAdminRequests** — §7.8. **C-85 ThemeSwitch** —
`Dark` (default), `Light`, `Follow system`; stored client-side. **C-86 AccessibilityOverrides** —
`Reduce transparency`, `Increase contrast`, `Reduce motion` toggles that force the §2.8/§2.9
fallbacks regardless of OS settings. **C-87 PrivacyMode** — §7.5. **C-88 LoginDialog** and
**C-89 ReauthDialog** — §7.9.

### 5.9 State catalogue (UI brief §5; each is a C-11 bar)

| State | Token | Exact copy | Actions |
| --- | --- | --- | --- |
| Disconnected | `bar.warning` | `Broker connection lost <mm:ss> ago. No new trades. GoldBot and the Guardian cannot act until it returns. Last broker-confirmed SL: <price> at <time UTC>` or `… Stop-loss status: UNKNOWN` | `View runbook` |
| Stale data | `bar.unknown` | `Prices <n> s old — entries blocked` | — |
| Market closed | neutral | `Gold market closed — reopens <ddd HH:MM> server time` | — |
| UNRECONCILED | `bar.warning` | `Positions not reconciled since <time UTC>. Entries stopped until reconciliation is clean.` | `View diff` |
| Session close approaching | `bar.warning` (last 15 min) | `Gold session closes <HH:MM> server time. New entries stopped. Positions close by <HH:MM>.` | — |
| UNRESOLVED EXPOSURE | `bar.critical` | `Position <volume> lot still open after the close deadline. Close attempts continue. Stop-loss status: confirmed <price>` or `Stop-loss status: UNKNOWN` | `Emergency Liquidation`, `View runbook` |
| Order rejected | inline row | `Entry rejected: <retcode> <retcode name>. Not retried.` | `Dismiss` |
| ENTRY_STOP | `bar.warning` | `New entries stopped: <trigger name> (<T#>). Exits still active.` | `Clear…` (per recovery class) |
| SUSPENDED | `bar.critical` | `Trading suspended: <trigger name> (<T#>). Manual recovery required.` | `Start recovery checklist` |
| Emergency in progress | `bar.critical` + lifecycle list | `Liquidation REQUESTED <time> · SUBMITTED · awaiting broker confirmation` | — |
| Emergency failed | `bar.critical` | `Close FAILED — 60 s deadline reached after <n> attempts. Position still open. Last broker-confirmed SL: <price> at <time UTC>` or `Stop-loss status: UNKNOWN` | `New Emergency Liquidation run`, `View runbook` |
| Guardian unknown or stale | `bar.unknown` | `Guardian heartbeat not seen for <n> s — entries stopped` | `View runbook` |
| Guardian FAILED | `bar.critical` | `Guardian message integrity failed (T22). Manual recovery required.` | `Start recovery checklist` |
| Automatic recovery pending | neutral + timer | `<cause> recovered. Entries resume in <m:ss> if all health checks keep passing.` | `Keep stopped` (sends Stop Entries) |
| Unknown health | `bar.unknown` | `Status unknown — not verified` | — |
| Close at weekend while disconnected (EXE-086) | `bar.critical` | `The terminal is disconnected at the close deadline. Any open position is held over the break with only its broker-side SL, if one was broker-confirmed.` | `View runbook` |

## 6. Emergency controls (UI-030, EXECUTION_SAFETY_SPEC §8)

### 6.1 Rules common to all three

- Three separate buttons, three separate routes, three separate audit records. **No combined
  kill-switch, panic or "stop everything" button, route, shortcut or menu item exists** (EMG-010,
  API_SPEC §4). The supported order Stop Entries → Cancel Pending Orders → Emergency Liquidation is
  shown as help text, not automated by the UI.
- Always visible on every screen and width, on `surface.solid`, never blurred, never covered except
  by their own dialog.
- Keyboard: reachable in the tab order right after the top-bar status chips; no single-key
  shortcut triggers any of them. Each opens a modal dialog with focus on the **Cancel** button;
  Esc closes the dialog without acting.
- Distinct identity by icon, label, shape and colour (never colour alone).
- In M4 they are rendered disabled with `aria-disabled="true"` and the visible text `Available from
  M7` (M4 scope).
- Each command carries a client UUID (API-021); a double click or retry returns the original
  result, never a second action.
- "Done" appears **only** after broker confirmation **and** the RECONCILED step (§6.5). Nothing shows
  a bare check mark.

### 6.2 Stop Entries

| Item | Specification |
| --- | --- |
| Identity | Outline button, 2 px `status.warning` border, `status.warning` text, pause icon, label `Stop Entries` |
| Route / command | `POST /v1/state/entry-stop` → `ENTRY_STOP` (always allowed) |
| Confirmation | One dialog. Title `Stop new entries?` Body `New entries and risk-increasing changes stop now. Open positions keep their exits and session-end closes. Clearing the stop later needs your recovery confirmation (T1, TOTP).` Buttons `Cancel` (default focus) and `Stop Entries` |
| Lifecycle copy | `Stop Entries REQUESTED <time>` → `ENTRY_STOP set <time> (read back)` → `Guardian echo: confirmed <time>` / `Guardian echo: waiting` / `Guardian echo: Unknown — not verified` |
| Done rule | Shown as `Entry stop in force` only after the latch is read back; the Guardian echo line stays separate |
| Disconnected | `Entry stop latched locally. The Guardian echo is Unknown until the terminal returns.` |

### 6.3 Cancel Pending Orders

| Item | Specification |
| --- | --- |
| Identity | Filled `btn.cancel` with `btn.on-cancel` text, list-x icon, label `Cancel Pending Orders` |
| Route / command | `POST /v1/emergency/cancel-pending` → `CANCEL_PENDING` |
| Step 1 | Title `Cancel pending orders?` Lists every eligible order (ticket, side, volume, price, owner). Checkbox `Include foreign orders` (unticked, EMG-030). Copy `ENTRY_STOP is set first, as a separate recorded action.` Buttons `Cancel`, `Continue` |
| Step 2 | Title `Confirm cancellation of <n> orders` Repeats the count and scope. Button `Cancel Pending Orders` |
| Empty | Step 1 shows `No eligible pending orders. Nothing will be cancelled.` and the confirm button is replaced by `Close` |
| Deadline | P-25 global deadline 60 s, shown as §6.5 |

### 6.4 Emergency Liquidation

| Item | Specification |
| --- | --- |
| Identity | Filled `btn.liquidate` with white text, exit-door icon, label `Emergency Liquidation`; placed apart (24 px gap and a divider) |
| Route / command | `POST /v1/emergency/liquidate` → `EMERGENCY_LIQUIDATE` (re-auth, two-step, scope flag EMG-030) |
| Step 1 | Title `Request emergency liquidation?` Lists every in-scope position: ticket, side, volume, open price, floating P/L, SL status (UI-015 wording). Checkbox `Include foreign positions` (unticked). Fixed text: `Requests closes. Fills are not guaranteed.` and `ENTRY_STOP is set first, as a separate recorded action. Trading becomes SUSPENDED (T17) and needs manual recovery.` Buttons `Cancel`, `Continue` |
| Step 2 | Re-authentication in the same dialog (§7.9): `Enter your authenticator code to request liquidation of <n> positions (<total volume> lot).` Button `Request Emergency Liquidation` |
| Market closed | Step 1 adds `The market is closed. The request will be recorded as BLOCKED — MARKET CLOSED and a new run starts at the next tradable moment.` |
| Empty | `No in-scope positions. Nothing will be closed.` |

### 6.5 Lifecycle display (UI-013) and deadline (P-25)

Source: `GET /v1/emergency/actions`, WS `emergency` (`emergency_action`: `lifecycle_state`,
`transitions`, `requested_at`, `global_deadline_at`, `attempts`, `result`, `unresolved_exposure`,
`reconciliation`). Shown in the state bar, the dialog after submission, and System → Emergency
history. When Liquidation sets ENTRY_STOP first, that appears as its own line above the run.

| `lifecycle_state` | Display label | Exact copy |
| --- | --- | --- |
| `REQUESTED` | `REQUESTED` | `<Action> requested <time UTC> — not yet authorized` |
| `AUTHORIZED` | `AUTHORIZED` | `Authorized <time UTC> — preparing broker requests` |
| `SUBMITTED` | `SUBMITTED` | `Submitted to broker <time UTC> · attempt <n> of 5 — awaiting broker confirmation` |
| `CONFIRMED` | `CONFIRMED` | `Broker confirmed <time UTC> — re-reading broker state` |
| `PARTIAL` | `PARTIAL` | `Partly done — <x> of <y> still open. Retrying until the deadline.` |
| `FAILED_DEADLINE` | `FAILED — DEADLINE` | `FAILED — 60 s deadline reached after <n> attempts. <k> still open. Last broker-confirmed SL: <price> at <time UTC>` or `Stop-loss status: UNKNOWN` |
| `BLOCKED_MARKET_CLOSED` | `BLOCKED — MARKET CLOSED` | `BLOCKED — MARKET CLOSED. A new run starts at the next tradable moment (<ddd HH:MM> server time). Until then each position has only its broker-side SL, if one is broker-confirmed.` |
| `RECONCILED` after `CONFIRMED` | `DONE` | `Done — broker-confirmed and reconciled <time UTC>` |
| `RECONCILED` after any other result | `RECONCILED` | `Reconciled <time UTC> — <k> still open. Not done.` |

- **Deadline:** a linear bar and the text `Deadline: <s> s left of 60 s` from `global_deadline_at`
  minus the message's `as_of_utc`, then counted down with the client's monotonic clock. At zero
  without confirmation the display waits for the engine's state; it never infers FAILED or DONE
  itself.
- The display never shows `DONE` for CANCEL_PENDING unless `orders_get` showed no eligible orders,
  nor for EMERGENCY_LIQUIDATE unless no in-scope positions **and** closing deals were found (§8
  confirmation rule); the UI takes this only from the engine's `result`.
- `FAILED_DEADLINE` also raises the UNRESOLVED EXPOSURE bar (§5.9) and a CRITICAL alert (OBS-011).

## 7. Flows

### 7.1 Proposal and approval (UI-031, API-030..033; M9a)

Applies whenever an entry needs human approval: mode `MANUAL_APPROVAL`, a strategy without
`auto_approved` in `AUTO_APPROVED_STRATEGIES`, a demotion (RISK-062), automation paused (RISK-050,
EXE-071), a narrowing rule (RISK-067), or fixture demo with that mode. With D-01 = `AUTO_ALL` the
Approvals screen normally shows: `Entry authorization is AUTO — ALL. Entries that pass the
RiskEngine are sent without approval. Proposals appear here only after a demotion, while automation
is paused, or in fixture demo with manual approval.`

**Approval card (C-90).** Source: `GET /v1/proposals`, WS `proposals` (`trade_proposal`). Content:
direction (`BUY` / `SELL` with an arrow icon), entry, SL, TP, volume, modelled loss
(`−25.00 USC · 0.25% of equity · ≈ $0.25`), R:R, spread now with freshness, `strategy@version`,
deterministic rationale (LLM-005), proposal hash (first 12 hex chars, full on hover), countdown to
expiry (P-23: 60 s or price drift).

| Card state | Copy | Approve control |
| --- | --- | --- |
| Live | `Expires in <s> s` | Enabled |
| Price drift beyond P-23 | `Expired — price moved` | Removed |
| Time expiry | `Expired — not approved` (card greyed) | Removed |
| Stale price | `Price STALE — cannot approve` | Disabled with reason |
| Unreconciled or not ACTIVE | `Entries are stopped — cannot approve` | Disabled with reason |
| Submitted | `Approval sent <time UTC> — RiskEngine re-checking (RISK-004)` | — |
| Re-check failed | `Not sent: <reason code>. No order was placed.` | — |
| Result | Order lifecycle from WS `commands` (EXE §2), never a bare check mark | — |

Approve: hold-to-confirm ≥ 800 ms (pointer) with a visible fill ring and the text `Hold to approve`,
or keyboard `Enter` on Approve opening a confirm dialog `Approve this entry? <side> <volume> lot,
modelled loss <amount>` (API-033). Reject: `POST /v1/proposals/{id}/reject`, one click, no
confirmation. Approval token issue route: OPEN-04. A new card raises the approval notification
(§7.6). History lists every proposal with outcome `APPROVED` / `REJECTED` / `EXPIRED` and time.

### 7.2 Entry authorization and mode change (UI-032, RISK-060..067)

Settings → Entry authorization shows the three modes as radio cards with the consequences from
TRADING_RISK_SPEC §9 (behaviour, technical, operational) in full text. Source: `GET
/v1/config/limits`; command `POST /v1/mode` (`MODE_CHANGE`).

- Current mode is marked `Current` with the approval date (`Decided by you 2026-11-13`). While
  undecided: `Not decided — entries blocked` and nothing is pre-selected.
- Fixture demo: `Fixture demo — <mode> (test setting, not a decision)`; controls disabled with
  `Set by fixture_demo_mode for this run`.
- Narrowing rules (RISK-067) are listed with `Applies next: <time>`; none exist until decided:
  `No narrowing rules decided.`
- **Moving to `MANUAL_APPROVAL`:** one confirmation, always allowed.
- **Enabling `AUTO_ALL` or `AUTO_APPROVED_STRATEGIES`, or auto-approving a strategy**
  (`POST /v1/strategies/{id}/auto-approval`): shows the RISK-061 checklist with each item
  `Met` / `Not met` / `Unknown` (promotion gate RISK-063 per strategy; trading state ACTIVE; on LIVE
  the M10 pilot report and GO). The confirm button stays disabled until all are `Met`. Then a typed
  phrase (`ENABLE AUTOMATIC ENTRIES`) and TOTP re-auth. The gate items need data the API does not
  yet expose (OPEN-01).
- After a demotion or recovery, the screen states `Automation paused by <cause>. Only you can
  re-enable it.`

### 7.3 Clearing a trading state (RISK-050, `POST /v1/state/clear`)

- `AUTO` class: no button; the automatic-recovery bar shows the timer and `Keep stopped`.
- `ACK` class: cause shown, HC-1..HC-10 results, `Acknowledge` + TOTP.
- `MANUAL` class: the recovery checklist: (1) cause shown and `I have read the cause` ticked;
  (2) HC-1..HC-10 all `Pass` (live, each with its reason; any `Fail` or `Unknown` disables the
  next step); (3) T24: `Secrets rotated` ticked; T16: `Process restarted with a valid config` shown
  from health; T18/HC-4: `Guardian re-armed in MT5` shown from the heartbeat; (4) typed phrase
  `RESUME TRADING` and TOTP. Result copy: `Trading state ACTIVE. Automatic entries stay paused until
  you re-confirm the mode.`

### 7.4 Tighten-only limit editing (RISK-090/091)

**OPEN-10:** RISK-091 says no API command can change a `P-xx`, while API_SPEC §4 has
`POST /v1/limits/tighten`. Until resolved, M7 builds the dialog behind a disabled control with the
text `Limit changes: edit config/risk_limits.yaml and restart (RISK-090).` If resolved in favour of
the route, the flow is:

- Only rows with direction `tighten` or `widen only` show `Tighten…`. The input accepts only values
  stricter than the current one (lower for `tighten`, wider window for `widen only`); a looser value
  shows `Only stricter values can be set here. Loosening needs a file edit and a restart.` and the
  confirm button stays disabled. The engine re-verifies (RISK-090); the UI is a convenience only.
- Confirm dialog shows old → new with unit, then TOTP re-auth (API-013).
- There is no control anywhere that loosens a limit, changes leverage or edits a config file
  (API_SPEC §4).

### 7.5 Privacy mode

MCP outputs have a privacy mode (MCP-040, default on, `privacy_amount`). For the dashboard no
requirement exists (**OPEN-12**). Proposed behaviour, display-only, for screen sharing:

- Toggle in the top bar user menu and Settings: `Privacy mode`. When on, every money amount is shown
  as % of equity or in R (`−0.25% · −1.00 R`), the account login hash and server name are hidden, and
  a `PRIVACY MODE` tag appears in the top bar.
- It changes display only. No data, limit, alert or control changes, and the emergency dialogs
  still list volumes and SL prices (they are needed to act).
- Stored client-side; default off.

### 7.6 Alerts and notification centre (OBS-020..024)

- **The dashboard is the only channel.** No email, SMS, Telegram or external service.
- **CRITICAL banner (C-10):** every CRITICAL event (OBS-011) appears within 5 s (OBS §5) as a
  persistent banner with: what happened, what the system has already done (OBS-022, e.g.
  `ENTRY_STOP set; liquidation REQUESTED, not yet confirmed`), time, a runbook link and
  `Acknowledge`. Acknowledging hides the banner but keeps the alert in history. Several criticals
  stack, newest first, `+<n> more`.
- **Missed alerts (OBS-023):** on opening the dashboard, a blocking sheet lists every CRITICAL alert
  raised while it was closed, with timestamps, before anything else: title `While the dashboard was
  closed`. The user must acknowledge (individually or `Acknowledge all <n>`) to reach the screens.
  The emergency strip stays usable while the sheet is open.
- **Notification centre (`/alerts`):** all alerts (OBS-021) with severity (text + icon), time,
  component, message, actions taken, runbook link, acknowledgement state; filters by severity and
  state. Empty: `No alerts.`
- **Approval notifications (OBS-024):** on by default, switchable in Settings; text exactly
  `GoldBot: trade proposal waiting, expires in <P-23> s` with a short chime; no amount, account or
  price. If permission is denied: `Browser notifications are blocked. Proposals are shown only on the
  Approvals screen.` Notification API on loopback is A-66.
- **Optional Windows notifications for other alerts:** off by default (OBS-020).
- **Routes:** OPEN-02 (no alert list, acknowledge route or command type exists in API_SPEC; the
  `command` enum has no acknowledge type).

### 7.7 Consents (PRV §5, `POST /v1/consents`)

LLM: disabled (P-28 = 0, user decision); the consent card shows `LLM disabled (spend cap 0)` and no
enable control until P-28 changes in the config. MCP: per client, with client id, allowed tools and
admin actions (MCP-030), a sample output, and the text that the MCP client's own conversations follow
its own policies. Withdrawal: `Withdraw consent` → `Consent withdrawn <time UTC>. Data already sent
is outside GoldBot's control.` (PRV-018). Re-auth for LLM/MCP (API-013).

### 7.8 MCP clients and admin requests (M8)

Register or revoke a client (`POST /v1/mcp/clients`, re-auth). Admin requests from MCP
(`generate_report`, `annotate_trade_journal`, `queue_research_job`) appear as PENDING cards with the
client, action, arguments (the journal note text in full) and a 5-minute expiry; approve with
`POST /v1/mcp/admin-requests/{id}/approve` (TOTP for `queue_research_job`). Listing and rejecting
need routes: OPEN-13.

### 7.9 Login and re-authentication (API-010..013)

Login dialog on `surface.modal`: username, password, TOTP code (6 digits, `inputmode="numeric"`,
`autocomplete="one-time-code"`). Errors: `Sign-in failed. Check your password and code.` (never
says which part failed); lockout `Too many attempts. Try again in <m> min.` (API-011). Idle expiry:
`Session expired after 30 min idle. Sign in again.` Re-auth step (TOTP within 2 min) is a field
inside the action's own dialog. Routes: OPEN-04.

## 8. Charts

- **Library:** TradingView Lightweight Charts on `surface.chart` (solid, never blurred, UI-002).
  Attribution as its licence requires.
- **Main pane:** candlesticks (up hollow `chart.up` outline, down filled `chart.down`), two moving
  averages (`chart.ma-fast`, `chart.ma-slow`) whose periods are named in the legend
  (`MA 20 · MA 50`, from the strategy or user setting, never implied as signals), price scale on the
  right with `font.numeric`, time scale labelled `UTC` or `server time`.
- **Panes:** tick-volume histogram labelled `Tick volume (not traded volume)` (MI-021, A-34); one
  indicator pane (e.g. RSI or MACD) chosen by the user; each pane has a text legend with current
  values.
- **Price lines:** entry (solid, `text.secondary`, label `Entry 4,061.20`), SL (dashed,
  `status.critical`, label `SL 4,046.00 · broker-confirmed 10:02:14 UTC` or `SL 4,046.00 · UNKNOWN`),
  TP (dashed, `accent.cyan`, label `TP 4,091.20`), live bid/ask lines. Each line has a text label;
  dash patterns differ so colour is not the only cue.
- **Trade markers:** entry ▲/▼ arrows with `B` / `S` text, exit markers with the reason code;
  tooltip lists ticket, volume, price, time.
- **Session overlays:** pre-close window (P-19) and P-33 deadline as labelled vertical bands; news
  blackout windows as labelled bands; SMC zones only in the Intelligence views, labelled `inferred
  from price`.
- **Staleness overlay:** when market data is STALE, a hatched `status.unknown` overlay covers the
  latest candle region with the text `STALE · <n> s old — entries blocked`; when UNKNOWN, the whole
  chart is covered with `Market data: Unknown — not verified` and the live price line is removed;
  when the market is closed, a neutral tag `MARKET CLOSED` replaces the live label.
- **Data:** bars come from a route that does not exist yet (OPEN-03); the live last bar updates from
  WS `market`. No bar is repainted after close (MI-014).
- **A11y:** the canvas has `role="img"` with an `aria-label` summarising symbol, timeframe, last
  price, change and freshness; a `View as table` toggle shows the last 50 bars as a table.

## 9. Copy rules

### 9.1 Status vocabulary (exact strings)

| Domain | Strings |
| --- | --- |
| Health | `Healthy`, `Degraded`, `Unhealthy`, `Failed`, `Unknown — not verified`, `Off` (MCP only) |
| Freshness | `REAL-TIME`, `DELAYED`, `STALE`, `MARKET CLOSED` |
| Reconciliation | `Reconciled <n> s ago`, `UNRECONCILED`, `Mismatch (T7)` |
| Trading state | `ACTIVE`, `ENTRY_STOP`, `SUSPENDED` |
| Recovery class | `AUTO`, `ACK`, `MANUAL` |
| Emergency lifecycle | `REQUESTED`, `AUTHORIZED`, `SUBMITTED`, `CONFIRMED`, `PARTIAL`, `FAILED — DEADLINE`, `BLOCKED — MARKET CLOSED`, `RECONCILED`, `DONE` (only per §6.5) |
| Stop-loss | `Broker-side SL at <price> (confirmed <time>)`, `Stop-loss status: UNKNOWN` |
| Exposure | `UNRESOLVED EXPOSURE` |
| Guardian | `Unknown` (no heartbeat or unreadable), `Failed` (T22) |
| Entry authorization | §5.1 C-06 table |
| Environment | `LIVE`, `DEMO`, `BACKTEST`, `REPLAY`; account class `CENT`, `STANDARD`, `ACCOUNT CLASS UNKNOWN` |
| Fixture | `FIXTURE PARAMETERS — NOT APPROVED SETTINGS` |
| Thresholds | `intervention at <value>` |

### 9.2 Banned words and phrases

No UI text, tooltip, aria-label, alert or chart label may contain (case-insensitive): `guaranteed`,
`guarantee` (except in the fixed negations `does not guarantee` and `Fills are not guaranteed`),
`max loss`, `maximum loss`, `capped at`, `cap on loss`, `risk-free`, `no risk`, `protected`,
`protection` applied to a position, `safe` applied to a position or trade, `secure profit`,
`sure`, `win probability`, `win chance`, `probability of success`, `chance to win`, `% to win`,
`high-probability` as a claim about an outcome (the MI-195 view name is shown as `Setup Scanner`),
`AI-powered`, `prediction`. A test scans the built bundle and rendered pages (UIT-26). Interventions
are always `intervention at`; a stop-loss is always followed somewhere on the same surface by
`A stop-loss does not guarantee the exit price.`

### 9.3 Money, prices and volumes

- Values arrive as decimal strings (`money`, `decimal` in `common.schema.json`; DATA-004). The UI
  never converts them to a JavaScript `number` for display or arithmetic; formatting is done on the
  string (grouping and sign only). A lint rule bans `parseFloat`, `Number(` and `toFixed` on money
  and price fields (UIT-16).
- **Currency always shown** (UI-005): `−24.30 USC`. The account currency is `account_info().currency`
  as reported (CENT §1); the UI never assumes it. A USD equivalent is secondary and labelled
  `≈ $0.24`, computed by the engine (CENT conversion), never by the UI.
- **Sign:** always `+` or `−` (U+2212) for P/L, plus ▲ or ▼; zero shows `0.00 USC` with no arrow.
  Signs are never rounded away: values keep the precision delivered by the engine, and a small
  negative value is never shown as `0.00`.
- **Decimal places:** prices use the symbol's `digits` from `symbol_spec`; volumes use the precision
  of `volume_step`; money uses the account currency's digits from MT5 (**OPEN-14**: no such field in
  `account_snapshot`; until fixed the string is shown exactly as received).
- **Percentages:** two decimals for utilisation (`0.42%`), as delivered by the engine.
- Grouping separator `,`, decimal `.`, fixed (no locale variation), so values match the audit log.

### 9.4 Tone

Short, literal, present tense. Say what happened, what the system already did and what the user can
do. No exclamation marks, no emoji, no reassurance words.

## 10. M4 design gate and acceptance checks

Before component code (brief §9, M4 block): moodboard with three procedurally generated backdrops
per theme (original art, UI-008; ≤ 400 KB each); `tokens.json` plus the automated contrast report;
static mockups of Overview, Approvals and Risk at 1440 px and 390 px, dark and light, including the
Disconnected, UNRECONCILED, SUSPENDED, UNRESOLVED EXPOSURE and Emergency-in-progress states; a
component inventory with every state from §4.2 and §5.9. **The user approves these before any
component is built.**

Numbered checks (Playwright + axe-core + Vitest unless noted). FakeBroker scenarios drive the
states.

| ID | Check | Tool |
| --- | --- | --- |
| UIT-01 | axe-core reports zero serious or critical violations on every screen, both themes, 1440 and 390 px | Playwright + axe |
| UIT-02 | Every screen is fully operable by keyboard: tab order reaches all controls, visible focus ring on each | Playwright |
| UIT-03 | Focus indicator is ≥ 2 px and ≥ 3:1 against the adjacent surface (computed style + contrast) | Playwright |
| UIT-04 | Every token pair in §2.5 meets its threshold against the real baked backdrops (worst-case patch sampled from the image) | Vitest script |
| UIT-05 | No raw hex or rgb colour appears in component code outside `tokens.json` | lint |
| UIT-06 | Resolved `brand.lime` differs from `status.healthy` and `pl.profit` in both themes; no element with a HEALTHY or profit meaning uses the lime token | Vitest + Playwright |
| UIT-07 | Data panels, tables and the chart have computed background alpha ≥ 0.85 | Playwright |
| UIT-08 | At most three elements with a non-`none` `backdrop-filter` are rendered at once, including with a dialog open; none behind the chart or a scrolling table | Playwright |
| UIT-09 | `prefers-reduced-transparency`, `prefers-contrast: more` emulation → zero `backdrop-filter`, solid surfaces | Playwright |
| UIT-10 | `prefers-reduced-motion` emulation → no CSS animation or transition longer than 0 ms; countdowns update as text | Playwright |
| UIT-11 | No element has a running infinite animation in any state (no pulsing) | Playwright |
| UIT-12 | **UNKNOWN never renders green:** for each component in §5, with (a) missing data, (b) a REST timeout, (c) the WebSocket silent for 6 s, the component shows `Unknown — not verified` and no element uses `status.healthy` | Playwright, one test per component |
| UIT-13 | After the stream goes silent > 5 s, the last good value is no longer in the DOM | Playwright |
| UIT-14 | Freshness labels: tick age 1 s → `REAL-TIME`; 5 s → `DELAYED`; 11 s with session open → `STALE` with age; session closed → `MARKET CLOSED` | Playwright |
| UIT-15 | Every element displaying a number has `font-variant-numeric` containing `tabular-nums` | Playwright |
| UIT-16 | No money or price field passes through `parseFloat`, `Number()` or `toFixed` | lint + unit |
| UIT-17 | Every rendered monetary value has a currency code next to it (regex scan of all screens) | Playwright |
| UIT-18 | P/L values carry `+`/`−` and ▲/▼ and a text sign, not colour alone | Playwright |
| UIT-19 | Env banner present, solid, not dismissible, visible after scrolling, on every route and width; correct colour and text for each of LIVE, DEMO, BACKTEST, REPLAY | Playwright |
| UIT-20 | Account class UNKNOWN shows `ACCOUNT CLASS UNKNOWN — not verified` in the banner | Playwright |
| UIT-21 | Fixture records → `FIXTURE PARAMETERS — NOT APPROVED SETTINGS` banner on every screen | Playwright |
| UIT-22 | Entry-authorization chip shows each C-06 row for its scenario, including `NOT DECIDED — ENTRIES BLOCKED` with nothing pre-selected in Settings | Playwright |
| UIT-23 | SL shown as broker-side only when `sl_broker_confirmed` is true, with the confirmation time and the no-guarantee sentence; otherwise `Stop-loss status: UNKNOWN` | Playwright |
| UIT-24 | UNRECONCILED (older than 2 × P-24, failed, or running after reconnect) shows the badge and disables risk-opening controls with the reason text | Playwright |
| UIT-25 | Broker-confirmed and Local ledger columns both rendered; each EXE-051 mismatch type shows icon + text | Playwright |
| UIT-26 | Banned-phrase scan (§9.2) of the built bundle and the rendered DOM of every screen and state returns zero hits | script + Playwright |
| UIT-27 | No percentage or score is labelled as a probability or win chance; confidence renders as `Score <x>` | Playwright (M9a) |
| UIT-28 | Three emergency buttons exist with distinct accessible names, icons and routes; no element or route named panic, kill-switch or combined stop exists | Playwright + route table test |
| UIT-29 | In M4 the three emergency buttons are disabled with `Available from M7` | Playwright |
| UIT-30 | Stop Entries: one confirmation; Cancel Pending: two steps listing orders; Liquidation: two steps listing positions and volumes, `Include foreign positions` unticked, the text `Requests closes. Fills are not guaranteed.`, TOTP step | Playwright (M7) |
| UIT-31 | Emergency lifecycle: each `lifecycle_state` renders its §6.5 copy; `DONE` appears only for RECONCILED after CONFIRMED; FAILED_DEADLINE shows the failure copy and the UNRESOLVED EXPOSURE bar | Playwright (M7) |
| UIT-32 | Deadline countdown starts from `global_deadline_at` and never shows DONE or FAILED by itself at zero | Playwright (M7) |
| UIT-33 | A duplicate click on any command sends the same client UUID | Playwright (M7) |
| UIT-34 | Every state in §5.9 renders with its exact copy, token, icon and actions | Playwright (FakeBroker scenarios) |
| UIT-35 | CRITICAL alert banner appears within 5 s of the event, stays until acknowledged, and remains in history | Playwright |
| UIT-36 | Missed CRITICAL alerts are shown first on open, before any screen content, with timestamps | Playwright |
| UIT-37 | Approval card: hold < 800 ms does not approve; ≥ 800 ms does; keyboard path uses a confirm dialog; expired card cannot be approved | Playwright (M9a) |
| UIT-38 | Approval notification text equals `GoldBot: trade proposal waiting, expires in <P-23> s` and contains no amount, account or price; one notification per proposal | Playwright (M9a) |
| UIT-39 | Tighten dialog rejects a looser value client-side and the server rejects it too | Playwright (M7, after OPEN-10) |
| UIT-40 | No UI element offers loosening a limit, changing leverage or editing config | Playwright |
| UIT-41 | Visual snapshots at 1440 px and 390 px, dark and light, for Overview, Approvals, Risk and each gate state | Playwright snapshots |
| UIT-42 | Phone width: emergency strip visible with full labels on every screen; no horizontal scroll | Playwright |
| UIT-43 | Text zoom 200%: no clipped content in the top bar, banners or emergency dialogs | Playwright |
| UIT-44 | Every displayed time carries a zone label (`UTC`, `server time` or `local`) | Playwright |
| UIT-45 | Every WebSocket message with an `env` different from the session's env hides data and shows `ENVIRONMENT MISMATCH — data hidden` | Playwright |
| UIT-46 | The page loads no resource from outside the served origin (fonts, icons, scripts) | Playwright network log |
| UIT-47 | Chart: STALE overlay, UNKNOWN cover, MARKET CLOSED tag; SL line label states broker-confirmed or UNKNOWN | Playwright |
| UIT-48 | 60 fps profile on the Market screen with live updates on a mid-range laptop; blur auto-disabled on dropped frames | manual profile, attached |

## 11. OPEN items

Each needs a spec or API change approved by the user; none is invented here.

| ID | File and requirement | What is missing | Needed by |
| --- | --- | --- | --- |
| OPEN-01 | `API_SPEC.md` §4 (routes), §6 API-050 (channels); DATA-011 | No response schemas for any GET route or WebSocket channel. Fields needed that no record schema holds: floating P/L, strategy state (ACTIVE/WATCH/PAUSED), risk utilisation per P-xx, active triggers with HC results, NTP and server offsets, metrics, RISK-061 gate status. Relates to M0b NB6/NB12 | M4 |
| OPEN-02 | `OBSERVABILITY_SPEC.md` OBS-020/023; `API_SPEC.md` §4, §6 | No alert list route, no `alerts` channel, no acknowledge route, and no acknowledge type in the `command` enum, although alerts persist until acknowledged | M4 |
| OPEN-03 | `API_SPEC.md` §4 | No route for chart bars or a spread series; only `/v1/market/snapshot` | M4 |
| OPEN-04 | `API_SPEC.md` API-010, API-013, API-031 | No login, logout, re-auth (TOTP) or approval-token issue route is listed | M4 (login), M7 (re-auth), M9a (token) |
| OPEN-05 | `API_SPEC.md` §4; SEC-022 | Only `/v1/audit/summary`; the Audit screen's search and event list need a route | M4 |
| OPEN-06 | `API_SPEC.md` §4; TRADING_RISK_SPEC §7 | No route for `failure_events` / trigger history (last fired, cooldown remaining) | M4 |
| OPEN-07 | `API_SPEC.md` §4; EXE-080, P-19, P-33 | No route for the session calendar, next close, P-19 window and P-33 deadline | M4 |
| OPEN-08 | `API_SPEC.md` §4 `/v1/positions`; UI-012 | Unstated whether the route returns broker-confirmed and ledger views separately | M4 |
| OPEN-09 | `MARKET_INTELLIGENCE_SPEC.md` MI-081, MI-195; `API_SPEC.md` §4 | No routes for decision records, rejected signals, setups, lifecycle or management events | M9a |
| OPEN-10 | `TRADING_RISK_SPEC.md` RISK-091 vs `API_SPEC.md` §4 `POST /v1/limits/tighten` | RISK-091 forbids any API command changing `P-xx`; the route exists (already raised in STATUS §11) | M7 |
| OPEN-11 | `TRADING_RISK_SPEC.md` RISK-061, RISK-065; D-01 | With P-37 = `AUTO_ALL` decided but RISK-061 not yet met, it is unstated whether entries are blocked or need manual approval; the chip copy depends on it | M7 |
| OPEN-12 | `PRIVACY_POLICY.md` (no requirement); MCP-040 | No dashboard privacy mode is specified; §7.5 is a proposal that needs a requirement ID and the user's confirmation | M8 |
| OPEN-13 | `MCP_SECURITY_SPEC.md` §4; `API_SPEC.md` §4 | No route lists pending MCP admin requests or rejects one | M8 |
| OPEN-14 | `schemas/account_snapshot.schema.json`; CENT §1 | No field for the account currency's decimal places; whether MT5 provides it on this account is checked in M2 | M4 |
