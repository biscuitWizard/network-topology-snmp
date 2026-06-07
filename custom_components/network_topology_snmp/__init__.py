"""The Network Topology SNMP integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_COMMUNITY,
    CONF_FLAP_THRESHOLD,
    CONF_FLAP_WINDOW,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_FLAP_THRESHOLD,
    DEFAULT_FLAP_WINDOW,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import SwitchSnmpCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

SwitchConfigEntry = ConfigEntry[SwitchSnmpCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: SwitchConfigEntry) -> bool:
    """Set up a switch from a config entry."""
    coordinator = SwitchSnmpCoordinator(
        hass,
        name=entry.data.get(CONF_NAME, entry.data[CONF_HOST]),
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        community=entry.data[CONF_COMMUNITY],
        scan_interval=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        flap_window=entry.options.get(CONF_FLAP_WINDOW, DEFAULT_FLAP_WINDOW),
        flap_threshold=entry.options.get(CONF_FLAP_THRESHOLD, DEFAULT_FLAP_THRESHOLD),
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SwitchConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_reload_entry(hass: HomeAssistant, entry: SwitchConfigEntry) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
