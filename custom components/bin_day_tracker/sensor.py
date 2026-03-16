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

    entities: list[SensorEntity] = [
        BinTrackerStatusSensor(entry),
        BinNextCollectionSensor(entry),
    ]

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


class BinNextCollectionSensor(SensorEntity):
    """Aggregate sensor for the next collection."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:calendar-arrow-right"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the aggregate sensor."""
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_next_collection"
        self._attr_name = "Bin Day Tracker Next Collection"

    def _get_enabled_bins_with_calculations(self) -> list[dict]:
        """Return enabled bins with calculated countdown data."""
        bins = self.entry.options.get("bins", [])
        calculated_bins: list[dict] = []

        for bin_item in bins:
            if not bin_item.get("enabled", True):
                continue

            calculation = calculate_next_collection(
                start_date_str=bin_item["start_date"],
                repeat_days=bin_item["repeat_days"],
            )

            combined = dict(bin_item)
            combined.update(calculation)
            calculated_bins.append(combined)

        return calculated_bins

    def _get_selected_bin(self) -> tuple[dict | None, list[dict]]:
        """Return the selected display bin and all bins due that day."""
        calculated_bins = self._get_enabled_bins_with_calculations()

        if not calculated_bins:
            return None, []

        earliest_days_until = min(bin_item["days_until"] for bin_item in calculated_bins)

        due_bins = [
            bin_item
            for bin_item in calculated_bins
            if bin_item["days_until"] == earliest_days_until
        ]

        due_bins.sort(key=lambda item: item.get("display_order", 9999))

        primary_bins = [bin_item for bin_item in due_bins if bin_item.get("primary", False)]

        if primary_bins:
            selected_bin = primary_bins[0]
        else:
            selected_bin = due_bins[0]

        return selected_bin, due_bins

    @property
    def native_value(self):
        """Return the selected bin label."""
        selected_bin, _due_bins = self._get_selected_bin()

        if selected_bin is None:
            return "No bins configured"

        return selected_bin["name"]

    @property
    def extra_state_attributes(self):
        """Return aggregate sensor attributes."""
        selected_bin, due_bins = self._get_selected_bin()

        if selected_bin is None:
            return {
                "days_until": None,
                "next_collection": None,
                "primary_bin_selected": None,
                "also_due": [],
                "selected_bin_label": None,
                "selected_bin_colour": None,
                "selected_bin_entity_id": None,
            }

        colour_key = selected_bin["colour"]
        colour_data = COLOUR_OPTIONS.get(
            colour_key,
            {"label": colour_key, "hex": "#808080"},
        )

        also_due = [
            bin_item["name"]
            for bin_item in due_bins
            if bin_item["id"] != selected_bin["id"]
        ]

        selected_entity_id = (
            f"sensor.{selected_bin['name'].lower().replace(' ', '_')}_bin"
        )

        return {
            "days_until": selected_bin["days_until"],
            "next_collection": selected_bin["next_collection"],
            "primary_bin_selected": selected_bin["primary"],
            "also_due": also_due,
            "selected_bin_label": selected_bin["name"],
            "selected_bin_colour": colour_data["hex"],
            "selected_bin_colour_key": colour_key,
            "selected_bin_colour_label": colour_data["label"],
            "selected_bin_entity_id": selected_entity_id,
            "material": selected_bin["material"],
            "display_text": selected_bin["display_text"],
            "all_due_today": [bin_item["name"] for bin_item in due_bins],
        }