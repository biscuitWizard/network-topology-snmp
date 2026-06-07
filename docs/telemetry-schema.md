# Telemetry Schema

The integration creates one sensor per configured switch. It does not create one
entity per physical port.

## Sensor

Typical entity ID:

```text
sensor.<switch_name>_ports
```

State:

```text
<connected>/<total> up
```

Example:

```text
12/28 up
```

Attributes:

- `ports`: dictionary keyed by SNMP `ifName`
- `polled`: ISO timestamp for the last successful poll

## Ports Attribute

`attributes.ports` is keyed by `ifName`, not by card port ID or `ifIndex`.

Example:

```yaml
ports:
  Te1/1:
    status: connected
    oper: up
    admin: up
    speed: 10000
    alias: Uplink to firewall
    descr: TenGigabitEthernet1/1
    in_bps: 123456
    out_bps: 789012
    flaps: 0
    if_index: 1
```

Current fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `status` | string | Card-facing status: `connected`, `disconnected`, `disabled`, or `flapping`. |
| `oper` | string | `up` when `ifOperStatus` is `1`; otherwise `down`. |
| `admin` | string | `up` when `ifAdminStatus` is `1`; otherwise `down`. |
| `speed` | number or null | `ifHighSpeed`, normally Mbps. |
| `alias` | string or null | `ifAlias`, often the interface description configured on the switch. |
| `descr` | string or null | `ifDescr`. |
| `in_bps` | number or null | Derived from `ifHCInOctets`; `null` on first sample, counter reset, or wrap. |
| `out_bps` | number or null | Derived from `ifHCOutOctets`; `null` on first sample, counter reset, or wrap. |
| `flaps` | number | Counted oper transitions/bounces in the configured flap window. |
| `if_index` | number | Numeric IF-MIB `ifIndex`. |

Optional card-compatible fields may appear in future or diagnostic payloads:

| Field | Meaning |
| --- | --- |
| `errors` | Interface error counters or a normalized error summary, if published. |
| `last_change` | `ifLastChange`, if published. The current integration uses it internally for flap detection. |

## Status Rules

The integration derives `status` in this order:

1. `disabled` when admin state is not up.
2. `flapping` when the flap count is at or above `flap_threshold`.
3. `connected` when oper state is up.
4. `disconnected` otherwise.

An administratively disabled port remains `disabled` even if flap history exists.

## Card Mapping

The Network Topology Card reads the telemetry sensor with `telemetry_entity`.
`port_map` maps visual card port IDs to SNMP `ifName` keys:

```yaml
telemetry_entity: sensor.core_switch_ports
port_map:
  "1": Te1/1
  "2": Te1/2
```

If a mapped `ifName` is missing from `attributes.ports`, the card cannot apply
live status to that visual port.

