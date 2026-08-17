"""Sensor platform for Heru integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPressure, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HeruDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class HeruSensorDescription(SensorEntityDescription):
    """Description of Heru sensor."""

    register_index: int
    scale: float = 1.0
    value_fn: Callable[[int], int | float] | None = None


SENSOR_DESCRIPTIONS: tuple[HeruSensorDescription, ...] = (
    HeruSensorDescription(key="component_id", translation_key="component_id", register_index=0, entity_category=EntityCategory.DIAGNOSTIC),
    HeruSensorDescription(key="outdoor_temperature", translation_key="outdoor_temperature", register_index=1, device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="supply_air_temperature", translation_key="supply_air_temperature", register_index=2, device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="exhaust_air_temperature", translation_key="exhaust_air_temperature", register_index=3, device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="waste_air_temperature", translation_key="waste_air_temperature", register_index=4, device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="water_temperature", translation_key="water_temperature", register_index=5, device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="heat_recovery_wheel_temperature", translation_key="heat_recovery_wheel_temperature", register_index=6, device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="room_temperature", translation_key="room_temperature", register_index=7, device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="supply_pressure", translation_key="supply_pressure", register_index=11, scale=0.1, device_class=SensorDeviceClass.PRESSURE, native_unit_of_measurement=UnitOfPressure.PA, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="exhaust_pressure", translation_key="exhaust_pressure", register_index=12, scale=0.1, device_class=SensorDeviceClass.PRESSURE, native_unit_of_measurement=UnitOfPressure.PA, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="relative_humidity", translation_key="relative_humidity", register_index=13, scale=0.1, device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="carbon_dioxide", translation_key="carbon_dioxide", register_index=14, device_class=SensorDeviceClass.CO2, native_unit_of_measurement="ppm", state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="sensors_open", translation_key="sensors_open", register_index=17, entity_category=EntityCategory.DIAGNOSTIC),
    HeruSensorDescription(key="sensors_shorted", translation_key="sensors_shorted", register_index=18, entity_category=EntityCategory.DIAGNOSTIC),
    HeruSensorDescription(key="filter_days_left", translation_key="filter_days_left", register_index=19, device_class=SensorDeviceClass.DURATION, native_unit_of_measurement="d", state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="current_weektimer_program", translation_key="current_weektimer_program", register_index=20),
    HeruSensorDescription(key="current_fan_speed", translation_key="current_fan_speed", register_index=21),
    HeruSensorDescription(key="current_supply_fan_step", translation_key="current_supply_fan_step", register_index=22),
    HeruSensorDescription(key="current_exhaust_fan_step", translation_key="current_exhaust_fan_step", register_index=23),
    HeruSensorDescription(key="current_supply_fan_power", translation_key="current_supply_fan_power", register_index=24, native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="current_exhaust_fan_power", translation_key="current_exhaust_fan_power", register_index=25, native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="current_supply_fan_speed_rpm", translation_key="current_supply_fan_speed_rpm", register_index=26, native_unit_of_measurement="rpm", state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="current_exhaust_fan_speed_rpm", translation_key="current_exhaust_fan_speed_rpm", register_index=27, native_unit_of_measurement="rpm", state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="current_heating_power", translation_key="current_heating_power", register_index=28, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="current_heat_cold_recovery_power", translation_key="current_heat_cold_recovery_power", register_index=29, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="current_cooling_power", translation_key="current_cooling_power", register_index=30, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="supply_fan_control_voltage", translation_key="supply_fan_control_voltage", register_index=31, scale=0.1, native_unit_of_measurement="V", state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="exhaust_fan_control_voltage", translation_key="exhaust_fan_control_voltage", register_index=32, scale=0.1, native_unit_of_measurement="V", state_class=SensorStateClass.MEASUREMENT),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Heru sensors from a config entry."""
    coordinator: HeruDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(HeruSensorEntity(coordinator, entry, description) for description in SENSOR_DESCRIPTIONS)


class HeruSensorEntity(CoordinatorEntity[HeruDataUpdateCoordinator], SensorEntity):
    """Heru sensor entity."""

    entity_description: HeruSensorDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator: HeruDataUpdateCoordinator, entry: ConfigEntry, description: HeruSensorDescription) -> None:
        """Initialize sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def device_info(self):
        """Return device info."""
        return self.coordinator.device_info

    @property
    def native_value(self):
        """Return state from coordinator data."""
        value = self.coordinator.data.input_registers[self.entity_description.register_index]
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(value)
        scaled_value = value * self.entity_description.scale
        if self.entity_description.scale == 1.0:
            return int(scaled_value)
        return round(scaled_value, 1)
