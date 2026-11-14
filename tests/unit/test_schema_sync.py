"""DATA-011: Pydantic record models stay in sync with schemas/*.schema.json (DATA-010 schema_version).

Checked per REGISTRY entry: property sets, required sets, enum/const values (recursively into nested
models), a model-dumped instance validates against the schema, and a schema-valid sample parses.
TypeScript types join this check in M4.
"""

import json
import types
import typing
from pathlib import Path
from typing import Any, Literal

import pytest
from jsonschema import Draft202012Validator
from pydantic import BaseModel, ValidationError
from referencing import Registry, Resource

from goldbot.models import REGISTRY, SCHEMAS_DIR, AuditEvent, ComponentHealth, HealthStatus, Record

TS = "2026-11-14T08:00:00.123Z"
H = "a" * 64


def _registry() -> Registry:
    resources = []
    for path in SCHEMAS_DIR.glob("*.schema.json"):
        contents = json.loads(path.read_text(encoding="utf-8"))
        resources.append((contents["$id"], Resource.from_contents(contents)))
    return Registry().with_resources(resources)


def _literals(annotation: Any) -> set[Any] | None:
    if typing.get_origin(annotation) is typing.Annotated:
        return _literals(typing.get_args(annotation)[0])
    if typing.get_origin(annotation) is Literal:
        return set(typing.get_args(annotation))
    if typing.get_origin(annotation) in (typing.Union, types.UnionType):
        found = [v for a in typing.get_args(annotation) if (v := _literals(a)) is not None]
        return set().union(*found) if found else None
    return None


def _nested_model(annotation: Any) -> type[BaseModel] | None:
    for arg in (annotation, *typing.get_args(annotation)):
        if isinstance(arg, type) and issubclass(arg, BaseModel):
            return arg
    return None


def _resolve(schema: dict[str, Any], resolver: Any) -> tuple[dict[str, Any], Any]:
    while "$ref" in schema:
        resolved = resolver.lookup(schema["$ref"])
        schema, resolver = resolved.contents, resolved.resolver
    return schema, resolver


def _values(schema: dict[str, Any], resolver: Any) -> set[Any] | None:
    schema, resolver = _resolve(schema, resolver)
    if "enum" in schema:
        return set(schema["enum"])
    if "const" in schema:
        return {schema["const"]}
    found = [v for sub in schema.get("anyOf", []) if (v := _values(sub, resolver)) is not None]
    return set().union(*found) if found else None


def sync_problems(model: type[BaseModel], schema: dict[str, Any], resolver: Any) -> list[str]:
    schema, resolver = _resolve(schema, resolver)
    name = model.__name__
    problems: list[str] = []
    props: dict[str, Any] = schema.get("properties", {})
    if set(model.model_fields) != set(props):
        problems.append(f"{name}: properties differ {sorted(set(model.model_fields) ^ set(props))}")
    required = {k for k, f in model.model_fields.items() if f.is_required()}
    if required != set(schema.get("required", [])):
        problems.append(f"{name}: required differ {sorted(required ^ set(schema.get('required', [])))}")
    if schema.get("additionalProperties") is not False or model.model_config.get("extra") != "forbid":
        problems.append(f"{name}: both must forbid extra properties")
    for field, info in model.model_fields.items():
        if field not in props:
            continue
        sub, sub_resolver = _resolve(props[field], resolver)
        if _literals(info.annotation) != _values(sub, sub_resolver):
            problems.append(f"{name}.{field}: enum/const values differ")
        nested = _nested_model(info.annotation)
        if nested is not None:
            item = sub.get("items", sub)
            problems += sync_problems(nested, item, sub_resolver)
    return problems


def check_entry(model: type[BaseModel], schema_file: str) -> list[str]:
    path = SCHEMAS_DIR / schema_file
    if not path.is_file():
        return [f"{model.__name__}: schema file {schema_file} not found"]
    schema = json.loads(path.read_text(encoding="utf-8"))
    resolver = _registry().resolver(base_uri=schema["$id"])
    return sync_problems(model, schema, resolver)


def _validator(schema_file: str) -> Draft202012Validator:
    schema = json.loads((SCHEMAS_DIR / schema_file).read_text(encoding="utf-8"))
    return Draft202012Validator(
        schema, registry=_registry(), format_checker=Draft202012Validator.FORMAT_CHECKER
    )


SAMPLES: dict[type[Record], dict[str, Any]] = {
    AuditEvent: {
        "schema_version": "1.0.0",
        "env": "DEMO",
        "seq": 0,
        "ts": TS,
        "actor": "engine",
        "event": "CONFIG_LOADED",
        "payload_hash": H,
        "prev_hash": None,
        "hash": "b" * 64,
    },
    HealthStatus: {
        "schema_version": "1.0.0",
        "env": "DEMO",
        "params": "FIXTURE",
        "fixture_demo_mode": "MANUAL_APPROVAL",
        "ts": TS,
        "aggregate": "UNKNOWN",
        "components": [{"component": "CLOCK", "state": "UNKNOWN", "reason": None, "since": TS}],
    },
}


def test_registry_covers_m1_records():
    assert {AuditEvent, HealthStatus} <= set(REGISTRY)
    assert set(SAMPLES) == set(REGISTRY)


@pytest.mark.parametrize(("model", "schema_file"), REGISTRY.items(), ids=lambda x: getattr(x, "__name__", x))
def test_model_matches_schema(model, schema_file):
    assert check_entry(model, schema_file) == []


@pytest.mark.parametrize(("model", "schema_file"), REGISTRY.items(), ids=lambda x: getattr(x, "__name__", x))
def test_schema_valid_sample_parses_and_round_trips(model, schema_file):
    sample = SAMPLES[model]
    _validator(schema_file).validate(sample)
    record = model.model_validate(sample)
    assert record.model_dump(mode="json") == sample
    _validator(schema_file).validate(record.model_dump(mode="json"))


def test_registry_entry_with_missing_schema_fails():
    assert check_entry(AuditEvent, "no_such.schema.json") == [
        "AuditEvent: schema file no_such.schema.json not found"
    ]


def test_sync_check_detects_a_drifted_model():
    class Drifted(Record):
        schema_version: Literal["1.0.0"]
        env: Literal["LIVE", "DEMO"]

    schema = json.loads((SCHEMAS_DIR / "audit_event.schema.json").read_text(encoding="utf-8"))
    problems = sync_problems(Drifted, schema, _registry().resolver(base_uri=schema["$id"]))
    assert any("properties differ" in p for p in problems)
    assert any("env: enum" in p for p in problems)


def test_absent_optional_fields_are_omitted_but_required_nulls_kept():
    dumped = AuditEvent.model_validate(SAMPLES[AuditEvent]).model_dump(mode="json")
    assert "params" not in dumped and "mono_seq" not in dumped
    assert dumped["prev_hash"] is None


@pytest.mark.parametrize(
    ("field", "bad"),
    [
        ("extra", 1),
        ("env", "PROD"),
        ("seq", 1.0),
        ("seq", "1"),
        ("seq", True),
        ("ts", "2026-11-14T08:00:00Z"),
        ("ts", "2026-13-14T08:00:00.000Z"),
        ("hash", "A" * 64),
        ("actor", "eng\nine"),
        ("params", "APPROVED"),
    ],
)
def test_audit_event_refuses_bad_values(field, bad):
    with pytest.raises(ValidationError):
        AuditEvent.model_validate({**SAMPLES[AuditEvent], field: bad})


def test_health_component_reason_is_required_even_when_null():
    component = dict(SAMPLES[HealthStatus]["components"][0])
    del component["reason"]
    with pytest.raises(ValidationError):
        ComponentHealth.model_validate(component)


def test_health_needs_at_least_one_component():
    with pytest.raises(ValidationError):
        HealthStatus.model_validate({**SAMPLES[HealthStatus], "components": []})


def test_every_registry_schema_has_schema_version():  # DATA-010
    for schema_file in REGISTRY.values():
        schema = json.loads((SCHEMAS_DIR / schema_file).read_text(encoding="utf-8"))
        assert "schema_version" in schema["required"]


def test_schemas_dir_is_repo_schemas():
    assert Path(__file__).resolve().parents[2] / "schemas" == SCHEMAS_DIR
