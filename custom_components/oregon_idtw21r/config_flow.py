"""Config flow and options for Oregon Scientific IDTW21xR."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigFlowResult, OptionsFlowWithReload
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .const import DOMAIN, NAME, SERVICE_UUID

DEFAULT_ALLOW_STATISTICS_WRITE = True
DEFAULT_AUTO_SYNC_ENABLED = False
DEFAULT_POLLING_INTERVAL = 5


class OregonIDTW21RConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Oregon Scientific IDTW21xR."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        """Handle manual setup."""
        if user_input is not None:
            address = user_input["address"].strip().upper()
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=address,
                data={
                    "address": address,
                    "name": NAME,
                    "service_uuid": SERVICE_UUID,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("address"): str}),
        )

    async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle Bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        name = discovery_info.name or discovery_info.address
        self.context["title_placeholders"] = {"name": name}
        self._discovery_info = discovery_info

        return self.async_show_form(step_id="confirm")

    async def async_step_confirm(self, user_input=None) -> ConfigFlowResult:
        """Confirm a discovered device."""
        discovery_info = self._discovery_info
        name = discovery_info.name or discovery_info.address

        if user_input is not None:
            return self.async_create_entry(
                title=name,
                data={
                    "address": discovery_info.address,
                    "name": name,
                    "service_uuid": SERVICE_UUID,
                },
            )

        return self.async_show_form(step_id="confirm")

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the options flow for this config entry."""
        return OregonIDTW21ROptionsFlow()


class OregonIDTW21ROptionsFlow(OptionsFlowWithReload):
    """Configure polling and hourly history synchronization."""

    async def async_step_init(self, user_input=None):
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    "allow_statistics_write",
                    default=options.get(
                        "allow_statistics_write", DEFAULT_ALLOW_STATISTICS_WRITE
                    ),
                ): bool,
                vol.Required(
                    "auto_sync_enabled",
                    default=options.get(
                        "auto_sync_enabled", DEFAULT_AUTO_SYNC_ENABLED
                    ),
                ): bool,
                vol.Required(
                    "polling_interval",
                    default=options.get("polling_interval", DEFAULT_POLLING_INTERVAL),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=1,
                        max=60,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                        translation_key="polling_interval",
                    )
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
