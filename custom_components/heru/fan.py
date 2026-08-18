"""Fan platform for Heru integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityDescription, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    HOLDING_REGISTER_EXHAUST_FAN_SPEED_EC,
    HOLDING_REGISTER_SUPPLY_FAN_SPEED_EC,
    INPUT_REGISTER_EXHAUST_FAN_POWER,
    INPUT_REGISTER_EXHAUST_FAN_RPM,
    INPUT_REGISTER_SUPPLY_FAN_POWER,
    INPUT_REGISTER_SUPPLY_FAN_RPM,
)
from .coordinator import HeruDataUpdateCoordinator

DEFAULT_ON_PERCENTAGE = 50


@dataclass(frozen=True, kw_only=True)
class HeruFanDescription(FanEntityDescription):
    """Description of a Heru fan."""

    register: int
    power_index: int
    rpm_index: int


FAN_DESCRIPTIONS: tuple[HeruFanDescription, ...] = (
    HeruFanDescription(
        key="supply_fan",
        translation_key="supply_fan",
        register=HOLDING_REGISTER_SUPPLY_FAN_SPEED_EC,
        power_index=INPUT_REGISTER_SUPPLY_FAN_POWER,
        rpm_index=INPUT_REGISTER_SUPPLY_FAN_RPM,
    ),
    HeruFanDescription(
        key="exhaust_fan",
        translation_key="exhaust_fan",
        register=HOLDING_REGISTER_EXHAUST_FAN_SPEED_EC,
        power_index=INPUT_REGISTER_EXHAUST_FAN_POWER,
        rpm_index=INPUT_REGISTER_EXHAUST_FAN_RPM,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Heru fans."""
    coordinator: HeruDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(HeruFanEntity(coordinator, entry, description) for description in FAN_DESCRIPTIONS)


class HeruFanEntity(CoordinatorEntity[HeruDataUpdateCoordinator], FanEntity):
    """A Heru EC fan, driven by its speed register.

    The percentage is the commanded speed. Boost, away and overpressure do not
    change it: the unit overlays its own speed while a mode is active and
    returns to this value afterwards, so the speed actually running is exposed
    as attributes rather than as the percentage.
    """

    entity_description: HeruFanDescription
    _attr_has_entity_name = True
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF
    )
    _attr_speed_count = 100

    def __init__(self, coordinator: HeruDataUpdateCoordinator, entry: ConfigEntry, description: HeruFanDescription) -> None:
        """Initialize fan."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._last_on_percentage = DEFAULT_ON_PERCENTAGE

    @property
    def device_info(self):
        """Return device info."""
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        """Return True if the unit exposes the fan speed register."""
        return super().available and self.coordinator.config_register(self.entity_description.register) is not None

    @property
    def percentage(self) -> int | None:
        """Return the commanded fan speed."""
        return self.coordinator.config_register(self.entity_description.register)

    @property
    def is_on(self) -> bool | None:
        """Return whether the fan is commanded to run."""
        percentage = self.percentage
        return None if percentage is None else percentage > 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the speed actually running, which a mode can override."""
        registers = self.coordinator.data.input_registers
        return {
            "current_power": registers[self.entity_description.power_index],
            "current_rpm": registers[self.entity_description.rpm_index],
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Remember the last running speed, to restore on turn on."""
        percentage = self.coordinator.config_register(self.entity_description.register)
        if percentage:
            self._last_on_percentage = percentage
        super()._handle_coordinator_update()

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the fan speed."""
        await self.coordinator.async_write_holding_register(self.entity_description.register, int(percentage))

    async def async_turn_on(self, percentage: int | None = None, preset_mode: str | None = None, **kwargs: Any) -> None:
        """Start the fan, restoring the last speed when none is given."""
        await self.async_set_percentage(self._last_on_percentage if percentage is None else percentage)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop the fan."""
        await self.async_set_percentage(0)
