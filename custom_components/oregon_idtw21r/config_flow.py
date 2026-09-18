"""Config flow for Oregon Scientific IDTW21xR."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigFlowResult

from .const import DOMAIN, NAME, SERVICE_UUID


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
