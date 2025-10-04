import logging

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .controller import KeepsmileController
from .cheshire.compiler.state import LightState

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    address = entry.data["mac"]
    controller = KeepsmileController(hass, address)
    async_add_entities([KeepsmileLight(controller, address)], True)


class KeepsmileLight(LightEntity):
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB
    _attr_is_on = False

    def __init__(self, controller: KeepsmileController, address: str):
        self._controller = controller
        self._attr_unique_id = address
        self._attr_name = f"Keepsmile {address[-5:]}"
        self._attr_brightness = 255
        self._attr_rgb_color = (255, 255, 255)
        self._attr_device_info = {
            "identifiers": {("keepsmile", address)},
            "name": self._attr_name,
            "manufacturer": "Keepsmile",
            "model": "BLE RGB Light",
            "connections": {(CONNECTION_BLUETOOTH, address)},
        }


    async def async_turn_on(self, **kwargs):
        rgb = kwargs.get(ATTR_RGB_COLOR, self._attr_rgb_color)
        brightness = kwargs.get(ATTR_BRIGHTNESS, self._attr_brightness)
        self._attr_rgb_color = rgb
        self._attr_brightness = brightness
        self._attr_is_on = True

        state = LightState(rgb=rgb, brightness=brightness)
        await self._controller.write_state(state)
        _LOGGER.debug("Keepsmile %s set to RGB=%s brightness=%s", self._attr_name, rgb, brightness)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self._attr_is_on = False
        state = LightState(rgb=(0, 0, 0), brightness=0)
        await self._controller.write_state(state)
        _LOGGER.debug("Keepsmile %s turned off", self._attr_name)
        self.async_write_ha_state()

    async def async_will_remove_from_hass(self):
        try:
            await self._controller.stop()
        except Exception as exc:
            _LOGGER.debug("Error stopping Keepsmile controller: %s", exc, exc_info=True)
