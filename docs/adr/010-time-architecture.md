# ADR-010: Time architecture per TIME_AND_CLOCK_SPEC; the Guardian exports server time

Status: Accepted (specification, 2026-11-13)

## Context

V1 used the latest tick time as broker "now", a confirmed defect (TIME_AND_CLOCK_SPEC header).
`TimeCurrent()` is the time of the last quote and stops advancing when quotes stop [VERIFIED S6].
The Python package has no `TimeTradeServer` equivalent [VERIFIED S9; A-21]. `TimeTradeServer()` and
`TimeGMT()` are computed from the local clock [VERIFIED S7, S8; A-25]. The documented meaning of
Python tick times ("UTC without the shift") is ambiguous [VERIFIED S10; A-22, BLOCKED for
interpretation until the TIME-005 measurement in M2].

## Options

| Option | Summary | Assessment |
| --- | --- | --- |
| A | Five separate clocks with fixed uses; the Guardian exports server time and the offset | Chosen |
| B | Last tick time as "server now" | Rejected: wrong when the market is quiet or closed, or the terminal is disconnected |
| C | Local wall clock for everything | Rejected: NTP steps and DST changes would alter timeouts; freshness would not measure the feed |

## Decision

- Five clocks, never interchanged (TIME_AND_CLOCK_SPEC §1): C1 local UTC wall clock (records,
  day/week boundaries); C2 monotonic (every duration, TIME-015); C3 tick-receive time (freshness,
  TIME-020); C4 estimated broker server time from the Guardian (sessions, swap time, calendar);
  C5 `tick.time_msc` (ordering and bar building only).
- TIME-001: no value is called "server now" unless it comes from TIME-030.
- TIME-030: every Guardian heartbeat (every 5 s, GRD-011) exports `TimeTradeServer()`,
  `TimeGMT()`, `TimeCurrent()`, `TimeLocal()` and `GetTickCount64()`; the engine accepts a new
  offset only when two consecutive estimates agree within P-17.
- C1 is NTP-checked every 5 minutes against at least two servers, with P-16 thresholds; NTP
  unreachable for more than 10 minutes → T11 (TIME-010).
- Staleness across processes is measured with the reader's monotonic clock (GRD-007); the
  Guardian measures tick freshness independently (TIME-023).

## Consequences

- Freshness, sessions and day boundaries stay correct in quiet and closed markets (TIME-022).
- Sessions and calendar depend on the Guardian; a stale Guardian heartbeat or missing clock fields
  → T9 (TIME-053).
- The expected Exness offset is 0 [VERIFIED S2; A-16 VERIFIED-DOC, LIVE CHECK]; a different measured
  value raises a BLOCKED item for the user (TIME-031). Both C4 inputs depend on C1, so the offset is
  only as good as TIME-010 (TIME-032).
- Session data is a weekday template only [VERIFIED S36; A-59]; holidays and early closes come from
  `config/session_exceptions.yaml`, maintained by the user (TIME-040).
- Restarts across a day or week boundary rebuild limit state from deal history (TIME-056).

## Reversal cost

High. Clock use is spread through freshness gates, heartbeats, approval expiry, session closes and
audit records; changing it would touch most safety tests.
