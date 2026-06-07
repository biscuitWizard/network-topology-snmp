"""Config and options flow for the Network Topology SNMP integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_COMMUNITY,
    CONF_FLAP_THRESHOLD,
    CONF_FLAP_WINDOW,
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_COMMUNITY,
    DEFAULT_FLAP_THRESHOLD,
    DEFAULT_FLAP_WINDOW,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class NetworkTopologySnmpConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for a single SNMP-polled switch."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Collect connection details and verify reachability."""
        errors: dict[str, str] = {}
        placeholders: dict[str, str] = {}

        if user_input is not None:
            # Import lazily so the flow always loads even if the SNMP library
            # has an unexpected layout; any failure surfaces as cannot_connect.
            from .coordinator import SnmpError, async_probe_switch

            host = user_input[CONF_HOST]
            await self.async_set_unique_id(f"{host}:{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()
            try:
                await async_probe_switch(
                    self.hass,
                    host,
                    user_input[CONF_PORT],
                    user_input[CONF_COMMUNITY],
                )
            except SnmpError as err:
                _LOGGER.warning("SNMP probe of %s failed: %s", host, err)
                errors["base"] = "cannot_connect"
            except Exception as err:  # noqa: BLE001 - surface the real cause
                _LOGGER.exception("Unexpected error probing %s", host)
                errors["base"] = "unknown"
                placeholders["error"] = f"{type(err).__name__}: {err}"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME] or host,
                    data={
                        CONF_HOST: host,
                        CONF_PORT: user_input[CONF_PORT],
                        CONF_COMMUNITY: user_input[CONF_COMMUNITY],
                        CONF_NAME: user_input[CONF_NAME] or host,
                    },
                    options={
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                        CONF_FLAP_WINDOW: user_input[CONF_FLAP_WINDOW],
                        CONF_FLAP_THRESHOLD: user_input[CONF_FLAP_THRESHOLD],
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=""): str,
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): cv.port,
                vol.Required(CONF_COMMUNITY, default=DEFAULT_COMMUNITY): str,
                vol.Required(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=600)),
                vol.Required(
                    CONF_FLAP_WINDOW, default=DEFAULT_FLAP_WINDOW
                ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
                vol.Required(
                    CONF_FLAP_THRESHOLD, default=DEFAULT_FLAP_THRESHOLD
                ): vol.All(vol.Coerce(int), vol.Range(min=2, max=50)),
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders=placeholders,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> NetworkTopologySnmpOptionsFlow:
        """Return the options flow handler."""
        return NetworkTopologySnmpOptionsFlow()


class NetworkTopologySnmpOptionsFlow(OptionsFlow):
    """Allow tuning of polling cadence and flap detection after setup."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        opts = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=opts.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=600)),
                vol.Required(
                    CONF_FLAP_WINDOW,
                    default=opts.get(CONF_FLAP_WINDOW, DEFAULT_FLAP_WINDOW),
                ): vol.All(vol.Coerce(int), vol.Range(min=30, max=3600)),
                vol.Required(
                    CONF_FLAP_THRESHOLD,
                    default=opts.get(CONF_FLAP_THRESHOLD, DEFAULT_FLAP_THRESHOLD),
                ): vol.All(vol.Coerce(int), vol.Range(min=2, max=50)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
