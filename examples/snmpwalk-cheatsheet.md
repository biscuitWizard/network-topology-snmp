# snmpwalk Cheatsheet

Use these commands from the Home Assistant host or from another machine with the
same network path to the switch. Replace `<community>` and `<host>`.

The integration uses SNMP v2c:

```bash
snmpwalk -v2c -c <community> <host> 1.3.6.1.2.1.31.1.1.1.1
```

## Core IF-MIB Checks

Verify interface names. These values are the keys used in
`sensor.<name>_ports` attributes and in the card `port_map`.

```bash
snmpwalk -v2c -c <community> <host> 1.3.6.1.2.1.31.1.1.1.1
```

Verify admin status:

```bash
snmpwalk -v2c -c <community> <host> 1.3.6.1.2.1.2.2.1.7
```

Verify oper status:

```bash
snmpwalk -v2c -c <community> <host> 1.3.6.1.2.1.2.2.1.8
```

Verify last change values used for bounce/flap detection:

```bash
snmpwalk -v2c -c <community> <host> 1.3.6.1.2.1.2.2.1.9
```

## Helpful Enrichment Columns

Interface descriptions:

```bash
snmpwalk -v2c -c <community> <host> 1.3.6.1.2.1.2.2.1.2
```

Interface aliases:

```bash
snmpwalk -v2c -c <community> <host> 1.3.6.1.2.1.31.1.1.1.18
```

High-speed interface values, normally Mbps:

```bash
snmpwalk -v2c -c <community> <host> 1.3.6.1.2.1.31.1.1.1.15
```

High-capacity octet counters used for `in_bps` and `out_bps`:

```bash
snmpwalk -v2c -c <community> <host> 1.3.6.1.2.1.31.1.1.1.6
snmpwalk -v2c -c <community> <host> 1.3.6.1.2.1.31.1.1.1.10
```

Error counters are useful when diagnosing switch-side issues, even though the
current telemetry payload does not publish normalized error fields:

```bash
snmpwalk -v2c -c <community> <host> 1.3.6.1.2.1.2.2.1.14
snmpwalk -v2c -c <community> <host> 1.3.6.1.2.1.2.2.1.20
```

## Expected Results

`ifName` should return at least one interface. If it returns no rows or times
out, the Home Assistant config flow will also fail because setup uses the same
SNMP v2c IF-MIB reachability check.

Remove community strings and private addresses before sharing command output.

