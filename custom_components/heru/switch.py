"""Switch platform for Heru integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    COIL_AWAY_MODE,
    COIL_BOOST_MODE,
    COIL_OVERPRESSURE_MODE,
    COIL_UNIT_ON,
    DOMAIN,
)
from .coordinator import HeruDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class HeruSwitchDescription(SwitchEntityDescription):
    """Description of a Heru switch."""

    coil: int


SWITCH_DESCRIPTIONS: tuple[HeruSwitchDescription, ...] = (
    HeruSwitchDescription(
        key="unit_on",
        translation_key="unit_on",
        coil=COIL_UNIT_ON,
        device_class=SwitchDeviceClass.SWITCH,
    ),
    HeruSwitchDescription(
        key="overpressure_mode",
        translation_key="overpressure_mode",
        coil=COIL_OVERPRESSURE_MODE,
        device_class=SwitchDeviceClass.SWITCH,
    ),
    HeruSwitchDescription(
        key="boost_mode",
        translation_key="boost_mode",
        coil=COIL_BOOST_MODE,
        device_class=SwitchDeviceClass.SWITCH,
    ),
    HeruSwitchDescription(
        key="away_mode",
        translation_key="away_mode",
        coil=COIL_AWAY_MODE,
        device_class=SwitchDeviceClass.SWITCH,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Heru switches."""
    coordinator: HeruDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(HeruSwitchEntity(coordinator, entry, description) for description in SWITCH_DESCRIPTIONS)


class HeruSwitchEntity(CoordinatorEntity[HeruDataUpdateCoordinator], SwitchEntity):
    """Heru mode switch backed by a coil."""

    entity_description: HeruSwitchDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator: HeruDataUpdateCoordinator, entry: ConfigEntry, description: HeruSwitchDescription) -> None:
        """Initialize switch."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def device_info(self):
        """Return device info."""
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        """Return True if the unit exposes its coils."""
        return super().available and self.coordinator.data.coils is not None

    @property
    def is_on(self) -> bool | None:
        """Return whether the mode is active."""
        coils = self.coordinator.data.coils
        if coils is None:
            return None
        return coils[self.entity_description.coil]

    async def async_turn_on(self, **kwargs) -> None:
        """Enable the mode."""
        await self.coordinator.async_write_coil(self.entity_description.coil, True)

    async def async_turn_off(self, **kwargs) -> None:
        """Disable the mode."""
        await self.coordinator.async_write_coil(self.entity_description.coil, False)
