"""Select platform for Heru integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, FAN_STEP_OPTIONS, HOLDING_REGISTER_USER_FAN_SPEED
from .coordinator import HeruDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Heru selects."""
    coordinator: HeruDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HeruFanStepSelect(coordinator, entry)])


class HeruFanStepSelect(CoordinatorEntity[HeruDataUpdateCoordinator], SelectEntity):
    """User fan speed step (4x00001).

    The unit applies this only to AC fans, and only while no weektimer program
    is active. On a unit with EC fans the supply and exhaust fan speed numbers
    are the ones that take effect.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "fan_step"
    # AC-only, so it is off by default: on an EC unit it would sit in the UI
    # accepting selections the unit ignores. AC owners can enable it.
    _attr_entity_registry_enabled_default = False
    _attr_options = FAN_STEP_OPTIONS

    def __init__(self, coordinator: HeruDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize select."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_fan_step"

    @property
    def device_info(self):
        """Return device info."""
        return self.coordinator.device_info

    @property
    def current_option(self) -> str | None:
        """Return the selected fan step."""
        value = self.coordinator.data.holding_registers[HOLDING_REGISTER_USER_FAN_SPEED]
        return FAN_STEP_OPTIONS[value] if 0 <= value < len(FAN_STEP_OPTIONS) else None

    async def async_select_option(self, option: str) -> None:
        """Set the fan step."""
        await self.coordinator.async_write_holding_register(
            HOLDING_REGISTER_USER_FAN_SPEED, FAN_STEP_OPTIONS.index(option)
        )
