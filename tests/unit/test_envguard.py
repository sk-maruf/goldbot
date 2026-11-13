"""Env guard: one SQLite file per env, env header, mismatch refusal (DATA-005)."""

import sqlite3

import pytest

from goldbot import envguard
from goldbot.envguard import EnvMismatchError


def test_new_db_records_env_and_reopens(tmp_path):
    path = tmp_path / "demo.sqlite"
    envguard.open_db("DEMO", path).close()
    assert envguard.recorded_env(path) == "DEMO"
    envguard.open_db("DEMO", path).close()


def test_env_db_mismatch_refused_and_header_unchanged(tmp_path):
    path = tmp_path / "live.sqlite"
    envguard.open_db("LIVE", path).close()
    with pytest.raises(EnvMismatchError, match="LIVE"):
        envguard.open_db("DEMO", path)
    assert envguard.recorded_env(path) == "LIVE"


def test_existing_db_without_env_header_refused(tmp_path):
    path = tmp_path / "foreign.sqlite"
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE t (x)")
    con.commit()
    con.close()
    with pytest.raises(EnvMismatchError, match="no env header"):
        envguard.open_db("DEMO", path)


def test_unknown_env_refused(tmp_path):
    with pytest.raises(EnvMismatchError, match="PROD"):
        envguard.open_db("PROD", tmp_path / "x.sqlite")
    assert not (tmp_path / "x.sqlite").exists()


def test_db_uses_wal_and_full_sync(tmp_path):
    con = envguard.open_db("DEMO", tmp_path / "d.sqlite")
    try:
        assert con.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert con.execute("PRAGMA synchronous").fetchone()[0] == 2  # FULL
    finally:
        con.close()


def test_recorded_env_of_missing_file_is_none_and_creates_nothing(tmp_path):
    path = tmp_path / "none.sqlite"
    assert envguard.recorded_env(path) is None
    assert not path.exists()


def test_db_paths_must_be_distinct_per_env(tmp_path):
    same = tmp_path / "data" / "goldbot.sqlite"
    paths = {"LIVE": same, "DEMO": tmp_path / "data" / ".." / "data" / "goldbot.sqlite"}
    assert any("LIVE" in p and "DEMO" in p for p in envguard.db_path_problems(paths))


def test_distinct_db_paths_have_no_problems(tmp_path):
    paths = {e: tmp_path / f"{e}.sqlite" for e in ("LIVE", "DEMO", "BACKTEST", "REPLAY")}
    assert envguard.db_path_problems(paths) == []


def test_db_path_for_every_env_is_required(tmp_path):
    assert any("REPLAY" in p for p in envguard.db_path_problems({"LIVE": tmp_path / "l", "DEMO": tmp_path / "d"}))
