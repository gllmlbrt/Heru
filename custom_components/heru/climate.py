"""Climate platform for Heru integration."""

from __future__ import annotations

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    COIL_UNIT_ON,
    DOMAIN,
    HOLDING_REGISTER_TEMPERATURE_SETPOINT,
    HOLDING_REGISTER_USER_FAN_SPEED,
    INPUT_REGISTER_EXHAUST_AIR_TEMPERATURE,
    TEMPERATURE_SCALE,
)
from .coordinator import HeruDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Heru climate entity."""
    coordinator: HeruDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HeruClimateEntity(coordinator, entry)])


class HeruClimateEntity(CoordinatorEntity[HeruDataUpdateCoordinator], ClimateEntity):
    """Temperature control for Heru.

    Fan control is deliberately not exposed here. The fan mode would have to
    write the user fan speed register, which the unit applies to AC fans only;
    on an EC unit it is stored and ignored. The supply and exhaust fan entities
    are the fan control, and the fan step select covers the unit's own steps.
    """

    _attr_has_entity_name = True
    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
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
    def hvac_mode(self) -> HVACMode:
        """Return whether the unit is running.

        Taken from the Unit on coil, which works regardless of fan type. The
        user fan speed register is only a usable proxy on AC fans, so it is a
        fallback for units that do not expose their coils.
        """
        coils = self.coordinator.data.coils
        if coils is not None:
            return HVACMode.HEAT if coils[COIL_UNIT_ON] else HVACMode.OFF
        fan_speed = self.coordinator.data.holding_registers[HOLDING_REGISTER_USER_FAN_SPEED]
        return HVACMode.OFF if fan_speed == 0 else HVACMode.HEAT

    async def async_set_temperature(self, **kwargs) -> None:
        """Set the temperature setpoint."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        await self.coordinator.async_write_holding_register(HOLDING_REGISTER_TEMPERATURE_SETPOINT, int(round(temperature)))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Start or stop the unit."""
        await self.coordinator.async_write_coil(COIL_UNIT_ON, hvac_mode != HVACMode.OFF)
