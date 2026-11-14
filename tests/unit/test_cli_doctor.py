"""`goldbot doctor`: configs + hashes (RISK-090), env/DB (DATA-005), Phase-0 (EXE-070), startup gate
(RISK-005/066), NTP vs P-16 (TIME-010), keyring backend (SEC-001), Guardian heartbeat (M7)."""

import shutil
from pathlib import Path

import keyring.backends.fail
import pytest

from goldbot import cli, envguard
from goldbot.core.ntp import NtpResult, OffsetCheck

REPO = Path(__file__).resolve().parents[2]


class _OkBackend:
    """A usable keyring backend that must never be asked for a secret."""

    priority = 5

    def get_password(self, *_):
        raise AssertionError("doctor must not read a secret")

    def get_credential(self, *_):
        raise AssertionError("doctor must not read a secret")


def _root(tmp_path: Path, app_edit: tuple[str, str] | None = None, app: bool = True) -> Path:
    (tmp_path / "config").mkdir()
    (tmp_path / "docs").mkdir()
    shutil.copy(REPO / "config" / "risk_limits.yaml", tmp_path / "config" / "risk_limits.yaml")
    shutil.copy(REPO / "docs" / "PHASE0_CLEARANCE.md", tmp_path / "docs" / "PHASE0_CLEARANCE.md")
    if app:
        text = (REPO / "config" / "app.example.yaml").read_text(encoding="utf-8")
        if app_edit:
            assert app_edit[0] in text
            text = text.replace(*app_edit, 1)
        (tmp_path / "config" / "app.yaml").write_bytes(text.encode("utf-8"))
    return tmp_path


def _run(root: Path, offline: bool = True, offsets=None, backend=_OkBackend, force_not_ok=False):
    calls: list[tuple[list[str], int]] = []

    def fake_check_offsets(servers, threshold_ms):
        calls.append((list(servers), threshold_ms))
        if isinstance(offsets, Exception):
            raise offsets
        results = tuple(NtpResult(s, o, 20) for s, o in zip(servers, offsets or [], strict=False))
        worst = max((r.offset_ms for r in results), key=abs, default=None)
        ok = len(results) >= 2 and worst is not None and abs(worst) <= threshold_ms and not force_not_ok
        return OffsetCheck(ok=ok, results=results, errors=(("x.example", "timeout"),), worst_offset_ms=worst)

    checks = cli.run_doctor(root, offline=offline, check_offsets=fake_check_offsets, keyring_backend=backend)
    return {c.name: c for c in checks}, calls


def test_offline_doctor_on_valid_root_passes_with_skips(tmp_path):
    checks, calls = _run(_root(tmp_path))
    assert not [c for c in checks.values() if c.status == "FAIL"]
    assert checks["NTP clock"].status == "SKIPPED"
    assert calls == []
    assert checks["Guardian heartbeat"].status == "SKIPPED"
    assert "NOT AVAILABLE (M7)" in checks["Guardian heartbeat"].detail
    assert checks["keyring"].status == "PASS"


def test_config_hashes_are_reported(tmp_path):
    import hashlib

    root = _root(tmp_path)
    checks, _ = _run(root)
    for name in ("risk_limits.yaml", "app.yaml"):
        digest = hashlib.sha256((root / "config" / name).read_bytes()).hexdigest()
        assert checks[name].status == "PASS"
        assert digest in checks[name].detail


def test_missing_app_yaml_fails_and_is_not_created(tmp_path):
    root = _root(tmp_path, app=False)
    checks, _ = _run(root)
    assert checks["app.yaml"].status == "FAIL"
    assert "app.example.yaml" in checks["app.yaml"].detail
    assert not (root / "config" / "app.yaml").exists()


def test_invalid_risk_limits_fails(tmp_path):
    root = _root(tmp_path)
    path = root / "config" / "risk_limits.yaml"
    path.write_bytes(path.read_bytes().replace(b"value: '0.25'", b"value: 0.25", 1))
    checks, _ = _run(root)
    assert checks["risk_limits.yaml"].status == "FAIL"


def test_session_exceptions_optional_but_validated_when_present(tmp_path):
    root = _root(tmp_path)
    checks, _ = _run(root)
    assert checks["session_exceptions.yaml"].status == "INFO"
    (root / "config" / "session_exceptions.yaml").write_text("schema_version: '1.0.0'\nexceptions: 3\n")
    checks, _ = _run(root)
    assert checks["session_exceptions.yaml"].status == "FAIL"


def test_env_db_mismatch_fails(tmp_path):
    root = _root(tmp_path)
    envguard.open_db("LIVE", root / "data" / "goldbot_demo.sqlite").close()
    checks, _ = _run(root)
    assert checks["env/DB"].status == "FAIL"
    assert "LIVE" in checks["env/DB"].detail


def test_shared_db_path_fails(tmp_path):
    root = _root(tmp_path, ("DEMO: data/goldbot_demo.sqlite", "DEMO: data/goldbot_live.sqlite"))
    checks, _ = _run(root)
    assert checks["env/DB"].status == "FAIL"


def test_phase0_is_informational_outside_live(tmp_path):
    checks, _ = _run(_root(tmp_path))
    assert checks["Phase-0"].status == "INFO"
    assert "NOT CLEARED" in checks["Phase-0"].detail


def test_live_fails_startup_gate_with_phase0_and_go(tmp_path):
    checks, _ = _run(_root(tmp_path, ("env: DEMO", "env: LIVE")))
    gate = checks["startup gate"]
    assert gate.status == "FAIL"
    assert "Phase-0" in gate.detail
    assert "release readiness GO missing (M10)" in gate.detail
    assert checks["Phase-0"].status == "FAIL"


def test_fixture_demo_with_live_fails_startup_gate(tmp_path):
    root = _root(tmp_path, ("env: DEMO", "env: LIVE"))
    path = root / "config" / "app.yaml"
    path.write_bytes(path.read_bytes().replace(b"fixture_demo: false", b"fixture_demo: true", 1))
    checks, _ = _run(root)
    assert "RISK-066" in checks["startup gate"].detail


def test_ntp_uses_configured_servers_and_p16_entry_stop_threshold(tmp_path):
    checks, calls = _run(_root(tmp_path), offline=False, offsets=[12, -30])
    assert calls == [(["time.google.com", "time.cloudflare.com"], 1000)]
    assert checks["NTP clock"].status == "PASS"


@pytest.mark.parametrize(
    ("offsets", "status"),
    [([499, -499], "PASS"), ([501, 0], "WARN"), ([0, -1001], "FAIL"), ([5], "FAIL"), ([], "FAIL")],
)
def test_ntp_offsets_against_p16(tmp_path, offsets, status):
    checks, _ = _run(_root(tmp_path), offline=False, offsets=offsets)
    assert checks["NTP clock"].status == status


def test_ntp_check_not_ok_fails_even_if_offsets_look_fine(tmp_path):
    checks, _ = _run(_root(tmp_path), offline=False, offsets=[0, 0], force_not_ok=True)
    assert checks["NTP clock"].status == "FAIL"


def test_ntp_error_fails_closed(tmp_path):
    checks, _ = _run(_root(tmp_path), offline=False, offsets=OSError("unreachable"))
    assert checks["NTP clock"].status == "FAIL"


def test_fewer_than_two_ntp_servers_fails_without_querying(tmp_path):
    root = _root(tmp_path, ("    - time.cloudflare.com\n", ""))
    checks, calls = _run(root, offline=False, offsets=[0])
    assert checks["NTP clock"].status == "FAIL"
    assert calls == []


def test_unusable_keyring_backend_fails(tmp_path):
    checks, _ = _run(_root(tmp_path), backend=keyring.backends.fail.Keyring)
    assert checks["keyring"].status == "FAIL"


def test_main_prints_checklist_and_exit_code(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "REPO_ROOT", _root(tmp_path))
    monkeypatch.setattr(cli, "_default_keyring_backend", _OkBackend)
    assert cli.main(["doctor", "--offline"]) == 0
    out = capsys.readouterr().out
    assert "[SKIPPED] NTP clock" in out
    assert "[PASS] risk_limits.yaml" in out


def test_main_exit_code_non_zero_on_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "REPO_ROOT", _root(tmp_path, app=False))
    monkeypatch.setattr(cli, "_default_keyring_backend", _OkBackend)
    assert cli.main(["doctor", "--offline"]) == 1
    assert "[FAIL] app.yaml" in capsys.readouterr().out


def test_main_requires_a_subcommand():
    with pytest.raises(SystemExit):
        cli.main([])
