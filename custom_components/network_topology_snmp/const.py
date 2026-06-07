"""Constants for the Network Topology SNMP integration."""

from __future__ import annotations

# Re-export the dependency-free constants so the rest of the package has a
# single import site. (compute.py owns them so it stays unit-testable alone.)
from .compute import (  # noqa: F401
    IF_STATUS_DOWN,
    IF_STATUS_UP,
    STATUS_CONNECTED,
    STATUS_DISABLED,
    STATUS_DISCONNECTED,
    STATUS_FLAPPING,
)

DOMAIN = "network_topology_snmp"

# Config / options keys.
CONF_HOST = "host"
CONF_PORT = "port"
CONF_COMMUNITY = "community"
CONF_NAME = "name"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_FLAP_WINDOW = "flap_window"
CONF_FLAP_THRESHOLD = "flap_threshold"

# Defaults.
DEFAULT_PORT = 161
DEFAULT_COMMUNITY = "public"
DEFAULT_SCAN_INTERVAL = 20  # seconds
DEFAULT_FLAP_WINDOW = 300  # seconds
DEFAULT_FLAP_THRESHOLD = 3  # oper transitions within the window

# IF-MIB / IF-MIB extension (numeric OIDs avoid MIB compilation at runtime).
OID_IF_DESCR = "1.3.6.1.2.1.2.2.1.2"
OID_IF_ADMIN_STATUS = "1.3.6.1.2.1.2.2.1.7"
OID_IF_OPER_STATUS = "1.3.6.1.2.1.2.2.1.8"
OID_IF_LAST_CHANGE = "1.3.6.1.2.1.2.2.1.9"
OID_IF_IN_ERRORS = "1.3.6.1.2.1.2.2.1.14"
OID_IF_OUT_ERRORS = "1.3.6.1.2.1.2.2.1.20"
OID_IF_NAME = "1.3.6.1.2.1.31.1.1.1.1"
OID_IF_HC_IN_OCTETS = "1.3.6.1.2.1.31.1.1.1.6"
OID_IF_HC_OUT_OCTETS = "1.3.6.1.2.1.31.1.1.1.10"
OID_IF_HIGH_SPEED = "1.3.6.1.2.1.31.1.1.1.15"
OID_IF_ALIAS = "1.3.6.1.2.1.31.1.1.1.18"
