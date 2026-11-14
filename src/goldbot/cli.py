"""`goldbot` command line. M1: `goldbot doctor` (RUNBOOK §3 steps 6 and 14)."""

from __future__ import annotations

import argparse
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import keyring
import keyring.backends.fail
import keyring.backends.null

from goldbot import config, envguard, phase0
from goldbot.config import REPO_ROOT, AppConfig, ConfigError, RiskLimits
from goldbot.core.ntp import OffsetCheck, check_offsets

_default_keyring_backend: Callable[[], Any] = keyring.get_keyring
_UNUSABLE_KEYRINGS = (keyring.backends.fail.Keyring, keyring.backends.null.Keyring)
CheckOffsets = Callable[[list[str], int], OffsetCheck]


@dataclass(frozen=True)
class Check:
    name: str
    status: str  # PASS | FAIL | WARN | SKIPPED | INFO; only FAIL makes the exit code non-zero
    detail: str

    def line(self) -> str:
        return f"[{self.status}] {self.name}: {self.detail}"


def _default_check_offsets(servers: list[str], threshold_ms: int) -> OffsetCheck:
    return check_offsets(servers, threshold_ms)


def _ntp(app: AppConfig, risk: RiskLimits | None, offline: bool, check_offsets: CheckOffsets) -> Check:
    name = "NTP clock"
    if offline:
        return Check(name, "SKIPPED", "--offline: not checked; this never counts as a pass (TIME-010)")
    servers = app.ntp_servers
    if len(servers) < 2:
        return Check(name, "FAIL", f"{len(servers)} NTP server(s) configured; TIME-010 needs at least 2")
    if risk is None:
        return Check(name, "FAIL", "P-16 thresholds unavailable: risk_limits.yaml is invalid")
    try:
        limits = config.setting(risk, "P-16")
        warn_ms, stop_ms = int(limits["warn_ms"]), int(limits["entry_stop_ms"])
        result = check_offsets(servers, stop_ms)
    except Exception as exc:  # fail closed on any NTP or config problem
        return Check(name, "FAIL", f"{type(exc).__name__}: {exc}")
    summary = ", ".join(
        [f"{r.server} {r.offset_ms} ms" for r in result.results]
        + [f"{s} error: {e}" for s, e in result.errors]
    )
    if len(result.results) < 2:
        return Check(name, "FAIL", f"{len(result.results)} servers answered; at least 2 needed: {summary}")
    worst = max(abs(r.offset_ms) for r in result.results)
    if not result.ok or worst > stop_ms:
        return Check(name, "FAIL", f"offset above P-16 entry-stop {stop_ms} ms: {summary}")
    if worst > warn_ms:
        return Check(name, "WARN", f"offset above P-16 warn {warn_ms} ms: {summary}")
    return Check(name, "PASS", summary)


def _env_db(app: AppConfig) -> Check:
    problems = envguard.db_path_problems(app.db_paths)
    states: list[str] = []
    for env, path in app.db_paths.items():
        try:
            found = envguard.recorded_env(path)
        except Exception as exc:  # unreadable or corrupt file
            problems.append(f"{env}: {path} cannot be read ({type(exc).__name__})")
            continue
        if path.exists() and found != env:
            problems.append(f"{env}: {path} has env header {found or 'none'} (DATA-005)")
        states.append(f"{env} {'ok' if found == env else 'not created yet'}")
    if problems:
        return Check("env/DB", "FAIL", "; ".join(problems))
    return Check("env/DB", "PASS", f"config env {app.env}; " + ", ".join(states))


def _keyring(backend_factory: Callable[[], Any]) -> Check:
    # Only the backend is inspected: no secret is read or printed (SEC-001).
    try:
        backend = backend_factory()
    except Exception as exc:
        return Check("keyring", "FAIL", f"no backend: {type(exc).__name__}")
    label = type(backend).__name__
    if isinstance(backend, _UNUSABLE_KEYRINGS):
        return Check("keyring", "FAIL", f"no usable keyring backend ({label})")
    return Check("keyring", "PASS", f"backend {type(backend).__module__}.{label}")


def run_doctor(
    root: Path,
    *,
    offline: bool = False,
    check_offsets: CheckOffsets = _default_check_offsets,
    keyring_backend: Callable[[], Any] | None = None,
) -> list[Check]:
    cfg = root / "config"
    checks: list[Check] = []

    risk: RiskLimits | None = None
    try:
        risk = config.load_risk_limits(cfg / "risk_limits.yaml")
        checks.append(Check("risk_limits.yaml", "PASS", f"valid, sha256 {risk.sha256}"))
    except ConfigError as exc:
        checks.append(Check("risk_limits.yaml", "FAIL", str(exc)))

    app: AppConfig | None = None
    if not (cfg / "app.yaml").exists():
        checks.append(
            Check("app.yaml", "FAIL", "config/app.yaml not found: create it from config/app.example.yaml")
        )
    else:
        try:
            app = config.load_app_config(cfg / "app.yaml", root=root)
            checks.append(Check("app.yaml", "PASS", f"valid, sha256 {app.sha256}"))
        except ConfigError as exc:
            checks.append(Check("app.yaml", "FAIL", str(exc)))

    sessions = cfg / "session_exceptions.yaml"
    if not sessions.exists():
        checks.append(Check("session_exceptions.yaml", "INFO", "not created yet (from the example; M2)"))
    else:
        try:
            loaded = config.load_session_exceptions(sessions)
            checks.append(Check("session_exceptions.yaml", "PASS", f"valid, sha256 {loaded.sha256}"))
        except ConfigError as exc:
            checks.append(Check("session_exceptions.yaml", "FAIL", str(exc)))

    clearance = root / "docs" / "PHASE0_CLEARANCE.md"
    cleared = phase0.phase0_cleared(clearance)
    if app is None or risk is None:
        needs = "needs valid app.yaml and risk_limits.yaml"
        checks += [Check("startup gate", "SKIPPED", needs), Check("env/DB", "SKIPPED", needs)]
        checks.append(Check("Phase-0", "INFO", "CLEARED" if cleared else "NOT CLEARED"))
        checks.append(
            Check("NTP clock", "SKIPPED", needs) if app is None else _ntp(app, risk, offline, check_offsets)
        )
    else:
        refusals = phase0.startup_refusals(app, risk, clearance)
        gate = (
            Check("startup gate", "FAIL", "; ".join(refusals))
            if refusals
            else Check("startup gate", "PASS", f"env {app.env}: no refusal (RISK-005/066)")
        )
        checks += [gate, _env_db(app)]
        if app.env == "LIVE":
            checks.append(
                Check("Phase-0", "PASS" if cleared else "FAIL", "CLEARED" if cleared else "NOT CLEARED")
            )
        else:
            checks.append(
                Check(
                    "Phase-0", "INFO", f"{'CLEARED' if cleared else 'NOT CLEARED'} (required for LIVE only)"
                )
            )
        checks.append(_ntp(app, risk, offline, check_offsets))

    checks.append(_keyring(keyring_backend or _default_keyring_backend))
    checks.append(Check("Guardian heartbeat", "SKIPPED", "NOT AVAILABLE (M7)"))
    return checks


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="goldbot")
    sub = parser.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor", help="check configs, env/DB, Phase-0, clock, keyring, Guardian")
    doctor.add_argument("--offline", action="store_true", help="skip NTP (reported SKIPPED, never PASS)")
    args = parser.parse_args(argv)

    checks = run_doctor(REPO_ROOT, offline=args.offline, keyring_backend=_default_keyring_backend)
    for check in checks:
        print(check.line())
    failed = [c.name for c in checks if c.status == "FAIL"]
    print(f"doctor: {len(failed)} required check(s) failed" + (f": {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0
