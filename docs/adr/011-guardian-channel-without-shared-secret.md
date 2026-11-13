# ADR-011: Engine ⇄ Guardian channel uses SHA-256 integrity, `seq`, `instance_id` and a Windows folder ACL, with no shared secret

Status: Accepted (specification, 2026-11-13)

## Context

The engine and the Guardian exchange JSON files in `TERMINAL_COMMONDATA_PATH\Files\goldbot\`
(GUARDIAN_SAFETY_SPEC §3; [VERIFIED S15]). V2 first used an HMAC key stored in the keyring and in a
`guardian.key` file, which broke the keyring-only rule for secrets (CLAUDE.md §3.14). MQL5 has
SHA-256 but no native HMAC or asymmetric signatures [VERIFIED S17; A-26]. No MQL5 function for the
Windows Credential Manager was found [ASSUMPTION, A-60]; reaching it would need DLL imports, which
GRD-005 forbids. Any process running as the same Windows user can read that user's keyring entries.

## Options

| Option | Summary | Assessment |
| --- | --- | --- |
| A | SHA-256 digest over canonical JSON + `instance_id` + strictly increasing `seq` + Windows folder ACL; no secret | Chosen (GRD-008) |
| B | HMAC key in a file or in EA inputs | Rejected: breaks the keyring-only rule, and gives no protection against same-user processes |
| C | DLL access to the Credential Manager | Rejected: forbidden by GRD-005 without a new ADR, a threat-model update and user approval |

## Decision

- Integrity: every message carries `digest = SHA-256(canonical_json_without_digest)`
  (`CRYPT_HASH_SHA256` [VERIFIED S17]; Python `hashlib`). This detects corruption and torn writes.
- Freshness and replay: random per-start `instance_id` plus strictly increasing `seq`; age measured
  by the reader's monotonic clock (GRD-007).
- Writer authentication: Windows ACL on the folder (owner = the trading account; inheritance off;
  full control for that account and SYSTEM only), verified by the engine at start and hourly. The
  ACL approach is [ASSUMPTION A-62], tested in M2.
- Atomic writes: temp file then rename (GRD-006); `os.replace` atomicity is [ASSUMPTION A-28],
  stress-tested in M2. Readers keep the last good message on any failure.
- Failures: three consecutive integrity failures, any ACL failure, or two live engine
  `instance_id`s within P-21 (`DUPLICATE_ENGINE`) → T22 (MANUAL) and a security alert (GRD-008,
  GRD-031).
- Key generation, storage, delivery and rotation: not applicable; no secret exists (GRD-008).

## Consequences

- No secret on disk, in EA inputs or in the channel; nothing to rotate or revoke.
- Same-Windows-user malware can forge messages. This residual risk is accepted and stated
  (TM-07, TM-10). Guardian hard limits remain user-set EA inputs that files can only tighten
  (GRD-002/003), and the kill flag clears only by user re-arm (GRD-016), which bounds what a forged
  file can do.
- The runbook needs a scripted `icacls` restore and the GRD-008 recovery steps.
- Python and MQL5 must produce identical canonical JSON; shared NIST SHA-256 fixtures test this
  (GUARDIAN_SAFETY_SPEC §12/§13).

## Reversal cost

Medium. Adding authentication later means a DLL-based design (new ADR, threat-model update, user
approval) and a new message schema version on both sides (DATA-010).
