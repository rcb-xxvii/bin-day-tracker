"""Helper functions for Bin Day Tracker."""

from __future__ import annotations

from datetime import date, datetime, timedelta


def parse_bin_date(date_str: str) -> date:
    """Parse a YYYY-MM-DD string into a date object."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def format_countdown(days_until: int) -> str:
    """Return the display text for a countdown."""
    if days_until == 0:
        return "today"
    if days_until == 1:
        return "tomorrow"
    return f"{days_until} days"


def calculate_next_collection(
    start_date_str: str,
    repeat_days: int,
    today: date | None = None,
) -> dict:
    """Calculate the next collection date and countdown details."""
    if today is None:
        today = date.today()

    start_date = parse_bin_date(start_date_str)

    if repeat_days <= 0:
        raise ValueError("repeat_days must be greater than 0")

    if start_date >= today:
        next_collection = start_date
    else:
        days_since_start = (today - start_date).days
        intervals_passed = days_since_start // repeat_days
        next_collection = start_date + timedelta(days=intervals_passed * repeat_days)

        if next_collection < today:
            next_collection += timedelta(days=repeat_days)

    days_until = (next_collection - today).days

    return {
        "next_collection": next_collection.isoformat(),
        "days_until": days_until,
        "display_text": format_countdown(days_until),
    }


def get_enabled_bins_with_calculations(bins: list[dict]) -> list[dict]:
    """Return enabled bins with calculated countdown data."""
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


def select_next_display_bin(bins: list[dict]) -> tuple[dict | None, list[dict]]:
    """Return the selected display bin and all bins due on the earliest day."""
    calculated_bins = get_enabled_bins_with_calculations(bins)

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