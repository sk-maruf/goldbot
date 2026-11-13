"""Clock abstraction: TIME-011 (UTC, ms, Z, no naive) and TIME-015 (durations are monotonic)."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from goldbot.core.clock import Clock, Deadline, FakeClock, SystemClock, elapsed_ms, format_utc


def test_system_clock_is_a_clock_and_returns_aware_utc() -> None:
    clock: Clock = SystemClock()
    now = clock.utc_now()
    assert now.tzinfo is UTC
    first = clock.monotonic_ns()
    assert clock.monotonic_ns() >= first


def test_fake_clock_advance_moves_wall_and_monotonic_together() -> None:
    start = datetime(2026, 11, 13, 9, 0, tzinfo=UTC)
    clock = FakeClock(start=start)
    mono0 = clock.monotonic_ns()
    clock.advance(1500)
    assert clock.utc_now() == start + timedelta(milliseconds=1500)
    assert clock.monotonic_ns() - mono0 == 1_500_000_000


def test_fake_clock_rejects_naive_start_and_negative_advance() -> None:
    with pytest.raises(ValueError, match="naive"):
        FakeClock(start=datetime(2026, 1, 1))  # noqa: DTZ001 - deliberately naive
    with pytest.raises(ValueError, match="backwards"):
        FakeClock().advance(-1)


def test_fake_clock_set_utc_converts_to_utc_and_leaves_monotonic_alone() -> None:
    clock = FakeClock()
    mono0 = clock.monotonic_ns()
    clock.set_utc(datetime(2026, 1, 1, 12, 0, tzinfo=timezone(timedelta(hours=2))))
    assert clock.utc_now() == datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
    assert clock.utc_now().tzinfo is UTC
    assert clock.monotonic_ns() == mono0
    with pytest.raises(ValueError, match="naive"):
        clock.set_utc(datetime(2026, 1, 1))  # noqa: DTZ001 - deliberately naive


@pytest.mark.parametrize("jump", [timedelta(hours=1), timedelta(hours=-1)])
def test_time_015_wall_clock_jump_does_not_change_any_duration(jump: timedelta) -> None:
    clock = FakeClock()
    start_ns = clock.monotonic_ns()
    deadline = Deadline.start(clock, duration_ms=10_000)

    clock.advance(4_000)
    clock.jump_wall(jump)  # NTP step, DST or manual change

    assert elapsed_ms(clock, start_ns) == 4_000
    assert not deadline.expired()  # not early
    assert deadline.remaining_ms() == 6_000

    clock.advance(5_999)
    assert not deadline.expired()
    clock.advance(1)
    assert deadline.expired()  # not late
    assert deadline.remaining_ms() == 0


def test_deadline_rejects_negative_duration() -> None:
    with pytest.raises(ValueError, match="negative"):
        Deadline.start(FakeClock(), duration_ms=-1)


def test_time_011_format_utc_iso8601_with_milliseconds_and_z() -> None:
    dt = datetime(2026, 11, 13, 9, 5, 7, 123_999, tzinfo=UTC)
    assert format_utc(dt) == "2026-11-13T09:05:07.123Z"  # truncated, never rounded into the next ms


def test_time_011_format_utc_converts_other_offsets_to_utc() -> None:
    dt = datetime(2026, 3, 29, 3, 30, 0, 5_000, tzinfo=timezone(timedelta(hours=3)))
    assert format_utc(dt) == "2026-03-29T00:30:00.005Z"


def test_time_011_format_utc_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="naive"):
        format_utc(datetime(2026, 1, 1))  # noqa: DTZ001 - deliberately naive
