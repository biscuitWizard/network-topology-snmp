"""Pure, dependency-free telemetry logic (no HA / pysnmp imports).

Kept import-clean on purpose so it can be unit-tested in isolation and so the
config-flow import chain never depends on SNMP libraries being importable.
"""

from __future__ import annotations

from collections import deque
from datetime import datetime, timedelta

# ifAdminStatus / ifOperStatus enumeration values we care about.
IF_STATUS_UP = 1
IF_STATUS_DOWN = 2

# Port status strings published in telemetry and understood by the card.
STATUS_CONNECTED = "connected"
STATUS_DISCONNECTED = "disconnected"
STATUS_DISABLED = "disabled"
STATUS_FLAPPING = "flapping"


def port_status(
    admin: int | None, oper: int | None, flaps: int, threshold: int
) -> str:
    """Derive the card-facing status string for one interface."""
    if admin is not None and admin != IF_STATUS_UP:
        return STATUS_DISABLED
    if flaps >= threshold:
        return STATUS_FLAPPING
    if oper == IF_STATUS_UP:
        return STATUS_CONNECTED
    return STATUS_DISCONNECTED


def bps(
    prev_ts: float | None,
    prev_val: int | None,
    cur_ts: float,
    cur_val: int | None,
) -> int | None:
    """Bits/sec from two HC octet samples; None on first sample/reset/wrap."""
    if prev_ts is None or prev_val is None or cur_val is None:
        return None
    dt = cur_ts - prev_ts
    if dt <= 0 or cur_val < prev_val:
        return None
    return int((cur_val - prev_val) * 8 / dt)


class FlapDetector:
    """Counts ifOperStatus transitions per interface within a sliding window.

    An advancing ifLastChange between polls is treated as a bounce even when the
    sampled oper value is identical on both polls (the interface changed and
    changed back between our samples).
    """

    def __init__(self, window_s: int, threshold: int) -> None:
        self.window = timedelta(seconds=window_s)
        self.threshold = threshold
        self._history: dict[int, deque[tuple[datetime, int]]] = {}
        self._prev_last_change: dict[int, int] = {}

    def update(
        self,
        index: int,
        oper: int | None,
        last_change: int | None,
        now: datetime,
    ) -> int:
        """Record a sample and return the flap count currently in the window."""
        history = self._history.setdefault(index, deque())

        bounced = (
            last_change is not None
            and index in self._prev_last_change
            and last_change != self._prev_last_change[index]
        )
        if last_change is not None:
            self._prev_last_change[index] = last_change

        if oper is not None:
            if not history or history[-1][1] != oper:
                history.append((now, oper))
            elif bounced:
                history.append((now, oper))

        cutoff = now - self.window
        while history and history[0][0] < cutoff:
            history.popleft()

        # Every appended entry after the first represents one flap event:
        # either a value transition or a same-value bounce.
        return max(len(history) - 1, 0)

    def is_flapping(self, flaps: int) -> bool:
        return flaps >= self.threshold
