"""Binary sensor platform for Bin Day Tracker."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .helpers import get_enabled_bins_with_calculations


def _next_midnight():
    """Return the next local midnight."""
    now = dt_util.now()
    tomorrow = now.date() + timedelta(days=1)
    return dt_util.as_local(dt_util.parse_datetime(f"{tomorrow.isoformat()}T00:00:00"))


class BinDayTrackerBinaryBaseEntity(BinarySensorEntity):
    """Base binary sensor for Bin Day Tracker."""

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
    """Set up Bin Day Tracker binary sensors."""
    async_add_entities(
        [
            BinCollectionTodayBinarySensor(entry),
            BinCollectionTomorrowBinarySensor(entry),
        ]
    )


class BinCollectionTodayBinarySensor(BinDayTrackerBinaryBaseEntity):
    """Binary sensor for any collection today."""

    _attr_has_entity_name = False
    _attr_name = "Bin Collection Today"
    _attr_unique_id = None
    _attr_icon = "mdi:calendar-today"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize binary sensor."""
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_collection_today"

    @property
    def is_on(self) -> bool:
        """Return true if any bin is due today."""
        bins = get_enabled_bins_with_calculations(self.entry.options.get("bins", []))
        return any(bin_item["days_until"] == 0 for bin_item in bins)

    @property
    def extra_state_attributes(self) -> dict:
        """Return due bins today."""
        bins = get_enabled_bins_with_calculations(self.entry.options.get("bins", []))
        due_today = [bin_item["name"] for bin_item in bins if bin_item["days_until"] == 0]
        return {"bins_due_today": due_today, "count": len(due_today)}


class BinCollectionTomorrowBinarySensor(BinDayTrackerBinaryBaseEntity):
    """Binary sensor for any collection tomorrow."""

    _attr_has_entity_name = False
    _attr_name = "Bin Collection Tomorrow"
    _attr_unique_id = None
    _attr_icon = "mdi:calendar"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize binary sensor."""
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_collection_tomorrow"

    @property
    def is_on(self) -> bool:
        """Return true if any bin is due tomorrow."""
        bins = get_enabled_bins_with_calculations(self.entry.options.get("bins", []))
        return any(bin_item["days_until"] == 1 for bin_item in bins)

    @property
    def extra_state_attributes(self) -> dict:
        """Return due bins tomorrow."""
        bins = get_enabled_bins_with_calculations(self.entry.options.get("bins", []))
        due_tomorrow = [
            bin_item["name"] for bin_item in bins if bin_item["days_until"] == 1
        ]
        return {"bins_due_tomorrow": due_tomorrow, "count": len(due_tomorrow)}