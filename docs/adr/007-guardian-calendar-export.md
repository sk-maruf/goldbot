# ADR-007: The Guardian exports the MQL5 economic calendar to a file

Status: Accepted (specification, 2026-11-13)

## Context

Strategies not validated for news cannot enter inside the news blackout around high-impact USD
events (RISK-018, P-18). The engine needs event times it can trust. The MQL5 terminal has a built-in
economic calendar; the Python package has no calendar function. Any third-party calendar API would
need an API key (a secret, SEC-001..007) and an extra outbound flow and trust boundary.

## Options

| Option | Summary | Assessment |
| --- | --- | --- |
| A | The Guardian exports high-impact USD events from the MQL5 calendar to `guardian_calendar.json` | Chosen |
| B | External calendar API called by the engine | Rejected: an extra key, an extra trust boundary, an extra outbound flow needing consent |
| C | Manual blackout schedule only | Rejected as the primary source: it depends on the user keeping it current. SYSTEM_ARCHITECTURE §6 keeps it as the named fallback |

## Decision

- The Guardian writes `guardian_calendar.json` (GUARDIAN_SAFETY_SPEC §3) with high-impact USD events
  for the next 7 days, refreshed every 6 h (GRD-041), using the same atomic write, digest and `seq`
  rules as every IPC file (GRD-006..008).
- The engine converts event times to UTC with the server offset accepted under TIME-030 (TIME-042).
  That MQL5 calendar times are in trade-server time is [ASSUMPTION A-33], checked in M7 against three
  known events on an independent public calendar.
- Data is used only when VALID under TIME-043 (exported < 24 h ago, accepted offset, the A-33 check
  passed once, impact, currency and a relevance class from a versioned mapping file). Anything else
  is AMBIGUOUS and treated as missing.
- Unknown-calendar policy (TIME-042): if the file is missing, older than 24 h, unparseable or not
  VALID, every strategy is treated as not news-validated and every entry is blocked during the US
  session window until valid data returns. This is the fail-closed behaviour in force.
- The manual blackout schedule named in SYSTEM_ARCHITECTURE §6 is **OPEN**: no spec defines its
  file, format or precedence. [RECOMMENDATION] When specified, it may only add blackout windows; it
  never makes calendar data VALID and never shortens the TIME-042 block.

## Consequences

- No calendar API key and no extra outbound flow.
- News handling depends on the Guardian running; a missing or stale Guardian blocks US-session
  entries for strategies that need the calendar (fail closed).
- The relevance mapping file is a new versioned artefact to maintain.
- The P-18 window (−30/+15 min) is [ASSUMPTION A-45], reviewed after M9.

## Reversal cost

Low to medium. The engine reads a file with a schema; another producer could write the same schema,
but an external source would need an ADR line, consent (PRV §5) and a threat-model update.
