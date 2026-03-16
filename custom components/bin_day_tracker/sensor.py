"""Sensor platform for Bin Day Tracker."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import COLOUR_OPTIONS
from .helpers import calculate_next_collection


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bin Day Tracker sensors."""
    bins = entry.options.get("bins", [])

    entities: list[SensorEntity] = [BinTrackerStatusSensor(entry)]

    for bin_item in bins:
        if bin_item.get("enabled", True):
            entities.append(BinCountdownSensor(entry, bin_item))

    async_add_entities(entities)


class BinTrackerStatusSensor(SensorEntity):
    """Status sensor showing bin tracker info."""

    _attr_has_entity_name = False

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_name = "Bin Day Tracker Status"

    @property
    def native_value(self):
        """Return sensor state."""
        bins = self.entry.options.get("bins", [])
        return f"{len(bins)} bins configured"

    @property
    def extra_state_attributes(self):
        """Return sensor attributes."""
        bins = self.entry.options.get("bins", [])
        calculated_bins = []

        for bin_item in bins:
            bin_data = dict(bin_item)

            if bin_item.get("enabled", True):
                calculation = calculate_next_collection(
                    start_date_str=bin_item["start_date"],
                    repeat_days=bin_item["repeat_days"],
                )
                bin_data.update(calculation)

            calculated_bins.append(bin_data)

        return {
            "total_bins": len(bins),
            "bins": calculated_bins,
        }


class BinCountdownSensor(SensorEntity):
    """Countdown sensor for an individual bin."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:trash-can-outline"

    def __init__(self, entry: ConfigEntry, bin_item: dict) -> None:
        """Initialize the bin sensor."""
        self.entry = entry
        self.bin_item = bin_item

        self._attr_unique_id = f"{entry.entry_id}_{bin_item['id']}"
        self._attr_name = f"{bin_item['name']} Bin"

    @property
    def native_value(self):
        """Return the countdown text."""
        calculation = calculate_next_collection(
            start_date_str=self.bin_item["start_date"],
            repeat_days=self.bin_item["repeat_days"],
        )
        return calculation["display_text"]

    @property
    def extra_state_attributes(self):
        """Return sensor attributes."""
        calculation = calculate_next_collection(
            start_date_str=self.bin_item["start_date"],
            repeat_days=self.bin_item["repeat_days"],
        )

        colour_key = self.bin_item["colour"]
        colour_data = COLOUR_OPTIONS.get(
            colour_key,
            {"label": colour_key, "hex": "#808080"},
        )

        return {
            "bin_name": self.bin_item["name"],
            "material": self.bin_item["material"],
            "bin_colour_key": colour_key,
            "bin_colour_label": colour_data["label"],
            "bin_colour_hex": colour_data["hex"],
            "start_date": self.bin_item["start_date"],
            "repeat_days": self.bin_item["repeat_days"],
            "days_until": calculation["days_until"],
            "next_collection": calculation["next_collection"],
            "primary": self.bin_item["primary"],
            "enabled": self.bin_item["enabled"],
            "display_order": self.bin_item["display_order"],
        }