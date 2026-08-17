"""Data coordinator for Heru integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pymodbus.client import AsyncModbusTcpClient

from .const import DEFAULT_SLAVE, DOMAIN, UPDATE_INTERVAL_SECONDS


@dataclass(slots=True)
class HeruData:
    """Heru runtime data."""

    input_registers: list[int]
    discrete_inputs: list[bool]
    holding_registers: list[int]


class HeruDataUpdateCoordinator(DataUpdateCoordinator[HeruData]):
    """Manage Heru data fetching and writing."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, host: str, port: int) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=hass.data.get("logger", __import__("logging")).getLogger(__name__),
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )
        self.entry = entry
        self.host = host
        self.port = port
        self.client = AsyncModbusTcpClient(host=host, port=port)
        self._lock = hass.loop.create_future()
        self._lock = None
        self._request_lock = __import__("asyncio").Lock()

    @property
    def device_info(self) -> DeviceInfo:
        """Return a shared device description."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=self.entry.data.get(CONF_NAME, self.entry.title),
            manufacturer="Östberg",
            model="HERU Gen 3",
            configuration_url=f"http://{self.host}",
        )

    async def async_close(self) -> None:
        """Close the Modbus client."""
        self.client.close()

    async def _ensure_connected(self) -> None:
        """Ensure the client is connected."""
        if self.client.connected:
            return
        if not await self.client.connect():
            raise UpdateFailed("Failed to connect to Modbus bridge")

    async def _async_update_data(self) -> HeruData:
        """Fetch data from the Heru unit."""
        async with self._request_lock:
            await self._ensure_connected()
            input_response = await self.client.read_input_registers(address=0, count=33, slave=DEFAULT_SLAVE)
            discrete_response = await self.client.read_discrete_inputs(address=0, count=34, slave=DEFAULT_SLAVE)
            holding_response = await self.client.read_holding_registers(address=0, count=2, slave=DEFAULT_SLAVE)

        if input_response.isError() or discrete_response.isError() or holding_response.isError():
            raise UpdateFailed("Failed to read one or more Modbus registers")

        return HeruData(
            input_registers=list(input_response.registers),
            discrete_inputs=[bool(value) for value in discrete_response.bits[:34]],
            holding_registers=list(holding_response.registers),
        )

    async def async_write_holding_register(self, register: int, value: int) -> None:
        """Write a holding register and refresh state."""
        async with self._request_lock:
            await self._ensure_connected()
            response = await self.client.write_register(address=register, value=value, slave=DEFAULT_SLAVE)

        if response.isError():
            raise UpdateFailed(f"Write failed for register {register + 1}")

        await self.async_request_refresh()
