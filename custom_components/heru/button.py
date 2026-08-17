"""Button platform for Heru integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COIL_CLEAR_ALARMS, COIL_RESET_FILTER_TIMER, DOMAIN
from .coordinator import HeruDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class HeruButtonDescription(ButtonEntityDescription):
    """Description of a Heru button."""

    coil: int


# These coils act on write and always read back 0, so they are buttons rather
# than switches.
BUTTON_DESCRIPTIONS: tuple[HeruButtonDescription, ...] = (
    HeruButtonDescription(
        key="clear_alarms",
        translation_key="clear_alarms",
        coil=COIL_CLEAR_ALARMS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    HeruButtonDescription(
        key="reset_filter_timer",
        translation_key="reset_filter_timer",
        coil=COIL_RESET_FILTER_TIMER,
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Heru buttons."""
    coordinator: HeruDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(HeruButtonEntity(coordinator, entry, description) for description in BUTTON_DESCRIPTIONS)


class HeruButtonEntity(CoordinatorEntity[HeruDataUpdateCoordinator], ButtonEntity):
    """Heru action button backed by a momentary coil."""

    entity_description: HeruButtonDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator: HeruDataUpdateCoordinator, entry: ConfigEntry, description: HeruButtonDescription) -> None:
        """Initialize button."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

    @property
    def device_info(self):
        """Return device info."""
        return self.coordinator.device_info

    async def async_press(self) -> None:
        """Trigger the action."""
        await self.coordinator.async_write_coil(self.entity_description.coil, True)
