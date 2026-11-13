"""Phase-0 guard and LIVE start gate (EXE-070, CLAUDE.md §3.17, RISK-005, M10 GO)."""

import copy
from pathlib import Path

import pytest

from goldbot import config, phase0
from goldbot.config import AppConfig, RiskLimits, StartupRefused

REPO = Path(__file__).resolve().parents[2]


def _file(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "PHASE0_CLEARANCE.md"
    path.write_bytes(text.encode("utf-8"))
    return path


def test_repo_clearance_file_is_not_cleared():
    text = (REPO / "docs" / "PHASE0_CLEARANCE.md").read_text(encoding="utf-8")
    assert "STATUS: CLEARED" in text  # the body mentions it; only the last line counts
    assert phase0.phase0_cleared(REPO / "docs" / "PHASE0_CLEARANCE.md") is False


def test_cleared_text_in_body_but_not_last_line_is_not_cleared(tmp_path):
    assert not phase0.phase0_cleared(_file(tmp_path, "STATUS: CLEARED\nbody\nSTATUS: NOT CLEARED\n"))


@pytest.mark.parametrize(
    "text",
    [
        "Checklist\n\nSTATUS: CLEARED",
        "Checklist\r\nSTATUS: CLEARED   \r\n",
        "Checklist\nSTATUS: CLEARED\n\n   \n\t\n",
        "﻿STATUS: CLEARED\n",
    ],
)
def test_last_non_empty_line_cleared(tmp_path, text):
    assert phase0.phase0_cleared(_file(tmp_path, text))


@pytest.mark.parametrize(
    "text",
    ["", "\n\n", "STATUS: CLEARED.\n", "status: cleared\n", "STATUS: CLEARED now\n", "STATUS:  CLEARED\n"],
)
def test_not_exactly_cleared(tmp_path, text):
    assert not phase0.phase0_cleared(_file(tmp_path, text))


def test_missing_file_is_not_cleared(tmp_path):
    assert not phase0.phase0_cleared(tmp_path / "missing.md")


def _app(env: str) -> AppConfig:
    app = config.load_app_config(REPO / "config" / "app.example.yaml")
    data = copy.deepcopy(app.data)
    data["env"] = env
    return AppConfig(path=app.path, sha256=app.sha256, data=data, root=app.root)


def _risk(unapprove: str | None = None) -> RiskLimits:
    risk = config.load_risk_limits(REPO / "config" / "risk_limits.yaml")
    data = copy.deepcopy(risk.data)
    for p in data["params"]:
        if p["id"] == unapprove:
            p["approved_by_user"], p["approved_on"] = False, None
    return RiskLimits(path=risk.path, sha256=risk.sha256, data=data)


def test_live_without_clearance_refused(tmp_path):
    with pytest.raises(StartupRefused, match="Phase-0"):
        phase0.assert_can_start(_app("LIVE"), _risk(), _file(tmp_path, "STATUS: NOT CLEARED\n"))


def test_live_cleared_and_approved_still_refused_without_go_verdict(tmp_path):
    reasons = phase0.startup_refusals(_app("LIVE"), _risk(), _file(tmp_path, "STATUS: CLEARED\n"))
    assert reasons == ["release readiness GO missing (M10)"]


def test_live_reports_every_missing_gate(tmp_path):
    reasons = phase0.startup_refusals(_app("LIVE"), _risk("P-01"), _file(tmp_path, "STATUS: NOT CLEARED\n"))
    assert len(reasons) == 3
    assert any("P-01" in r for r in reasons)


def test_demo_does_not_need_phase0(tmp_path):
    phase0.assert_can_start(_app("DEMO"), _risk(), _file(tmp_path, "STATUS: NOT CLEARED\n"))


def test_demo_still_applies_risk_005(tmp_path):
    with pytest.raises(StartupRefused, match="P-01"):
        phase0.assert_can_start(_app("DEMO"), _risk("P-01"), _file(tmp_path, "STATUS: CLEARED\n"))
