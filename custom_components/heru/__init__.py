"""The Heru integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import CONF_DEVICE_ID, CONF_FRAMER, DEFAULT_FRAMER, DEFAULT_SLAVE, DOMAIN
from .coordinator import HeruDataUpdateCoordinator

PLATFORMS = ["binary_sensor", "button", "climate", "number", "sensor", "switch"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Heru integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Heru from a config entry."""
    coordinator = HeruDataUpdateCoordinator(
        hass=hass,
        entry=entry,
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        device_id=entry.data.get(CONF_DEVICE_ID, DEFAULT_SLAVE),
        framer=entry.data.get(CONF_FRAMER, DEFAULT_FRAMER),
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: HeruDataUpdateCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_close()
    return unload_ok
