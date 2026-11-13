# RUNBOOK — Operating GoldBot on your Windows computer

> M0c deliverable (kickoff §5). Written for the person who runs GoldBot, not for developers.
> Last update: 2026-11-13. **Nothing is built yet.** Steps that need GoldBot code name the milestone
> that delivers them, for example "(available from M1)". Commands are the planned commands from
> `CLAUDE.md` §6 or the specs; a command the specs do not name yet is shown as `<… from Mx>`.
> Anything about MT5 or Windows menus that the specs do not confirm is marked **(verify on your PC)**.

**Read this first.** When MT5, the computer or the broker connection is unavailable, neither the
engine nor the Guardian can act. Only SL/TP orders that were broker-confirmed before the outage
remain at the broker, and they do not guarantee the exit price (GRD-030). Loss levels in this
project (P-02, P-03, P-04) are intervention thresholds: they trigger protective actions, and losses
can go past them through gaps, slippage, rejected closes, closed markets or outages (RISK-040/041).

## Contents

1. Words used in this runbook
2. Where things live
3. Install (one time)
4. Secrets: entering, rotating, and responding to compromise (SEC-001..007)
5. Guardian folder ACL: setup and verification (GRD-008)
6. Guardian attach instructions (GRD-002, GRD-013)
7. Start and stop order
8. Daily checks
9. Emergency procedures (three separate controls)
10. Emergency when the dashboard or engine is down (manual action in MT5)
11. Failed session-end close (EXE-084, T26)
12. Guardian re-arm (GRD-016)
13. Session-exception maintenance (EXE-080)
14. Outage behaviour
15. Windows update policy
16. Power and sleep settings for trading sessions
17. Backup and restore test (PRV-030/031)
18. Recovery after a trigger (RISK-050..053)
19. Alert banner → runbook section

## 1. Words used in this runbook

These are the canonical terms from `specifications/SYSTEM_ARCHITECTURE.md` §2.

| Term | Meaning for you |
| --- | --- |
| Stop Entries, Cancel Pending Orders, Emergency Liquidation | The three separate **emergency controls** on the dashboard. There is no combined button. |
| ENTRY_STOP | Trading state: no new entries. Exits and stop tightening still work. |
| SUSPENDED | ENTRY_STOP plus automatic strategies shut down. Leaving it needs manual recovery approval (RISK-050). |
| Broker-confirmed | Read back from MT5 after the action (positions, orders, deal history), not just "sent". |
| CONFIRMED / RECONCILED | Lifecycle states of an emergency action. Only CONFIRMED followed by RECONCILED means done. |
| UNRESOLVED EXPOSURE | A position that should have been closed but has no broker-confirmed close (EXE-084). |
| UNRECONCILED | The last reconciliation is too old, failed, or is still running after a reconnect (UI-012). |
| Health | `HEALTHY`, `DEGRADED`, `UNHEALTHY`, `FAILED` or `UNKNOWN`. UNKNOWN is never shown as healthy. |
| `env` | `LIVE`, `DEMO`, `BACKTEST` or `REPLAY`. Every screen shows it. |
| Recovery class | `AUTO` (resumes by itself after checks), `ACK` (you acknowledge with TOTP), `MANUAL` (full manual recovery). |

## 2. Where things live

| Item | Location | Notes |
| --- | --- | --- |
| GoldBot repository | `C:\GoldBot` | Config, code, docs. |
| Risk limits | `C:\GoldBot\config\risk_limits.yaml` | Approved values (2026-11-13). Never edit without deciding to; loosening needs file edit, restart and typed confirmation (RISK-090). |
| App settings | `C:\GoldBot\config\app.yaml` (you create it from `app.example.yaml`) | No secrets in it, ever. |
| Session exceptions | `C:\GoldBot\config\session_exceptions.yaml` (you create it from the example) | Holidays and early closes (§13). |
| Databases, logs | `data\` and `logs\` under `C:\GoldBot` (paths in `app.yaml`) | LIVE and DEMO use separate database files (DATA-005). |
| Engine ⇄ Guardian files | `TERMINAL_COMMONDATA_PATH\Files\goldbot\` | The MT5 "common data" folder. On many PCs this is `%APPDATA%\MetaQuotes\Terminal\Common\Files` **(verify on your PC)**. From M2, `uv run goldbot doctor` is planned to show the exact path (A-29). |
| Secrets | Windows Credential Manager, through `keyring` | Never in a file, Git, chat, screenshot or log (SEC-001). |

## 3. Install (one time)

Do these steps on the computer that will run GoldBot. Steps tagged with a milestone cannot be done
before that milestone is built.

1. **Windows host.** Use 64-bit Windows; the MetaTrader5 Python package ships Windows x86-64 wheels
   only (A-20).
2. **Dedicated Windows user** (SEC-010). Create a separate Windows account used only for the MT5
   terminal and GoldBot. Run the terminal, the engine and the dashboard as this user. Install no
   browser extensions for this user.
3. **Host protection** (SEC-010). Turn on BitLocker for the drive that holds `C:\GoldBot`. Keep
   Windows Defender on. Turn off Remote Desktop. Keep the Windows firewall on; inbound connections to
   the API port must be blocked (SEC-011).
4. **MT5 terminal.** Install the Exness MT5 terminal from your Exness Personal Area. Do not install
   Market EAs, third-party EAs or anything that uses DLL imports in this terminal (SEC-012). The
   Guardian is the only EA on it.
5. **MT5 saved password.** When you log in to the terminal, leave "Save password" unticked
   **(verify on your PC)**; from M2 the engine supplies the password from the keyring at login. The
   specs do not address the terminal's own password store; treat it as not allowed until the M2
   review decides.
6. **Tools** (available from M1). Install Git and `uv`. `uv` installs a Python version supported by
   the MetaTrader5 wheel. Then, in `C:\GoldBot`:
   1. `uv sync`
   2. `uv run pytest -q -m "not mt5"` (must pass)
   3. `uv run goldbot doctor` (checks environment, clocks, specs, limits, keyring, Guardian heartbeat)
7. **Dashboard tools** (available from M4). Install Node.js and `pnpm`, then
   `pnpm --dir web install`.
8. **App settings.** Copy `config\app.example.yaml` to `config\app.yaml`. Fill in:
   1. `api.port`: a free local port. Leave `bind_host: 127.0.0.1` unchanged (API-001).
   2. `mt5.magic_engine` and `mt5.magic_guardian`: two different whole numbers that you choose once.
      Write them down; you type the same numbers into the Guardian inputs (§6).
   3. `mt5.symbol`: leave empty until M2 discovery lists the gold symbols on your account; then pick
      from that list (CENT-003). Never type a symbol from memory.
   4. Leave `ntp.servers` as `time.google.com` and `time.cloudflare.com` (your choice, 2026-11-13).
   5. Leave `llm.enabled: false` and `mcp.enabled: false` until a later milestone and your consent.
   6. Never write a password, token or key in this file.
9. **Session exceptions.** Copy `config\session_exceptions.example.yaml` to
   `config\session_exceptions.yaml` (M2 creates it if you have not). Maintain it as in §13.
10. **Secrets** (available from M1/M2): see §4.
11. **Guardian folder ACL** (available from M2): see §5.
12. **Guardian build and attach** (observer build from M2; full Guardian from M7b): build with
    `uv run goldbot mql5-build` (GUARDIAN_SAFETY_SPEC §13), then attach as in §6.
13. **Dashboard login** (available from M4; full authentication in M8): set the dashboard password
    and enrol the TOTP authenticator (API-010). Keep the TOTP device with you.
14. **Final check:** `uv run goldbot doctor` passes with no failures.

## 4. Secrets: entering, rotating, and responding to compromise

### 4.1 Rules

- Secrets live only in Windows Credential Manager through `keyring` (SEC-001): MT5 trading and
  investor passwords, dashboard password, TOTP seed, session tokens, approval server key,
  `local_salt`, backup keys, MCP tokens, any API key.
- Never put a secret in a file (including `.env` and `app.yaml`), Git, chat, a screenshot, an email
  or a note-taking app. Never paste one into Claude Code.
- GoldBot never asks for your Exness Personal Area login, deposit or withdrawal details, identity
  documents or payment data (SEC-003). If anything asks for them, stop and treat it as suspicious.
- Use the **investor (read-only) password** for every read-only step (M2 observer, research data).
  The **trading password** is entered only when a milestone permits trading: Standard demo in M7,
  the live cent account only after a GO in M10 (SEC-002).
- The keyring protects against other Windows accounts and offline disk access (with BitLocker). It
  does not protect against malware running as your Windows user (TM-07).

### 4.2 Entering a secret (available from M1)

1. Log in to Windows as the dedicated GoldBot user (§3 step 2).
2. Open a terminal in `C:\GoldBot`.
3. Run `uv run python -m keyring set <service> <name>`, using the service and name that M1
   documents for that secret (the specs do not fix them yet, except `goldbot/privacy/local_salt/v<n>`
   in PRV-012). The command asks for the value with hidden input; type or paste it there only.
4. Check it is stored: open **Control Panel → Credential Manager → Windows Credentials** and look
   for the entry name **(verify on your PC)**. Do not reveal the value.
5. Run `uv run goldbot doctor`; its keyring check must pass.

### 4.3 Routine rotation

| Secret | When | How |
| --- | --- | --- |
| `local_salt` | Once a year, or at once on exposure (PRV-012) | GoldBot creates a new version; old records keep their version (available from M8). |
| Any secret found by the secret scan (gitleaks, SEC-005) | Immediately | Rotate it. Deleting it from the file or history is not enough. |
| MT5 passwords, dashboard password, TOTP, MCP tokens, approval key | On suspected compromise (§4.4) | As in §4.4. |

### 4.4 Credential compromise response (SEC-007, trigger T24)

Signs: a secret-scan hit, an unexpected login, a keyring entry that changed, a Guardian integrity
or ACL alert (T22), or anything you report yourself. When GoldBot detects it, the engine enters
SUSPENDED (T24, MANUAL recovery) and the dashboard lists what to rotate.

1. **Stop Entries** on the dashboard (§9.1) if the engine has not already gone to SUSPENDED.
2. **Decide about open positions.** If you believe someone else can trade on the account, close
   positions with Emergency Liquidation (§9.3) or by hand in MT5 (§10). Do not switch the computer
   off while a position is open (§14).
3. **Scan the computer.** Run a Windows Defender full scan, and an offline scan if offered
   **(verify on your PC)**.
4. **From a different, clean device**, change the MT5 trading and investor passwords through the
   broker (SEC-007). If you suspect the Exness Personal Area itself, change that too, at Exness;
   GoldBot never handles it.
5. On the GoldBot computer, after the scan is clean, rotate in this order (available from M8,
   where the dashboard lists each item):
   1. the new MT5 passwords into the keyring (§4.2);
   2. the dashboard password;
   3. the TOTP seed (re-enrol your authenticator);
   4. MCP client tokens (if MCP is in use);
   5. the approval server key;
   6. `local_salt` (PRV-012; mark the exposed version `compromised`).
   Old tokens are deny-listed by GoldBot.
6. **Check the Guardian folder ACL** (§5.3). If it changed, restore it (§5.4).
7. **Manual recovery** (§18): the T24 checklist requires the rotation to be done before the
   typed phrase and TOTP are accepted.

## 5. Guardian folder ACL: setup and verification (GRD-008)

The engine and the Guardian exchange files in `TERMINAL_COMMONDATA_PATH\Files\goldbot\`. No secret
protects them. Instead, a Windows ACL limits the folder to **your GoldBot Windows user and SYSTEM
only**, with inheritance disabled. The engine checks the ACL at start and every hour; any deviation
raises T22 (SUSPENDED, MANUAL). Setting it up is part of M2. A-62 (that this ACL does not break the
terminal's access) is an assumption tested in M2.

### 5.0 Safety rules for these commands

- Run them only on the `goldbot` folder inside the common `Files` folder. Never on `Common`,
  `Files`, the terminal's own data folder, `C:\GoldBot` or a drive root.
- Never add `/T` (recursive) and never run them on a parent folder.
- Run them as the GoldBot Windows user, in a normal (not administrator) Command Prompt.
- Do this while the engine is stopped.

### 5.1 Find the folder

1. In MT5, open **File → Open Data Folder** **(verify on your PC)**. The common folder is not the
   same as this data folder; on many PCs the common folder is
   `%APPDATA%\MetaQuotes\Terminal\Common\Files` **(verify on your PC)**. From M2,
   `uv run goldbot doctor` is planned to print the exact common-data path (A-29).
2. Open Command Prompt and set a variable to that path plus `\goldbot`, for example:
   `set GB_IPC=%APPDATA%\MetaQuotes\Terminal\Common\Files\goldbot` **(verify the path first)**.
3. Create the folder if it does not exist: `mkdir "%GB_IPC%"`. Creating it yourself makes your
   user its owner.

### 5.2 Set the ACL

1. Grant full control to your user and to SYSTEM first (the order avoids locking yourself out):
   `icacls "%GB_IPC%" /grant:r "%USERDOMAIN%\%USERNAME%:(OI)(CI)F" "*S-1-5-18:(OI)(CI)F"`
   (`*S-1-5-18` is the language-independent identifier of SYSTEM.)
2. Remove inherited permissions:
   `icacls "%GB_IPC%" /inheritance:r`
3. If step 4 below still lists any other account or group, remove it explicitly, for example
   `icacls "%GB_IPC%" /remove "BUILTIN\Users"`. Remove only accounts other than your user and SYSTEM.

### 5.3 Verify

1. `icacls "%GB_IPC%"` must list exactly two entries: your user and `NT AUTHORITY\SYSTEM`, each with
   `(OI)(CI)(F)` and none marked `(I)` (inherited).
2. Check the owner in PowerShell: `(Get-Acl "$env:GB_IPC").Owner` (or
   `Get-Acl "<path>" | Format-List Owner`) must show your GoldBot user. If it shows another
   account, stop and ask before changing ownership.
3. Start the MT5 terminal and the Guardian (observer build from M2). Within about 10 seconds
   `guardian_hb.json` must appear in the folder and keep updating. If the terminal cannot write
   there, A-62 failed: stop and report it (do not loosen the ACL to make it work).
4. From M2: `uv run goldbot doctor` reports the ACL check as passed, and the dashboard shows the
   Guardian `HEALTHY` (from M4).

### 5.4 Restore after an ACL or integrity alert (T22)

GRD-008 recovery: stop the engine, restore the ACL, remove the IPC files, restart, then complete
manual recovery.

1. Stop the engine (§7.2). Leave MT5 running if a position is open.
2. Repeat §5.2 and §5.3.
3. Move (do not delete) the files in the folder to a dated folder outside it, for example
   `C:\GoldBot\data\quarantine\YYYY-MM-DD\`, so the evidence is kept. The heartbeat, config,
   session and calendar files are rebuilt by their writers. `guardian_state.json` and
   `guardian_audit.jsonl` also live here: moving `guardian_state.json` makes the Guardian rebuild
   its state and possibly latch `STATE_LOST` (GRD-027), which then needs a re-arm (§12). GRD-008
   does not say whether these two count as "IPC files" (a spec gap raised in the M0c review); until
   that is settled, ask in the session before moving them.
4. Run a malware scan (§4.4 step 3). If you suspect compromise, follow §4.4 in full.
5. Restart in the normal order (§7.1) and complete manual recovery (§18).

## 6. Guardian attach instructions (GRD-002, GRD-013)

The Guardian's hard limits are **EA inputs that you type by hand** when you attach it. Engine files
can only tighten them (GRD-003). Each input must be **equal to or tighter than** the approved value
in `config/risk_limits.yaml` (approved 2026-11-13), **never looser**. If the engine finds any input
looser, it sets ENTRY_STOP and shows "Guardian inputs looser than policy" (GRD-013).

### 6.1 Approved values to compare against (from `config/risk_limits.yaml`)

| Guardian input (GRD-002) | Approved policy | What you may type | Notes |
| --- | --- | --- | --- |
| Daily-loss % | P-02 = 1.00% of equity at day start (00:00 UTC) | 1.00 or lower | Lower is tighter. |
| Drawdown % | P-04 = 5.00% below the equity high-water mark | 5.00 or lower | Lower is tighter. |
| Max open positions | P-05 = set per strategy within P-31 (0.25%) | **1** (user decision 2026-11-13) | With P-31 = P-01 = 0.25%, at most one full-risk position is open (STATUS §8). |
| Max volume per position | No P-xx defines it | Not yet decided | Settled with you in M7b. Must not exceed the volume the RiskEngine can approve for one trade. |
| Emergency-SL loss budget % (GRD-020) | GRD-013 compares the Guardian with P-32 = 0.25% | **0.20** (user decision 2026-11-13) | Tighter than the engine's 0.25%, so the Guardian never acts beyond what the engine allowed. |
| Missing-stop grace (s) | P-22: Guardian acts at 10 s | 10 | Type exactly 10 until the direction rule in GRD-003 is clarified. |
| Guardian close deadline | Must be later than the P-33 engine deadline (30 min before the daily break or a session end; 60 min before the last session of the week or a known early close) and at least 2 × the P-25 global deadline (2 × 60 s) before the session end (GRD-013, GRD-028) | A value inside that window | The exact value and its input format are settled in M7b. |
| Emergency retry settings | P-25: per-attempt timeout 5 s; back-off 1, 2, 4, 8 s; 5 attempts; 60 s global deadline | The same values | Same structure as P-25. |
| `MAGIC_ENGINE`, `MAGIC_GUARDIAN` | `mt5.magic_engine`, `mt5.magic_guardian` in `config/app.yaml` | Exactly the same numbers | A mismatch makes engine positions look foreign (T14). |
| `rearm_counter` | — | Any whole number; write it down | Changing it later is the re-arm (§12). |

P-03 (weekly loss 2.00%) is not a Guardian input; the engine enforces it (T3).

For illustration only, at 10,000 USC equity: P-02 triggers at about 100 USC (≈ $1), P-03 at about
200 USC (≈ $2), P-04 at about 500 USC (≈ $5). These are triggers, not limits on loss (RISK-040).

**Steps** (observer build from M2; full Guardian from M7b; menu names **verify on your PC**)

1. In MT5 enable **Algo Trading** in the toolbar, and in **Tools → Options → Expert Advisors** allow
   algorithmic trading. Do not allow DLL imports (GRD-005, SEC-012).
2. Open one chart of the gold symbol chosen in M2. The Guardian runs on **one chart only**
   (GRD-001). Never attach a second copy.
3. In the **Navigator**, under **Expert Advisors**, drag `GoldBotGuardian` onto the chart.
4. On the **Common** tab, allow algorithmic trading for this EA.
5. On the **Inputs** tab, type each value from the table above. Read every value twice.
6. Click OK. The chart should show the EA as active, and the **Experts** tab should show no errors.
7. Within about 10 seconds `guardian_hb.json` appears in the Guardian folder and keeps updating.
8. In the dashboard (from M4), open the System screen. The Guardian shows `HEALTHY`, and its
   effective limits are listed. GRD-013 must be green (no "looser than policy").
9. Write down the date, every input value and the `rearm_counter` value in your own notes (no
   passwords). M10 checks that the inputs are equal to or tighter than the approved values.

## 7. Start and stop order

### 7.1 Start (before a trading session)

The terminal and the Guardian start before the engine, because the engine reads the Guardian
heartbeat, server time and sessions during startup (EXE-070).

1. Computer plugged in; power settings as in §16; no Windows restart pending (§15).
2. **Clock.** **Settings → Time & language → Date & time**: "Set time automatically" is On
   **(verify on your PC)**. In Command Prompt, `w32tm /query /status` shows a recent successful sync
   (TIME-010).
3. Start the MT5 terminal and log in. The connection indicator (bottom right) shows a live
   connection **(verify on your PC)**. **Algo Trading** is on.
4. The Guardian is on its chart with no errors in the **Experts** tab (§6).
5. Start the engine: `<engine start command, from M1/M2>`. It loads and checks config, applies the
   Phase-0 guard for LIVE, connects to MT5, discovers the account and symbol, reads the Guardian
   heartbeat, reconciles, rebuilds limit state from deal history, and **starts in ENTRY_STOP**.
6. Start the API and open the dashboard: `<api start command, from M4>`; then open the dashboard
   address on `127.0.0.1` in your desktop browser. Log in with password and TOTP.
7. Run `uv run goldbot doctor` (available from M1).
8. In the dashboard: read every CRITICAL alert raised while it was closed (OBS-023); the top bar
   must be GREEN (every required component HEALTHY); reconciliation is clean; the Guardian is
   HEALTHY with GRD-013 green; `env` is what you expect.
9. **Leaving ENTRY_STOP.** If the last shutdown was clean and every active trigger is `AUTO` with its
   checks passing, the engine moves to ACTIVE by itself (RISK-052). Otherwise follow §18. After an
   unclean restart, automatic entry permission stays paused until you re-enable it (EXE-071).

### 7.2 Stop (after a session)

Stop only when no position and no pending order is open, preferably after the session-end close
(EXE-083). Shutting down with a position open leaves it with only its broker-side SL.

1. In the dashboard, confirm there are **no open positions and no pending orders**, broker-confirmed
   (the Positions view shows none; reconciliation clean). Cross-check the MT5 **Trade** tab
   **(verify on your PC)**.
2. If you must stop during an open session: press **Stop Entries** (§9.1), then wait for the
   strategy exits, or use **Emergency Liquidation** (§9.3) if you cannot wait. Stopping with
   Stop Entries means T1 must be cleared with TOTP next time.
3. Close the dashboard tab, then stop the API: `<api stop command, from M4>`.
4. Stop the engine with its clean-shutdown command: `<engine stop command, from M1/M2>`. A clean
   shutdown matters: after an unclean one, the next start needs manual recovery (EXE-070).
5. The MT5 terminal may stay open. When the engine stops, the Guardian marks it stale and latches
   ENTRY_STOP with reason `ENGINE_STALE`; that clears by itself after the engine is back and healthy
   for 60 s (GRD-016).
6. Only now may the computer sleep or shut down.

## 8. Daily checks

Do these at the start of every trading day, and glance at the top bar during the day.

| # | Check | Where | Pass | If it fails |
| --- | --- | --- | --- | --- |
| 1 | Missed CRITICAL alerts | Dashboard opens with them (OBS-023) | Each read and acknowledged | Follow the linked section (§19) |
| 2 | Aggregate health | Top bar | GREEN; nothing UNKNOWN | Open the System screen; the worst component explains it |
| 3 | `uv run goldbot doctor` (from M1) | Terminal | All checks pass | Fix before allowing entries |
| 4 | Clock | System screen; `w32tm /query /status` | NTP offset under 500 ms (P-16 warn) | Over 1,000 ms or NTP unreachable for 10 min → T11 ENTRY_STOP; fix Windows time |
| 5 | MT5 terminal | MT5 status bar; System screen | Connected; Algo Trading on | T12; see §14 |
| 6 | Guardian | System screen | HEALTHY; heartbeat fresh; kill flag clear; GRD-013 green | §12 (re-arm) or §5.4 (ACL) |
| 7 | Reconciliation | System screen | Clean; not UNRECONCILED | Do not trade; T7/T8 need manual recovery |
| 8 | Stop-loss protection | Positions view | Every open position shows a broker-confirmed SL | UNKNOWN → T25; see §9 and §10 |
| 9 | Session-end readiness | Overview (P-33 countdown) | Next close deadline known; calendar valid | Calendar UNKNOWN blocks entries (EXE-085); see §13 |
| 10 | Session exceptions | `config/session_exceptions.yaml` | Holidays and early closes for the next 7 days entered | §13 |
| 11 | No unresolved items | Dashboard | No UNRESOLVED EXPOSURE, no FAILED_DEADLINE, no UNKNOWN operation | §11 |
| 12 | Audit chain and database | System screen (daily jobs, from M8) | `verify_chain()` passed; `PRAGMA integrity_check` ok (DATA-022) | T23 SUSPENDED; stop and ask |
| 13 | Backup | System screen (from M8) | Last night's backup succeeded | §17 |
| 14 | Minimum-volume rejection rate | Strategy view (CENT-030) | Read it; above 50% is flagged CAPITAL-INFEASIBLE | Report it in the next session |
| 15 | Windows | Settings → Windows Update | No restart pending during the session | §15 |

## 9. Emergency procedures (three separate controls)

The three controls are separate on purpose (EMG-010). Use them in this order when you need more
than one: **Stop Entries → Cancel Pending Orders → Emergency Liquidation**. Each has its own
confirmation, deadline, retries and audit record.

**"Done" means broker-confirmed.** A request is not a result. The dashboard shows each action's
lifecycle: `REQUESTED → AUTHORIZED → SUBMITTED → CONFIRMED | PARTIAL | FAILED_DEADLINE |
BLOCKED_MARKET_CLOSED`, then `RECONCILED`. Treat an action as done only when it shows **CONFIRMED and
RECONCILED**. Emergency Liquidation is best-effort: gaps, slippage, rejects, closed markets, partial
closes and outages can delay it or make the result worse (EMG-001).

### 9.1 Stop Entries

1. Press **Stop Entries** (amber outline, pause icon). Confirm once.
2. Effect: trading state ENTRY_STOP (T1). New entries and risk-increasing changes are blocked.
   Exits, stop tightening and session-end closes continue.
3. Done when the dashboard shows the latch persisted and the Guardian echoing the kill flag.
4. Other ways (if the dashboard is down but the engine runs): the engine CLI or a `STOP` file
   (T1). The command and the file location are defined in M7a (`<stop-entries command, from M7a>`).
5. Clearing T1 needs your TOTP (MANUAL clear by the user).

### 9.2 Cancel Pending Orders

1. Press **Cancel Pending Orders** (amber filled, remove-list icon).
2. Step 1 of 2: the dialog lists the pending orders. Tick "include foreign" only if you also want
   orders not placed by GoldBot removed (EMG-030). Step 2: confirm.
3. ENTRY_STOP is set first, as a separate audited action.
4. Each order is removed with retries within the 60 s global deadline (P-25).
5. Done when CONFIRMED and RECONCILED: MT5 shows no eligible pending orders.
6. `FAILED_DEADLINE` → T19 (SUSPENDED). `BLOCKED_MARKET_CLOSED` → a new run starts at the next
   tradable moment.

Note: P-06 is 0, so GoldBot places no pending orders until a strategy needs them.

### 9.3 Emergency Liquidation

1. Press **Emergency Liquidation** (red filled, exit icon, placed apart from the other two).
2. Step 1 of 2: the dialog lists positions and volumes, offers "include foreign positions"
   (unticked), and warns that it requests closes and that fills are not assured. Step 2: confirm and
   enter your TOTP.
3. ENTRY_STOP is set first (separate audited action), and T17 puts the system in SUSPENDED.
4. Each position is closed at market with up to 5 attempts (5 s each, back-off 1, 2, 4, 8 s) within
   the 60 s global deadline (P-25, EMG-020).
5. Done only when CONFIRMED and RECONCILED: no in-scope position remains **and** closing deals are
   found in history.
6. If the result is:
   - `PARTIAL`: some volume is still open. Start a new run, or close the rest in MT5 (§10).
   - `FAILED_DEADLINE`: T19 and an UNRESOLVED EXPOSURE alert listing each open position and whether
     its SL is broker-confirmed. Start a new run, or use §10.
   - `BLOCKED_MARKET_CLOSED`: the market is closed; a new run starts at the next tradable moment.
     Meanwhile the position has only its broker-side SL, **if** that SL is broker-confirmed. Keep the
     computer and MT5 running.
7. Afterwards: manual recovery (§18).

## 10. Emergency when the dashboard or engine is down (manual action in MT5)

Use this when the dashboard cannot be reached, the engine is not running, or an emergency run keeps
failing while the market is open. Menu names **verify on your PC**.

1. Bring the MT5 terminal to the front. Check the connection indicator. If it shows no connection,
   nothing can close a position until it returns (§14).
2. Open the **Toolbox → Trade** tab. It lists open positions and pending orders.
3. **Close a position:** right-click it → **Close position** (or double-click it and use the close
   button in the order window). Close one position at a time.
4. **Remove a pending order:** right-click it → **Delete order**.
5. **Confirm it is done, by the broker:** the position or order is gone from the **Trade** tab
   **and** the closing deal appears in the **History** tab. Until you see both, it is not done.
6. If MT5 rejects the close (for example "market closed" or "trade disabled"), the position stays
   open with only its broker-side SL. Check the **S/L** column of that position. Try again when the
   market opens.
7. Do **not** open any new trade by hand on this account. A manual position is foreign to GoldBot
   (T14).
8. Switching off **Algo Trading** in MT5 stops the engine from sending orders, and it also stops the
   Guardian from acting. Do it only if you believe the engine is misbehaving and you will manage
   positions by hand.
9. When the engine starts again, it reconciles: a position you closed by hand is found in deal
   history and resolved (EXE-051). Then follow §18.

## 11. Failed session-end close (EXE-084, T26)

GoldBot does not hold positions overnight or over the weekend. At the P-33 deadline (30 min before
the daily break or a session end; 60 min before the last session of the week or a known early
close) any open position is closed by a strategy exit or Emergency Liquidation. If a position is
still open after that run, the engine raises **T26 (SUSPENDED, MANUAL)** and the dashboard shows a
persistent **UNRESOLVED EXPOSURE** bar with the position, its volume and its broker-confirmed SL (or
UNKNOWN). Close runs continue while the market is open, and never stop silently.

1. **Do not switch off the computer, MT5 or the engine.** They are the only things that can close
   the position.
2. Read the UNRESOLVED EXPOSURE bar: ticket, volume, SL status (confirmed price and time, or
   UNKNOWN).
3. Check the MT5 connection indicator and whether the market is still open.
4. Watch the emergency-action lifecycle in the dashboard:
   - runs ending `FAILED_DEADLINE` while the market is open: let the next run start, or close by
     hand in MT5 (§10);
   - `BLOCKED_MARKET_CLOSED`: the market has closed. The position is held over the break or weekend
     with only its broker-side SL, if one is broker-confirmed. A new run starts at the first tradable
     moment (EXE-086). Keep everything running and awake.
5. If the terminal is disconnected at the deadline, neither the engine nor the Guardian can act
   (EXE-086). Restore the connection (§14); close runs start on reconnect.
6. Done only when the position is gone from MT5 **and** its closing deal is in history, and the
   dashboard shows the action CONFIRMED and RECONCILED.
7. Note any swap charged on the held position; it is recorded against the failed close (CGV-08).
8. Find the cause before trading again. Common ones: a missing early close in
   `session_exceptions.yaml` (§13), rejects from the broker, a disconnection.
9. Recovery: the Guardian may also have latched `UNRESOLVED_EXPOSURE` or `TAKEOVER`; re-arm it
   (§12), then complete manual recovery (§18).

## 12. Guardian re-arm (GRD-016)

When the Guardian latches its kill flag for any reason other than `ENGINE_STALE`
(`TAKEOVER`, `EQUITY_INTERVENTION`, `STATE_LOST`, `DUPLICATE_ENGINE`, `UNRESOLVED_EXPOSURE`, or
`DISCONNECTED` with an SL re-verification failure), only you can clear it, by changing the EA input
`rearm_counter` by hand. No file from the engine can clear it. During manual recovery the dashboard
shows "Guardian re-arm required", and health check HC-4 fails until you re-arm.

1. Understand the reason first: read the Guardian reason in the dashboard and the Guardian entries
   in the audit log.
2. Fix the cause. For `UNRESOLVED_EXPOSURE` or `TAKEOVER`, re-arm only after every in-scope position
   is broker-confirmed closed (§11). For `DUPLICATE_ENGINE`, make sure only one engine runs. For
   `STATE_LOST`, check that the Guardian folder is intact (§5.3).
3. In MT5, on the Guardian's chart, open the EA properties (right-click the chart → **Expert
   Advisors → Properties**, or F7) **(verify on your PC)**.
4. On the **Inputs** tab, change `rearm_counter` to a new number (for example, add 1). While the tab
   is open, check every other input still matches §6.
5. Click OK. Changing an input restarts the EA (A-61, an assumption tested in M7b).
6. In the dashboard, check that the Guardian heartbeat is fresh, the kill flag is clear, and GRD-013
   is green.
7. Write down the new `rearm_counter` value and the date.
8. Continue with manual recovery (§18).

## 13. Session-exception maintenance (EXE-080)

MT5's session data is a weekday template only: it has no dates, holidays or one-off early closes
(A-59). You keep `config/session_exceptions.yaml` up to date from the broker's announcements.

1. **Every week, before the week's first session**, read the broker's announcements about trading
   hours for gold (holidays, early closes). Use only the broker's own announcements.
2. For each holiday or early close in the coming weeks, add an entry under `exceptions:`:
   - `date`: the trading date in broker server time, quoted `"YYYY-MM-DD"`;
   - `type`: `full_close` or `early_close`;
   - `close_time_server`: for `early_close`, the close time in server time, quoted `"HH:MM"`
     (24 h); `null` for `full_close`;
   - `source`: which announcement and the date you read it.
3. Never enter a date or time you are not sure of. A known early close uses the longer P-19 and
   P-33 windows (EXE-085).
4. Validate the file. A schema for it does not exist yet (review item NB8, `docs/BACKLOG.md`); from
   the milestone that adds it, validation runs at engine start.
5. Load the change: how the engine picks up an edit (reload or restart) is fixed in M2. Until then,
   restart the engine (§7) outside a session and with no position open.
6. Keep a record of the change (for example a Git commit of the file).
7. If the live session export and the file disagree, the session calendar becomes UNKNOWN and
   entries are blocked (EXE-085). That is the safe behaviour; correct the file.
8. Remove entries for past dates when you like; they do no harm.

## 14. Outage behaviour

| Event | What GoldBot and the Guardian do | What you do |
| --- | --- | --- |
| Computer asleep, off, or power cut | Nothing can act. Only broker-confirmed SL/TP orders remain at the broker, and they do not guarantee the exit price (GRD-030). | Prevent it during sessions (§16). On return, start in order (§7.1); the engine starts in ENTRY_STOP and reconciles. |
| MT5 terminal closed or crashed | Engine: T12 ENTRY_STOP. Guardian stopped with it. | Restart the terminal; check the Guardian (§6). T12 resumes automatically only if reconciliation after reconnect is clean. |
| Broker connection lost | Engine: T12 ENTRY_STOP; emergency runs fail their deadline. Guardian latches its kill flag and re-verifies SLs on reconnect (GRD-033). | Check your internet. On reconnect, check reconciliation and SL status. |
| Internet down beyond the broker (NTP) | NTP unreachable for over 10 min → T11 ENTRY_STOP. | Restore the connection; T11 resumes automatically after the clock is good for 5 min. |
| Engine crashed or stopped | Guardian marks it stale after 15 s, latches ENTRY_STOP, keeps the missing-stop and equity checks; it does **not** close positions just because the engine is quiet (GRD-015). | Restart the engine (§7.1). After an unclean stop, manual recovery (§18). |
| Dashboard or API down | Engine and Guardian keep running; protection does not depend on the UI. | Restart the API (§7.1 step 6). Use §10 if you need to act now. |
| Guardian removed or stale | Engine: T9 ENTRY_STOP within 20 s. | Re-attach (§6). T9 resumes automatically after the Guardian is HEALTHY for 60 s. |
| Market closed (break, weekend, holiday) | No entries. Emergency actions record `BLOCKED_MARKET_CLOSED` and retry at the next tradable moment (EXE-072). | Nothing, unless a position is open (§11). |
| AI service unavailable | Not applicable: the LLM is disabled (P-28 = 0). Trading never depends on it (LLM-006). | Nothing. |

## 15. Windows update policy

Requirement (SEC-010): automatic OS updates stay on, but Windows must never restart during a
trading session. Gold trades from Sunday evening to Friday evening server time with a short daily
break (A-11, checked live in M2), so "active hours" alone may not cover a whole trading day.

1. Keep **Windows Update** on. Do not disable the update service.
2. **Settings → Windows Update → Advanced options → Active hours**: set them to cover the hours you
   run GoldBot **(verify on your PC; menu names differ between Windows versions)**.
3. During weeks you trade, use **Pause updates** so Windows does not restart mid-session, and
   install updates in the weekend gap (after Friday's close, before Sunday's open), with no position
   open.
4. After installing updates and restarting: run `uv run goldbot doctor`, check the clock (§7.1
   step 2) and the Guardian folder ACL (§5.3) before the next session.
5. Turn on "Notify me when a restart is required" **(verify on your PC)**, and check for a pending
   restart in the daily checks (§8 #15).
6. Never apply an update while a position is open.

## 16. Power and sleep settings for trading sessions

The computer must stay awake while GoldBot runs (SYSTEM_ARCHITECTURE §7). The screen may turn off.

1. **Settings → System → Power** (or **Power & battery**) → **Screen and sleep**: set "When plugged
   in, put my device to sleep after" to **Never** **(verify on your PC)**.
2. Or, in Command Prompt: `powercfg /change standby-timeout-ac 0` and
   `powercfg /change hibernate-timeout-ac 0`. If it reports access denied, use the Settings app.
3. Laptop: **Control Panel → Power Options → Choose what closing the lid does**: "When plugged in:
   Do nothing" **(verify on your PC)**. Keep it plugged in during sessions.
4. Network adapter: in **Device Manager**, on your network adapter's **Power Management** tab, untick
   "Allow the computer to turn off this device to save power" **(verify on your PC)**.
5. A UPS (battery backup) helps with short power cuts. It is optional; without power nothing can act.
6. Test once: leave the computer idle for longer than your old sleep time with MT5 running, then
   check that the Guardian heartbeat kept updating.

## 17. Backup and restore test (PRV-030/031)

Available from M8. Backups cover the SQLite databases and config, **never** keyring contents.

### 17.1 Daily backup (automatic)

1. Runs daily and is encrypted. Keys: one per monthly generation, stored in the keyring.
2. Keeps 30 daily and 12 monthly generations.
3. When a new monthly key is created, make the **offline recovery copy** the spec requires: printed
   on paper or on a separate offline device. Keep it physically safe. Never store it in
   `C:\GoldBot`, Git, cloud notes or a photo.
4. A failed backup raises an alert (OBS-021); see §8 #13.

### 17.2 Monthly restore test

1. Run `<restore-test command, from M8>` (the spec calls it automated; M8 names the command).
2. It restores the latest backup to a temporary folder, verifies the audit chain, opens the
   database and compares row counts.
3. Pass: the System screen records the date. M10 needs a passed test within the last 30 days.
4. Fail: an alert is raised. Do not trade on LIVE until a test passes; ask in the next session.

### 17.3 Real restore (after a disk failure or a damaged database)

1. Make sure no position is open (MT5 **Trade** tab). If one is, close it first (§10).
2. Stop the API and the engine.
3. Restore the database and config files with the restore command from M8, using the key for that
   generation (from the keyring, or your offline recovery copy).
4. Re-enter secrets into the keyring if this is a new Windows install (§4.2); backups never contain
   them. A lost `local_salt` version is accepted: GoldBot creates a new one (PRV-012).
5. Redo the Guardian folder ACL (§5) on a new install.
6. Start in order (§7.1). The engine reconciles with the broker and rebuilds limit state from deal
   history (TIME-056); it starts in ENTRY_STOP.

## 18. Recovery after a trigger (RISK-050..053)

| Recovery class | Triggers (examples) | What happens |
| --- | --- | --- |
| `AUTO` | T5, T9, T11, T12, T13, T27 | Resumes by itself after the cooldown with every health check passing, at most 3 times per trigger per UTC day (P-34). |
| `ACK` | T2 (daily loss) | Not before the next UTC day; then one acknowledgement with TOTP plus all checks. |
| `MANUAL` | T1, T3, T4, T6, T7, T8, T10, T14..T26 | Full manual recovery. |

Automatic recovery is never allowed while any of these is unresolved: T7/T8, T16, T19, T20, T21,
T22, T23, T24, T25 (RISK-053).

### 18.1 Manual recovery approval (RISK-050)

1. Read the cause in the dashboard and acknowledge it.
2. Fix it. For T24, rotate secrets first (§4.4). For T16, restart with a valid config. For T18 and
   other Guardian latches, re-arm the Guardian (§12).
3. Check that health checks HC-1..HC-10 all pass: terminal connected and trading allowed; tick fresh;
   reconciliation clean; Guardian HEALTHY with kill flag clear; clock within P-16; spec hash
   unchanged; config valid; audit chain verifies; every open position has a broker-confirmed SL; no
   emergency action in progress or unresolved.
4. Type the confirmation phrase and your TOTP.
5. The state becomes ACTIVE with **automatic entry permission paused**: entries need your approval
   until you re-confirm the configured mode (`AUTO_ALL`, D-01).

## 19. Alert banner → runbook section

| Banner or state | Section |
| --- | --- |
| Disconnected (terminal or broker) | §14 |
| UNRECONCILED, T7, T8 | §8 #7, §18 |
| SUSPENDED (any cause) | §18 |
| UNRESOLVED EXPOSURE, T26 | §11 |
| Emergency in progress, emergency failed (T19) | §9, §10 |
| Guardian unknown or stale (T9) | §6, §14 |
| Guardian integrity or ACL failure (T22) | §5.4, §4.4 |
| Guardian re-arm required, takeover (T18) | §12 |
| "Guardian inputs looser than policy" (GRD-013) | §6 |
| Clock warning, T11 | §7.1 step 2, §14 |
| Session calendar UNKNOWN, T27 | §13 |
| Suspected credential compromise (T24) | §4.4 |
| Backup or restore-test failure | §17 |
