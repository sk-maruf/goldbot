"""Append-only, SHA-256 hash-chained audit log (SEC-022, PRV-013).

Storage: the SQLite table ``audit_log`` (DATA_ARCHITECTURE §2 names it; sqlite3 is stdlib).
A transaction makes each append atomic (no torn record after a crash, unlike a plain JSONL file),
and triggers refuse UPDATE and DELETE through any connection. Retention truncation (PRV §4) is a
later, explicit TRUNCATION event and is not implemented here.

Chain: ``hash = sha256(canonical_json(record without "hash"))``; ``prev_hash`` is the previous
record's hash, and the first record's is ``GENESIS_PREV_HASH`` (null, as audit_event.schema.json
requires). The payload itself is not stored, only its ``payload_hash`` (PRV-013).
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Self, cast

from goldbot.core.clock import Clock, format_utc

SCHEMA_VERSION = "1.0.0"
GENESIS_PREV_HASH: str | None = None
ENVS = frozenset({"LIVE", "DEMO", "BACKTEST", "REPLAY"})
_EVENT = re.compile(r"[A-Z][A-Z0-9_]{0,63}")
_ACTOR = re.compile(r"[^\x00-\x1f\x7f]{1,128}")
_COLUMNS = ("schema_version", "env", "seq", "ts", "actor", "event", "payload_hash", "prev_hash", "hash")
_SELECT = (
    "SELECT schema_version, env, seq, ts, actor, event, payload_hash, prev_hash, hash"
    " FROM audit_log ORDER BY id"
)
_INSERT = (
    "INSERT INTO audit_log (schema_version, env, seq, ts, actor, event, payload_hash, prev_hash, hash)"
    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
)

_DDL = """
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY,
    schema_version TEXT NOT NULL,
    env TEXT NOT NULL,
    seq INTEGER NOT NULL UNIQUE,
    ts TEXT NOT NULL,
    actor TEXT NOT NULL,
    event TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    prev_hash TEXT,
    hash TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS audit_log_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_log_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
"""

AuditRecord = dict[str, str | int | None]


class AuditChainError(Exception):
    def __init__(self, index: int, reason: str) -> None:
        super().__init__(f"audit chain broken at index {index}: {reason}")
        self.index = index


def _check_json(value: object) -> None:
    if isinstance(value, float):
        raise TypeError("floats are not allowed in audit JSON (use decimal strings)")
    if isinstance(value, dict):
        for k, v in cast("dict[object, object]", value).items():
            if not isinstance(k, str):
                raise TypeError(f"audit JSON keys must be str, got {type(k).__name__}")
            _check_json(v)
    elif isinstance(value, (list, tuple)):
        for v in cast("list[object]", value):
            _check_json(v)
    elif not (value is None or isinstance(value, (str, int))):  # bool is an int
        raise TypeError(f"{type(value).__name__} is not allowed in audit JSON")


def canonical_json(value: object) -> bytes:
    """Sorted keys, no whitespace, UTF-8; floats and non-JSON types are rejected."""
    _check_json(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


class AuditLog:
    def __init__(self, path: Path | str, env: str, clock: Clock) -> None:
        if env not in ENVS:
            raise ValueError(f"unknown env {env!r}")
        self._env = env
        self._clock = clock
        self._con = sqlite3.connect(path, isolation_level=None)
        self._con.execute("PRAGMA journal_mode=WAL")
        self._con.execute("PRAGMA synchronous=FULL")
        self._con.executescript(_DDL)
        first = self._con.execute("SELECT env FROM audit_log ORDER BY id LIMIT 1").fetchone()
        if first is not None and first[0] != env:
            self.close()
            raise ValueError(f"audit log env is {first[0]}, not {env} (DATA-005)")

    def close(self) -> None:
        self._con.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def append(self, event_type: str, actor: str, payload: object) -> AuditRecord:
        if not _EVENT.fullmatch(event_type):
            raise ValueError(f"invalid audit event type {event_type!r}")
        if not _ACTOR.fullmatch(actor):
            raise ValueError(f"invalid audit actor {actor!r}")
        payload_hash = _sha256(payload)
        self._con.execute("BEGIN IMMEDIATE")
        try:
            last = self._con.execute("SELECT seq, hash FROM audit_log ORDER BY id DESC LIMIT 1").fetchone()
            record: AuditRecord = {
                "schema_version": SCHEMA_VERSION,
                "env": self._env,
                "seq": 0 if last is None else last[0] + 1,
                "ts": format_utc(self._clock.utc_now()),
                "actor": actor,
                "event": event_type,
                "payload_hash": payload_hash,
                "prev_hash": GENESIS_PREV_HASH if last is None else last[1],
            }
            record["hash"] = _sha256(record)
            self._con.execute(_INSERT, [record[c] for c in _COLUMNS])
            self._con.execute("COMMIT")
        except BaseException:
            self._con.execute("ROLLBACK")
            raise
        return record

    def records(self) -> list[AuditRecord]:
        rows = self._con.execute(_SELECT)
        return [dict(zip(_COLUMNS, row, strict=True)) for row in rows]

    def verify_chain(self) -> bool:
        """True if intact; otherwise raise AuditChainError with the first bad index."""
        prev_hash = GENESIS_PREV_HASH
        for index, record in enumerate(self.records()):
            body = {k: v for k, v in record.items() if k != "hash"}
            if record["seq"] != index:
                raise AuditChainError(index, f"seq {record['seq']} out of place")
            if record["prev_hash"] != prev_hash:
                raise AuditChainError(index, "prev_hash does not match the previous record")
            if record["hash"] != _sha256(body):
                raise AuditChainError(index, "hash does not match the record")
            prev_hash = record["hash"]
        return True
