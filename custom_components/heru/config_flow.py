"""Config flow for Heru integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow

try:
    from homeassistant.config_entries import ConfigFlowResult
except ImportError:  # HA < 2024.6 does not export ConfigFlowResult here
    from homeassistant.data_entry_flow import FlowResult as ConfigFlowResultfrom homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from pymodbus.client import AsyncModbusTcpClient

from .const import DEFAULT_NAME, DEFAULT_PORT, DOMAIN


async def _can_connect(host: str, port: int) -> bool:
    """Check if Modbus bridge is reachable."""
    client = AsyncModbusTcpClient(host=host, port=port)
    try:
        connected = await client.connect()
    except Exception:
        return False
    finally:
        client.close()
    return connected


class HeruConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Heru."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}")
            self._abort_if_unique_id_configured()

            if await _can_connect(user_input[CONF_HOST], user_input[CONF_PORT]):
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                    },
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                }
            ),
            errors=errors,
        )
