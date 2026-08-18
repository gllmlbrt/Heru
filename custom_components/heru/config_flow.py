"""Config flow for Heru integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_DEVICE_ID,
    CONF_FRAMER,
    DEFAULT_FRAMER,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SLAVE,
    DOMAIN,
    FRAMER_OPTIONS,
)
from .coordinator import async_probe_unit


class HeruConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Heru."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}:{user_input[CONF_DEVICE_ID]}"
            )
            self._abort_if_unique_id_configured()

            error = await async_probe_unit(
                host=user_input[CONF_HOST],
                port=user_input[CONF_PORT],
                device_id=user_input[CONF_DEVICE_ID],
                framer=user_input[CONF_FRAMER],
            )
            if error is None:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_HOST: user_input[CONF_HOST],
                        CONF_PORT: user_input[CONF_PORT],
                        CONF_DEVICE_ID: user_input[CONF_DEVICE_ID],
                        CONF_FRAMER: user_input[CONF_FRAMER],
                    },
                )
            errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
                    vol.Required(CONF_DEVICE_ID, default=DEFAULT_SLAVE): vol.All(
                        int, vol.Range(min=0, max=247)
                    ),
                    vol.Required(CONF_FRAMER, default=DEFAULT_FRAMER): SelectSelector(
                        SelectSelectorConfig(
                            options=FRAMER_OPTIONS,
                            translation_key="framer",
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
        )
