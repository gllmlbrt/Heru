"""Sensor platform for Heru integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfElectricPotential, UnitOfPressure, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    HOLDING_REGISTER_CLOCK_HOURS,
    HOLDING_REGISTER_FILTER_CHANGE_PERIOD,
    HOLDING_REGISTER_CLOCK_MINUTES,
    HOLDING_REGISTER_CLOCK_SECONDS,
    HOLDING_REGISTER_CLOCK_WEEKDAY,
    SECONDS_PER_WEEK,
    WEEKDAY_NAMES,
    FAN_STEP_OPTIONS,
    INPUT_REGISTER_ROOM_TEMPERATURE,
    POWER_255_TO_PERCENT,
    TEMPERATURE_SCALE,
)
from .coordinator import HeruDataUpdateCoordinator

RPM = "rpm"


@dataclass(frozen=True, kw_only=True)
class HeruSensorDescription(SensorEntityDescription):
    """Description of Heru sensor."""

    register_index: int
    scale: float = 1.0
    signed: bool = False
    value_fn: Callable[[int], int | float | str | None] | None = None


def _to_signed(value: int) -> int:
    """Interpret a 16-bit register as a signed value."""
    return value - 0x10000 if value >= 0x8000 else value


def _fan_speed_option(value: int) -> str | None:
    """Map a fan speed register value to its step label."""
    return FAN_STEP_OPTIONS[value] if 0 <= value < len(FAN_STEP_OPTIONS) else None


SENSOR_DESCRIPTIONS: tuple[HeruSensorDescription, ...] = (
    HeruSensorDescription(key="component_id", translation_key="component_id", register_index=0, entity_category=EntityCategory.DIAGNOSTIC),
    HeruSensorDescription(key="outdoor_temperature", translation_key="outdoor_temperature", register_index=1, scale=TEMPERATURE_SCALE, signed=True, device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="supply_air_temperature", translation_key="supply_air_temperature", register_index=2, scale=TEMPERATURE_SCALE, signed=True, device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="exhaust_air_temperature", translation_key="exhaust_air_temperature", register_index=3, scale=TEMPERATURE_SCALE, signed=True, device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="waste_air_temperature", translation_key="waste_air_temperature", register_index=4, scale=TEMPERATURE_SCALE, signed=True, device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="water_temperature", translation_key="water_temperature", register_index=5, scale=TEMPERATURE_SCALE, signed=True, device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="heat_recovery_wheel_temperature", translation_key="heat_recovery_wheel_temperature", register_index=6, scale=TEMPERATURE_SCALE, signed=True, device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="room_temperature", translation_key="room_temperature", register_index=INPUT_REGISTER_ROOM_TEMPERATURE, scale=TEMPERATURE_SCALE, signed=True, device_class=SensorDeviceClass.TEMPERATURE, native_unit_of_measurement=UnitOfTemperature.CELSIUS, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="supply_pressure", translation_key="supply_pressure", register_index=11, scale=0.1, device_class=SensorDeviceClass.PRESSURE, native_unit_of_measurement=UnitOfPressure.PA, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="exhaust_pressure", translation_key="exhaust_pressure", register_index=12, scale=0.1, device_class=SensorDeviceClass.PRESSURE, native_unit_of_measurement=UnitOfPressure.PA, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="relative_humidity", translation_key="relative_humidity", register_index=13, scale=0.1, device_class=SensorDeviceClass.HUMIDITY, native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="carbon_dioxide", translation_key="carbon_dioxide", register_index=14, device_class=SensorDeviceClass.CO2, native_unit_of_measurement="ppm", state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="sensors_open", translation_key="sensors_open", register_index=17, entity_category=EntityCategory.DIAGNOSTIC),
    HeruSensorDescription(key="sensors_shorted", translation_key="sensors_shorted", register_index=18, entity_category=EntityCategory.DIAGNOSTIC),
    HeruSensorDescription(key="filter_days_left", translation_key="filter_days_left", register_index=19, device_class=SensorDeviceClass.DURATION, native_unit_of_measurement=UnitOfTime.DAYS, state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC),
    HeruSensorDescription(key="current_weektimer_program", translation_key="current_weektimer_program", register_index=20, entity_category=EntityCategory.DIAGNOSTIC),
    HeruSensorDescription(key="current_fan_speed", translation_key="current_fan_speed", register_index=21, value_fn=_fan_speed_option, device_class=SensorDeviceClass.ENUM, options=FAN_STEP_OPTIONS, entity_category=EntityCategory.DIAGNOSTIC),
    HeruSensorDescription(key="current_supply_fan_step", translation_key="current_supply_fan_step", register_index=22, value_fn=_fan_speed_option, device_class=SensorDeviceClass.ENUM, options=FAN_STEP_OPTIONS, entity_category=EntityCategory.DIAGNOSTIC),
    HeruSensorDescription(key="current_exhaust_fan_step", translation_key="current_exhaust_fan_step", register_index=23, value_fn=_fan_speed_option, device_class=SensorDeviceClass.ENUM, options=FAN_STEP_OPTIONS, entity_category=EntityCategory.DIAGNOSTIC),
    HeruSensorDescription(key="current_supply_fan_power", translation_key="current_supply_fan_power", register_index=24, native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="current_exhaust_fan_power", translation_key="current_exhaust_fan_power", register_index=25, native_unit_of_measurement=PERCENTAGE, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="current_supply_fan_speed_rpm", translation_key="current_supply_fan_speed_rpm", register_index=26, native_unit_of_measurement=RPM, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="current_exhaust_fan_speed_rpm", translation_key="current_exhaust_fan_speed_rpm", register_index=27, native_unit_of_measurement=RPM, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="current_heating_power", translation_key="current_heating_power", scale=POWER_255_TO_PERCENT, native_unit_of_measurement=PERCENTAGE, register_index=28, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="current_heat_cold_recovery_power", translation_key="current_heat_cold_recovery_power", scale=POWER_255_TO_PERCENT, native_unit_of_measurement=PERCENTAGE, register_index=29, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="current_cooling_power", translation_key="current_cooling_power", scale=POWER_255_TO_PERCENT, native_unit_of_measurement=PERCENTAGE, register_index=30, state_class=SensorStateClass.MEASUREMENT),
    HeruSensorDescription(key="supply_fan_control_voltage", translation_key="supply_fan_control_voltage", register_index=31, scale=0.1, native_unit_of_measurement=UnitOfElectricPotential.VOLT, state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC),
    HeruSensorDescription(key="exhaust_fan_control_voltage", translation_key="exhaust_fan_control_voltage", register_index=32, scale=0.1, native_unit_of_measurement=UnitOfElectricPotential.VOLT, state_class=SensorStateClass.MEASUREMENT, entity_category=EntityCategory.DIAGNOSTIC),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Heru sensors from a config entry."""
    coordinator: HeruDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        SENSOR_CLASSES.get(description.key, HeruSensorEntity)(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    ]
    entities.append(HeruSystemTimeSensor(coordinator, entry))
    async_add_entities(entities)


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
        if self.entity_description.signed:
            value = _to_signed(value)
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(value)
        scaled_value = value * self.entity_description.scale
        if self.entity_description.scale == 1.0:
            return int(scaled_value)
        return round(scaled_value, 1)


class HeruFilterDaysLeftSensor(HeruSensorEntity):
    """Days until the filter change is due.

    3x00020 reads 0 in two situations that are not a countdown of no days
    left: the filter timer is off (4x00044 = 0), and a unit whose firmware
    answers for the register without ever populating it, which is what a
    HERU 62-250 Gen 3 does even with a period set, the timer reset and no
    filter alarm raised. Neither is a duration, so report nothing rather
    than a permanent 0 days.

    A filter that really is due is reported by the filter alarms, which the
    alarm entity already covers, so nothing is lost by not reporting 0 here.
    The attributes carry the timer's configuration, because 1 - 5 months
    disables the timer on this unit rather than shortening it.
    """

    @property
    def _period(self) -> int | None:
        """Return the configured filter change period in months."""
        return self.coordinator.config_register(HOLDING_REGISTER_FILTER_CHANGE_PERIOD)

    @property
    def native_value(self):
        """Return the days left, or nothing when the unit reports no count."""
        value = super().native_value
        return None if value == 0 else value

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the filter timer's configuration."""
        period = self._period
        if period is None:
            return None
        return {
            "filter_change_period_months": period,
            "filter_timer_running": period != 0,
        }


class HeruSystemTimeSensor(CoordinatorEntity[HeruDataUpdateCoordinator], SensorEntity):
    """The unit's own clock.

    The unit keeps a weekday and a time of day but no date, so this cannot be
    a timestamp. The drift attribute is how far the unit is from Home
    Assistant, which is what the sync button corrects.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "system_time"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: HeruDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the clock sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_system_time"

    @property
    def device_info(self):
        """Return device info."""
        return self.coordinator.device_info

    @property
    def _clock(self) -> tuple[int, int, int, int] | None:
        """Return the unit's weekday, hours, minutes and seconds."""
        values = [
            self.coordinator.config_register(register)
            for register in (
                HOLDING_REGISTER_CLOCK_WEEKDAY,
                HOLDING_REGISTER_CLOCK_HOURS,
                HOLDING_REGISTER_CLOCK_MINUTES,
                HOLDING_REGISTER_CLOCK_SECONDS,
            )
        ]
        if any(value is None for value in values):
            return None
        return tuple(values)  # type: ignore[return-value]

    @property
    def available(self) -> bool:
        """Return True if the unit exposes its clock."""
        return super().available and self._clock is not None

    @property
    def native_value(self) -> str | None:
        """Return the unit's weekday and time."""
        clock = self._clock
        if clock is None:
            return None
        weekday, hours, minutes, seconds = clock
        name = WEEKDAY_NAMES[weekday] if 0 <= weekday < len(WEEKDAY_NAMES) else "?"
        return f"{name} {hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the parts, and how far the unit has drifted."""
        clock = self._clock
        if clock is None:
            return None
        weekday, hours, minutes, seconds = clock
        now = dt_util.now()
        unit_of_week = weekday * 86400 + hours * 3600 + minutes * 60 + seconds
        local_of_week = now.weekday() * 86400 + now.hour * 3600 + now.minute * 60 + now.second
        # Shortest signed distance, so a Sunday/Monday wrap is seconds not days.
        drift = (unit_of_week - local_of_week + SECONDS_PER_WEEK // 2) % SECONDS_PER_WEEK
        drift -= SECONDS_PER_WEEK // 2
        return {
            "weekday": weekday,
            "hours": hours,
            "minutes": minutes,
            "seconds": seconds,
            "drift_seconds": drift,
        }


# Entities that need behaviour beyond a scaled register read.
SENSOR_CLASSES: dict[str, type[HeruSensorEntity]] = {
    "filter_days_left": HeruFilterDaysLeftSensor,
}
