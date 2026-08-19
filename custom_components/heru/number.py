"""Number platform for Heru integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    HOLDING_REGISTER_BOOST_DURATION,
    HOLDING_REGISTER_BOOST_SPEED,
    HOLDING_REGISTER_MAX_EXHAUST_FAN_SPEED_EC,
    HOLDING_REGISTER_MIN_EXHAUST_FAN_SPEED_EC,
    HOLDING_REGISTER_MOD_EXHAUST_FAN_SPEED_EC,
    HOLDING_REGISTER_OVERPRESSURE_DURATION,
    HOLDING_REGISTER_SNC_DIFF_LIMIT,
    HOLDING_REGISTER_SNC_HIGH_LIMIT,
    HOLDING_REGISTER_SNC_LOW_LIMIT,
    SNC_DIFF_LIMIT_MAX,
    SNC_DIFF_LIMIT_MIN,
    SNC_HIGH_LIMIT_MAX,
    SNC_HIGH_LIMIT_MIN,
    SNC_LOW_LIMIT_MAX,
    SNC_LOW_LIMIT_MIN,
    FREEZE_PROTECTION_LIMIT_MAX,
    FREEZE_PROTECTION_LIMIT_MIN,
    HOLDING_REGISTER_FREEZE_PROTECTION_LIMIT,
)
from .coordinator import HeruDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class HeruNumberDescription(NumberEntityDescription):
    """Description of a Heru number backed by a holding register."""

    register: int
    scale: float = 1.0


# Freeze protection has no enable register on this unit, only the limit below
# which it engages.
NUMBER_DESCRIPTIONS: tuple[HeruNumberDescription, ...] = (
    HeruNumberDescription(
        key="freeze_protection_limit",
        translation_key="freeze_protection_limit",
        register=HOLDING_REGISTER_FREEZE_PROTECTION_LIMIT,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=FREEZE_PROTECTION_LIMIT_MIN,
        native_max_value=FREEZE_PROTECTION_LIMIT_MAX,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
    ),
    # What each mode actually runs at on an EC unit.
    HeruNumberDescription(
        key="min_exhaust_fan_speed_ec",
        translation_key="min_exhaust_fan_speed_ec",
        register=HOLDING_REGISTER_MIN_EXHAUST_FAN_SPEED_EC,
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
    ),
    HeruNumberDescription(
        key="mod_exhaust_fan_speed_ec",
        translation_key="mod_exhaust_fan_speed_ec",
        register=HOLDING_REGISTER_MOD_EXHAUST_FAN_SPEED_EC,
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
    ),
    HeruNumberDescription(
        key="max_exhaust_fan_speed_ec",
        translation_key="max_exhaust_fan_speed_ec",
        register=HOLDING_REGISTER_MAX_EXHAUST_FAN_SPEED_EC,
        native_unit_of_measurement=PERCENTAGE,
        native_min_value=0,
        native_max_value=100,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
    ),
    HeruNumberDescription(
        key="boost_speed",
        translation_key="boost_speed",
        register=HOLDING_REGISTER_BOOST_SPEED,
        native_min_value=3,
        native_max_value=4,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
    ),
    HeruNumberDescription(
        key="boost_duration",
        translation_key="boost_duration",
        register=HOLDING_REGISTER_BOOST_DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        native_min_value=10,
        native_max_value=240,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
    ),
    # 4x00013 - 4x00015 decide when free cooling runs. Without them the enable
    # switch acts on whatever thresholds the unit happens to hold.
    HeruNumberDescription(
        key="snc_high_limit",
        translation_key="snc_high_limit",
        register=HOLDING_REGISTER_SNC_HIGH_LIMIT,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=SNC_HIGH_LIMIT_MIN,
        native_max_value=SNC_HIGH_LIMIT_MAX,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
    ),
    HeruNumberDescription(
        key="snc_low_limit",
        translation_key="snc_low_limit",
        register=HOLDING_REGISTER_SNC_LOW_LIMIT,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=SNC_LOW_LIMIT_MIN,
        native_max_value=SNC_LOW_LIMIT_MAX,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
    ),
    HeruNumberDescription(
        key="snc_diff_limit",
        translation_key="snc_diff_limit",
        register=HOLDING_REGISTER_SNC_DIFF_LIMIT,
        scale=0.1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_min_value=SNC_DIFF_LIMIT_MIN,
        native_max_value=SNC_DIFF_LIMIT_MAX,
        native_step=0.1,
        entity_category=EntityCategory.CONFIG,
    ),
    HeruNumberDescription(
        key="overpressure_duration",
        translation_key="overpressure_duration",
        register=HOLDING_REGISTER_OVERPRESSURE_DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        native_min_value=10,
        native_max_value=60,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Heru numbers."""
    coordinator: HeruDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(HeruNumberEntity(coordinator, entry, description) for description in NUMBER_DESCRIPTIONS)


class HeruNumberEntity(CoordinatorEntity[HeruDataUpdateCoordinator], NumberEntity):
    """Heru configuration value backed by a holding register."""

    entity_description: HeruNumberDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator: HeruDataUpdateCoordinator, entry: ConfigEntry, description: HeruNumberDescription) -> None:
        """Initialize number."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def device_info(self):
        """Return device info."""
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        """Return True if the unit exposes its configuration registers."""
        return super().available and self.coordinator.config_register(self.entity_description.register) is not None

    @property
    def native_value(self) -> float | None:
        """Return the configured value, in the unit the register reports."""
        value = self.coordinator.config_register(self.entity_description.register)
        if value is None:
            return None
        scale = self.entity_description.scale
        return float(value) if scale == 1.0 else round(value * scale, 1)

    async def async_set_native_value(self, value: float) -> None:
        """Write the configured value back in the register's own unit."""
        raw = int(round(value / self.entity_description.scale))
        await self.coordinator.async_write_holding_register(self.entity_description.register, raw)
