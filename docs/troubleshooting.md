# Troubleshooting

Start by confirming that Home Assistant can reach the switch over SNMP v2c and
that IF-MIB returns interface names.

## Config Flow Cannot Connect

The setup flow probes `ifName` before creating the entry. If setup reports that
it cannot connect:

- Verify the switch management IP or hostname in `host`.
- Verify UDP `port`, usually `161`.
- Verify the SNMP v2c `community` string.
- Confirm the switch allows SNMP from the Home Assistant host.
- Confirm firewalls allow UDP traffic between Home Assistant and the switch.
- Run the `snmpwalk` checks in
  [`../examples/snmpwalk-cheatsheet.md`](../examples/snmpwalk-cheatsheet.md).

## Config Flow Could Not Be Loaded

This usually points to a Python import or dependency problem inside the Home
Assistant environment. From a checkout or mounted copy of this repository, pass
the deployed component path:

```bash
python3 scripts/validate_snmp.py --component /config/custom_components/network_topology_snmp
```

See [`../examples/validate_snmp-usage.md`](../examples/validate_snmp-usage.md)
for the expected checks.

## Sensor Exists But No Live Card Status

Check the sensor attributes in Home Assistant Developer Tools.

The card mapping must use SNMP `ifName` keys from `attributes.ports`:

```yaml
telemetry_entity: sensor.core_switch_ports
port_map:
  "1": Te1/1
```

If the switch reports a different `ifName`, update `port_map` to match exactly.
Common vendor differences include `Te1/1`, `TenGigabitEthernet1/1`, `Gi1/0/1`,
or `GigabitEthernet1/0/1`.

## Throughput Is Null

`in_bps` and `out_bps` are calculated from high-capacity octet counters. They
are `null` on the first sample because there is no previous counter value. They
can also be `null` after counter reset, wrap, restart, or if the switch does not
return `ifHCInOctets`/`ifHCOutOctets`.

Wait for a second successful poll. If values remain `null`, verify the HC octet
OIDs with `snmpwalk`.

## Ports Show Disabled

`disabled` means `ifAdminStatus` is not up. Enable the interface on the switch
if it should be considered active.

## Ports Show Flapping

Review [`flapping.md`](flapping.md). A port is `flapping` when its transition
count in `flap_window` reaches `flap_threshold`. `ifLastChange` can also reveal
bounces that happen between polls.

## Useful Debug Checks

- `snmpwalk -v2c -c <community> <host> 1.3.6.1.2.1.31.1.1.1.1`
- `snmpwalk -v2c -c <community> <host> 1.3.6.1.2.1.2.2.1.7`
- `snmpwalk -v2c -c <community> <host> 1.3.6.1.2.1.2.2.1.8`
- `python3 scripts/validate_snmp.py --host <host> --community <community>`

Remove community strings, private IPs, and other sensitive details before
sharing logs or issue reports.

