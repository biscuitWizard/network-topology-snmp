# Configuration

Each config entry represents one SNMP-polled switch. The integration probes the
switch during setup by walking IF-MIB `ifName` over SNMP v2c.

## Setup Fields

| Field | Default | Notes |
| --- | --- | --- |
| `name` | empty | Friendly switch name. If blank, the host is used. |
| `host` | required | Switch IP address or hostname. |
| `port` | `161` | SNMP UDP port. |
| `community` | `public` | SNMP v2c community string. |
| `scan_interval` | `20` | Poll interval in seconds. Valid range: `5` to `600`. |
| `flap_window` | `300` | Sliding flap detection window in seconds. Valid range: `30` to `3600`. |
| `flap_threshold` | `3` | Transitions in the window before a port is `flapping`. Valid range: `2` to `50`. |

The setup flow stores connection details (`host`, `port`, `community`, `name`)
as entry data. Polling and flap tuning (`scan_interval`, `flap_window`,
`flap_threshold`) are entry options.

## Options Flow

After setup, open the integration entry options to tune:

- `scan_interval`
- `flap_window`
- `flap_threshold`

Changing options reloads the entry so the coordinator uses the new polling
cadence and flap detector settings.

## SNMP Data Used

The integration walks IF-MIB and IF-MIB extension columns by numeric OID. Local
MIB files are not required on the Home Assistant host.

Current polling uses:

- `ifName`
- `ifDescr`
- `ifAlias`
- `ifAdminStatus`
- `ifOperStatus`
- `ifHighSpeed`
- `ifLastChange`
- `ifHCInOctets`
- `ifHCOutOctets`

`ifName` is the key used in the telemetry payload. Use the exact returned value
when building a Network Topology Card `port_map`.

## Pairing With Network Topology Card

Install the companion card from:
`https://github.com/biscuitWizard/network-topology-card`

In the card config, put `telemetry_entity` on the switch device and map visual
port IDs to SNMP `ifName` values:

```yaml
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

See [`../examples/card-live-status.yaml`](../examples/card-live-status.yaml) for
a fuller snippet.

