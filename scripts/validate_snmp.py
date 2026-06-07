#!/usr/bin/env python3
"""Authoritative validation for the Network Topology SNMP integration.

Run this INSIDE the Home Assistant environment (the container/venv that runs
HA), because it relies on HA's bundled `homeassistant` and `pysnmp`.

What it checks:
  1. Import chain  - imports the integration exactly as HA does. If this fails,
     that is the cause of "Config flow could not be loaded: Invalid handler
     specified". A clean pass means the config flow will register.
  2. pysnmp shape  - prints the resolved pysnmp version and confirms the
     version-tolerant SNMP layer binds correctly.
  3. Live probe    - (optional) walks ifName on a real switch over SNMP v2c.

Examples:
  # import-chain + pysnmp checks only
  python3 validate_snmp.py

  # also probe a real switch
  python3 validate_snmp.py --host 10.0.1.2 --community public
"""

from __future__ import annotations

import argparse
import asyncio
import importlib
import os
import sys


def _load_package(component_dir: str):
    """Import the integration as the package `network_topology_snmp`."""
    component_dir = os.path.abspath(component_dir)
    parent = os.path.dirname(component_dir)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    pkg_name = os.path.basename(component_dir)
    return importlib.import_module(pkg_name)


async def _probe(coordinator_mod, host: str, port: int, community: str) -> int:
    snmp = coordinator_mod._snmp()
    engine = snmp["SnmpEngine"]()
    comm = snmp["CommunityData"](community, mpModel=1)  # v2c
    target = await coordinator_mod._make_target(host, port, timeout=5, retries=1)
    from network_topology_snmp.const import OID_IF_NAME  # type: ignore

    names = await coordinator_mod._walk_column(engine, comm, target, OID_IF_NAME)
    print(f"[probe] {host}:{port} returned {len(names)} interfaces")
    for idx in sorted(names):
        print(f"        ifIndex {idx}: {names[idx]}")
    return len(names)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--component",
        default="/config/custom_components/network_topology_snmp",
        help="Path to the deployed integration directory.",
    )
    ap.add_argument("--host", help="Switch IP/hostname for an optional live probe.")
    ap.add_argument("--port", type=int, default=161)
    ap.add_argument("--community", default="public")
    args = ap.parse_args()

    print("== 1. Import chain ==")
    try:
        pkg = _load_package(args.component)
        importlib.import_module(f"{pkg.__name__}.config_flow")
        coordinator = importlib.import_module(f"{pkg.__name__}.coordinator")
        print("[ok] integration + config_flow imported cleanly "
              "(config flow handler will register)")
    except Exception as err:  # noqa: BLE001
        print(f"[FAIL] import chain broke: {type(err).__name__}: {err}")
        import traceback

        traceback.print_exc()
        return 2

    print("\n== 2. pysnmp ==")
    try:
        import pysnmp  # type: ignore

        print(f"[ok] pysnmp version: {getattr(pysnmp, '__version__', 'unknown')}")
        snmp = coordinator._snmp()
        print(f"[ok] bound symbols: {', '.join(sorted(snmp))}")
        udp = snmp["UdpTransportTarget"]
        mode = "6.x async (.create)" if hasattr(udp, "create") else "5.x sync ctor"
        print(f"[ok] transport target mode: {mode}")
    except Exception as err:  # noqa: BLE001
        print(f"[FAIL] pysnmp unusable: {type(err).__name__}: {err}")
        import traceback

        traceback.print_exc()
        return 3

    if not args.host:
        print("\n== 3. Live probe == skipped (pass --host to enable)")
        print("\nResult: import chain OK -> config flow will load.")
        return 0

    print("\n== 3. Live probe ==")
    try:
        count = asyncio.run(_probe(coordinator, args.host, args.port, args.community))
    except Exception as err:  # noqa: BLE001
        print(f"[FAIL] probe error: {type(err).__name__}: {err}")
        import traceback

        traceback.print_exc()
        return 4
    if count == 0:
        print("[FAIL] switch reachable path but returned 0 interfaces "
              "(check community string / v2c enabled)")
        return 5
    print("\nResult: import chain OK and live SNMP probe succeeded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
