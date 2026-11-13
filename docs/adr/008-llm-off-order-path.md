# ADR-008: The LLM is off the order path, disabled by default, spend-limited, schema-validated and tool-less

Status: Accepted (specification, 2026-11-13)

## Context

GoldBot is AI-assisted: statistics generate signals, and an LLM may help with research and
explanations (SYSTEM_ARCHITECTURE §1). Published evidence on LLM trading is weak and inconsistent
[S30, S31], and any LLM that reads external text has a prompt-injection surface [S24]. The user has
not enabled an LLM: kickoff question 4 is recorded as "Disabled", and P-28 (the monthly spend
limit) is still USER_DECISION_REQUIRED (`docs/STATUS.md` §9). Trading must keep working with every
AI provider unreachable (LLM-006).

## Options

| Option | Summary | Assessment |
| --- | --- | --- |
| A | Optional LLM for research drafts, report summaries and metric explanations only; off the order path | Chosen |
| B | LLM signal generation or LLM-approved entries | Rejected: weak evidence [S30, S31]; prompt-injection path to orders [S24]; conflicts with LLM-001 |
| C | No LLM component at all | Not chosen: it would remove the permitted advisory uses (LLM-002) that the user may enable later |

## Decision

- LLM-001: no LLM output can create, approve, size, modify or cancel an order, or change any limit,
  mode or state. The order path has no import of the `llm` module, enforced by a static test.
- LLM-002: permitted uses are research hypothesis drafts (each tested hypothesis counts as a trial,
  RES-021), summaries of deterministic reports and plain-language metric explanations, labelled
  "AI-generated, advisory".
- LLM-003: inputs follow PRV-020/021 (sanitised minimum data, never PRV-024 items); outputs are
  schema-validated and never executed (SEC-031).
- LLM-004: disabled by default. When enabled: provider pinned in config, P-28 enforced in code
  (calls refused at the limit), consent recorded (PRV-018). P-28 = 0 means disabled.
- LLM-005: the trade-proposal rationale is a deterministic template, never LLM text.
- LLM-006: no AI service is a dependency of authorization, risk, stop calculation, sizing,
  emergency operations or reconciliation; a REPLAY run with every AI provider blocked must produce
  identical trades.
- The LLM has no tools (SYSTEM_ARCHITECTURE §3).

## Consequences

- The system's safety and its edge verdict never rest on an LLM.
- Enabling the LLM is a user decision with consent and a spend value (P-28); nothing is enabled in M0.
- Failure handling is bounded: at most one retry, then a 5-minute wait; no queued user data
  (LLM-006).
- An LLM-generated signal model is not possible under this ADR; D-11 records that an external AI
  service in the signal path conflicts with LLM-001/LLM-006.

## Reversal cost

Very high, by design. Putting an LLM on the order path would break invariants 21 and 23 in
CLAUDE.md §3, LLM-001 and TRADING_RISK_SPEC §10, and would require the user to change the
constitution.
