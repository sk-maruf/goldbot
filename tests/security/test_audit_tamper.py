"""SEC-022 / TM-13: tampering with stored audit records is detected at the first bad index.

The tamper helper bypasses the append-only triggers on purpose: it plays a same-user process that
edits the SQLite file directly.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

import pytest

from goldbot.core.audit import AuditChainError, AuditLog
from goldbot.core.clock import FakeClock

Row = dict[str, object]
COLUMNS = ("schema_version", "env", "seq", "ts", "actor", "event", "payload_hash", "prev_hash", "hash")


def tamper(path: Path, edit: Callable[[list[Row]], list[Row]]) -> None:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    try:
        rows = [dict(r) for r in con.execute(f"SELECT {', '.join(COLUMNS)} FROM audit_log ORDER BY id")]
        rows = edit(rows)
        con.execute("DROP TRIGGER audit_log_no_update")
        con.execute("DROP TRIGGER audit_log_no_delete")
        con.execute("DELETE FROM audit_log")
        for r in rows:
            con.execute(
                f"INSERT INTO audit_log ({', '.join(COLUMNS)}) VALUES ({', '.join('?' * len(COLUMNS))})",
                [r[c] for c in COLUMNS],
            )
        con.commit()
    finally:
        con.close()


@pytest.fixture
def path(tmp_path: Path) -> Path:
    path = tmp_path / "audit.db"
    clock = FakeClock(datetime(2026, 11, 14, tzinfo=UTC))
    with AuditLog(path, "LIVE", clock) as log:
        for i in range(5):
            log.append(f"EVENT_{i}", "engine", {"i": i})
            clock.advance(10)
        assert log.verify_chain()
    return path


def expect_break(path: Path, index: int) -> None:
    with AuditLog(path, "LIVE", FakeClock()) as log, pytest.raises(AuditChainError) as info:
        log.verify_chain()
    assert info.value.index == index


def set_field(i: int, field: str, value: object) -> Callable[[list[Row]], list[Row]]:
    def edit(rows: list[Row]) -> list[Row]:
        rows[i][field] = value
        return rows

    return edit


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("actor", "attacker"),
        ("event", "NOTHING_HAPPENED"),
        ("ts", "2026-11-14T00:00:00.001Z"),
        ("payload_hash", "0" * 64),
        ("env", "DEMO"),
        ("hash", "f" * 64),
    ],
)
def test_modified_record_breaks_at_its_index(path: Path, field: str, value: object) -> None:
    tamper(path, set_field(2, field, value))
    expect_break(path, 2)


def test_modified_genesis_prev_hash_breaks_at_zero(path: Path) -> None:
    tamper(path, set_field(0, "prev_hash", "0" * 64))
    expect_break(path, 0)


def test_deleted_record_breaks_at_its_index(path: Path) -> None:
    tamper(path, lambda rows: rows[:2] + rows[3:])
    expect_break(path, 2)


def test_deleted_first_record_breaks_at_zero(path: Path) -> None:
    tamper(path, lambda rows: rows[1:])
    expect_break(path, 0)


def test_reordered_records_break_at_the_first_moved_index(path: Path) -> None:
    tamper(path, lambda rows: [rows[0], rows[1], rows[3], rows[2], rows[4]])
    expect_break(path, 2)


def test_inserted_forged_record_breaks_at_its_index(path: Path) -> None:

    def insert(rows: list[Row]) -> list[Row]:
        forged = dict(rows[1], seq=99, event="FORGED")
        return [*rows[:2], forged, *rows[2:]]

    tamper(path, insert)
    expect_break(path, 2)


def test_appended_record_with_copied_hashes_breaks_at_its_index(path: Path) -> None:
    tamper(path, lambda rows: [*rows, dict(rows[4], seq=5, prev_hash=rows[4]["hash"])])
    expect_break(path, 5)


def test_truncated_tail_is_not_detectable_by_the_chain_alone(path: Path) -> None:
    """Documented limit (TM-13): dropping the newest records leaves a valid chain.

    The off-box export (SEC-022) is what covers this case.
    """
    tamper(path, lambda rows: rows[:3])
    with AuditLog(path, "LIVE", FakeClock()) as log:
        assert log.verify_chain() is True
