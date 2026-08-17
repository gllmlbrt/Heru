"""Climate platform for Heru integration."""

from __future__ import annotations

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import ClimateEntityFeature, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    HOLDING_REGISTER_TEMPERATURE_SETPOINT,
    HOLDING_REGISTER_USER_FAN_SPEED,
)
from .coordinator import HeruDataUpdateCoordinator

FAN_MODE_TO_VALUE = {
    "off": 0,
    "min": 1,
    "std": 2,
    "mod": 3,
    "max": 4,
}
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

    @property
    def device_info(self):
        """Return device info."""
        return self.coordinator.device_info

    @property
    def current_temperature(self) -> float | None:
        """Return current room temperature."""
        return float(self.coordinator.data.input_registers[7])

    @property
    def target_temperature(self) -> float | None:
        """Return target temperature."""
        return float(self.coordinator.data.holding_registers[1])

    @property
    def fan_mode(self) -> str | None:
        """Return current configured fan mode."""
        return VALUE_TO_FAN_MODE.get(self.coordinator.data.holding_registers[0], "std")

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current hvac mode."""
        fan_speed = self.coordinator.data.holding_registers[0]
        return HVACMode.OFF if fan_speed == 0 else HVACMode.HEAT

    async def async_set_temperature(self, **kwargs) -> None:
        """Set the temperature setpoint."""
        if (temperature := kwargs.get("temperature")) is None:
            return
        await self.coordinator.async_write_holding_register(HOLDING_REGISTER_TEMPERATURE_SETPOINT, int(round(temperature)))

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set user fan mode."""
        if fan_mode not in FAN_MODE_TO_VALUE:
            return
        await self.coordinator.async_write_holding_register(HOLDING_REGISTER_USER_FAN_SPEED, FAN_MODE_TO_VALUE[fan_mode])

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_write_holding_register(HOLDING_REGISTER_USER_FAN_SPEED, 0)
            return
        await self.coordinator.async_write_holding_register(HOLDING_REGISTER_USER_FAN_SPEED, 2)
