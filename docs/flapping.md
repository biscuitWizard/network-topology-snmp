# Flapping Detection

The integration tracks interface instability so the Network Topology Card can
show a port as `flapping` instead of simply alternating between `connected` and
`disconnected`.

## Options

Flap behavior is controlled by two options:

- `flap_window`: sliding window in seconds. Default: `300`.
- `flap_threshold`: number of transitions in that window before the port is
  marked `flapping`. Default: `3`.

These values are configured during setup and can be changed later from the
integration options flow.

## What Counts As A Flap

The integration records samples by IF-MIB `ifIndex`.

A flap event is counted when:

- `ifOperStatus` changes between polls.
- `ifLastChange` advances between polls even when the sampled `ifOperStatus`
  value is the same. This catches down/up or up/down bounces that happened
  between polling intervals.

Events older than `flap_window` are pruned from the in-memory history. The
published `flaps` field is the current count inside that window.

## Status Precedence

Status is derived in this order:

1. `disabled` if `ifAdminStatus` is not up.
2. `flapping` if the current flap count is greater than or equal to
   `flap_threshold`.
3. `connected` if `ifOperStatus` is up.
4. `disconnected` otherwise.

In practice, `flapping` overrides the normal connected/disconnected result for
admin-up ports. Admin-down ports remain `disabled`.

## Tuning Guidance

Shorter polling intervals detect transitions sooner and produce more timely
`in_bps`/`out_bps` values. Longer intervals reduce switch and Home Assistant
load.

If brief maintenance or cable moves produce too many flap warnings, increase
`flap_threshold` or reduce how long events stay relevant by lowering
`flap_window`. If short bounces are being missed, lower `scan_interval`.

