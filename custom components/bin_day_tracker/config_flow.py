"""Config flow for Bin Day Tracker."""

from __future__ import annotations

from copy import deepcopy
import uuid

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlowWithReload
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

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


CONF_ACTION = "action"
ACTION_SAVE = "save"
ACTION_DELETE = "delete"


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
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowWithReload:
        """Return the options flow."""
        return BinDayTrackerOptionsFlowHandler()


class BinDayTrackerOptionsFlowHandler(OptionsFlowWithReload):
    """Handle options flow for Bin Day Tracker."""

    def __init__(self) -> None:
        """Initialize options flow."""
        self._selected_bin_id: str | None = None

    def _get_bins(self) -> list[dict]:
        """Return a mutable copy of configured bins."""
        return deepcopy(self.config_entry.options.get(CONF_BINS, []))

    def _save_bins(self, bins: list[dict]) -> FlowResult:
        """Save bins back to config entry options."""
        return self.async_create_entry(
            title="",
            data={CONF_BINS: bins},
        )

    def _find_bin_by_id(self, bins: list[dict], bin_id: str) -> dict | None:
        """Find a bin by ID."""
        for bin_item in bins:
            if bin_item[CONF_ID] == bin_id:
                return bin_item
        return None

    def _build_colour_selector(self, default: str = "blue") -> selector.SelectSelector:
        """Build colour dropdown selector."""
        options = [
            selector.SelectOptionDict(value=key, label=value["label"])
            for key, value in COLOUR_OPTIONS.items()
        ]
        return selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=options,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )

    def _build_bin_selector(self, bins: list[dict]) -> selector.SelectSelector:
        """Build bin dropdown selector."""
        options = [
            selector.SelectOptionDict(
                value=bin_item[CONF_ID],
                label=f"{bin_item[CONF_NAME]} ({bin_item[CONF_MATERIAL]})",
            )
            for bin_item in bins
        ]
        return selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=options,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )

    def _build_action_selector(self) -> selector.SelectSelector:
        """Build action dropdown selector."""
        return selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(value=ACTION_SAVE, label="Save changes"),
                    selector.SelectOptionDict(value=ACTION_DELETE, label="Delete bin"),
                ],
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        )

    def _build_bin_schema(self, defaults: dict | None = None) -> vol.Schema:
        """Build the add/edit bin form schema."""
        defaults = defaults or {}

        return vol.Schema(
            {
                vol.Required(
                    CONF_NAME,
                    default=defaults.get(CONF_NAME, ""),
                ): str,
                vol.Required(
                    CONF_MATERIAL,
                    default=defaults.get(CONF_MATERIAL, ""),
                ): str,
                vol.Required(
                    CONF_COLOUR,
                    default=defaults.get(CONF_COLOUR, "blue"),
                ): self._build_colour_selector(defaults.get(CONF_COLOUR, "blue")),
                vol.Required(
                    CONF_ENABLED,
                    default=defaults.get(CONF_ENABLED, True),
                ): bool,
                vol.Required(
                    CONF_PRIMARY,
                    default=defaults.get(CONF_PRIMARY, True),
                ): bool,
                vol.Required(
                    CONF_START_DATE,
                    default=defaults.get(CONF_START_DATE, ""),
                ): str,
                vol.Required(
                    CONF_REPEAT_DAYS,
                    default=defaults.get(CONF_REPEAT_DAYS, 14),
                ): int,
            }
        )

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage Bin Day Tracker options."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["add_bin", "manage_bins"],
        )

    async def async_step_add_bin(self, user_input=None) -> FlowResult:
        """Add a new bin."""
        bins = self._get_bins()
        errors: dict[str, str] = {}

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
                return self._save_bins(bins)

        return self.async_show_form(
            step_id="add_bin",
            data_schema=self._build_bin_schema(),
            errors=errors,
        )

    async def async_step_manage_bins(self, user_input=None) -> FlowResult:
        """Select a bin to edit."""
        bins = self._get_bins()

        if not bins:
            return self.async_abort(reason="no_bins_configured")

        if user_input is not None:
            self._selected_bin_id = user_input["selected_bin"]
            return await self.async_step_edit_selected_bin()

        schema = vol.Schema(
            {
                vol.Required("selected_bin"): self._build_bin_selector(bins),
            }
        )

        return self.async_show_form(
            step_id="manage_bins",
            data_schema=schema,
        )

    async def async_step_edit_selected_bin(self, user_input=None) -> FlowResult:
        """Edit the selected bin or route to delete."""
        bins = self._get_bins()

        if self._selected_bin_id is None:
            return self.async_abort(reason="bin_not_found")

        selected_bin = self._find_bin_by_id(bins, self._selected_bin_id)
        if selected_bin is None:
            return self.async_abort(reason="bin_not_found")

        errors: dict[str, str] = {}

        if user_input is not None:
            action = user_input.get(CONF_ACTION, ACTION_SAVE)

            if action == ACTION_DELETE:
                return await self.async_step_delete_selected_bin()

            existing_names = {
                bin_item[CONF_NAME].strip().lower()
                for bin_item in bins
                if bin_item[CONF_ID] != self._selected_bin_id
            }

            if user_input[CONF_NAME].strip().lower() in existing_names:
                errors[CONF_NAME] = "duplicate_name"
            elif user_input[CONF_REPEAT_DAYS] <= 0:
                errors[CONF_REPEAT_DAYS] = "repeat_days_invalid"
            else:
                updated_bins = []

                for bin_item in bins:
                    if bin_item[CONF_ID] == self._selected_bin_id:
                        updated_bin = dict(bin_item)
                        updated_bin.update(
                            {
                                CONF_NAME: user_input[CONF_NAME].strip(),
                                CONF_MATERIAL: user_input[CONF_MATERIAL].strip(),
                                CONF_COLOUR: user_input[CONF_COLOUR],
                                CONF_ENABLED: user_input[CONF_ENABLED],
                                CONF_PRIMARY: user_input[CONF_PRIMARY],
                                CONF_START_DATE: user_input[CONF_START_DATE].strip(),
                                CONF_REPEAT_DAYS: user_input[CONF_REPEAT_DAYS],
                            }
                        )
                        updated_bins.append(updated_bin)
                    else:
                        updated_bins.append(bin_item)

                return self._save_bins(updated_bins)

        schema = self._build_bin_schema(selected_bin)
        schema = schema.extend(
            {
                vol.Required(CONF_ACTION, default=ACTION_SAVE): self._build_action_selector(),
            }
        )

        return self.async_show_form(
            step_id="edit_selected_bin",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "bin_name": selected_bin[CONF_NAME],
            },
        )

    async def async_step_delete_selected_bin(self, user_input=None) -> FlowResult:
        """Delete the selected bin."""
        bins = self._get_bins()

        if self._selected_bin_id is None:
            return self.async_abort(reason="bin_not_found")

        selected_bin = self._find_bin_by_id(bins, self._selected_bin_id)
        if selected_bin is None:
            return self.async_abort(reason="bin_not_found")

        if user_input is not None:
            if user_input["confirm"]:
                updated_bins = [
                    bin_item
                    for bin_item in bins
                    if bin_item[CONF_ID] != self._selected_bin_id
                ]

                for index, bin_item in enumerate(updated_bins):
                    bin_item[CONF_DISPLAY_ORDER] = index

                return self._save_bins(updated_bins)

            return await self.async_step_edit_selected_bin()

        schema = vol.Schema(
            {
                vol.Required("confirm", default=False): bool,
            }
        )

        return self.async_show_form(
            step_id="delete_selected_bin",
            data_schema=schema,
            description_placeholders={
                "bin_name": selected_bin[CONF_NAME],
            },
        )