"""Binary sensor platform for Heru integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import HeruDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class HeruBinarySensorDescription(BinarySensorEntityDescription):
    """Description of a Heru binary sensor."""

    bit_index: int


BINARY_SENSOR_DESCRIPTIONS: tuple[HeruBinarySensorDescription, ...] = (
    HeruBinarySensorDescription(key="fire_alarm_switch", translation_key="fire_alarm_switch", bit_index=0),
    HeruBinarySensorDescription(key="boost_switch", translation_key="boost_switch", bit_index=1),
    HeruBinarySensorDescription(key="overpressure_switch", translation_key="overpressure_switch", bit_index=2),
    HeruBinarySensorDescription(key="aux_switch", translation_key="aux_switch", bit_index=3),
    HeruBinarySensorDescription(key="fire_alarm", translation_key="fire_alarm", bit_index=9, entity_category=EntityCategory.DIAGNOSTIC, device_class=BinarySensorDeviceClass.PROBLEM),
    HeruBinarySensorDescription(key="rotor_alarm", translation_key="rotor_alarm", bit_index=10, entity_category=EntityCategory.DIAGNOSTIC, device_class=BinarySensorDeviceClass.PROBLEM),
    HeruBinarySensorDescription(key="freeze_alarm", translation_key="freeze_alarm", bit_index=12, entity_category=EntityCategory.DIAGNOSTIC, device_class=BinarySensorDeviceClass.PROBLEM),
    HeruBinarySensorDescription(key="low_supply_alarm", translation_key="low_supply_alarm", bit_index=13, entity_category=EntityCategory.DIAGNOSTIC, device_class=BinarySensorDeviceClass.PROBLEM),
    HeruBinarySensorDescription(key="low_rotor_temperature_alarm", translation_key="low_rotor_temperature_alarm", bit_index=14, entity_category=EntityCategory.DIAGNOSTIC, device_class=BinarySensorDeviceClass.PROBLEM),
    HeruBinarySensorDescription(key="temperature_sensor_open_circuit_alarm", translation_key="temperature_sensor_open_circuit_alarm", bit_index=17, entity_category=EntityCategory.DIAGNOSTIC, device_class=BinarySensorDeviceClass.PROBLEM),
    HeruBinarySensorDescription(key="temperature_sensor_short_circuit_alarm", translation_key="temperature_sensor_short_circuit_alarm", bit_index=18, entity_category=EntityCategory.DIAGNOSTIC, device_class=BinarySensorDeviceClass.PROBLEM),
    HeruBinarySensorDescription(key="pulser_alarm", translation_key="pulser_alarm", bit_index=19, entity_category=EntityCategory.DIAGNOSTIC, device_class=BinarySensorDeviceClass.PROBLEM),
    HeruBinarySensorDescription(key="supply_fan_alarm", translation_key="supply_fan_alarm", bit_index=20, entity_category=EntityCategory.DIAGNOSTIC, device_class=BinarySensorDeviceClass.PROBLEM),
    HeruBinarySensorDescription(key="exhaust_fan_alarm", translation_key="exhaust_fan_alarm", bit_index=21, entity_category=EntityCategory.DIAGNOSTIC, device_class=BinarySensorDeviceClass.PROBLEM),
    HeruBinarySensorDescription(key="supply_filter_alarm", translation_key="supply_filter_alarm", bit_index=22, entity_category=EntityCategory.DIAGNOSTIC, device_class=BinarySensorDeviceClass.PROBLEM),
    HeruBinarySensorDescription(key="exhaust_filter_alarm", translation_key="exhaust_filter_alarm", bit_index=23, entity_category=EntityCategory.DIAGNOSTIC, device_class=BinarySensorDeviceClass.PROBLEM),
    HeruBinarySensorDescription(key="filter_timer_alarm", translation_key="filter_timer_alarm", bit_index=24, entity_category=EntityCategory.DIAGNOSTIC, device_class=BinarySensorDeviceClass.PROBLEM),
    HeruBinarySensorDescription(key="freeze_protection_b_level", translation_key="freeze_protection_b_level", bit_index=25),
    HeruBinarySensorDescription(key="freeze_protection_a_level", translation_key="freeze_protection_a_level", bit_index=26),
    HeruBinarySensorDescription(key="startup_phase_1", translation_key="startup_phase_1", bit_index=27),
    HeruBinarySensorDescription(key="startup_phase_2", translation_key="startup_phase_2", bit_index=28),
    HeruBinarySensorDescription(key="heating", translation_key="heating", bit_index=29),
    HeruBinarySensorDescription(key="recovering_heat_cold", translation_key="recovering_heat_cold", bit_index=30),
    HeruBinarySensorDescription(key="cooling", translation_key="cooling", bit_index=31),
    HeruBinarySensorDescription(key="co2_boost", translation_key="co2_boost", bit_index=32),
    HeruBinarySensorDescription(key="rh_boost", translation_key="rh_boost", bit_index=33),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Heru binary sensors."""
    coordinator: HeruDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(HeruBinarySensorEntity(coordinator, entry, description) for description in BINARY_SENSOR_DESCRIPTIONS)


class HeruBinarySensorEntity(CoordinatorEntity[HeruDataUpdateCoordinator], BinarySensorEntity):
    """Heru binary sensor."""

    entity_description: HeruBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator: HeruDataUpdateCoordinator, entry: ConfigEntry, description: HeruBinarySensorDescription) -> None:
        """Initialize entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def device_info(self):
        """Return device info."""
        return self.coordinator.device_info

    @property
    def is_on(self) -> bool:
        """Return true if the bit is set."""
        return self.coordinator.data.discrete_inputs[self.entity_description.bit_index]
