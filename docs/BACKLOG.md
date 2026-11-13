# BACKLOG — Deferred items and the gate each must pass

> M0c deliverable (kickoff §5). Created 2026-11-13. Source: `specifications/SYSTEM_ARCHITECTURE.md`
> §8, other deferrals written in the specs, the user's decisions of 2026-11-13 (`docs/STATUS.md` §8
> and §9), and the non-blocking M0b review items (`docs/STATUS.md` §11).
> Nothing here is scheduled or approved. An item leaves the backlog only when its whole gate is met
> and the user approves it in chat. A gate never lowers a requirement in `specifications/`.

## 1. Deferred from SYSTEM_ARCHITECTURE.md §8 (not in v1)

| ID | Item | Why deferred | Gate it must pass (requirement IDs, milestone, evidence) |
| --- | --- | --- | --- |
| BL-01 | Strategy selection or regime switching outside the M6f prevalidated selector | Switching on unvalidated rules or recent P/L is how losses are chased (RES-061) | A new user decision and an ADR; the rule is registered and validated as one C4 strategy (RES-023, RES-061, MI-052) with every candidate × selection-rule combination counted as a trial; A1–A10 verdict PASS (RES-024); no input is a strategy's own P/L (RES-061); then the RISK-063 forward test on demo |
| BL-02 | ML signal models (PyTorch, XGBoost or any fitted model in the signal path) | D-10 decided rule-based only (2026-11-13); not in the v1 stack (CLAUDE.md §5) | See BL-11 |
| BL-03 | PostgreSQL | No benefit at this scale (ADR-004) | A new ADR reversing ADR-004 with measured evidence that SQLite (WAL) does not meet a stated need; migration scripts and a schema-version gate (DATA-020); DATA-001 single-writer and DATA-005 env separation kept; dependency approval (CLAUDE.md §7); full regression of M1, M5, M7 tests |
| BL-04 | Multi-symbol trading | v1 is one gold symbol; aggregate risk assumes one correlated symbol (P-31 rationale) | A new user decision and an ADR; spec changes for aggregate risk and exposure across symbols (RISK-015, EXP-001..009) and per-symbol discovery and validation (CENT-002..018); new golden vectors (TRADING_RISK_SPEC §11); full M3 and M7 regression; a new M10 readiness review |
| BL-05 | Cloud or VPS hosting | User decision: local Windows computer only (ADR-013) | Not in the design. Only through a separate ADR reversing ADR-013, a SECURITY_THREAT_MODEL update, and an explicit user decision; then the M8 security tests re-run |
| BL-06 | Remote access to the dashboard or API | Loopback only (API-001/002, SEC-011, ADR-013) | Not in the design. Only through a separate ADR, a threat-model update (TM-05, TM-17), an explicit user decision, and the API-040 route × scope tests re-run for the new exposure |
| BL-07 | Telegram, email, SMS or any other external notification channel | Dashboard is the only channel (OBS-020, ADR-013) | Not in the design. Only through a separate ADR, recorded consent for the outbound flow (PRV-004, PRV-018), a threat-model update, and a test that safety works with the channel down (as LLM-006 for AI) |
| BL-08 | MCP trading tools (place, modify or close orders; change risk, Guardian or safety state) | Unacceptable path to trading actions | **Permanently prohibited** (MCP-010, MCP-011, ADR-009). No gate exists |
| BL-09 | Any LLM-generated trade logic, orders, limits, modes or states | LLM must never touch the order path | **Permanently prohibited** (LLM-001, ADR-008). No gate exists |

## 2. Other deferrals written in the specs

| ID | Item | Source | Gate it must pass |
| --- | --- | --- | --- |
| BL-10 | Engine-side Windows toast that works with the dashboard closed | OBS-024 ("goes to the backlog"): needs a new dependency | Dependency approval (CLAUDE.md §7) and an ADR line (SEC-012); notification text with no amount, account or price (OBS-024); no external channel (OBS-020); test in M9 or later |
| BL-12 | DLL-based Windows Credential Manager access for the Guardian | GRD-008 "Future alternative" | A new ADR, a SECURITY_THREAT_MODEL update (TM-07, TM-10) and explicit user approval; changes GRD-005 (no DLLs); M7b Guardian tests re-run |
| BL-13 | Network (non-stdio) MCP transport | M8 out of scope; MCP is stdio only (ADR-009) | A new ADR, a threat-model update (TM-03), an explicit user decision, and the MCP-060 tests re-run |
| BL-14 | Off-box (remote) backups | Off by default (PRIVACY_POLICY §5, SEC-022) | User chooses a destination and records consent (PRV-004); encrypted archive only (PRV-030); the TM-13 residual is restated |
| BL-15 | Automatic entry on the live account after a pilot that ran with human approval | M10 out of scope; the readiness review recommends `MANUAL_APPROVAL` for the first 4 weeks; D-01 is `AUTO_ALL` | `prompts/03_RELEASE_READINESS_PROMPT.md` run for "enabling automatic entry on live": the live pilot report with ≥ 4 weeks and ≥ 30 trades; RISK-061 (promotion gate RISK-063 per strategy, state ACTIVE, re-authentication); the user's written decision |

## 3. Deferred by the user's decisions of 2026-11-13

| ID | Item | Decision | Gate to reconsider |
| --- | --- | --- | --- |
| BL-11 | ML-assisted or hybrid signals | D-10: rule-based only, no model in the signal path; D-11: no AI in signals | A new user decision replacing D-10 (and D-11 for any AI component); the model runs locally, is versioned and validated as class C3 (RES-023: purging and embargo RES-007, nested walk-forward, feature-importance stability, PBO, DSR, A8 on hyperparameters, frozen model hash); no external AI service in the signal path (LLM-001, LLM-006); dependency approval (CLAUDE.md §5, §7); verdict PASS, then RISK-063 |
| BL-16 | LLM integration (research summaries, hypothesis drafts) | §4 question 4 and D-11: disabled; P-28 = 0 | The user sets P-28 > 0 by editing `config/risk_limits.yaml` (RISK-090, RISK-092); provider pinned and consent recorded with provider, model, data categories, retention policy and spend cap (LLM-004, PRV-018, PRV-023); payloads only through `build_llm_payload()` (PRV-020, PRV-021, PRV-024, PRV-025); the order-path import ban and the blocked-network REPLAY test pass (LLM-001, LLM-006); the M8 privacy tests pass |
| BL-17 | Deploying a strategy that the system researched and reported (D-11) | D-11: the system may research and report, never deploy without approval | Registered in the experiment registry (RES-010); A1–A10 verdict PASS (RES-024); news status and envelope declared (RES-070, RES-071); the RISK-063 forward test; the user's explicit approval in chat |

## 4. Non-blocking M0b review items (from `docs/STATUS.md` §11)

Each must be resolved by the milestone named, at the latest. Resolving one may need a spec change,
which needs the user's approval (CLAUDE.md §2).

| ID | Item | Must be resolved by | Gate |
| --- | --- | --- | --- |
| NB5 | Money values in MCP outputs under privacy mode | M8 (MCP server) | MCP output schemas state how money is shown or redacted (MCP-040, PRV-020); redaction tests (MCP-060) pass |
| NB6 | Structured values (not free text) in `get_risk_status` output | M8 (MCP server) | Output schema uses typed fields (decimal strings plus currency, DATA-004); MCP-041 data-only outputs; schema validates |
| NB8 | Schemas for `config/app.yaml` and `config/session_exceptions.yaml` | M1 (config loader with schema validation; `session_exceptions.yaml` is first read in M2) | Both schemas exist and pass `check-jsonschema`; the examples validate; the loader rejects an invalid file (RISK-090 pattern) |
| NB11 | `expires_mono` (proposal expiry on the monotonic clock) across engine or computer restarts | M8 (approval-token implementation, API-030..033), before M9a uses approvals | A stated rule that a proposal from a previous process start is expired (monotonic values do not survive a restart, TIME-015); a restart test |
| NB12 | Per-command payload schemas for the `commands` table | Before M4 starts (STATUS §11 says "before M4"); M1–M3 | One schema per command type (API_SPEC §4); the API and engine validate payloads (API-020); schema sync test (DATA-011) |
| NB13 | Confidence scores as JSON numbers inside hashed canonical JSON | M6a (Evidence and decision records) | A canonical representation for non-money decimals in hashed JSON (for example decimal strings), identical in Python and MQL5 where shared; a determinism test showing equal hashes across runs (MI-017) |
