# Installation

Network Topology SNMP is a Home Assistant custom integration with the domain
`network_topology_snmp`.

Repository:
`https://github.com/biscuitWizard/network-topology-snmp`

Companion card:
`https://github.com/biscuitWizard/network-topology-card`

## HACS

1. Open HACS in Home Assistant.
2. Add a custom repository:
   `https://github.com/biscuitWizard/network-topology-snmp`
3. Select the repository type **Integration**.
4. Install **Network Topology SNMP**.
5. Restart Home Assistant.
6. Add the integration from **Settings > Devices & services > Add integration**.

## Manual Install

HACS is recommended. For manual testing, deploy the integration directory to:

```text
/config/custom_components/network_topology_snmp
```

Restart Home Assistant after copying the files. If the integration does not
appear in the UI, run the helper described in
[`examples/validate_snmp-usage.md`](../examples/validate_snmp-usage.md) from
inside the Home Assistant environment.

## Requirements

- Home Assistant can reach the switch management IP or hostname.
- The switch allows SNMP v2c from the Home Assistant host.
- The configured community string can read IF-MIB.
- UDP port `161` is reachable unless you configure a different SNMP port.

