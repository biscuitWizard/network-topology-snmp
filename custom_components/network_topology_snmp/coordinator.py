"""SNMP polling coordinator for the Network Topology SNMP integration.

Walks the IF-MIB over SNMP v2c and builds a per-port telemetry dict keyed by
``ifName``. The pysnmp import is deliberately lazy and version-tolerant so that
importing this module (e.g. from the config flow) never fails just because the
SNMP library is a different major version or not yet installed.
"""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .compute import FlapDetector, bps, port_status
from .const import (
    DEFAULT_FLAP_THRESHOLD,
    DEFAULT_FLAP_WINDOW,
    OID_IF_ADMIN_STATUS,
    OID_IF_ALIAS,
    OID_IF_DESCR,
    OID_IF_HC_IN_OCTETS,
    OID_IF_HC_OUT_OCTETS,
    OID_IF_HIGH_SPEED,
    OID_IF_LAST_CHANGE,
    OID_IF_NAME,
    OID_IF_OPER_STATUS,
    STATUS_CONNECTED,
)

_LOGGER = logging.getLogger(__name__)

# Columns walked each poll, mapped to the per-port key we expose.
_COLUMNS: dict[str, str] = {
    "name": OID_IF_NAME,
    "descr": OID_IF_DESCR,
    "alias": OID_IF_ALIAS,
    "admin": OID_IF_ADMIN_STATUS,
    "oper": OID_IF_OPER_STATUS,
    "speed": OID_IF_HIGH_SPEED,
    "last_change": OID_IF_LAST_CHANGE,
    "in_octets": OID_IF_HC_IN_OCTETS,
    "out_octets": OID_IF_HC_OUT_OCTETS,
}

# Lazily-populated pysnmp symbol bundle (see _snmp()).
_SNMP: dict[str, Any] | None = None


class SnmpError(Exception):
    """Raised when the switch cannot be reached or returns no interfaces."""


def _snmp() -> dict[str, Any]:
    """Import pysnmp lazily, tolerating both 5.x and 6.x hlapi layouts."""
    global _SNMP
    if _SNMP is not None:
        return _SNMP

    try:
        from pysnmp.hlapi.asyncio import (  # type: ignore
            CommunityData,
            ContextData,
            ObjectIdentity,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
        )

        try:
            from pysnmp.hlapi.asyncio import bulkCmd  # type: ignore
        except ImportError:  # pysnmp 6.x snake_case
            from pysnmp.hlapi.asyncio import bulk_cmd as bulkCmd  # type: ignore
    except ImportError:
        # pysnmp 6.x reorganized hlapi under v3arch.
        from pysnmp.hlapi.v3arch.asyncio import (  # type: ignore
            CommunityData,
            ContextData,
            ObjectIdentity,
            ObjectType,
            SnmpEngine,
            UdpTransportTarget,
        )

        try:
            from pysnmp.hlapi.v3arch.asyncio import bulkCmd  # type: ignore
        except ImportError:
            from pysnmp.hlapi.v3arch.asyncio import bulk_cmd as bulkCmd  # type: ignore

    _SNMP = {
        "CommunityData": CommunityData,
        "ContextData": ContextData,
        "ObjectIdentity": ObjectIdentity,
        "ObjectType": ObjectType,
        "SnmpEngine": SnmpEngine,
        "UdpTransportTarget": UdpTransportTarget,
        "bulkCmd": bulkCmd,
    }
    return _SNMP


async def _make_target(host: str, port: int, timeout: int, retries: int) -> Any:
    """Build a UdpTransportTarget across pysnmp 5.x (sync) and 6.x (async)."""
    udp = _snmp()["UdpTransportTarget"]
    create = getattr(udp, "create", None)
    if create is not None:  # pysnmp 6.x: async factory (resolves DNS off-loop)
        return await create((host, port), timeout=timeout, retries=retries)
    return udp((host, port), timeout=timeout, retries=retries)  # pysnmp 5.x


def _last_oid_subid(oid: Any) -> int | None:
    """Return the final sub-identifier (the ifIndex) of an OID."""
    try:
        return int(oid[-1])
    except (TypeError, ValueError, IndexError):
        return None


async def _walk_column(
    engine: Any, community: Any, target: Any, base_oid: str
) -> dict[int, Any]:
    """Walk a single IF-MIB column, returning {ifIndex: value}."""
    snmp = _snmp()
    bulk_cmd = snmp["bulkCmd"]
    object_type = snmp["ObjectType"]
    object_identity = snmp["ObjectIdentity"]
    context = snmp["ContextData"]()

    results: dict[int, Any] = {}
    base_tuple = tuple(int(p) for p in base_oid.split("."))
    var = object_type(object_identity(base_oid))

    # Safety cap: even huge chassis stay well under this many bulk rounds.
    for _ in range(512):
        error_indication, error_status, _error_index, var_binds = await bulk_cmd(
            engine, community, target, context, 0, 25, var
        )
        if error_indication:
            raise SnmpError(str(error_indication))
        if error_status:
            raise SnmpError(error_status.prettyPrint())
        if not var_binds:
            break

        last_oid = None
        for oid, value in var_binds:
            oid_tuple = tuple(oid)
            if oid_tuple[: len(base_tuple)] != base_tuple:
                return results  # left the requested subtree
            index = _last_oid_subid(oid_tuple)
            if index is not None:
                results[index] = value
            last_oid = oid

        if last_oid is None:
            break
        var = object_type(object_identity(last_oid))

    return results


async def async_probe_switch(
    hass: HomeAssistant, host: str, port: int, community: str
) -> None:
    """Lightweight reachability check used by the config flow."""
    snmp = _snmp()
    engine = snmp["SnmpEngine"]()
    community_data = snmp["CommunityData"](community, mpModel=1)  # v2c
    target = await _make_target(host, port, timeout=4, retries=1)
    names = await _walk_column(engine, community_data, target, OID_IF_NAME)
    if not names:
        raise SnmpError("no interfaces returned")


class SwitchSnmpCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls one switch and produces a {ports: {...}} telemetry payload."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        name: str,
        host: str,
        port: int,
        community: str,
        scan_interval: int,
        flap_window: int = DEFAULT_FLAP_WINDOW,
        flap_threshold: int = DEFAULT_FLAP_THRESHOLD,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{name} SNMP",
            update_interval=timedelta(seconds=scan_interval),
        )
        self._host = host
        self._port = port
        self._community = community
        self._flap_threshold = flap_threshold
        self._flaps = FlapDetector(flap_window, flap_threshold)
        self._prev_octets: dict[int, tuple[float, int, int]] = {}
        self._engine: Any = None

    async def _async_update_data(self) -> dict[str, Any]:
        snmp = _snmp()
        if self._engine is None:
            self._engine = snmp["SnmpEngine"]()
        community = snmp["CommunityData"](self._community, mpModel=1)
        try:
            target = await _make_target(self._host, self._port, timeout=5, retries=1)
            columns = {
                key: await _walk_column(self._engine, community, target, oid)
                for key, oid in _COLUMNS.items()
            }
        except SnmpError as err:
            raise UpdateFailed(str(err)) from err
        except Exception as err:  # noqa: BLE001 - surface pysnmp quirks cleanly
            raise UpdateFailed(f"SNMP poll failed: {err}") from err

        names = columns["name"]
        if not names:
            raise UpdateFailed("no interfaces returned")

        now = dt_util.utcnow()
        ports: dict[str, Any] = {}
        up_count = 0

        for index, raw_name in names.items():
            if_name = str(raw_name)
            admin = _to_int(columns["admin"].get(index))
            oper = _to_int(columns["oper"].get(index))
            speed = _to_int(columns["speed"].get(index))
            last_change = _to_int(columns["last_change"].get(index))
            in_octets = _to_int(columns["in_octets"].get(index))
            out_octets = _to_int(columns["out_octets"].get(index))

            flaps = self._flaps.update(index, oper, last_change, now)
            status = port_status(admin, oper, flaps, self._flap_threshold)
            if status == STATUS_CONNECTED:
                up_count += 1

            in_bps, out_bps = self._throughput(index, in_octets, out_octets, now)

            ports[if_name] = {
                "status": status,
                "oper": "up" if oper == 1 else "down",
                "admin": "up" if admin == 1 else "down",
                "speed": speed,
                "alias": str(columns["alias"].get(index, "")) or None,
                "descr": str(columns["descr"].get(index, "")) or None,
                "in_bps": in_bps,
                "out_bps": out_bps,
                "flaps": flaps,
                "if_index": index,
            }

        return {
            "ports": ports,
            "up": up_count,
            "total": len(ports),
            "polled": now.isoformat(),
        }

    def _throughput(
        self, index: int, in_octets: int | None, out_octets: int | None, now
    ) -> tuple[int | None, int | None]:
        ts = now.timestamp()
        prev = self._prev_octets.get(index)
        prev_ts = prev[0] if prev else None
        in_bps = bps(prev_ts, prev[1] if prev else None, ts, in_octets)
        out_bps = bps(prev_ts, prev[2] if prev else None, ts, out_octets)
        if in_octets is not None and out_octets is not None:
            self._prev_octets[index] = (ts, in_octets, out_octets)
        return in_bps, out_bps


def _to_int(value: Any) -> int | None:
    """Best-effort conversion of a pysnmp value to int."""
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
