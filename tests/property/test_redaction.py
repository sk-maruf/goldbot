"""SEC-004 property: a registered secret embedded anywhere in a log call never appears in the output."""

from __future__ import annotations

import io
import json
import logging
import string
from datetime import UTC, datetime

import structlog
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from goldbot.core.clock import FakeClock
from goldbot.core.logs import REDACTED, configure_logging, register_secret

# Brackets excluded so a secret cannot straddle the "[REDACTED]" marker it is replaced by.
SECRET_CHARS = string.ascii_letters + string.digits + "!#$%&()*+,-./:;<=>?@^_`{|}~'\" \\"
secrets_st = st.text(alphabet=SECRET_CHARS, min_size=8, max_size=40)
text_st = st.text(max_size=20)


def strings_in(value: object) -> list[str]:
    if isinstance(value, dict):
        return [s for k, v in value.items() for s in [str(k), *strings_in(v)]]
    if isinstance(value, list):
        return [s for v in value for s in strings_in(v)]
    return [str(value)]


@settings(max_examples=200, deadline=None)
@given(
    secret=secrets_st,
    prefix=text_st,
    suffix=text_st,
    where=st.sampled_from(["event", "value", "key", "nested", "exception", "stdlib", "stdlib_exc"]),
)
def test_sec_004_registered_secret_never_appears_in_any_log_path(
    secret: str, prefix: str, suffix: str, where: str
) -> None:
    assume(secret not in REDACTED)
    embedded = prefix + secret + suffix
    out = io.StringIO()
    root = logging.getLogger()
    saved, level = root.handlers[:], root.level
    configure_logging("LIVE", "engine", clock=FakeClock(datetime(2026, 1, 1, tzinfo=UTC)), stream=out)
    register_secret(secret)
    log = structlog.get_logger()
    try:
        if where == "event":
            log.info(embedded)
        elif where == "value":
            log.info("e", field=embedded)
        elif where == "key":
            log.info("e", **{"x": {embedded: 1}})
        elif where == "nested":
            log.info("e", payload={"a": [1, {"b": (embedded, 2)}]})
        elif where == "exception":
            try:
                raise ValueError(embedded)
            except ValueError:
                log.exception("e")
        elif where == "stdlib":
            logging.getLogger("lib").warning("msg %s", embedded)
        else:
            try:
                raise KeyError(embedded)
            except KeyError:
                logging.getLogger("lib").exception("failed")
    finally:
        root.handlers = saved
        root.setLevel(level)
        structlog.reset_defaults()

    raw = out.getvalue()
    assert raw, "nothing was logged"
    forms = {secret, repr(secret)[1:-1]}  # also the escaped form shown by repr(), e.g. in KeyError text
    for line in raw.splitlines():
        assert not [s for s in strings_in(json.loads(line)) for f in forms if f in s]
