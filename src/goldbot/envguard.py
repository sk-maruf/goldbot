"""One SQLite database per env, with an env header that must match the config (DATA-005)."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Mapping
from pathlib import Path

ENVS = ("LIVE", "DEMO", "BACKTEST", "REPLAY")
_HEADER_SQL = "CREATE TABLE goldbot_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL) STRICT"


class EnvMismatchError(Exception):
    """The database belongs to another env, has no env header, or the env is unknown."""


def _read_env(con: sqlite3.Connection) -> str | None:
    try:
        row = con.execute("SELECT value FROM goldbot_meta WHERE key = 'env'").fetchone()
    except sqlite3.OperationalError:  # no goldbot_meta table
        return None
    return row[0] if row else None


def recorded_env(path: Path) -> str | None:
    """The env header of an existing database, or None. Never creates or modifies a file."""
    if not path.is_file():
        return None
    con = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    try:
        return _read_env(con)
    finally:
        con.close()


def open_db(env: str, path: Path) -> sqlite3.Connection:
    """Open (or create, recording ``env``) the operational database. Refuses any env mismatch."""
    if env not in ENVS:
        raise EnvMismatchError(f"unknown env {env!r}; expected one of {', '.join(ENVS)}")
    existed = path.exists()
    if not existed:
        path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    try:
        if existed:
            found = _read_env(con)
            if found is None:
                raise EnvMismatchError(f"{path}: no env header; refusing to open it as {env} (DATA-005)")
            if found != env:
                raise EnvMismatchError(f"{path} belongs to env {found}; config env is {env} (DATA-005)")
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=FULL")
        if not existed:
            with con:
                con.execute(_HEADER_SQL)
                con.execute("INSERT INTO goldbot_meta (key, value) VALUES ('env', ?)", (env,))
    except BaseException:
        con.close()
        raise
    return con


def db_path_problems(paths: Mapping[str, Path]) -> list[str]:
    """Every env needs its own database file (DATA-005)."""
    problems = [f"no database path for {env}" for env in ENVS if env not in paths]
    seen: dict[str, str] = {}
    for env, path in paths.items():
        key = os.path.normcase(path.resolve())
        if key in seen:
            problems.append(f"{seen[key]} and {env} share database file {path} (DATA-005)")
        else:
            seen[key] = env
    return problems
