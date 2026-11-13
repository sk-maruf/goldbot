"""TIME-011 / TIME-015: static ban on naive datetimes and wall-clock durations in src/goldbot.

Rule (applied to every .py file under src/goldbot, with import aliases resolved):

* ``datetime.now()`` / ``datetime.fromtimestamp(x)`` without a tz argument (or with ``tz=None``);
* ``datetime(...)`` constructed without ``tzinfo`` (keyword, or the 8th positional argument);
* ``datetime.utcnow()``, ``datetime.utcfromtimestamp()``, ``datetime.today()``,
  ``date.today()``, ``date.fromtimestamp()`` - always naive or local;
* ``time.time()`` / ``time.time_ns()`` - always. Wall time comes from ``Clock.utc_now()`` and
  durations from ``Clock.monotonic_ns()``; whether a ``time.time()`` value is "used for a duration"
  cannot be decided statically, so every use is banned.

Not covered (ruff DTZ also runs in CI): ``strptime`` without ``%z``, ``.replace(tzinfo=None)``,
calls through ``getattr`` or other dynamic indirection.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src" / "goldbot"

_ALWAYS = {
    "datetime.datetime.utcnow",
    "datetime.datetime.utcfromtimestamp",
    "datetime.datetime.today",
    "datetime.date.today",
    "datetime.date.fromtimestamp",
    "time.time",
    "time.time_ns",
}
# qualified name -> positional index of the tz argument
_NEED_TZ = {"datetime.datetime.now": 0, "datetime.datetime.fromtimestamp": 1}


def _aliases(tree: ast.Module) -> dict[str, str]:
    names: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                names[a.asname or a.name.split(".")[0]] = a.name if a.asname else a.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.module:
            for a in node.names:
                names[a.asname or a.name] = f"{node.module}.{a.name}"
    return names


def _qualname(func: ast.expr, aliases: dict[str, str]) -> str | None:
    parts: list[str] = []
    while isinstance(func, ast.Attribute):
        parts.append(func.attr)
        func = func.value
    if not isinstance(func, ast.Name) or func.id not in aliases:
        return None
    return ".".join([aliases[func.id], *reversed(parts)])


def _has_tz(call: ast.Call, index: int, keyword: str) -> bool:
    arg: ast.expr | None = call.args[index] if len(call.args) > index else None
    for kw in call.keywords:
        if kw.arg == keyword:
            arg = kw.value
    return arg is not None and not (isinstance(arg, ast.Constant) and arg.value is None)


def violations(source: str, filename: str = "<snippet>") -> list[str]:
    tree = ast.parse(source, filename)
    aliases = _aliases(tree)
    found: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _qualname(node.func, aliases)
        bad = (
            name in _ALWAYS
            or (name in _NEED_TZ and not _has_tz(node, _NEED_TZ[name], "tz"))
            or (name == "datetime.datetime" and not _has_tz(node, 7, "tzinfo"))
        )
        if bad:
            found.append(f"{filename}:{node.lineno}: {name}")
    return found


BAD_SNIPPETS = [
    "from datetime import datetime\ndatetime.now()",
    "from datetime import datetime\ndatetime.now(tz=None)",
    "import datetime\ndatetime.datetime.now()",
    "import datetime as dt\ndt.datetime.utcnow()",
    "from datetime import datetime as DT\nDT.today()",
    "from datetime import date\ndate.today()",
    "from datetime import datetime\ndatetime.utcfromtimestamp(0)",
    "from datetime import datetime\ndatetime.fromtimestamp(0)",
    "from datetime import datetime\ndatetime(2026, 1, 1)",
    "import time\nstart = time.time()",
    "import time as t\nt.time_ns()",
    "from time import time\ntime()",
]

GOOD_SNIPPETS = [
    "from datetime import UTC, datetime\ndatetime.now(UTC)",
    "from datetime import UTC, datetime\ndatetime.now(tz=UTC)",
    "from datetime import UTC, datetime\ndatetime.fromtimestamp(0, UTC)",
    "from datetime import UTC, datetime\ndatetime(2026, 1, 1, tzinfo=UTC)",
    "from datetime import UTC, datetime\ndatetime(2026, 1, 1, 0, 0, 0, 0, UTC)",
    "import time\ntime.monotonic_ns()",
    "def now():\n    return 1\nnow()",
]


@pytest.mark.parametrize("snippet", BAD_SNIPPETS)
def test_scanner_self_test_catches_planted_snippet(snippet: str) -> None:
    assert violations(snippet), snippet


@pytest.mark.parametrize("snippet", GOOD_SNIPPETS)
def test_scanner_self_test_allows_aware_and_monotonic_calls(snippet: str) -> None:
    assert violations(snippet) == []


def test_time_011_no_naive_datetime_or_wall_clock_duration_in_src() -> None:
    files = sorted(SRC.rglob("*.py"))
    assert files, f"no sources found under {SRC}"
    found = [v for f in files for v in violations(f.read_text(encoding="utf-8"), str(f))]
    assert found == []
