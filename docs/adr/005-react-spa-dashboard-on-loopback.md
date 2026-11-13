# ADR-005: Local desktop dashboard as a React + TypeScript SPA served on loopback

Status: Proposed (pack default, not confirmed by user, 2026-11-13)

> **DEFAULT — not confirmed by user** (`docs/STATUS.md` §9, kickoff question 1). This ADR records the
> pack default. Flutter desktop remains an open user choice.

## Context

The dashboard is GoldBot's only notification channel (OBS-020) and the place where the user sees
health, reconciliation, proposals and the three emergency controls. It must be truthful about
status (UI-010..015), meet WCAG 2.2 AA (UI-003), work at desktop and phone widths, and never become
a path that bypasses the engine (API-020). The API binds to 127.0.0.1 only (API-001/002). The user
chose not to be stopped for the technology question, so the pack default applies until answered.

## Options

| Option | Summary | Assessment |
| --- | --- | --- |
| A | React + TypeScript (strict) + Vite SPA, served same-origin by the loopback API and opened in a desktop browser window; responsive | Pack default, recorded here |
| B | Flutter desktop application | Open alternative; the user may still choose it |

## Decision

- Build the dashboard as option A with the CLAUDE.md §5 stack: React + TypeScript (strict) + Vite,
  TradingView Lightweight Charts, TanStack Query, Vitest, Playwright, axe-core.
- The SPA is served by the API on 127.0.0.1, same-origin with no CORS (API-003). It reads state
  over REST/WebSocket and writes only through validated commands (API-020).
- The visual direction follows the user's 2026-11-10 decision: the `Inspiration.jpg` dark
  near-black-green look with lime and cyan accents and glass panels, under every numbered rule
  UI-001..UI-032 (`docs/STATUS.md` §10).

## Consequences

- One technology for the dashboard and the M4/M9 Playwright and axe-core tests; JSON schemas
  generate the TypeScript types (DATA-011).
- Browser constraints apply: approval notifications need the dashboard open (OBS-024), and the
  Notification API on loopback is [ASSUMPTION A-66], tested in M9.
- If the user later chooses Flutter, the UI spec (`docs/UI_SPEC.md`), the M4 tests and the session
  model (API-010..013) must be re-planned. The API and engine do not change.
- Light theme vs dark only is still OPEN for the user (`docs/STATUS.md` §10); both stay specified.

## Reversal cost

Low before M4 starts (no UI code exists). After M4, high: the dashboard, its component tests, the
E2E suite and the design-gate deliverables would be rebuilt.
