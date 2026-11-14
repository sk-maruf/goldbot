"""Structured JSON-line logging (OBS-010/011) with SEC-004 redaction on every path.

Both structlog calls and stdlib ``logging`` records (third-party libraries) go through the same
shaping and redaction processors. Redaction removes:

* every registered secret value (and its ``repr``/JSON-escaped forms) from all keys, values,
  nested containers, the event text and exception text;
* assignment patterns such as ``password=...``, ``token: ...``, ``api_key=...`` (a quoted value is
  removed whole, spaces included), ``Authorization: <scheme> <credentials>`` and ``Bearer <token>``;
* the whole value of a sensitive field (name containing pass, secret, token, key, auth, cookie or
  credential). This is stricter than SEC-004's "16+ char base64/hex runs in sensitive fields".
"""

from __future__ import annotations

import itertools
import json
import logging
import re
import sys
import threading
from typing import TextIO, cast

import structlog
from structlog.typing import EventDict, Processor, WrappedLogger

from goldbot.core.clock import Clock, format_utc

REDACTED = "[REDACTED]"

_KEYWORDS = r"password|passwd|secret|token|api[_-]?key|key|authorization|bearer|credential|cookie"
# A quoted value is taken whole (it may contain spaces); an unquoted one runs to a delimiter.
_ASSIGNMENT = re.compile(rf"(?i)({_KEYWORDS})([\"']?\s*[=:]\s*)(\"[^\"]*\"|'[^']*'|[^\s,;&\"']+)")
_AUTH_HEADER = re.compile(r"(?i)\b(authorization\s*:\s*)\S+(?:\s+\S+)?")  # scheme + credentials
_BEARER = re.compile(r"(?i)\b(bearer\s+)\S+")
_SENSITIVE_FIELD = re.compile(r"(?i)pass|secret|token|key|auth|cookie|credential")
_LEVELS = {"warning": "WARN", "exception": "ERROR", "fatal": "CRITICAL", "msg": "INFO"}
_STRUCTLOG_KEYS = ("_record", "_from_structlog")

_lock = threading.Lock()
_secrets: set[str] = set()
_secret_pattern: re.Pattern[str] | None = None


def register_secret(value: str) -> None:
    """Redact ``value`` from every later log line. Empty values are ignored."""
    global _secret_pattern
    if not value:
        return
    with _lock:
        _secrets.update({value, repr(value)[1:-1], json.dumps(value)[1:-1]})
        alternatives = sorted(_secrets, key=len, reverse=True)  # longest first: no partial leftovers
        _secret_pattern = re.compile("|".join(map(re.escape, alternatives)))


def _redact_text(text: str) -> str:
    pattern = _secret_pattern
    if pattern is not None:
        text = pattern.sub(REDACTED, text)
    text = _AUTH_HEADER.sub(lambda m: m.group(1) + REDACTED, text)
    text = _BEARER.sub(lambda m: m.group(1) + REDACTED, text)
    return _ASSIGNMENT.sub(lambda m: m.group(1) + m.group(2) + REDACTED, text)


def redact(value: object) -> object:
    """Return a JSON-ready copy of ``value`` with secrets removed (see the module docstring)."""
    if isinstance(value, dict):
        items = cast("dict[object, object]", value).items()
        return {
            _redact_text(str(k)): REDACTED if _SENSITIVE_FIELD.search(str(k)) else redact(v) for k, v in items
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [redact(v) for v in cast("list[object]", value)]
    if isinstance(value, str):
        return _redact_text(value)
    text = str(value)
    clean = _redact_text(text)
    if isinstance(value, (int, float)) or value is None:  # bool is an int
        return value if clean == text else clean
    return clean  # unknown objects are logged as their (redacted) text


def _shaper(env: str, component: str, clock: Clock) -> Processor:
    seq = itertools.count()

    def shape(_logger: WrappedLogger, method_name: str, event_dict: EventDict) -> EventDict:
        for key in _STRUCTLOG_KEYS:
            event_dict.pop(key, None)
        record: dict[str, object] = {
            "ts_utc": format_utc(clock.utc_now()),
            "mono_seq": next(seq),
            "level": _LEVELS.get(method_name, method_name.upper()),
            "component": component,
            "env": env,
            "event": event_dict.pop("event", ""),
            "trace_id": event_dict.pop("trace_id", None),
        }
        for key in ("op_id", "command_id"):
            if key in event_dict:
                record[key] = event_dict.pop(key)
        record["details"] = dict(event_dict)
        return cast("EventDict", redact(record))

    return shape


def configure_logging(env: str, component: str, *, clock: Clock, stream: TextIO = sys.stderr) -> None:
    """Route structlog and stdlib logging to ``stream`` as redacted OBS-010 JSON lines."""
    shape = _shaper(env, component, clock)
    chain: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.format_exc_info,
        shape,
        structlog.processors.JSONRenderer(),
    ]
    structlog.configure(
        processors=chain,
        logger_factory=structlog.PrintLoggerFactory(file=stream),
        cache_logger_on_first_use=False,
    )
    handler = logging.StreamHandler(stream)
    handler.setFormatter(structlog.stdlib.ProcessorFormatter(processors=chain))
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
