# Network Topology SNMP

[![HACS custom repository](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=biscuitWizard&repository=network-topology-snmp&category=integration)
[![GitHub](https://img.shields.io/badge/GitHub-network--topology--snmp-blue?logo=github)](https://github.com/biscuitWizard/network-topology-snmp)

Home Assistant custom integration for live switch-port telemetry in the
[Network Topology Card](https://github.com/biscuitWizard/network-topology-card).
The integration domain is `network_topology_snmp`.

It polls SNMP v2c IF-MIB data from each configured switch and creates one
telemetry sensor per switch, for example `sensor.core_switch_ports`. The sensor
state is a compact link summary such as `12/28 up`, and the `ports` attribute is
keyed by SNMP `ifName` for card port mapping.

## Quick Start

1. Add this repository to HACS as a custom integration repository:
   `https://github.com/biscuitWizard/network-topology-snmp`.
2. Install **Network Topology SNMP** from HACS.
3. Restart Home Assistant.
4. Go to **Settings > Devices & services > Add integration** and search for
   **Network Topology SNMP**.
5. Enter the switch details:
   `host`, `community`, `port`, `name`, `scan_interval`,
   `flap_window`, and `flap_threshold`.
6. Add the telemetry sensor to a Network Topology Card device with
   `telemetry_entity` and map card port IDs to SNMP `ifName` values with
   `port_map`.

## What It Creates

Each config entry represents one SNMP-polled switch. The integration creates a
single sensor entity for that switch:

- Entity name: `<switch name> Ports`
- Typical entity ID: `sensor.<switch_name>_ports`
- State: `<connected>/<total> up`
- Attributes: `ports` and `polled`

The `ports` attribute is a dictionary keyed by `ifName`. Each port includes the
card-facing status plus raw and derived telemetry such as admin/oper state,
speed, alias, bits-per-second counters, and flap count.

## SNMP Requirements

The switch must expose IF-MIB over SNMP v2c from the Home Assistant host. The
integration walks numeric OIDs, so Home Assistant does not need local MIB files.
At minimum, the switch should return `ifName`, `ifAdminStatus`, and
`ifOperStatus`; richer cards benefit from `ifAlias`, `ifHighSpeed`,
`ifHCInOctets`, and `ifHCOutOctets`.

The integration uses community-based SNMP v2c only. SNMP v3 is not currently
supported.

## Pairing With The Card

Install the companion
[Network Topology Card](https://github.com/biscuitWizard/network-topology-card),
then point a switch device at the telemetry sensor:

```yaml
type: custom:network-topology-card
devices:
  - id: core
    name: Core Switch
    template: cisco-4500x
    telemetry_entity: sensor.core_switch_ports
    port_map:
      "1": Te1/1
      "2": Te1/2
      "3": Te1/3
```

`port_map` maps the card's visual port IDs to SNMP `ifName` values. Verify the
exact `ifName` strings with the integration sensor attributes, `snmpwalk`, or
`scripts/validate_snmp.py`.

## Documentation

- [Installation](docs/installation.md)
- [Configuration](docs/configuration.md)
- [Telemetry Schema](docs/telemetry-schema.md)
- [Flapping Detection](docs/flapping.md)
- [Troubleshooting](docs/troubleshooting.md)

## Examples

- [Card live status snippet](examples/card-live-status.yaml)
- [snmpwalk cheatsheet](examples/snmpwalk-cheatsheet.md)
- [validate_snmp.py usage](examples/validate_snmp-usage.md)

