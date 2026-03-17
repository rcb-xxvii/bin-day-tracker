"""Calendar platform for Bin Day Tracker."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.util import dt as dt_util

from .const import COLOUR_OPTIONS, DOMAIN
from .helpers import expand_bin_events_in_range


def _next_midnight():
    """Return the next local midnight."""
    now = dt_util.now()
    tomorrow = now.date() + timedelta(days=1)
    return dt_util.as_local(dt_util.parse_datetime(f"{tomorrow.isoformat()}T00:00:00"))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bin Day Tracker calendar."""
    async_add_entities([BinDayTrackerCalendar(entry)])


class BinDayTrackerCalendar(CalendarEntity):
    """Calendar entity for Bin Day Tracker."""

    _attr_has_entity_name = False
    _attr_name = "Bin Day Tracker"
    _attr_icon = "mdi:calendar"

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize the calendar."""
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._unsub_midnight: CALLBACK_TYPE | None = None

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
        """Refresh at midnight and reschedule."""
        self.async_write_ha_state()
        self._schedule_next_midnight_refresh()

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current or next upcoming event."""
        bins = self.entry.options.get("bins", [])
        today = dt_util.now().date()
        tomorrow = today + timedelta(days=366)

        events = expand_bin_events_in_range(bins, today, tomorrow)
        if not events:
            return None

        next_event = events[0]
        colour = COLOUR_OPTIONS.get(
            next_event["colour"],
            {"label": next_event["colour"], "hex": "#808080"},
        )

        return CalendarEvent(
            summary=next_event["name"],
            start=next_event["start"],
            end=next_event["end"],
            description=(
                f"Material: {next_event['material']}\n"
                f"Primary: {'Yes' if next_event['primary'] else 'No'}\n"
                f"Colour: {colour['label']} ({colour['hex']})"
            ),
        )

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events in the given range."""
        bins = self.entry.options.get("bins", [])

        start_day: date = start_date.date()
        end_day: date = end_date.date()

        events = expand_bin_events_in_range(bins, start_day, end_day)
        calendar_events: list[CalendarEvent] = []

        for item in events:
            colour = COLOUR_OPTIONS.get(
                item["colour"],
                {"label": item["colour"], "hex": "#808080"},
            )

            calendar_events.append(
                CalendarEvent(
                    summary=item["name"],
                    start=item["start"],
                    end=item["end"],
                    description=(
                        f"Material: {item['material']}\n"
                        f"Primary: {'Yes' if item['primary'] else 'No'}\n"
                        f"Colour: {colour['label']} ({colour['hex']})"
                    ),
                )
            )

        return calendar_events