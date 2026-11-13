"""Config loader: schema validation, exact-bytes hashing, decimal safety, RISK-005/066 gate.

Requirements: RISK-090 (validate + hash), RISK-005 (pending-parameter gate, GV-33),
RISK-066 (fixture demo, GV-40), RISK-092 (approval record), RISK-020 (no floats), NB8.
"""

import copy
import hashlib
from decimal import Decimal
from pathlib import Path

import pytest

from goldbot import config
from goldbot.config import AppConfig, ConfigError, RiskLimits

REPO = Path(__file__).resolve().parents[2]
RISK = REPO / "config" / "risk_limits.yaml"
APP_EXAMPLE = REPO / "config" / "app.example.yaml"
SESSIONS_EXAMPLE = REPO / "config" / "session_exceptions.example.yaml"


def _write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_bytes(text.encode("utf-8"))
    return path


# ---- RISK-090: validation and hashing -------------------------------------------------------


def test_repo_risk_limits_valid_and_hash_is_sha256_of_exact_bytes():
    risk = config.load_risk_limits(RISK)
    assert risk.sha256 == hashlib.sha256(RISK.read_bytes()).hexdigest()


def test_hash_changes_when_any_byte_changes(tmp_path):
    original = config.load_risk_limits(RISK).sha256
    changed = _write(tmp_path, "r.yaml", RISK.read_text(encoding="utf-8") + "# edited\n")
    assert config.load_risk_limits(changed).sha256 != original


@pytest.mark.parametrize(
    ("loader", "path"),
    [
        (config.load_risk_limits, REPO / "config" / "risk_limits.example.yaml"),
        (config.load_app_config, APP_EXAMPLE),
        (config.load_session_exceptions, SESSIONS_EXAMPLE),
    ],
)
def test_example_files_validate(loader, path):
    loader(path)


def test_invalid_risk_limits_refused(tmp_path):
    text = RISK.read_text(encoding="utf-8").replace("profile_name: null\n", "")
    with pytest.raises(ConfigError, match="profile_name"):
        config.load_risk_limits(_write(tmp_path, "r.yaml", text))


def test_unquoted_decimal_is_refused_not_read_as_float(tmp_path):
    text = RISK.read_text(encoding="utf-8").replace("value: '0.25'", "value: 0.25", 1)
    with pytest.raises(ConfigError):
        config.load_risk_limits(_write(tmp_path, "r.yaml", text))


def test_yaml_numbers_never_become_floats():
    data = config.parse_yaml(b"a: 0.25\nb: 200\nc: '0.10'\n")
    assert data == {"a": Decimal("0.25"), "b": 200, "c": "0.10"}
    assert not any(isinstance(v, float) for v in data.values())


def test_duplicate_yaml_key_refused():
    with pytest.raises(ConfigError, match="duplicate"):
        config.parse_yaml(b"a: '1'\na: '2'\n")


def test_malformed_yaml_refused(tmp_path):
    with pytest.raises(ConfigError):
        config.load_app_config(_write(tmp_path, "app.yaml", "env: [DEMO\n"))


def test_missing_file_refused(tmp_path):
    with pytest.raises(ConfigError, match="not found"):
        config.load_app_config(tmp_path / "app.yaml")


# ---- NB8: app.yaml schema --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("old", "new"),
    [
        ("bind_host: 127.0.0.1", "bind_host: 0.0.0.0"),
        ("env: DEMO", "env: PROD"),
        ("fixture_demo: false", "fixture_demo: 'false'"),
        ("fixture_demo_mode: null", "fixture_demo_mode: SOMETIMES"),
        ("  enabled: false\n  provider: null", "  enabled: false\n  provider: null\n  api_key: x"),
    ],
)
def test_app_schema_refuses(tmp_path, old, new):
    text = APP_EXAMPLE.read_text(encoding="utf-8")
    assert old in text
    with pytest.raises(ConfigError):
        config.load_app_config(_write(tmp_path, "app.yaml", text.replace(old, new, 1)))


def test_app_config_exposes_env_and_db_paths(tmp_path):
    app = config.load_app_config(APP_EXAMPLE, root=tmp_path)
    assert app.env == "DEMO"
    assert app.fixture_demo is False
    assert app.db_paths["LIVE"] == tmp_path / "data" / "goldbot_live.sqlite"
    assert app.ntp_servers == ["time.google.com", "time.cloudflare.com"]
    assert app.sha256 == hashlib.sha256(APP_EXAMPLE.read_bytes()).hexdigest()


# ---- NB8: session_exceptions.yaml schema -----------------------------------------------------

_SESSION_HEAD = 'schema_version: "1.0.0"\nexceptions:\n  - date: "2026-12-24"\n    source: "Broker notice"\n'


@pytest.mark.parametrize(
    ("entry", "ok"),
    [
        ('    type: early_close\n    close_time_server: "18:00"\n', True),
        ("    type: early_close\n    close_time_server: null\n", False),
        ("    type: early_close\n", False),
        ("    type: full_close\n    close_time_server: null\n", True),
        ("    type: full_close\n", True),
        ('    type: full_close\n    close_time_server: "18:00"\n', False),
        ('    type: early_close\n    close_time_server: "25:00"\n', False),
        ("    type: half_day\n", False),
    ],
)
def test_session_exceptions_schema(tmp_path, entry, ok):
    path = _write(tmp_path, "s.yaml", _SESSION_HEAD + entry)
    if ok:
        config.load_session_exceptions(path)
    else:
        with pytest.raises(ConfigError):
            config.load_session_exceptions(path)


# ---- RISK-005 / RISK-066 startup gate ----------------------------------------------------------


def _app(env="DEMO", fixture_demo=False, mode=None) -> AppConfig:
    app = config.load_app_config(APP_EXAMPLE)
    data = copy.deepcopy(app.data)
    data.update(env=env, fixture_demo=fixture_demo, fixture_demo_mode=mode)
    return AppConfig(path=app.path, sha256=app.sha256, data=data, root=app.root)


def _risk(unapprove: str | None = None, drop_date: str | None = None) -> RiskLimits:
    risk = config.load_risk_limits(RISK)
    data = copy.deepcopy(risk.data)
    for p in data["params"]:
        if p["id"] == unapprove:
            p["approved_by_user"] = False
            p["approved_on"] = None
        if p["id"] == drop_date:
            p["approved_on"] = None
    return RiskLimits(path=risk.path, sha256=risk.sha256, data=data)


def test_repo_config_has_no_gate_refusals():
    assert config.gate_refusals(_app(), _risk()) == []


def test_gv33_demo_without_fixture_demo_refuses_unapproved_decision():
    reasons = config.gate_refusals(_app("DEMO"), _risk(unapprove="P-01"))
    assert any("P-01" in r and "RISK-005" in r for r in reasons)


def test_live_refuses_unapproved_decision():
    assert any("P-37" in r for r in config.gate_refusals(_app("LIVE"), _risk(unapprove="P-37")))


def test_approval_without_date_counts_as_unapproved():
    assert any("P-02" in r for r in config.gate_refusals(_app("DEMO"), _risk(drop_date="P-02")))


def test_broker_verification_param_is_not_a_user_decision():
    # P-14 is BROKER_VERIFICATION_REQUIRED and unapproved in the repo file; RISK-005 covers only
    # USER_DECISION_REQUIRED (its null value is refused at arming time, M7a / CH-104).
    assert config.unapproved_decisions(_risk()) == []


def test_fixture_demo_allows_unapproved_decision():
    assert config.gate_refusals(_app("DEMO", True, "MANUAL_APPROVAL"), _risk(unapprove="P-01")) == []


@pytest.mark.parametrize("env", ["BACKTEST", "REPLAY"])
def test_backtest_and_replay_may_run_on_fixtures(env):
    assert config.gate_refusals(_app(env), _risk(unapprove="P-01")) == []


def test_gv40_live_with_fixture_demo_refuses():
    reasons = config.gate_refusals(_app("LIVE", True, "MANUAL_APPROVAL"), _risk())
    assert any("RISK-066" in r for r in reasons)


def test_fixture_demo_without_run_mode_refuses():
    assert any("fixture_demo_mode" in r for r in config.gate_refusals(_app("DEMO", True), _risk()))


def test_fixture_demo_mode_outside_fixture_demo_refuses():
    reasons = config.gate_refusals(_app("DEMO", False, "AUTO_ALL"), _risk())
    assert any("fixture_demo_mode" in r for r in reasons)


# ---- Settings come from params only, never from fixtures (RISK-005) ---------------------------


def test_setting_reads_param_value_not_fixture():
    # P-37 value is AUTO_ALL; its fixture is MANUAL_APPROVAL.
    assert config.setting(_risk(), "P-37") == "AUTO_ALL"


def test_unapproved_decision_has_no_setting_and_no_fixture_fallback():
    with pytest.raises(ConfigError, match="P-01"):
        config.setting(_risk(unapprove="P-01"), "P-01")


def test_null_value_has_no_setting():
    with pytest.raises(ConfigError, match="P-14"):
        config.setting(_risk(), "P-14")


# ---- Decimal conversion: str -> Decimal, never float -----------------------------------------


@pytest.mark.parametrize(("raw", "expected"), [("0.25", Decimal("0.25")), (200, Decimal(200)), ("-1", Decimal(-1))])
def test_as_decimal(raw, expected):
    assert config.as_decimal(raw) == expected


@pytest.mark.parametrize("raw", [True, 0.25, "1e5", "abc", "", None, Decimal("0.25"), " 1"])
def test_as_decimal_refuses(raw):
    with pytest.raises(ConfigError):
        config.as_decimal(raw)


# ---- RISK-090: hashes go to the audit log ----------------------------------------------------


class _FakeAudit:
    def __init__(self):
        self.events: list[tuple[str, str, dict]] = []

    def append(self, event_type, actor, payload):
        self.events.append((event_type, actor, payload))


def test_config_hashes_are_written_to_audit_log():
    audit = _FakeAudit()
    risk, app = _risk(), _app()
    config.record_config_hashes(audit, risk, app)
    [(event, actor, payload)] = audit.events
    assert event == "CONFIG_LOADED"
    assert actor == "engine"
    assert payload == {"risk_limits.yaml": risk.sha256, "app.example.yaml": app.sha256}
