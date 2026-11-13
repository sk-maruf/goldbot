# ADR-013: Local-only deployment on the user's Windows computer; dashboard-only notifications; no remote access

Status: Accepted (specification, 2026-11-13)

## Context

The user decided that GoldBot runs on their local Windows computer, with no cloud-hosted trading
architecture (SYSTEM_ARCHITECTURE §7), and that the local dashboard is the only alert channel
(OBS-020). The MetaTrader5 package ships Windows x86-64 wheels only [VERIFIED S18], and the design
runs it beside the terminal on one machine (SYSTEM_ARCHITECTURE §3). Every additional network path or external service is a new trust boundary
and a new outbound data flow (PRIVACY_POLICY §5).

## Options

| Option | Summary | Assessment |
| --- | --- | --- |
| A | Local Windows host; API on 127.0.0.1; dashboard-only alerts | Chosen (user decision) |
| B | Cloud or VPS hosting | Rejected: contrary to the user's decision; new attack surface and credential placement |
| C | Remote access to the dashboard or API | Rejected: not part of the design; would need TLS, a separate ADR and a threat-model update (API-002, SEC-011) |
| D | External notification services (Telegram, email, SMS) or external monitoring | Rejected: an extra dependency and outbound flow; any external channel needs a separate ADR (OBS-020) |

## Decision

- The MT5 terminal, Guardian EA, engine and API run on the same local host (SYSTEM_ARCHITECTURE §7).
- The API binds to `127.0.0.1` with a `Host` allowlist; the startup self-check refuses any
  non-loopback bind (API-001/002); the firewall blocks inbound connections to the API port and RDP is
  disabled (SEC-010/011).
- Alerts live in the dashboard: persistent CRITICAL banners until acknowledged, alert history
  (OBS-020), and missed alerts shown first on open (OBS-023). Local Windows notifications are
  allowed: approval notifications are on by default (OBS-024), other alerts optional and off by
  default.
- Trading, risk, stops, sizing, emergency operations and reconciliation do not depend on any
  external service beyond the broker connection (LLM-006, SYSTEM_ARCHITECTURE §7).

## Consequences

- Availability is bounded by the host: if the computer sleeps or shuts down, or the terminal or
  broker connection is down, neither the engine nor the Guardian can act. Only SL/TP orders that were
  broker-confirmed earlier remain at the broker, and they do not guarantee the exit price (GRD-030).
  The runbook requires power and sleep settings that keep the computer awake during sessions
  (SEC-010), and the no-overnight rule limits exposure time (EXE-080).
- The user sees alerts only while the dashboard is open; with it closed, a waiting proposal expires
  unseen (OBS-024). Browser notifications on loopback are [ASSUMPTION A-66], tested in M9. An
  engine-side Windows toast that works with the dashboard closed needs a new dependency and a stop
  for the user (CLAUDE.md §7).
- Optional off-box encrypted backups remain a separate user-consented outbound flow, off by default
  (PRIVACY_POLICY §5, SEC-022); they are not remote access or monitoring.
- Host compromise remains the dominant residual risk (TM-07).

## Reversal cost

Medium to high. Remote viewing, a VPS or an external channel each need a separate ADR, a
threat-model update, TLS and authentication changes in API_SPEC, privacy consent flows and user
approval.
