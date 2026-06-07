# validate_snmp.py Usage

`scripts/validate_snmp.py` is a helper for checking the deployed integration
inside the Home Assistant Python environment. Run it in the Home Assistant
container or virtual environment so it can import Home Assistant and `pysnmp` as
Home Assistant sees them.

## Import And Dependency Check

From the repository checkout or another location that has the script:

```bash
python3 scripts/validate_snmp.py --component /config/custom_components/network_topology_snmp
```

If the integration is deployed at the default path and the script is run from an
environment where `/config/custom_components/network_topology_snmp` exists, the
`--component` argument can be omitted:

```bash
python3 scripts/validate_snmp.py
```

This checks:

- The integration package imports.
- `config_flow` imports, which verifies the config flow handler can register.
- The version-tolerant `pysnmp` binding resolves the expected symbols.

## Live Switch Probe

Add `--host` to walk `ifName` from a real switch over SNMP v2c:

```bash
python3 scripts/validate_snmp.py \
  --component /config/custom_components/network_topology_snmp \
  --host 10.0.1.2 \
  --port 161 \
  --community public
```

Expected output includes the number of interfaces returned and a list of
`ifIndex` to `ifName` values. Use those `ifName` values in the Network Topology
Card `port_map`.

## Exit Codes

- `0`: checks passed.
- `2`: integration import chain failed.
- `3`: `pysnmp` could not be imported or bound.
- `4`: live SNMP probe raised an error.
- `5`: live SNMP probe returned zero interfaces.

Avoid pasting real community strings into issue reports or chat logs.

