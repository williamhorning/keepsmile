from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from home_assistant_bluetooth import BluetoothServiceInfoBleak

from . import DOMAIN


class KeepsmileConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Keepsmile BLE lights."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step of the config flow."""
        errors = {}

        if user_input is not None:
            mac = user_input["device"]

            # Prevent duplicate entries for the same device
            await self.async_set_unique_id(mac)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Keepsmile {mac[-5:]}",
                data={"mac": mac},
            )

        # Get list of discovered Bluetooth devices (from cache)
        service_infos: list[BluetoothServiceInfoBleak] = bluetooth.async_discovered_service_info(
            self.hass, connectable=True
        )

        # Filter for Keepsmile devices (e.g., name starts with "KS")
        keepsmile_devices = [
            info for info in service_infos
            if info.name and info.name.startswith("KS")
        ]

        if not keepsmile_devices:
            errors["base"] = "no_devices_found"
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({}),
                errors=errors,
            )

        # Create selection options for user
        device_choices = {
            info.address: f"{info.name or 'Unknown'} ({info.address})"
            for info in keepsmile_devices
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("device"): vol.In(device_choices)
            }),
            errors=errors,
        )
