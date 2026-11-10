# PRIVACY_POLICY — How GoldBot handles the user's data

> Status: **SPECIFICATION** (an engineering policy for a single-user, self-hosted tool). This is not
> legal advice. Which data-protection laws apply in the user's country has **not** been assessed
> [OPEN-PRV-1]. Nothing here claims compliance with any law.

## 1. Principles

- **PRV-001 Local-first.** All operational and research data stays on the user's machine(s).
  There is no GoldBot cloud service.
- **PRV-002 Minimisation.** Collect only what a stated function needs (§3). GoldBot never collects
  identity documents, deposit/withdrawal details, payment card or bank data, or broker Personal Area
  credentials (SEC-003).
- **PRV-003 Telemetry off.** No usage telemetry, crash upload or analytics is sent anywhere unless
  the user explicitly opts in (§6). The default build contains no telemetry endpoints.
- **PRV-004 Explicit consent** for every outbound data flow other than the broker connection itself
  (§5).

## 2. Data classification

| Class | Examples | Storage | In logs? | To LLM? | To MCP? |
|---|---|---|---|---|---|
| C1 Public/low | Market ticks, bars, calendar events, research metrics | Parquet/SQLite | Yes | Aggregates only | Yes |
| C2 Internal (integrity-critical) | Risk config, strategy versions, audit log, health | SQLite, Git | Yes | No | Summaries only |
| C3 Confidential (personal financial) | Account login, server name, balance, equity, positions, trade history, P/L | SQLite (BitLocker volume) | Login **hashed**; amounts allowed | **No** identifiers; amounts only as % or R (PRV-020) | Yes, redacted (MCP-040) |
| C4 Secret | Passwords, TOTP seed, session tokens, approval server key, `local_salt` versions, backup keys, MCP tokens, API keys | OS keyring only | **Never** | **Never** | **Never** |

- **PRV-010** Each SQLite table and log field is tagged with its class in `DATA_ARCHITECTURE.md` §3.
- **PRV-011** The account login appears in logs, audit payloads and exports only as
  `HMAC-SHA256(local_salt, login)[:12]` plus a `salt_version`.
- **PRV-012 `local_salt` lifecycle.**

  | Step | Rule |
  |---|---|
  | Generation | 32 bytes from the OS CSPRNG (`secrets.token_bytes`) at install; `salt_version = 1` |
  | Storage | OS keyring only (`goldbot/privacy/local_salt/v<n>`); never in files, logs, exports, backups or prompts |
  | Why it is secret | MT5 logins are short numbers. An unsalted or exposed-salt hash can be reversed by trying every number, so the salt is handled as C4 |
  | Rotation | Annually, or on exposure. A new version is generated and new records use it. Old records keep their `salt_version`. No mapping between versions is ever stored |
  | Recovery | If a salt version is lost, records under that version can no longer be linked to a login. That is accepted (pseudonymisation still holds); the system creates a new version and carries on |
  | Exposure response | Treat as T24-class (credential compromise): rotate immediately; mark the exposed version `compromised` in the audit; hashes under it are treated as linkable personal data for retention purposes |
  | Deletion of identifiers | Deleting every salt version makes all stored login hashes permanently unlinkable (crypto-shredding). This is the deletion method for identifiers inside hash-chained records (PRV-013) |

- **PRV-013 Deletion vs hash-chained audit records.** Audit records are never rewritten to satisfy
  a deletion request; a silent rewrite would break the integrity guarantee (SEC-022). The audit
  log is designed so that this is not needed: it stores only IDs, hashed identifiers, amounts in R
  or %, and `payload_hash` values. Personal content (account snapshots, deal details, notes) lives
  in separate, deletable tables. Deletion therefore means: (1) delete the content tables;
  (2) crypto-shred the identifiers (PRV-012); (3) append an explicit `DELETION_PERFORMED` audit
  event stating what was deleted and when. The chain stays verifiable. Retention-based truncation
  of old audit records (§4) is likewise an explicit, audited event, never a silent edit.

## 3. What is collected, and why

| Data | Purpose | Source |
|---|---|---|
| Account properties and snapshots | Risk, display, reconciliation | MT5 |
| Positions, orders, deals | Ledger, reconciliation, P/L, audit | MT5 |
| Ticks/bars | Signals, freshness, research | MT5 / tick archive |
| UI actions (approvals, mode changes, emergency actions) | Accountability | User |
| Dashboard username, password hash, TOTP seed | Authentication | User |
| Phase-0 attestation (yes/no + date, no documents) | Gate for LIVE | User |

## 4. Retention and deletion

| Data | Retention (default) | Deletion |
|---|---|---|
| Tick/bar research data (C1) | Until the user deletes it | `goldbot data purge --before <date>` |
| Trade ledger, deals, audit log (C2/C3) | 7 years by default [ASSUMPTION: a reasonable personal record-keeping period; the user may set it shorter after checking local tax/record rules — OPEN-PRV-2] | Retention job deletes expired content rows. Expired audit records are removed only as a whole prefix of the chain, with an explicit `TRUNCATION` event that records the last removed hash, so the remaining chain still verifies (PRV-013) |
| Application logs (C2, redacted) | 90 days | Daily rotation job |
| Heartbeat/IPC files | Overwritten continuously; Guardian audit ingested then rotated after 30 days | Automatic |
| LLM request/response records (if enabled) | 30 days | Automatic; `goldbot llm purge` |
| Session tokens | Until expiry (≤ 30 min idle, 12 h absolute) | Automatic |
| Backups | 30 daily + 12 monthly | Rotation; deletion is verified by listing. Each monthly generation has its own encryption key, so destroying a key crypto-shreds that generation (PRV-030) |
| MCP client histories | Outside GoldBot's control | GoldBot keeps only its own audit of calls (MCP-045). Conversations held by the MCP client app or its model provider follow their policies. The consent screen says so (MCP-031) |
| External AI provider copies | Outside GoldBot's control | Provider retention is shown on the consent screen with the provider name and policy link recorded at consent time (PRV-023) |

- **PRV-015 Full deletion workflow.** `goldbot privacy delete-all --confirm` stops the processes,
  deletes the SQLite DBs, Parquet, logs, IPC files and backups in configured locations, destroys the
  backup keys and every salt version, and removes keyring entries. It prints a checklist of anything
  outside its reach (e.g. off-box backup copies the user made, MCP client histories, LLM provider
  retention).
- **PRV-014 Partial deletion request** (e.g. "forget my account identifiers"): content tables
  holding the identifiers are deleted or overwritten, the salt is crypto-shredded (PRV-012), backups
  that contain the data are listed with their expiry dates (they are not rewritten), and a
  `DELETION_PERFORMED` audit event is appended (PRV-013).
- **PRV-016 Export workflow.** `goldbot privacy export` writes a ZIP of C2/C3 data (CSV + JSON +
  schema) with secrets excluded. The export file itself is classed C3.

## 5. Outbound flows and consent

| Flow | Default | Consent mechanism | Data sent |
|---|---|---|---|
| Broker (MT5 terminal) | On (inherent) | — | Whatever MT5 sends; GoldBot adds only orders |
| LLM provider | **Off** | Opt-in in Settings with provider name, data preview and spend cap (P-28); consent recorded with date | Sanitised statistics only (PRV-020) |
| MCP clients | **Off** | Opt-in per client; client id, allowed tools and admin actions recorded (MCP-030); each admin action approved per invocation | Redacted read tool outputs; admin action results (report files, job status) |
| Telemetry | **Off** | Separate opt-in | None defined in v1 |
| Off-box backups | Off | User chooses destination | Encrypted archive only |

- **PRV-018** Consent can be withdrawn in Settings. Withdrawal stops the flow immediately and is
  audited. Data already sent is outside GoldBot's control, and the UI says so.

## 6. LLM data exposure rules

- **PRV-020 What may be shared** with an external AI service (minimum necessary for the requested
  function): aggregate performance metrics in R or %; strategy names and versions; regime labels;
  anonymised trade lists (timestamps rounded to the hour, sizes as R); public market data; research
  text written by the user.
- **PRV-024 What must never be shared:** passwords, MT5 trading or investor credentials, TOTP seeds,
  session or API tokens, keyring contents, salts, identity documents, deposit or withdrawal details,
  bank or card data, account numbers (even hashed), server names, balances or equity in currency,
  the user's name, email or location, and unnecessary personal information of any kind.
- **PRV-025 Sanitisation.** `build_llm_payload()` (PRV-021) builds payloads from an allowlist
  schema only. Free text written by the user is scanned for secrets and identifiers (the same
  patterns as SEC-004, plus email/phone/number patterns) and blocked if any match. The exact payload
  is shown to the user before the first send of each payload type.
- **PRV-021** Prompt construction goes through a single `build_llm_payload()` function with an
  allowlist schema. A test asserts that C3 identifiers and all C4 values are absent.
- **PRV-022** Responses are stored ≤ 30 days (§4) and never forwarded to other services.
- **PRV-023 Provider disclosure and consent.** Consent (PRV-018) records the provider name, model,
  the data categories from PRV-020 that will be sent, the provider's stated retention policy (link
  and date), and the spend cap (P-28). A provider change requires new consent.
- **PRV-026 Provider unavailable.** AI features show "unavailable". Nothing containing user data is
  queued for later sending. At most 1 retry, then a 5-minute wait. Trading is unaffected (LLM-006).

## 7. Backups and restore

- **PRV-030** Daily encrypted backup (e.g. `age` or 7-Zip AES-256) of SQLite and config (never of
  keyring contents). Encryption keys: one per monthly generation, stored in the keyring, with an
  offline recovery copy kept by the user (printed or on a separate device). Destroying a
  generation's key makes that generation unreadable (crypto-shredding). Backups are never
  decrypted and rewritten to remove individual records; they expire by rotation.
- **PRV-031** Restore test monthly (automated in the runbook): restore to a temporary directory,
  verify the audit chain, open the DB, compare row counts. A failed restore test is an alert.

## 8. Open items

OPEN-PRV-1 applicable data-protection law; OPEN-PRV-2 record-retention requirements for trading
records in the user's jurisdiction. Both are for the user to check and are listed in
`quality/ASSUMPTIONS_AND_UNKNOWNS.md`.
