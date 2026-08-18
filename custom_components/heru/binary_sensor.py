"""Binary sensor platform for Heru integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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

from .const import ALARM_BITS, DOMAIN
from .coordinator import HeruDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class HeruBinarySensorDescription(BinarySensorEntityDescription):
    """Description of a Heru binary sensor."""

    bit_index: int


BINARY_SENSOR_DESCRIPTIONS: tuple[HeruBinarySensorDescription, ...] = (
    HeruBinarySensorDescription(key="fire_alarm_switch", translation_key="fire_alarm_switch", bit_index=0, entity_category=EntityCategory.DIAGNOSTIC),
    HeruBinarySensorDescription(key="boost_switch", translation_key="boost_switch", bit_index=1, entity_category=EntityCategory.DIAGNOSTIC),
    HeruBinarySensorDescription(key="overpressure_switch", translation_key="overpressure_switch", bit_index=2, entity_category=EntityCategory.DIAGNOSTIC),
    HeruBinarySensorDescription(key="aux_switch", translation_key="aux_switch", bit_index=3, entity_category=EntityCategory.DIAGNOSTIC),
    HeruBinarySensorDescription(key="freeze_protection_b_level", translation_key="freeze_protection_b_level", bit_index=25, entity_category=EntityCategory.DIAGNOSTIC),
    HeruBinarySensorDescription(key="freeze_protection_a_level", translation_key="freeze_protection_a_level", bit_index=26, entity_category=EntityCategory.DIAGNOSTIC),
    HeruBinarySensorDescription(key="startup_phase_1", translation_key="startup_phase_1", bit_index=27, entity_category=EntityCategory.DIAGNOSTIC),
    HeruBinarySensorDescription(key="startup_phase_2", translation_key="startup_phase_2", bit_index=28, entity_category=EntityCategory.DIAGNOSTIC),
    HeruBinarySensorDescription(key="heating", translation_key="heating", bit_index=29, device_class=BinarySensorDeviceClass.RUNNING),
    HeruBinarySensorDescription(key="recovering_heat_cold", translation_key="recovering_heat_cold", bit_index=30, device_class=BinarySensorDeviceClass.RUNNING),
    HeruBinarySensorDescription(key="cooling", translation_key="cooling", bit_index=31, device_class=BinarySensorDeviceClass.RUNNING),
    HeruBinarySensorDescription(key="co2_boost", translation_key="co2_boost", bit_index=32, device_class=BinarySensorDeviceClass.RUNNING),
    HeruBinarySensorDescription(key="rh_boost", translation_key="rh_boost", bit_index=33, device_class=BinarySensorDeviceClass.RUNNING),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Heru binary sensors."""
    coordinator: HeruDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[BinarySensorEntity] = [
        HeruBinarySensorEntity(coordinator, entry, description) for description in BINARY_SENSOR_DESCRIPTIONS
    ]
    entities.append(HeruAlarmBinarySensor(coordinator, entry))
    async_add_entities(entities)


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


class HeruAlarmBinarySensor(CoordinatorEntity[HeruDataUpdateCoordinator], BinarySensorEntity):
    """Every alarm bit as one entity, listing the ones currently active."""

    _attr_has_entity_name = True
    _attr_translation_key = "alarm"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: HeruDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the alarm summary."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_alarm"

    @property
    def device_info(self):
        """Return device info."""
        return self.coordinator.device_info

    @property
    def _active_alarms(self) -> list[str]:
        """Return the names of the alarms currently raised."""
        bits = self.coordinator.data.discrete_inputs
        return [name for index, name in ALARM_BITS if bits[index]]

    @property
    def is_on(self) -> bool:
        """Return True while any alarm is raised."""
        return bool(self._active_alarms)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """List the raised alarms, so one entity replaces thirteen."""
        active = self._active_alarms
        return {"active_alarms": active, "active_alarm_count": len(active)}
