"""Telemetry sensor for the Network Topology SNMP integration.

One sensor per switch. Its state is a quick "<up>/<total> up" summary and its
attributes carry the full per-port telemetry dict consumed by the
network-topology-card. This avoids creating one entity per physical port.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SwitchConfigEntry
from .const import CONF_HOST, CONF_NAME, DOMAIN
from .coordinator import SwitchSnmpCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SwitchConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the telemetry sensor for a switch."""
    async_add_entities([SwitchPortsSensor(entry)])


class SwitchPortsSensor(CoordinatorEntity[SwitchSnmpCoordinator], SensorEntity):
    """Summarizes a switch's port status and exposes the full ports dict."""

    _attr_has_entity_name = True
    _attr_name = "Ports"
    _attr_icon = "mdi:lan"

    def __init__(self, entry: SwitchConfigEntry) -> None:
        super().__init__(entry.runtime_data)
        self._switch_name = entry.data.get(CONF_NAME, entry.data[CONF_HOST])
        self._attr_unique_id = f"{entry.entry_id}_ports"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=self._switch_name,
            manufacturer="Network Topology SNMP",
            configuration_url=f"http://{entry.data[CONF_HOST]}",
        )

    @property
    def native_value(self) -> str | None:
        """A compact link-up summary, e.g. '12/28 up'."""
        data = self.coordinator.data
        if not data:
            return None
        return f"{data.get('up', 0)}/{data.get('total', 0)} up"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the per-port telemetry the card reads via port_map."""
        data = self.coordinator.data or {}
        return {
            "ports": data.get("ports", {}),
            "polled": data.get("polled"),
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()
