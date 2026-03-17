"""The Bin Day Tracker integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.CALENDAR,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema("bin_day_tracker")


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Bin Day Tracker integration."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bin Day Tracker from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Bin Day Tracker config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)