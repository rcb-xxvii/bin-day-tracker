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
    """Calculate the next collection date and countdown details.

    Future collections are based on:
    start_date + (N * repeat_days)

    Where N is the smallest non-negative integer such that the result
    is on or after today.
    """
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