"""Injectable clocks (TIME_AND_CLOCK_SPEC §3-4).

* ``utc_now()`` is wall time (C1): only for records, never for durations.
* ``monotonic_ns()`` is monotonic time (C2): every duration is measured with it (TIME-015).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

_NS_PER_MS = 1_000_000


class Clock(Protocol):
    def utc_now(self) -> datetime: ...

    def monotonic_ns(self) -> int: ...


class SystemClock:
    def utc_now(self) -> datetime:
        return datetime.now(UTC)

    def monotonic_ns(self) -> int:
        return time.monotonic_ns()


def _require_aware(dt: datetime) -> None:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError(f"naive datetime is forbidden (TIME-011): {dt!r}")


class FakeClock:
    """Test clock. ``advance`` moves both clocks; ``jump_wall``/``set_utc`` move only wall time."""

    def __init__(self, start: datetime = datetime(2026, 1, 1, tzinfo=UTC), mono_ns: int = 0) -> None:
        _require_aware(start)
        self._utc = start.astimezone(UTC)
        self._mono_ns = mono_ns

    def utc_now(self) -> datetime:
        return self._utc

    def monotonic_ns(self) -> int:
        return self._mono_ns

    def advance(self, ms: int) -> None:
        if ms < 0:
            raise ValueError("monotonic time never goes backwards")
        self._mono_ns += ms * _NS_PER_MS
        self._utc += timedelta(milliseconds=ms)

    def jump_wall(self, delta: timedelta) -> None:
        self._utc += delta

    def set_utc(self, dt: datetime) -> None:
        _require_aware(dt)
        self._utc = dt.astimezone(UTC)


def elapsed_ms(clock: Clock, since_ns: int) -> int:
    return (clock.monotonic_ns() - since_ns) // _NS_PER_MS


@dataclass(frozen=True)
class Deadline:
    """A timeout measured on monotonic time only (TIME-015)."""

    clock: Clock
    start_ns: int
    duration_ms: int

    @classmethod
    def start(cls, clock: Clock, duration_ms: int) -> Deadline:
        if duration_ms < 0:
            raise ValueError("duration must not be negative")
        return cls(clock, clock.monotonic_ns(), duration_ms)

    def remaining_ms(self) -> int:
        return max(0, self.duration_ms - elapsed_ms(self.clock, self.start_ns))

    def expired(self) -> bool:
        return elapsed_ms(self.clock, self.start_ns) >= self.duration_ms


def format_utc(dt: datetime) -> str:
    """ISO-8601 UTC with milliseconds (truncated) and a ``Z`` suffix (TIME-011)."""
    _require_aware(dt)
    utc = dt.astimezone(UTC)
    return utc.strftime("%Y-%m-%dT%H:%M:%S.") + f"{utc.microsecond // 1000:03d}Z"
