import asyncio
import logging
from typing import Optional

from homeassistant.core import HomeAssistant
from homeassistant.components import bluetooth

from bleak import BleakClient
from bleak.exc import BleakError
from bleak.backends.device import BLEDevice

from .cheshire.compiler.compiler import StateCompiler
from .cheshire.compiler.state import LightState
from .cheshire.hal.devices import DeviceProfile, device_profile_from_ble_device

_LOGGER = logging.getLogger(__name__)


class KeepsmileController:
    def __init__(self, hass: HomeAssistant, address: str):
        self._hass = hass
        self._address = address
        self._device: Optional[BLEDevice] = None
        self._client: Optional[BleakClient] = None
        self._profile: Optional[DeviceProfile] = None
        self._compiler: Optional[StateCompiler] = None
        self._connected = False
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        if self._connected:
            return

        _LOGGER.debug("Connecting to Keepsmile %s", self._address)

        self._device = bluetooth.async_ble_device_from_address(
            self._hass, self._address, connectable=True
        )
        if not self._device:
            raise RuntimeError(f"No Bluetooth device found for address {self._address}")

        try:
            self._client = BleakClient(self._device)
            await asyncio.wait_for(self._client.connect(), timeout=20.0)

            self._profile = device_profile_from_ble_device(self._device)
        except (BleakError, asyncio.TimeoutError) as exc:
            _LOGGER.exception(
                "Failed to connect to Keepsmile device %s: %s", self._address, exc
            )
            try:
                if self._client is not None:
                    await self._client.disconnect()
            except Exception:
                _LOGGER.debug("Error while cleaning up BleakClient after failed connect", exc_info=True)
            self._client = None
            raise RuntimeError(f"Failed to connect to {self._address}") from exc

        self._connected = True
        _LOGGER.info("Connected to Keepsmile device %s", self._address)

    async def stop(self) -> None:
        if self._client is not None:
            try:
                is_conn = getattr(self._client, "is_connected", None)
                if is_conn is None or (callable(is_conn) and is_conn()) or (not callable(is_conn) and is_conn):
                    await self._client.disconnect()
            except Exception as exc:
                _LOGGER.debug("Error disconnecting from %s: %s", self._address, exc, exc_info=True)
            finally:
                self._client = None

        self._connected = False
        _LOGGER.info("Disconnected from Keepsmile device %s", self._address)

    async def write_state(self, state: LightState) -> None:
        async with self._lock:
            if not self._connected:
                await self.connect()

            if not self._device:
                raise RuntimeError("BLE device not available after connect()")
            
            if not self._profile:
                raise RuntimeError("Device profile not available after connect()")

            connection = await self._profile.connect(self._device, client=self._client)
            await connection.apply(state)

            _LOGGER.debug("Wrote state to Keepsmile %s: %s", self._address, state)
