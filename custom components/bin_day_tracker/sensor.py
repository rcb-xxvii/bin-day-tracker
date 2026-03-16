"""Sensor platform for Bin Day Tracker."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bin Day Tracker sensor based on a config entry."""
    async_add_entities([BinDayTrackerStatusSensor(entry)])


class BinDayTrackerStatusSensor(SensorEntity):
    """Representation of a simple Bin Day Tracker status sensor."""

    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_name = "Status"
        self._attr_native_value = "Ready"

    @property
    def extra_state_attributes(self) -> dict:
        """Return additional state attributes."""
        return {
            "integration": "Bin Day Tracker",
        }