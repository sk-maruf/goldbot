"""OBS-010 JSON-line fields, OBS-011 level names, SEC-004 redaction (secrets, patterns, sensitive fields)."""

from __future__ import annotations

import io
import json
import logging
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
import structlog

from goldbot.core.clock import FakeClock
from goldbot.core.logs import REDACTED, configure_logging, redact, register_secret

START = datetime(2026, 11, 14, 8, 0, 0, 123_000, tzinfo=UTC)


@pytest.fixture
def stream() -> Iterator[io.StringIO]:
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    out = io.StringIO()
    configure_logging("DEMO", "engine", clock=FakeClock(START), stream=out)
    yield out
    root.handlers = handlers
    root.setLevel(level)
    structlog.contextvars.clear_contextvars()
    structlog.reset_defaults()


def lines(out: io.StringIO) -> list[dict[str, object]]:
    return [json.loads(line) for line in out.getvalue().splitlines()]


def test_obs_010_every_line_carries_the_required_fields(stream: io.StringIO) -> None:
    structlog.get_logger().info("order_submitted", op_id="op-1", volume="0.01")
    (rec,) = lines(stream)
    assert rec == {
        "ts_utc": "2026-11-14T08:00:00.123Z",
        "mono_seq": 0,
        "level": "INFO",
        "component": "engine",
        "env": "DEMO",
        "event": "order_submitted",
        "trace_id": None,
        "op_id": "op-1",
        "details": {"volume": "0.01"},
    }


def test_obs_010_mono_seq_increases_and_trace_id_comes_from_context(stream: io.StringIO) -> None:
    log = structlog.get_logger()
    structlog.contextvars.bind_contextvars(trace_id="tr-9")
    log.info("a", command_id="cmd-1")
    log.warning("b")
    first, second = lines(stream)
    assert (first["mono_seq"], second["mono_seq"]) == (0, 1)
    assert first["trace_id"] == second["trace_id"] == "tr-9"
    assert first["command_id"] == "cmd-1"
    assert "op_id" not in first


@pytest.mark.parametrize(
    ("method", "level"),
    [("debug", "DEBUG"), ("info", "INFO"), ("warning", "WARN"), ("error", "ERROR"), ("critical", "CRITICAL")],
)
def test_obs_011_level_names(stream: io.StringIO, method: str, level: str) -> None:
    getattr(structlog.get_logger(), method)("x")
    assert lines(stream)[0]["level"] == level


def test_sec_004_registered_secret_is_removed_from_event_details_and_nested_values(
    stream: io.StringIO,
) -> None:
    register_secret("Sup3r-S3cret-Value")
    structlog.get_logger().info(
        "login Sup3r-S3cret-Value", details={"nested": ["x Sup3r-S3cret-Value y"], "Sup3r-S3cret-Value": 1}
    )
    out = stream.getvalue()
    assert "Sup3r-S3cret-Value" not in out
    assert REDACTED in out


def test_sec_004_exception_text_is_redacted(stream: io.StringIO) -> None:
    register_secret("exc-secret-123456")
    try:
        raise RuntimeError("connect failed with exc-secret-123456")
    except RuntimeError:
        structlog.get_logger().exception("connect_failed")
    (rec,) = lines(stream)
    assert rec["level"] == "ERROR"
    assert "RuntimeError" in str(rec["details"])
    assert "exc-secret-123456" not in stream.getvalue()


def test_sec_004_stdlib_logging_path_is_shaped_and_redacted(stream: io.StringIO) -> None:
    register_secret("stdlib-secret-abcdef")
    try:
        raise ValueError("boom stdlib-secret-abcdef")
    except ValueError:
        logging.getLogger("thirdparty").error("failed %s", "stdlib-secret-abcdef", exc_info=True)
    (rec,) = lines(stream)
    assert rec["level"] == "ERROR"
    assert rec["component"] == "engine"
    assert "stdlib-secret-abcdef" not in stream.getvalue()


@pytest.mark.parametrize(
    "text",
    [
        "password=hunter2",
        "PASSWORD: hunter2",
        "api_key=hunter2",
        "token = 'hunter2'",
        '{"secret": "hunter2"}',
        "dsn?user=a&passwd=hunter2&x=1",
        'password="my pass phrase hunter2"',
        "secret: 'phrase hunter2 here'",
        '{"api-key": "two words hunter2"}',
        "Authorization: Bearer hunter2",
        "authorization: Basic hunter2",
        "sent bearer hunter2 to the api",
        "credential=hunter2",
        "cookie: hunter2",
        "apikey=hunter2",
    ],
)
def test_sec_004_assignment_patterns_are_redacted(text: str) -> None:
    clean = redact(text)
    assert isinstance(clean, str)
    assert "hunter2" not in clean
    assert REDACTED in clean


@pytest.mark.parametrize("field", ["password", "api_key", "session_token", "Authorization", "secret"])
def test_sec_004_sensitive_field_values_are_redacted_whatever_their_length(field: str) -> None:
    assert redact({field: "abc", "keep": "visible"}) == {field: REDACTED, "keep": "visible"}
    assert redact({field: {"a": 1}}) == {field: REDACTED}


def test_redact_keeps_clean_scalars_and_their_types() -> None:
    assert redact({"n": 3, "f": 1.5, "b": True, "z": None, "t": (1, "a")}) == {
        "n": 3,
        "f": 1.5,
        "b": True,
        "z": None,
        "t": [1, "a"],
    }


def test_redact_stringifies_unknown_objects_and_checks_the_text() -> None:
    class Thing:
        def __str__(self) -> str:
            return "thing obj-secret-998877"

    register_secret("obj-secret-998877")
    assert redact(Thing()) == f"thing {REDACTED}"
    register_secret("424242424242")
    assert redact(424242424242) == REDACTED  # a number equal to a secret is not kept either


def test_register_secret_ignores_empty_value() -> None:
    register_secret("")
    assert redact("plain text") == "plain text"
