"""Sensor platform for Bin Day Tracker."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.util import dt as dt_util

from .const import COLOUR_OPTIONS, DOMAIN
from .helpers import (
    calculate_next_collection,
    get_enabled_bins_with_calculations,
    select_next_display_bin,
)


def _next_midnight():
    """Return the next local midnight."""
    now = dt_util.now()
    tomorrow = now.date() + timedelta(days=1)
    return dt_util.as_local(dt_util.parse_datetime(f"{tomorrow.isoformat()}T00:00:00"))


class BinDayTrackerBaseEntity(SensorEntity):
    """Base entity for Bin Day Tracker."""

    _attr_should_poll = False
    _unsub_midnight: CALLBACK_TYPE | None = None

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the base entity."""
        self.entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for grouping entities."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name="Bin Day Tracker",
            manufacturer="Community",
            model="Bin Day Tracker",
        )

    async def async_added_to_hass(self) -> None:
        """Register midnight refresh."""
        self._schedule_next_midnight_refresh()

    async def async_will_remove_from_hass(self) -> None:
        """Clean up listeners."""
        if self._unsub_midnight:
            self._unsub_midnight()
            self._unsub_midnight = None

    @callback
    def _schedule_next_midnight_refresh(self) -> None:
        """Schedule the next midnight refresh."""
        if self._unsub_midnight:
            self._unsub_midnight()

        self._unsub_midnight = async_track_point_in_time(
            self.hass,
            self._handle_midnight_refresh,
            _next_midnight(),
        )

    @callback
    def _handle_midnight_refresh(self, _now) -> None:
        """Refresh state at midnight and reschedule."""
        self.async_schedule_update_ha_state()
        self._schedule_next_midnight_refresh()


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


class BinTrackerStatusSensor(BinDayTrackerBaseEntity):
    """Status sensor showing bin tracker info."""

    _attr_has_entity_name = False

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(entry)
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


class BinCountdownSensor(BinDayTrackerBaseEntity):
    """Countdown sensor for an individual bin."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:trash-can-outline"

    def __init__(self, entry: ConfigEntry, bin_item: dict) -> None:
        """Initialize the bin sensor."""
        super().__init__(entry)
        self.bin_item = bin_item
        self._attr_unique_id = f"{entry.entry_id}_{bin_item['id']}"
        self._attr_name = f"Bin {bin_item['name']}"

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


class BinNextCollectionSensor(BinDayTrackerBaseEntity):
    """Aggregate sensor for the next collection."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:calendar-arrow-right"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the aggregate sensor."""
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_next_collection"
        self._attr_name = "Bin Day Tracker Next Collection"

    @property
    def native_value(self):
        """Return the selected bin label."""
        selected_bin, _due_bins = select_next_display_bin(
            self.entry.options.get("bins", [])
        )

        if selected_bin is None:
            return "No bins configured"

        return selected_bin["name"]

    @property
    def extra_state_attributes(self):
        """Return aggregate sensor attributes."""
        selected_bin, due_bins = select_next_display_bin(
            self.entry.options.get("bins", [])
        )

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

        selected_entity_id = f"sensor.bin_{selected_bin['name'].lower().replace(' ', '_')}"

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