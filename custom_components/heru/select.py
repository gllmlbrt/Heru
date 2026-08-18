"""Select platform for Heru integration."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    COIL_AWAY_MODE,
    COIL_BOOST_MODE,
    COIL_UNIT_ON,
    DOMAIN,
    FAN_STEP_OPTIONS,
    HOLDING_REGISTER_BOOST_SPEED,
    INPUT_REGISTER_CURRENT_SUPPLY_FAN_STEP,
)
from .coordinator import HeruDataUpdateCoordinator

STEP_OFF, STEP_MIN, STEP_STD, STEP_MOD, STEP_MAX = FAN_STEP_OPTIONS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Heru selects."""
    coordinator: HeruDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HeruFanStepSelect(coordinator, entry)])


class HeruFanStepSelect(CoordinatorEntity[HeruDataUpdateCoordinator], SelectEntity):
    """Fan step, driven through the unit's own modes.

    The documented step register 4x00001 is rejected by a unit with EC fans:
    writing it is acknowledged and then discarded, so it cannot command a step.
    The modes can, and the unit maps each to a speed - away runs at min
    (4x00005) and boost at mod or max (4x00006/4x00007, chosen by 4x00026) -
    so selecting a step sets the mode that produces it.

    Steps 3 and 4 use boost, which the unit ends by itself after the boost
    duration, so those are not permanent.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "fan_step"
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
    def available(self) -> bool:
        """Return True if the mode coils can be reached."""
        return super().available and self.coordinator.data.coils is not None

    @property
    def current_option(self) -> str | None:
        """Return the step the unit is actually running.

        Read from 3x00023 rather than from the mode that was selected, so a
        boost that has expired shows as the step now in effect.
        """
        step = self.coordinator.data.input_registers[INPUT_REGISTER_CURRENT_SUPPLY_FAN_STEP]
        return FAN_STEP_OPTIONS[step] if 0 <= step < len(FAN_STEP_OPTIONS) else None

    async def async_select_option(self, option: str) -> None:
        """Set the mode that produces the requested step."""
        coordinator = self.coordinator

        if option == STEP_OFF:
            await coordinator.async_write_coil(COIL_UNIT_ON, False)
            return

        # Clear whichever mode is active before selecting the new one, so the
        # steps stay mutually exclusive.
        await coordinator.async_write_coil(COIL_AWAY_MODE, option == STEP_MIN, refresh=False)
        if option in (STEP_MOD, STEP_MAX):
            await coordinator.async_write_holding_register(
                HOLDING_REGISTER_BOOST_SPEED, FAN_STEP_OPTIONS.index(option), refresh=False
            )
        await coordinator.async_write_coil(COIL_BOOST_MODE, option in (STEP_MOD, STEP_MAX), refresh=False)
        await coordinator.async_write_coil(COIL_UNIT_ON, True)
