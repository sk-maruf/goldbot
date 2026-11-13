# ADR-012: Entry authorization mode

Status: Accepted (user decision D-01, 2026-11-13: AUTO_ALL)

## Context

The entry authorization mode (P-37, decision D-01) decides how new entries are authorised. It is
USER_DECISION_REQUIRED (TRADING_RISK_SPEC §2). CLAUDE.md §3.22 forbids choosing it on the user's
behalf. On 2026-11-10 the user stated `AUTO_ALL` as the intended final mode; that is recorded as
**intent, not an approval** of P-37 (MI-162, RISK-092; `docs/STATUS.md` §8). No approval record
(`approved_by_user`, `approved_on`, `reason`) exists in `config/risk_limits.yaml`.

## Options

From TRADING_RISK_SPEC §9:

| Mode | Behaviour | Technical consequences | Operational consequences |
| --- | --- | --- | --- |
| `MANUAL_APPROVAL` | Every entry is proposed; the user approves each in the dashboard (API-031) | Approval UI, approval tokens, P-23 expiry and re-evaluation (RISK-004); the backtest models approval delay (BT-035) | The user must be present; signals in the user's absence expire unused; lowest automation risk; forward results include approval behaviour |
| `AUTO_ALL` | Every entry that passes the RiskEngine is sent automatically | No approval in the loop; needs the promotion gate (RISK-063) and demotion triggers (RISK-062); execution-quality monitoring (EXE-060) becomes critical | Trades happen while the user is away; errors repeat faster; needs the strongest evidence before LIVE |
| `AUTO_APPROVED_STRATEGIES` | Automatic entry only for strategies the user marked `auto_approved` (each passed RISK-063 on its own); others need manual approval | Versioned per-strategy flag (RES-011); a new strategy version loses `auto_approved` | Mature strategies run unattended; new ones stay supervised |

Any mode may also be narrowed by schedule or conditions (RISK-067), only ever moving entries from
automatic to human approval. No narrowing rule exists until the user decides one.

## Decision

**`AUTO_ALL`**, decided by the user on 2026-11-13 (D-01; approval record in `config/risk_limits.yaml`,
`docs/STATUS.md` §8). It authorises entries only for strategies that passed the promotion gate
(RISK-063), in state ACTIVE and within every limit (TRADING_RISK_SPEC §9). The live-money gates of
CLAUDE.md §3.17 still apply. The rules that applied before the approval, and still apply to any
environment without an approval record:

- In `LIVE`, and in `DEMO` outside fixture demo, the engine generates no entries (RISK-065), and it
  refuses to start while P-37 lacks an approval record (RISK-005).
- In fixture demo (RISK-066) the user sets `fixture_demo_mode` per run; any of the three modes may
  be exercised. A fixture-demo run never approves a mode (RISK-092).
- BACKTEST and REPLAY state which mode they simulate (RISK-065).
- All three modes are specified and built so that the user's choice needs no redesign.

## Consequences

- Whatever is chosen, the RiskEngine is never bypassed and position closing stays automatic in every
  mode (RISK-064). Mode changes are persisted and audited (RISK-060).
- Enabling an automatic mode outside fixture demo needs RISK-061: the promotion gate (RISK-063) per
  strategy, trading state ACTIVE, typed phrase + TOTP, an audit entry, and on `env=LIVE` the M10
  pilot report and a GO from the release-readiness review. Demotion to human approval follows
  RISK-062.
- Even after a choice of `AUTO_ALL`, it stays unavailable until RISK-061 and RISK-063 are met for
  every strategy concerned, P-37 is approved, Phase 0 is cleared and the release-readiness review is
  GO (MI-162).
- D-01 blocks LIVE entries, the M9 scope and M10 (ASSUMPTIONS_AND_UNKNOWNS §5).

## Reversal cost

Not applicable until decided. After a decision, changing mode is a configuration change under
RISK-060/061 and RISK-090..092, not a code change; moving to a more automatic mode always repeats
the RISK-061 requirements.
