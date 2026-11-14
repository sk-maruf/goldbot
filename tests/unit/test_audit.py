"""SEC-022 audit log: append-only SHA-256 hash chain, canonical JSON, schema-valid records."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from goldbot import envguard
from goldbot.core.audit import GENESIS_PREV_HASH, AuditChainError, AuditLog, canonical_json
from goldbot.core.clock import FakeClock
from goldbot.envguard import EnvMismatchError

SCHEMAS = Path(__file__).resolve().parents[2] / "schemas"
START = datetime(2026, 11, 14, 8, 0, tzinfo=UTC)


def validator() -> Draft202012Validator:
    load = lambda name: json.loads((SCHEMAS / name).read_text(encoding="utf-8"))  # noqa: E731
    common = Resource.from_contents(load("common.schema.json"))
    registry = Registry().with_resource(common.id() or "", common)
    return Draft202012Validator(load("audit_event.schema.json"), registry=registry)


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock(START)


@pytest.fixture
def log(tmp_path: Path, clock: FakeClock) -> Iterator[AuditLog]:
    with AuditLog(tmp_path / "audit.db", "DEMO", clock) as audit:
        yield audit


def test_sec_022_first_record_starts_the_chain_at_the_genesis_value(log: AuditLog) -> None:
    rec = log.append("ENGINE_STARTED", "engine", {"version": "0.1.0"})
    assert GENESIS_PREV_HASH is None  # audit_event.schema.json: prev_hash is null only for the first record
    assert rec["seq"] == 0
    assert rec["prev_hash"] is None
    assert rec["ts"] == "2026-11-14T08:00:00.000Z"
    assert rec["env"] == "DEMO"
    assert rec["payload_hash"] == hashlib.sha256(b'{"version":"0.1.0"}').hexdigest()


def test_sec_022_each_record_hashes_its_canonical_body_and_links_to_the_previous(
    log: AuditLog, clock: FakeClock
) -> None:
    first = log.append("A", "engine", {})
    clock.advance(5)
    second = log.append("B", "user", {"n": 1})
    assert second["seq"] == 1
    assert second["prev_hash"] == first["hash"]
    body = {k: v for k, v in second.items() if k != "hash"}
    assert second["hash"] == hashlib.sha256(canonical_json(body)).hexdigest()
    assert log.verify_chain() is True


def test_records_validate_against_the_audit_event_schema(log: AuditLog) -> None:
    v = validator()
    for i in range(3):
        v.validate(log.append(f"EVENT_{i}", "engine", {"i": i}))


def test_records_reads_back_what_was_appended(log: AuditLog) -> None:
    written = [log.append("A", "engine", {}), log.append("B", "engine", {"x": "y"})]
    assert log.records() == written


def test_empty_chain_verifies(log: AuditLog) -> None:
    assert log.verify_chain() is True


def test_chain_survives_reopen(tmp_path: Path, clock: FakeClock) -> None:
    path = tmp_path / "audit.db"
    with AuditLog(path, "DEMO", clock) as log:
        first = log.append("A", "engine", {})
    with AuditLog(path, "DEMO", clock) as reopened:
        second = reopened.append("B", "engine", {})
        assert (second["seq"], second["prev_hash"]) == (1, first["hash"])
        assert reopened.verify_chain() is True


def test_data_005_opening_a_log_of_another_env_is_refused(tmp_path: Path, clock: FakeClock) -> None:
    path = tmp_path / "audit.db"
    with AuditLog(path, "DEMO", clock) as log:
        log.append("A", "engine", {})
    with pytest.raises(EnvMismatchError, match="env"):
        AuditLog(path, "LIVE", clock)


def test_unknown_env_is_rejected(tmp_path: Path, clock: FakeClock) -> None:
    with pytest.raises(EnvMismatchError, match="env"):
        AuditLog(tmp_path / "a.db", "PROD", clock)


@pytest.mark.parametrize("event", ["lower", "", "A-B", "A" * 65])
def test_event_type_must_match_the_schema_pattern(log: AuditLog, event: str) -> None:
    with pytest.raises(ValueError, match="event"):
        log.append(event, "engine", {})


@pytest.mark.parametrize(
    "actor", ["", "a" * 129, "bad\nactor", "user alice", "password=hunter2", "x/y", "é", "a\tb"]
)
def test_actor_must_match_the_schema(log: AuditLog, actor: str) -> None:
    with pytest.raises(ValueError, match="actor"):
        log.append("A", actor, {})


def test_canonical_json_sorts_keys_compactly_and_keeps_unicode() -> None:
    assert canonical_json({"b": [1, None, True], "a": "é"}) == '{"a":"é","b":[1,null,true]}'.encode()


@pytest.mark.parametrize("bad", [1.5, {"x": 0.1}, [float("nan")], {"d": object()}, {1: "int key"}])
def test_canonical_json_rejects_floats_and_non_json_values(bad: object) -> None:
    with pytest.raises(TypeError):
        canonical_json(bad)


def test_float_payload_is_rejected_and_nothing_is_appended(log: AuditLog) -> None:
    with pytest.raises(TypeError, match="float"):
        log.append("A", "engine", {"volume": 0.01})
    assert log.records() == []


def test_sec_022_update_and_delete_are_refused_by_the_store(tmp_path: Path, clock: FakeClock) -> None:
    path = tmp_path / "audit.db"
    with AuditLog(path, "DEMO", clock) as log:
        log.append("A", "engine", {})
    con = sqlite3.connect(path)
    try:
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            con.execute("UPDATE audit_log SET actor = 'x'")
        with pytest.raises(sqlite3.DatabaseError, match="append-only"):
            con.execute("DELETE FROM audit_log")
    finally:
        con.close()


def test_chain_error_carries_the_index() -> None:
    err = AuditChainError(3, "hash mismatch")
    assert err.index == 3
    assert "3" in str(err)
    assert "hash mismatch" in str(err)


def test_log_is_a_context_manager_and_close_releases_the_database(tmp_path: Path, clock: FakeClock) -> None:
    path = tmp_path / "audit.db"
    with AuditLog(path, "DEMO", clock) as log:
        log.append("A", "engine", {})
    with pytest.raises(sqlite3.ProgrammingError):
        log.records()
    path.unlink()  # Windows refuses this while a connection is still open


def test_failure_inside_append_rolls_back_and_the_log_stays_usable(tmp_path: Path) -> None:
    class BrokenClock(FakeClock):
        broken = True

        def utc_now(self) -> datetime:
            if self.broken:
                raise RuntimeError("clock failure")
            return super().utc_now()

    clock = BrokenClock(START)
    with AuditLog(tmp_path / "audit.db", "DEMO", clock) as log:
        with pytest.raises(RuntimeError, match="clock failure"):
            log.append("A", "engine", {})
        clock.broken = False
        assert log.append("B", "engine", {})["seq"] == 0
        assert log.verify_chain() is True


@pytest.mark.parametrize("actor", ["engine", "user:alice", "guardian.ea-1", "risk_engine", "A" * 128])
def test_actor_allows_identifier_characters_only(log: AuditLog, actor: str) -> None:
    assert log.append("A", actor, {})["actor"] == actor


def test_data_005_empty_db_with_another_env_header_is_refused(tmp_path: Path, clock: FakeClock) -> None:
    path = tmp_path / "live.db"
    envguard.open_db("LIVE", path).close()  # header only, zero audit rows
    with pytest.raises(EnvMismatchError, match="LIVE"):
        AuditLog(path, "DEMO", clock)


def test_data_005_existing_file_without_env_header_is_refused(tmp_path: Path, clock: FakeClock) -> None:
    path = tmp_path / "plain.db"
    sqlite3.connect(path).close()
    with pytest.raises(EnvMismatchError, match="header"):
        AuditLog(path, "DEMO", clock)


def test_data_005_new_audit_db_records_its_env_header(tmp_path: Path, clock: FakeClock) -> None:
    path = tmp_path / "new.db"
    with AuditLog(path, "REPLAY", clock):
        pass
    assert envguard.recorded_env(path) == "REPLAY"
