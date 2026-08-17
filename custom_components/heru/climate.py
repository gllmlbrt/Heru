"""Climate platform for Heru integration."""

from __future__ import annotations

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    TEMPERATURE_SCALE,
    FAN_STEP_OPTIONS,
    INPUT_REGISTER_EXHAUST_AIR_TEMPERATURE,
    HOLDING_REGISTER_TEMPERATURE_SETPOINT,
    HOLDING_REGISTER_USER_FAN_SPEED,
)
from .coordinator import HeruDataUpdateCoordinator

FAN_MODE_TO_VALUE = {option: value for value, option in enumerate(FAN_STEP_OPTIONS)}
VALUE_TO_FAN_MODE = {value: key for key, value in FAN_MODE_TO_VALUE.items()}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Heru climate entity."""
    coordinator: HeruDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HeruClimateEntity(coordinator, entry)])


class HeruClimateEntity(CoordinatorEntity[HeruDataUpdateCoordinator], ClimateEntity):
    """Climate control for Heru."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_fan_modes = list(FAN_MODE_TO_VALUE)
    _attr_min_temp = 15
    _attr_max_temp = 40
    _attr_target_temperature_step = 1

    def __init__(self, coordinator: HeruDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize climate entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_climate"
        self._last_nonzero_fan_speed = 2

    @property
    def device_info(self):
        """Return device info."""
        return self.coordinator.device_info

    @property
    def current_temperature(self) -> float | None:
        """Return the temperature of the air extracted from the house."""
        raw = self.coordinator.data.input_registers[INPUT_REGISTER_EXHAUST_AIR_TEMPERATURE]
        if raw >= 0x8000:  # tenths of a degree, signed
            raw -= 0x10000
        return round(raw * TEMPERATURE_SCALE, 1)

    @property
    def target_temperature(self) -> float | None:
        """Return target temperature."""
        return float(self.coordinator.data.holding_registers[HOLDING_REGISTER_TEMPERATURE_SETPOINT])

    @property
    def fan_mode(self) -> str | None:
        """Return current configured fan mode."""
        fan_speed = self.coordinator.data.holding_registers[HOLDING_REGISTER_USER_FAN_SPEED]
        if fan_speed > 0:
            self._last_nonzero_fan_speed = fan_speed
        return VALUE_TO_FAN_MODE.get(fan_speed)

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current hvac mode."""
        fan_speed = self.coordinator.data.holding_registers[HOLDING_REGISTER_USER_FAN_SPEED]
        return HVACMode.OFF if fan_speed == 0 else HVACMode.HEAT

    async def async_set_temperature(self, **kwargs) -> None:
        """Set the temperature setpoint."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        await self.coordinator.async_write_holding_register(HOLDING_REGISTER_TEMPERATURE_SETPOINT, int(round(temperature)))

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set user fan mode."""
        if fan_mode not in FAN_MODE_TO_VALUE:
            return
        target_speed = FAN_MODE_TO_VALUE[fan_mode]
        if target_speed > 0:
            self._last_nonzero_fan_speed = target_speed
        await self.coordinator.async_write_holding_register(HOLDING_REGISTER_USER_FAN_SPEED, target_speed)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_write_holding_register(HOLDING_REGISTER_USER_FAN_SPEED, 0)
            return
        current_speed = self.coordinator.data.holding_registers[HOLDING_REGISTER_USER_FAN_SPEED]
        restore_speed = current_speed if current_speed > 0 else self._last_nonzero_fan_speed
        await self.coordinator.async_write_holding_register(HOLDING_REGISTER_USER_FAN_SPEED, restore_speed)
