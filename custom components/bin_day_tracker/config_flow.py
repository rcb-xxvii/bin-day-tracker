"""Config flow for Bin Day Tracker."""

from __future__ import annotations

from copy import deepcopy
import uuid

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_BINS,
    CONF_COLOUR,
    CONF_DISPLAY_ORDER,
    CONF_ENABLED,
    CONF_ID,
    CONF_MATERIAL,
    CONF_NAME,
    CONF_PRIMARY,
    CONF_REPEAT_DAYS,
    CONF_START_DATE,
    COLOUR_OPTIONS,
    DOMAIN,
    MAX_BINS,
)


class BinDayTrackerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bin Day Tracker."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(
            title="Bin Day Tracker",
            data={},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return BinDayTrackerOptionsFlow()


class BinDayTrackerOptionsFlow(OptionsFlow):
    """Handle options flow for Bin Day Tracker."""

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage Bin Day Tracker options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_bin"],
        )

    async def async_step_add_bin(self, user_input=None) -> FlowResult:
        """Add a new bin."""
        errors: dict[str, str] = {}

        bins = deepcopy(self.config_entry.options.get(CONF_BINS, []))

        if user_input is not None:
            existing_names = {bin_item[CONF_NAME].strip().lower() for bin_item in bins}

            if len(bins) >= MAX_BINS:
                errors["base"] = "max_bins_reached"
            elif user_input[CONF_NAME].strip().lower() in existing_names:
                errors[CONF_NAME] = "duplicate_name"
            elif user_input[CONF_REPEAT_DAYS] <= 0:
                errors[CONF_REPEAT_DAYS] = "repeat_days_invalid"
            else:
                new_bin = {
                    CONF_ID: str(uuid.uuid4()),
                    CONF_NAME: user_input[CONF_NAME].strip(),
                    CONF_MATERIAL: user_input[CONF_MATERIAL].strip(),
                    CONF_COLOUR: user_input[CONF_COLOUR],
                    CONF_ENABLED: user_input[CONF_ENABLED],
                    CONF_PRIMARY: user_input[CONF_PRIMARY],
                    CONF_START_DATE: user_input[CONF_START_DATE].strip(),
                    CONF_REPEAT_DAYS: user_input[CONF_REPEAT_DAYS],
                    CONF_DISPLAY_ORDER: len(bins),
                }

                bins.append(new_bin)

                return self.async_create_entry(
                    title="",
                    data={CONF_BINS: bins},
                )

        colour_choices = {
            key: value["label"] for key, value in COLOUR_OPTIONS.items()
        }

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_MATERIAL): str,
                vol.Required(CONF_COLOUR, default="blue"): vol.In(colour_choices),
                vol.Required(CONF_ENABLED, default=True): bool,
                vol.Required(CONF_PRIMARY, default=True): bool,
                vol.Required(CONF_START_DATE): str,
                vol.Required(CONF_REPEAT_DAYS, default=14): int,
            }
        )

        return self.async_show_form(
            step_id="add_bin",
            data_schema=schema,
            errors=errors,
        )