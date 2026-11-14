"""Phase-0 guard and the LIVE start gate (EXE-070, CLAUDE.md §3.17, RISK-005, M10 GO)."""

from __future__ import annotations

from pathlib import Path

from goldbot.config import REPO_ROOT, AppConfig, RiskLimits, StartupRefused, gate_refusals

CLEARANCE_FILE = REPO_ROOT / "docs" / "PHASE0_CLEARANCE.md"
CLEARED = "STATUS: CLEARED"


def phase0_cleared(path: Path = CLEARANCE_FILE) -> bool:
    """True only if the last non-empty line is exactly ``STATUS: CLEARED`` (trailing space ignored)."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return False
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    return bool(lines) and lines[-1] == CLEARED


def startup_refusals(app: AppConfig, risk: RiskLimits, clearance: Path = CLEARANCE_FILE) -> list[str]:
    reasons = gate_refusals(app, risk)
    if app.env == "LIVE":
        if not phase0_cleared(clearance):
            reasons.append(f"Phase-0 not cleared: last non-empty line of {clearance.name} is not '{CLEARED}'")
        # shortcut: no M10 release-readiness artifact exists yet, so LIVE always refuses; M10 adds the check.
        reasons.append("release readiness GO missing (M10)")
    return reasons


def assert_can_start(app: AppConfig, risk: RiskLimits, clearance: Path = CLEARANCE_FILE) -> None:
    reasons = startup_refusals(app, risk, clearance)
    if reasons:
        raise StartupRefused("; ".join(reasons))
