"""Number platform for Heru integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    FREEZE_PROTECTION_LIMIT_MAX,
    FREEZE_PROTECTION_LIMIT_MIN,
    HOLDING_REGISTER_FREEZE_PROTECTION_LIMIT,
)
from .coordinator import HeruDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class HeruNumberDescription(NumberEntityDescription):
    """Description of a Heru number backed by a holding register."""

    register: int


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
        """Return the configured value."""
        value = self.coordinator.config_register(self.entity_description.register)
        return None if value is None else float(value)

    async def async_set_native_value(self, value: float) -> None:
        """Write the configured value."""
        await self.coordinator.async_write_holding_register(self.entity_description.register, int(round(value)))
