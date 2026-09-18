"""Config flow for Oregon Scientific IDTW21xR."""

from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigFlowResult

from .const import DOMAIN, NAME, SERVICE_UUID


class OregonIDTW21RConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Oregon Scientific IDTW21xR."""

    VERSION = 1

    async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle Bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        name = discovery_info.name or discovery_info.address

        self.context["title_placeholders"] = {
            "name": name,
        }

        return self.async_create_entry(
            title=name,
            data={
                "address": discovery_info.address,
                "name": name,
                "service_uuid": SERVICE_UUID,
            },
        )
