"""Minimal SNTP v4 client over stdlib UDP (TIME-010; RFC 4330 offset and delay).

The request carries a random 64-bit nonce in the transmit field and zeros elsewhere (no local
time leaves the host); the reply must echo it. The round-trip is measured on monotonic time, so a
wall-clock jump during a query changes neither result (TIME-015).
"""

from __future__ import annotations

import os
import socket
import struct
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from goldbot.core.clock import Clock, SystemClock

NTP_PORT = 123
_NTP_EPOCH = datetime(1900, 1, 1, tzinfo=UTC)
_NS = 1_000_000_000
_REQUEST_HEAD = bytes([0x23]) + bytes(39)  # LI 0, version 4, mode 3 (client)

Transport = Callable[[str, bytes, float], bytes]


class NtpError(Exception):
    """The server did not answer in time, or answered with an unusable reply."""


@dataclass(frozen=True)
class NtpResult:
    server: str
    offset_ms: int
    rtt_ms: int


@dataclass(frozen=True)
class OffsetCheck:
    ok: bool
    results: tuple[NtpResult, ...]
    errors: tuple[tuple[str, str], ...]
    worst_offset_ms: int | None


def _udp_exchange(server: str, request: bytes, timeout_s: float, *, port: int = NTP_PORT) -> bytes:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout_s)
        sock.connect((server, port))  # the OS then drops datagrams from any other address
        sock.send(request)
        return sock.recv(512)


def _to_ns(ts: bytes) -> int:
    secs, frac = struct.unpack("!II", ts)
    return secs * _NS + (frac * _NS >> 32)


def _round_ms(ns: int) -> int:
    return (ns + 500_000) // 1_000_000


def query_offset(
    server: str, timeout_s: float = 2.0, *, clock: Clock | None = None, transport: Transport | None = None
) -> NtpResult:
    """Offset of the server clock relative to ``clock.utc_now()`` (positive: local clock is behind)."""
    clock = clock or SystemClock()
    nonce = os.urandom(8)
    t1 = (clock.utc_now() - _NTP_EPOCH) // timedelta(microseconds=1) * 1000
    m1 = clock.monotonic_ns()
    try:
        data = (transport or _udp_exchange)(server, _REQUEST_HEAD + nonce, timeout_s)
    except TimeoutError as exc:
        raise NtpError(f"{server}: timeout after {timeout_s} s") from exc
    except OSError as exc:
        raise NtpError(f"{server}: {exc}") from exc
    t4 = t1 + clock.monotonic_ns() - m1

    if len(data) < 48:
        raise NtpError(f"{server}: reply length {len(data)} < 48")
    li, mode, stratum = data[0] >> 6, data[0] & 0x7, data[1]
    if mode != 4:
        raise NtpError(f"{server}: reply mode {mode} is not server (4)")
    if not 1 <= stratum <= 15:
        raise NtpError(f"{server}: stratum {stratum} (kiss-of-death or invalid)")
    if li == 3:
        raise NtpError(f"{server}: server clock is unsynchronised (LI=3)")
    if data[24:32] != nonce:
        raise NtpError(f"{server}: origin timestamp does not echo the request")
    if data[40:48] == bytes(8):
        raise NtpError(f"{server}: transmit timestamp is zero")

    t2, t3 = _to_ns(data[32:40]), _to_ns(data[40:48])
    offset = ((t2 - t1) + (t3 - t4)) // 2
    rtt = max(0, (t4 - t1) - (t3 - t2))
    return NtpResult(server=server, offset_ms=_round_ms(offset), rtt_ms=_round_ms(rtt))


def check_offsets(
    servers: Iterable[str],
    threshold_ms: int,
    *,
    timeout_s: float = 2.0,
    clock: Clock | None = None,
    transport: Transport | None = None,
) -> OffsetCheck:
    """TIME-010: pass only if at least two distinct servers answered and none is beyond ``threshold_ms``.

    Fail closed: any answering server beyond the threshold fails the check (the worst offset counts,
    not the median), and fewer than two answers fail it too.
    """
    if threshold_ms < 0:
        raise ValueError("threshold_ms must not be negative")
    results: list[NtpResult] = []
    errors: list[tuple[str, str]] = []
    for server in dict.fromkeys(servers):
        try:
            results.append(query_offset(server, timeout_s, clock=clock, transport=transport))
        except NtpError as exc:
            errors.append((server, str(exc)))
    worst = max((r.offset_ms for r in results), key=abs, default=None)
    ok = len(results) >= 2 and worst is not None and abs(worst) <= threshold_ms
    return OffsetCheck(ok=ok, results=tuple(results), errors=tuple(errors), worst_offset_ms=worst)
