"""Pydantic v2 record models mirroring schemas/*.schema.json (DATA-010, DATA-011).

``REGISTRY`` maps each model to its schema file; tests/unit/test_schema_sync.py keeps them in sync.
TypeScript types join the sync check in M4.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    model_serializer,
)

SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "schemas"

Env = Literal["LIVE", "DEMO", "BACKTEST", "REPLAY"]
EntryAuthorizationMode = Literal["MANUAL_APPROVAL", "AUTO_ALL", "AUTO_APPROVED_STRATEGIES"]
HealthState = Literal["HEALTHY", "DEGRADED", "UNHEALTHY", "FAILED", "UNKNOWN"]
SchemaVersion = Literal["1.0.0"]
ParamsLabel = Literal["FIXTURE"]


def _real_utc(value: str) -> str:
    datetime.fromisoformat(value)  # the pattern fixes the shape; this rejects e.g. month 13
    return value


UtcTimestamp = Annotated[
    str,
    Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}Z$"),
    AfterValidator(_real_utc),
]
Sha256Hex = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Actor = Annotated[str, Field(min_length=1, max_length=128, pattern=r"^[^\x00-\x1F\x7F]*$")]
EventType = Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9_]{0,63}$")]
NonNegInt = Annotated[int, Field(ge=0)]


class Record(BaseModel):
    """Strict, closed record. Optional fields that are unset are omitted on dump, as the schemas
    define them as absent (not null); required nullable fields are kept as null."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    @model_serializer(mode="wrap")
    def _omit_absent(self, handler: SerializerFunctionWrapHandler) -> dict[str, Any]:
        data: dict[str, Any] = handler(self)
        fields = type(self).model_fields
        return {k: v for k, v in data.items() if v is not None or fields[k].is_required()}


class AuditEvent(Record):
    """schemas/audit_event.schema.json (SEC-022 hash chain)."""

    schema_version: SchemaVersion
    env: Env
    params: ParamsLabel | None = None
    fixture_demo_mode: EntryAuthorizationMode | None = None
    mono_seq: NonNegInt | None = None
    seq: NonNegInt
    ts: UtcTimestamp
    actor: Actor
    event: EventType
    payload_hash: Sha256Hex
    prev_hash: Sha256Hex | None
    hash: Sha256Hex


class ComponentHealth(Record):
    component: Literal[
        "MT5_TERMINAL",
        "BROKER_CONNECTION",
        "MARKET_DATA",
        "GUARDIAN",
        "CLOCK",
        "RECONCILIATION",
        "STOP_LOSS_PROTECTION",
        "SESSION_END_READINESS",
        "RISK_ENGINE",
        "INTELLIGENCE_MODULES",
        "EXECUTION",
        "API_WEB",
        "MCP",
    ]
    state: HealthState
    reason: Annotated[str, Field(max_length=256)] | None
    since: UtcTimestamp


class HealthStatus(Record):
    """schemas/health_status.schema.json (OBSERVABILITY_SPEC §3)."""

    schema_version: SchemaVersion
    env: Env
    params: ParamsLabel | None = None
    fixture_demo_mode: EntryAuthorizationMode | None = None
    mono_seq: NonNegInt | None = None
    ts: UtcTimestamp
    aggregate: HealthState
    components: Annotated[list[ComponentHealth], Field(min_length=1)]


REGISTRY: dict[type[Record], str] = {
    AuditEvent: "audit_event.schema.json",
    HealthStatus: "health_status.schema.json",
}
