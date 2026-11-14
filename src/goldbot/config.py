"""Config loading: schema validation, exact-bytes SHA-256 and the startup gate.

RISK-090 (validate + hash + audit), RISK-005 (pending-parameter gate), RISK-065/066 (fixture demo),
RISK-092 (approval record), RISK-020 (no floats: YAML numbers become Decimal, never float).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

import yaml
from jsonschema import Draft202012Validator

from goldbot.core.convert import parse_decimal

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "config" / "schema"
ENVS = ("LIVE", "DEMO", "BACKTEST", "REPLAY")


class ConfigError(Exception):
    """A config file is missing, malformed, invalid, or a setting is not approved."""


class StartupRefused(Exception):
    """The engine must not start (RISK-005, RISK-066, EXE-070 Phase-0 guard)."""


@dataclass(frozen=True)
class ConfigFile:
    path: Path
    sha256: str
    data: dict[str, Any]


class RiskLimits(ConfigFile):
    """config/risk_limits.yaml. Settings come from ``params`` only; ``fixtures`` are never read."""


@dataclass(frozen=True)
class AppConfig(ConfigFile):
    root: Path = field(default=REPO_ROOT)

    @property
    def env(self) -> str:
        return self.data["env"]

    @property
    def fixture_demo(self) -> bool:
        return self.data["fixture_demo"]

    @property
    def db_paths(self) -> dict[str, Path]:
        return {env: self.root / p for env, p in self.data["paths"]["databases"].items()}

    @property
    def ntp_servers(self) -> list[str]:
        return list(self.data["ntp"]["servers"])


class AuditSink(Protocol):
    def append(self, event_type: str, actor: str, payload: dict[str, Any]) -> Any: ...


# ---- decimals --------------------------------------------------------------------------------


def as_decimal(raw: object) -> Decimal:
    """Plain decimal string or int -> Decimal. Floats, exponents, spaces and other types refused."""
    if isinstance(raw, int) and not isinstance(raw, bool):
        raw = str(raw)
    try:
        return parse_decimal(raw, "config value")
    except (TypeError, ValueError, ArithmeticError):
        # The parser's message may echo the text; keep values out of errors and logs.
        raise ConfigError("not a plain decimal string or int (RISK-020, DATA-004)") from None


# ---- YAML ------------------------------------------------------------------------------------


class _Loader(yaml.SafeLoader):
    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        seen: set[Any] = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=True)  # type: ignore[no-untyped-call]
            try:
                duplicate = key in seen
            except TypeError:  # unhashable (complex) key
                raise ConfigError(f"unsupported complex key at line {key_node.start_mark.line + 1}") from None
            if duplicate:
                raise ConfigError(f"duplicate key {key!r} at line {key_node.start_mark.line + 1}")
            seen.add(key)
        return super().construct_mapping(node, deep)


def _yaml_float(loader: _Loader, node: yaml.ScalarNode) -> Decimal:
    text = str(loader.construct_scalar(node)).replace("_", "")
    try:
        return as_decimal(text)
    except ConfigError as exc:
        raise ConfigError(f"unsupported number at line {node.start_mark.line + 1}: {exc}") from None


_Loader.add_constructor("tag:yaml.org,2002:float", _yaml_float)


def parse_yaml(raw: bytes) -> Any:
    """YAML -> Python. Non-integer numbers become Decimal (never float); duplicate keys refused."""
    try:
        return yaml.load(raw, Loader=_Loader)  # noqa: S506 - _Loader is a SafeLoader subclass
    except yaml.YAMLError as exc:
        mark = getattr(exc, "problem_mark", None)
        where = f" at line {mark.line + 1}" if mark is not None else ""
        # The message is kept short on purpose: a YAML excerpt could echo a mistyped secret.
        raise ConfigError(f"malformed YAML{where}") from None


# ---- loading ---------------------------------------------------------------------------------


def _validator(schema_name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


def _describe(error: Any) -> str:
    where = "/".join(str(p) for p in error.absolute_path) or "<root>"
    # Only these messages name keys, never values (a value could be a mistyped secret).
    if error.validator in ("required", "additionalProperties"):
        return f"{where}: {error.message}"
    return f"{where}: fails '{error.validator}'"


def _load(path: Path, schema_name: str) -> tuple[str, dict[str, Any]]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        raise ConfigError(f"{path}: not found") from None
    except OSError as exc:
        raise ConfigError(f"{path}: cannot read ({exc.strerror})") from None
    try:
        data = parse_yaml(raw)
    except ConfigError as exc:
        raise ConfigError(f"{path}: {exc}") from None
    errors = sorted(_validator(schema_name).iter_errors(data), key=lambda e: list(map(str, e.absolute_path)))
    if errors:
        raise ConfigError(f"{path}: invalid: " + "; ".join(_describe(e) for e in errors))
    return hashlib.sha256(raw).hexdigest(), data


def load_risk_limits(path: Path) -> RiskLimits:
    sha256, data = _load(path, "risk_limits.schema.json")
    return RiskLimits(path=path, sha256=sha256, data=data)


def load_app_config(path: Path, root: Path = REPO_ROOT) -> AppConfig:
    sha256, data = _load(path, "app.schema.json")
    mt5 = data.get("mt5") or {}
    engine, guardian = mt5.get("magic_engine"), mt5.get("magic_guardian")
    if engine is not None and engine == guardian:  # EXE-022/EXP-009; JSON Schema cannot express this
        raise ConfigError(f"{path}: invalid: mt5.magic_engine and mt5.magic_guardian must differ")
    return AppConfig(path=path, sha256=sha256, data=data, root=root)


def load_session_exceptions(path: Path) -> ConfigFile:
    sha256, data = _load(path, "session_exceptions.schema.json")
    return ConfigFile(path=path, sha256=sha256, data=data)


def record_config_hashes(audit: AuditSink, *files: ConfigFile) -> None:
    """RISK-090: the hash of every loaded config file goes to the audit log."""
    audit.append("CONFIG_LOADED", "engine", {f.path.name: f.sha256 for f in files})


# ---- approvals and the startup gate ----------------------------------------------------------


def _approved(param: dict[str, Any]) -> bool:
    return param.get("approved_by_user") is True and bool(param.get("approved_on"))


def unapproved_decisions(risk: RiskLimits) -> list[str]:
    """USER_DECISION_REQUIRED parameters without approved_by_user: true and a date (RISK-005)."""
    return [
        p["id"] for p in risk.data["params"] if p["status"] == "USER_DECISION_REQUIRED" and not _approved(p)
    ]


def gate_refusals(app: AppConfig, risk: RiskLimits) -> list[str]:
    """Reasons the engine must refuse to start under RISK-005/065/066. Empty list = no refusal."""
    reasons: list[str] = []
    fixture_demo, mode = app.data["fixture_demo"], app.data["fixture_demo_mode"]
    if fixture_demo and app.env == "LIVE":
        reasons.append("fixture_demo: true with env LIVE is refused (RISK-066)")
    if fixture_demo and mode is None:
        reasons.append("fixture demo needs fixture_demo_mode set by the user for this run (RISK-066)")
    if not fixture_demo and mode is not None:
        reasons.append("fixture_demo_mode is set outside fixture demo; it is never a default (RISK-065)")
    if app.env == "LIVE" or (app.env == "DEMO" and not fixture_demo):
        reasons += [
            f"{pid} is USER_DECISION_REQUIRED and not approved with a date (RISK-005)"
            for pid in unapproved_decisions(risk)
        ]
    return reasons


def setting(risk: RiskLimits, param_id: str) -> Any:
    """The approved value of a parameter. Never a fixture or recommendation (RISK-005, RISK-092)."""
    param = next((p for p in risk.data["params"] if p["id"] == param_id), None)
    if param is None:
        raise ConfigError(f"{param_id}: no such parameter")
    if not _approved(param):
        raise ConfigError(f"{param_id}: not approved by the user; no value is available (RISK-005)")
    if param["value"] is None:
        raise ConfigError(f"{param_id}: has no value")
    return param["value"]
