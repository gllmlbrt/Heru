"""Data coordinator for Heru integration."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pymodbus import FramerType
from pymodbus.client import AsyncModbusTcpClient

from .const import (
    COIL_COUNT,
    HOLDING_CONFIG_BLOCKS,
    DEFAULT_FRAMER,
    DEFAULT_SLAVE,
    DISCRETE_INPUT_BLOCKS,
    DISCRETE_INPUT_COUNT,
    DOMAIN,
    EXPECTED_COMPONENT_ID,
    FRAMER_RTU,
    INPUT_REGISTER_COMPONENT_ID,
    UPDATE_INTERVAL_SECONDS,
)


def _framer_type(framer: str) -> FramerType:
    """Map the configured framer name to a pymodbus framer."""
    return FramerType.RTU if framer == FRAMER_RTU else FramerType.SOCKET


def _build_client(host: str, port: int, framer: str) -> AsyncModbusTcpClient:
    """Create a Modbus client for the configured bridge."""
    return AsyncModbusTcpClient(host, port=port, framer=_framer_type(framer))


async def async_probe_unit(host: str, port: int, device_id: int, framer: str) -> str | None:
    """Check that a HERU unit answers, returning an error key or None on success.

    A bridge with the wrong framer or unit ID accepts the TCP connection and
    then never replies, so a plain connect check is not enough to validate the
    settings the user entered.
    """
    client = _build_client(host, port, framer)
    try:
        if not await client.connect():
            return "cannot_connect"
        response = await client.read_input_registers(
            address=INPUT_REGISTER_COMPONENT_ID, count=1, device_id=device_id
        )
        if response.isError() or response.registers[0] != EXPECTED_COMPONENT_ID:
            return "no_heru_response"
    except Exception:  # noqa: BLE001 - any Modbus failure means these settings do not work
        return "no_heru_response"
    finally:
        client.close()
    return None


@dataclass(slots=True)
class HeruData:
    """Heru runtime data."""

    input_registers: list[int]
    discrete_inputs: list[bool]
    holding_registers: list[int]
    coils: list[bool] | None
    config_registers: dict[int, int] | None


class HeruDataUpdateCoordinator(DataUpdateCoordinator[HeruData]):
    """Manage Heru data fetching and writing."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        host: str,
        port: int,
        device_id: int = DEFAULT_SLAVE,
        framer: str = DEFAULT_FRAMER,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger=logging.getLogger(__name__),
            name=DOMAIN,
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )
        self.entry = entry
        self.host = host
        self.port = port
        self.device_id = device_id
        self.framer = framer
        self.client = _build_client(host, port, framer)
        self._request_lock = asyncio.Lock()
        self._coil_warning_logged = False
        self._config_warning_logged = False

    @property
    def _connection_description(self) -> str:
        """Describe the active connection settings for log messages."""
        return f"{self.host}:{self.port} (unit {self.device_id}, {self.framer} framing)"

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

    def _raise_on_error(self, response, request: str) -> None:
        """Raise if the unit rejected a request."""
        if response.isError():
            raise UpdateFailed(
                f"Modbus {request} rejected by {self._connection_description}: {response}"
            )

    async def _async_read_coils(self) -> list[bool] | None:
        """Read the mode coils, returning None if the unit does not expose them.

        Coil support is not fatal: a unit that rejects the read still provides
        every sensor, so only the coil-backed entities go unavailable.
        """
        try:
            response = await self.client.read_coils(address=0, count=COIL_COUNT, device_id=self.device_id)
        except Exception as err:  # noqa: BLE001 - optional block, never fatal
            self._log_coils_unavailable(err)
            return None
        if response.isError():
            self._log_coils_unavailable(response)
            return None
        self._coil_warning_logged = False
        return [bool(value) for value in response.bits[:COIL_COUNT]]

    def _log_coils_unavailable(self, reason: object) -> None:
        """Warn once that the mode coils cannot be read."""
        if not self._coil_warning_logged:
            self._coil_warning_logged = True
            self.logger.warning(
                "Heru at %s did not answer the coil read (%s); mode switches and buttons "
                "will be unavailable, all other entities are unaffected",
                self._connection_description,
                reason,
            )

    async def _async_read_config_registers(self) -> dict[int, int] | None:
        """Read the configuration register blocks, keyed by absolute index.

        Optional like the coils, and per block: a unit that rejects one block
        still reports the others, and every other entity keeps working.
        """
        values: dict[int, int] = {}
        for address, count in HOLDING_CONFIG_BLOCKS:
            try:
                response = await self.client.read_holding_registers(
                    address=address, count=count, device_id=self.device_id
                )
            except Exception as err:  # noqa: BLE001 - optional block, never fatal
                self._log_config_unavailable(err)
                continue
            if response.isError():
                self._log_config_unavailable(response)
                continue
            for offset, value in enumerate(response.registers[:count]):
                values[address + offset] = value
        if not values:
            return None
        self._config_warning_logged = False
        return values

    def _log_config_unavailable(self, reason: object) -> None:
        """Warn once that the configuration registers cannot be read."""
        if not self._config_warning_logged:
            self._config_warning_logged = True
            self.logger.warning(
                "Heru at %s did not answer the configuration register read (%s); the "
                "hardware and freeze protection entities will be unavailable",
                self._connection_description,
                reason,
            )

    def config_register(self, index: int) -> int | None:
        """Return a configuration register by its absolute index."""
        registers = self.data.config_registers
        return None if registers is None else registers.get(index)

    async def async_write_coil(self, coil: int, value: bool, refresh: bool = True) -> None:
        """Write a coil, refreshing unless part of a larger sequence."""
        try:
            async with self._request_lock:
                await self._ensure_connected()
                self.logger.debug(
                    "Writing coil 0x%05d = %s on %s",
                    coil + 1, value, self._connection_description,
                )
                response = await self.client.write_coil(address=coil, value=value, device_id=self.device_id)

            if response.isError():
                raise UpdateFailed(f"Write failed for coil {coil + 1}")
        except UpdateFailed:
            raise
        except Exception as err:
            self.client.close()
            self.client = _build_client(self.host, self.port, self.framer)
            raise UpdateFailed(f"Unexpected Modbus coil write error: {err}") from err

        if refresh:
            await self.async_request_refresh()

    async def _async_update_data(self) -> HeruData:
        """Fetch data from the Heru unit."""
        request = "connect"
        try:
            async with self._request_lock:
                await self._ensure_connected()
                self.logger.debug("Polling Heru at %s", self._connection_description)

                request = "read_input_registers(address=0, count=33)"
                input_response = await self.client.read_input_registers(address=0, count=33, device_id=self.device_id)
                self._raise_on_error(input_response, request)

                discrete_inputs = [False] * DISCRETE_INPUT_COUNT
                for address, count in DISCRETE_INPUT_BLOCKS:
                    request = f"read_discrete_inputs(address={address}, count={count})"
                    discrete_response = await self.client.read_discrete_inputs(
                        address=address, count=count, device_id=self.device_id
                    )
                    self._raise_on_error(discrete_response, request)
                    for offset, value in enumerate(discrete_response.bits[:count]):
                        discrete_inputs[address + offset] = bool(value)

                request = "read_holding_registers(address=0, count=2)"
                holding_response = await self.client.read_holding_registers(address=0, count=2, device_id=self.device_id)
                self._raise_on_error(holding_response, request)

                coils = await self._async_read_coils()
                config_registers = await self._async_read_config_registers()

                return HeruData(
                    input_registers=list(input_response.registers),
                    discrete_inputs=discrete_inputs,
                    holding_registers=list(holding_response.registers),
                    coils=coils,
                    config_registers=config_registers,
                )
        except UpdateFailed:
            raise
        except Exception as err:
            self.client.close()
            self.client = _build_client(self.host, self.port, self.framer)
            raise UpdateFailed(
                f"Modbus {request} failed against {self._connection_description}: {err}"
            ) from err

    async def async_write_holding_register(self, register: int, value: int, refresh: bool = True) -> None:
        """Write a holding register, refreshing unless part of a larger sequence."""
        try:
            async with self._request_lock:
                await self._ensure_connected()
                self.logger.debug(
                    "Writing holding register 4x%05d = %s on %s",
                    register + 1, value, self._connection_description,
                )
                response = await self.client.write_register(address=register, value=value, device_id=self.device_id)

            if response.isError():
                raise UpdateFailed(f"Write failed for register {register + 1}")
        except UpdateFailed:
            raise
        except Exception as err:
            self.client.close()
            self.client = _build_client(self.host, self.port, self.framer)
            raise UpdateFailed(f"Unexpected Modbus write error: {err}") from err

        if refresh:
            await self.async_request_refresh()
