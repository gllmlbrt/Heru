"""Button platform for Heru integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.util import dt as dt_util

from .const import (
    COIL_CLEAR_ALARMS,
    COIL_RESET_FILTER_TIMER,
    DOMAIN,
    HOLDING_REGISTER_CLOCK_HOURS,
    HOLDING_REGISTER_CLOCK_MINUTES,
    HOLDING_REGISTER_CLOCK_SECONDS,
    HOLDING_REGISTER_CLOCK_WEEKDAY,
)
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
    entities: list[ButtonEntity] = [
        HeruButtonEntity(coordinator, entry, description) for description in BUTTON_DESCRIPTIONS
    ]
    entities.append(HeruSyncClockButton(coordinator, entry))
    async_add_entities(entities)


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


class HeruSyncClockButton(CoordinatorEntity[HeruDataUpdateCoordinator], ButtonEntity):
    """Set the unit's clock from Home Assistant.

    The clock registers are a buffer: the weekday, hours and minutes are
    staged, and writing the seconds commits them. So the seconds are written
    last, and only that write refreshes.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "sync_clock"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, coordinator: HeruDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sync button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_sync_clock"

    @property
    def device_info(self):
        """Return device info."""
        return self.coordinator.device_info

    async def async_press(self) -> None:
        """Write Home Assistant's local time to the unit."""
        now = dt_util.now()
        # 0 = Monday ... 6 = Sunday on both sides.
        for register, value in (
            (HOLDING_REGISTER_CLOCK_WEEKDAY, now.weekday()),
            (HOLDING_REGISTER_CLOCK_HOURS, now.hour),
            (HOLDING_REGISTER_CLOCK_MINUTES, now.minute),
        ):
            await self.coordinator.async_write_holding_register(register, value, refresh=False)
        await self.coordinator.async_write_holding_register(
            HOLDING_REGISTER_CLOCK_SECONDS, now.second
        )
