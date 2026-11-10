# SECURITY_THREAT_MODEL — Assets, controls and residual risk

> Status: **SPECIFICATION.** Method: assets → trust boundaries (`SYSTEM_ARCHITECTURE.md` §4) →
> threats (STRIDE + LLM/MCP-specific) → controls → residual risk. Likelihood and impact use
> L/M/H. They are judgements for a single-user Windows host, not measurements.

## 1. Assets

| Asset | Why it matters | Classification (`PRIVACY_POLICY.md` §2) |
|---|---|---|
| MT5 trading password | Allows trading on the account | C4 Secret |
| MT5 investor (read-only) password | Reveals positions/history | C4 Secret |
| Broker Personal Area credentials | Funds, withdrawals, KYC | **Never handled by GoldBot** (SEC-003) |
| Dashboard password, TOTP seed, session tokens | Approve trades, change entry mode, use the emergency controls | C4 Secret |
| Guardian IPC folder and its ACL (no secret exists, GRD-008) | Integrity of engine ⇄ Guardian files | C2 Internal (integrity-critical) |
| Per-client MCP tokens, approval HMAC server key, `local_salt` | Attribution, approval integrity, pseudonymisation | C4 Secret |
| LLM provider API key (optional) | Cost; data exfiltration route | C4 Secret |
| Account number, balances, trade history | Personal financial data | C3 Confidential |
| Risk config, strategy code/version | Loosening = financial harm | C2 Internal (integrity-critical) |
| Audit log | Accountability | C2 Internal (integrity-critical) |
| Market data, research results | Low sensitivity | C1 |

## 2. Credential protection

- **SEC-001** Secrets live in the OS credential store via `keyring` (Windows Credential Manager).
  They are never stored in source code, Git, ordinary configuration files (including `.env`),
  logs, prompts, screenshots, exported reports, error messages, MCP outputs or LLM inputs. **What
  the keyring protects against:** other Windows accounts and offline disk access (together with
  BitLocker). **What it does not protect against:** any process running as the same Windows user,
  which can read that user's entries. This is why same-user malware remains an accepted residual
  risk (TM-07) and why no design decision relies on a secret being hidden from same-user processes.
- **SEC-007 Credential compromise response** (T24): the engine enters SUSPENDED; the dashboard lists
  what to rotate (MT5 trading and investor passwords via the broker, dashboard password, TOTP seed,
  MCP tokens, approval server key, `local_salt` per PRV-012); the user rotates them; old tokens are
  deny-listed; recovery is MANUAL (RISK-053).
- **SEC-002** The investor password is used for every read-only path (M2 Observer, research data
  pulls). The trading password is loaded only by the `engine` process and only when `env ∈
  {DEMO, LIVE}` and the milestone permits trading.
- **SEC-003** GoldBot never asks for, stores or uses the broker Personal Area login, withdrawal or
  deposit credentials, identity documents or payment details.
- **SEC-004** Redaction: a logging filter removes registered secret values and patterns (password=,
  token=, key=, 16+ char base64/hex runs in sensitive fields). A property test feeds random secrets
  through every log path.
- **SEC-005** Pre-commit `gitleaks` + a CI secret scan. A detected secret fails the build and must be
  rotated, not merely deleted.
- **SEC-006** Separate permissions: *monitoring* (investor password; API `ui:read`, `mcp:read`)
  versus *trading* (trading password; API `ui:command`). The MCP server never receives `ui:command`.

## 3. Host and supply-chain controls

- **SEC-010 Host:** dedicated Windows user for the terminal + engine; BitLocker; automatic OS updates
  with active hours set so they never reboot during sessions (RUNBOOK); RDP disabled; power and sleep settings keep the computer awake during trading sessions; Windows Defender on; no browser extensions on the trading user.
- **SEC-011 Network:** the API binds to `127.0.0.1` (API-001). **No remote access** is part of the
  design (user decision, ADR-013). Adding remote viewing later needs a separate ADR and a
  threat-model update. The firewall blocks inbound connections to the API port.
- **SEC-012 Dependencies:** `uv.lock` / `pnpm-lock.yaml` committed with hashes; `pip-audit` and
  `pnpm audit` in CI; new dependencies need an ADR line; no MQL5 Market/third-party EAs or DLL
  imports in the terminal used for GoldBot.
- **SEC-013 Builds:** CI runs lint, type checks, tests and secret scan on every commit. Releases
  are tagged, and the engine refuses to start `env=LIVE` from a dirty working tree.

## 4. Integrity of configuration, approvals and logs

- **SEC-020** `risk_limits.yaml` hash checked at start and on every cycle (T16).
- **SEC-021** Approval tokens: HMAC over `sha256(proposal)` + nonce + expiry; single-use; bound to the
  session and the user (API-031).
- **SEC-022** Audit log append-only with a SHA-256 hash chain. `verify_chain()` runs daily, and the
  daily export is written locally, encrypted (PRV-030). It goes off-box only when the user enabled
  off-box backups (`PRIVACY_POLICY.md` §5, off by default).
- **SEC-023** Commands (approve, mode change, emergency, clear) are re-validated by the engine
  regardless of what the API checked (API-020).

## 5. LLM and content security

- **SEC-030** LLM inputs are built from structured, sanitised statistics only (PRV-020). v1 feeds no
  raw web text, news text or email to the LLM.
- **SEC-031** LLM outputs are parsed against a JSON schema, shown to humans as advisory text, and
  never executed, never turned into orders or config, and never passed to tools.
- **SEC-032** Calendar/news data is structured (time, currency, impact level) and treated as data. No
  free text from it reaches a decision path or an LLM.

## 6. Threat register

| ID | Threat | Surface | L | I | Mitigations (requirement IDs) | Residual |
|---|---|---|---|---|---|---|
| TM-01 | Prompt injection (direct) via a user-pasted research note | LLM | M | L | LLM off the order path (LLM-001); schema output (SEC-031) | L: misleading text a human might read |
| TM-02 | Indirect prompt injection via malicious news/web content | LLM, calendar | M | M | No raw external text to the LLM (SEC-030, SEC-032); calendar is structured | L |
| TM-03 | Compromised or malicious MCP client calls tools | MCP | M | M | Per-client scopes enforced by the API (MCP-020/021); no trading or safety route accepts any `mcp:*` scope (MCP-011); admin actions need per-invocation human approval (MCP-030); redaction (MCP-040); rate limits | L for actions; **M for reads**: a same-user process can impersonate a registered client and read the data that client may read (MCP-022) |
| TM-04 | MCP tool output used for injection against the user's AI client | MCP | M | L | Outputs are data-only JSON with no free-text fields from external sources (MCP-041) | L |
| TM-05 | Local API abuse by another local process or a web page (CSRF, DNS rebinding) | API | M | H | Loopback bind; Host/Origin allowlist; CSRF tokens; SameSite=Strict; auth on every route (API-001..012) | L |
| TM-06 | Credential theft from disk, logs or memory dumps | Host | M | H | Keyring (SEC-001); redaction (SEC-004); BitLocker; investor password for reads | M if the host is compromised |
| TM-07 | Malware on the host | Host | L–M | H | SEC-010; minimal software on the trading user | **H if it occurs**: it can trade with the terminal's session. Accepted risk; mitigated only by host hygiene |
| TM-08 | Dependency compromise (PyPI/npm) | Build | L | H | Lockfiles with hashes; audits; minimal deps (SEC-012) | M |
| TM-09 | Unauthorised config change (loosening limits) | Config | L | H | Tighten-only UI; hash check T16; restart + confirmation (RISK-090) | L |
| TM-10 | Tampering with Guardian files | IPC | L | H | SHA-256 integrity + seq + instance + folder ACL check (GRD-008); Guardian hard limits as user-set inputs that files can only tighten (GRD-002/003); kill-flag clearing only by user re-arm (GRD-016) | M against same-user malware (see TM-07); L otherwise |
| TM-11 | Replay of an approval or command | API | M | H | Nonce + single use + expiry + proposal hash binding (API-031) | L |
| TM-12 | Approval forgery / UI redress (clickjacking) | Web | L | H | `frame-ancestors 'none'`; hold-to-confirm; re-auth for mode/clear (API-033) | L |
| TM-13 | Log tampering to hide actions | Audit | L | M | Hash chain + daily encrypted export, off-box only when the user enabled it (SEC-022) | L with the off-box export enabled; M by default, because a same-user process could rewrite the local chain and the local export together (TM-07) |
| TM-14 | Data exfiltration via the LLM provider | LLM | M | M | Minimum data, no identifiers (PRV-020/021), disabled by default | L–M depending on provider terms |
| TM-15 | Privilege escalation from `ui:read` / `mcp:read` to commands | API | L | H | Server-side scope checks per route; tests for every route × scope (API-040) | L |
| TM-16 | Session hijacking | Web | L | H | HttpOnly, Secure (when TLS), SameSite=Strict, 30-min idle expiry, rotation on login (API-010) | L |
| TM-17 | API exposed to the local network or internet by mistake (e.g. a changed bind address or firewall rule) | Network | L | H | Startup self-check refuses a non-loopback bind (API-002); firewall rule check in `goldbot doctor` | L |
| TM-18 | SSRF through a configurable URL (LLM endpoint, calendar fallback) | Engine | L | M | Fixed allowlist of outbound hosts; no user-supplied URLs at runtime | L |
| TM-19 | Malicious strategy/research code from the internet | Research | M | H | Research runs without trading credentials (B8); code review before version freeze (RES-011) | L |
| TM-20 | Social engineering: "approve this trade quickly" | Human | M | M | Approval card shows the full numbers; expiry; no external approval channels (dashboard only) | M |
| TM-21 | Abuse of MCP admin actions (resource exhaustion, misleading journal notes) | MCP | L | M | Per-invocation approval; `queue_research_job` pauses whenever a position is open; notes are append-only, labelled `mcp_client` and never read by decision paths (MCP §4.1) | L |
| TM-22 | Two engine instances running at once (duplicate orders) | Engine/IPC | L | H | In-flight lock (EXE-002); duplicate-instance detection by the Guardian (GRD-008) → T22; single-instance lock file at engine start | L |

## 7. Security testing (M8 + M9)

Route × scope authorisation matrix tests; CSRF and Origin tests; a DNS-rebinding test (Host header
spoof); replay/expired/altered approval tests; secret-redaction property tests; log-chain tamper
test; Guardian file tamper/replay/ACL/duplicate-instance tests; MCP per-client scope and admin-approval tests (MCP-060); MCP tool allowlist and redaction tests, including attempts to
call unlisted tools, pass SQL or paths, and request secrets; dependency audit; a non-loopback bind
refusal test; an ECC `security-reviewer` review plus Claude Code `/security-review` on the full diff
of M8.
