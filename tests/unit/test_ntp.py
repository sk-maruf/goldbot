"""TIME-010: SNTP offset query and the two-server pass/fail check (no real network: injected transport)."""

from __future__ import annotations

import socket
import struct
import threading
from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import pytest

from goldbot.core.clock import FakeClock
from goldbot.core.ntp import NtpError, NtpResult, _udp_exchange, check_offsets, query_offset

NTP_EPOCH = datetime(1900, 1, 1, tzinfo=UTC)
START = datetime(2026, 11, 14, 8, 0, tzinfo=UTC)


def ntp_ts(dt: datetime) -> bytes:
    ns = (dt - NTP_EPOCH) // timedelta(microseconds=1) * 1000
    secs, rem = divmod(ns, 1_000_000_000)
    return struct.pack("!II", secs, (rem << 32) // 1_000_000_000)


def reply(
    request: bytes, t2: datetime, t3: datetime, *, li: int = 0, mode: int = 4, stratum: int = 2
) -> bytes:
    head = bytes([(li << 6) | (4 << 3) | mode, stratum, 6, 0xEC]) + bytes(20)
    return head + request[40:48] + ntp_ts(t2) + ntp_ts(t3)  # origin = our transmit field


def server(clock: FakeClock, offset_ms: int, rtt_ms: int = 40, *, jump: timedelta | None = None):
    """A fake SNTP server whose clock is ``offset_ms`` ahead; the exchange takes ``rtt_ms``."""

    def transport(host: str, request: bytes, timeout_s: float) -> bytes:
        clock.advance(rtt_ms // 2)
        t2 = clock.utc_now() + timedelta(milliseconds=offset_ms)
        clock.advance(rtt_ms - rtt_ms // 2)
        if jump is not None:
            clock.jump_wall(jump)
        return reply(request, t2, t2)

    return transport


@pytest.mark.parametrize("offset_ms", [500, -1_250, 0])
def test_time_010_query_offset_computes_offset_and_rtt(offset_ms: int) -> None:
    clock = FakeClock(START)
    result = query_offset("time.example", clock=clock, transport=server(clock, offset_ms))
    assert result == NtpResult(server="time.example", offset_ms=offset_ms, rtt_ms=40)


@pytest.mark.parametrize("jump", [timedelta(hours=1), timedelta(hours=-1)])
def test_time_015_wall_jump_during_query_changes_neither_offset_nor_rtt(jump: timedelta) -> None:
    clock = FakeClock(START)
    result = query_offset("t", clock=clock, transport=server(clock, 300, jump=jump))
    assert (result.offset_ms, result.rtt_ms) == (300, 40)


def test_request_is_a_minimal_sntp_v4_client_packet_with_random_transmit_nonce() -> None:
    seen: list[bytes] = []

    def transport(host: str, request: bytes, timeout_s: float) -> bytes:
        seen.append(request)
        return reply(request, START, START)

    clock = FakeClock(START)
    query_offset("t", clock=clock, transport=transport)
    query_offset("t", clock=clock, transport=transport)
    first, second = seen
    assert len(first) == 48
    assert first[0] == 0x23  # LI 0, version 4, mode 3 (client)
    assert first[1:40] == bytes(39)  # data minimisation: no client time or other fields sent
    assert first[40:48] != second[40:48]  # transmit field is a fresh nonce, not the local clock


def test_timeout_raises_a_clear_ntp_error() -> None:
    def transport(host: str, request: bytes, timeout_s: float) -> bytes:
        raise TimeoutError

    with pytest.raises(NtpError, match=r"t\.example.*timeout"):
        query_offset("t.example", timeout_s=0.5, clock=FakeClock(START), transport=transport)


def test_network_error_raises_ntp_error() -> None:
    def transport(host: str, request: bytes, timeout_s: float) -> bytes:
        raise socket.gaierror("name not known")

    with pytest.raises(NtpError, match="name not known"):
        query_offset("nowhere", clock=FakeClock(START), transport=transport)


def _bad(make: Callable[[bytes], bytes]) -> Callable[[str, bytes, float], bytes]:
    return lambda host, request, timeout_s: make(request)


@pytest.mark.parametrize(
    ("make", "message"),
    [
        (lambda r: reply(r, START, START)[:47], "length"),
        (lambda r: reply(r, START, START, mode=3), "mode"),
        (lambda r: reply(r, START, START, stratum=0), "stratum"),  # kiss-of-death
        (lambda r: reply(r, START, START, stratum=16), "stratum"),
        (lambda r: reply(r, START, START, li=3), "unsynchronised"),
        (lambda r: reply(bytes(48), START, START), "origin"),  # does not echo our nonce
        (lambda r: reply(r, START, START)[:40] + bytes(8), "transmit"),
    ],
)
def test_invalid_reply_is_rejected(make: Callable[[bytes], bytes], message: str) -> None:
    with pytest.raises(NtpError, match=message):
        query_offset("t", clock=FakeClock(START), transport=_bad(make))


def _servers(clock: FakeClock, offsets: dict[str, int | None]) -> Callable[[str, bytes, float], bytes]:
    def transport(host: str, request: bytes, timeout_s: float) -> bytes:
        offset = offsets[host]
        if offset is None:
            raise TimeoutError
        return server(clock, offset)(host, request, timeout_s)

    return transport


def test_time_010_two_servers_within_threshold_pass() -> None:
    clock = FakeClock(START)
    check = check_offsets(["a", "b"], 1_000, clock=clock, transport=_servers(clock, {"a": 120, "b": -1_000}))
    assert check.ok
    assert [r.server for r in check.results] == ["a", "b"]
    assert check.worst_offset_ms == -1_000  # equal to the threshold still passes ("> P-16" stops)
    assert check.errors == ()


def test_time_010_any_answering_server_beyond_threshold_fails() -> None:
    clock = FakeClock(START)
    check = check_offsets(["a", "b"], 1_000, clock=clock, transport=_servers(clock, {"a": 0, "b": 1_001}))
    assert not check.ok
    assert check.worst_offset_ms == 1_001


def test_time_010_fewer_than_two_answering_servers_fails_closed() -> None:
    clock = FakeClock(START)
    check = check_offsets(["a", "b"], 1_000, clock=clock, transport=_servers(clock, {"a": 0, "b": None}))
    assert not check.ok
    assert [r.server for r in check.results] == ["a"]
    assert len(check.errors) == 1
    assert check.errors[0][0] == "b"
    assert "timeout" in check.errors[0][1]


def test_time_010_duplicate_server_names_count_once_and_empty_list_fails() -> None:
    clock = FakeClock(START)
    check = check_offsets(["a", "a"], 1_000, clock=clock, transport=_servers(clock, {"a": 0}))
    assert not check.ok
    assert len(check.results) == 1
    empty = check_offsets([], 1_000, clock=clock, transport=_servers(clock, {}))
    assert not empty.ok
    assert empty.worst_offset_ms is None


def test_check_offsets_rejects_negative_threshold() -> None:
    with pytest.raises(ValueError, match="threshold"):
        check_offsets(["a", "b"], -1)


def test_default_transport_exchanges_one_udp_datagram_on_loopback() -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    srv.bind(("127.0.0.1", 0))
    port = srv.getsockname()[1]

    def answer() -> None:
        data, addr = srv.recvfrom(512)
        srv.sendto(data[::-1], addr)

    thread = threading.Thread(target=answer)
    thread.start()
    try:
        assert _udp_exchange("127.0.0.1", b"abc", 2.0, port=port) == b"cba"
    finally:
        thread.join(timeout=5)
        srv.close()


def test_default_transport_times_out_when_nobody_answers() -> None:
    silent = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    silent.bind(("127.0.0.1", 0))
    try:
        with pytest.raises(TimeoutError):
            _udp_exchange("127.0.0.1", b"x", 0.2, port=silent.getsockname()[1])
    finally:
        silent.close()
