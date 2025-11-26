from __future__ import annotations

from datetime import time as datetime_time

DAY_LABELS = {
    "M": "Mon",
    "T": "Tue",
    "W": "Wed",
    "TR": "Thu",
    "F": "Fri",
    "TBA": "TBA",
}


def get_day_label(day_code: str | None) -> str:
    """
    Convert a raw day code into a display-friendly label.
    """
    if not day_code:
        return DAY_LABELS["TBA"]
    return DAY_LABELS.get(day_code, day_code)


def format_time_range(start: datetime_time | None, end: datetime_time | None) -> str:
    """
    Build a human-readable time range for a meeting.
    """
    if not start or not end:
        return "TBA"
    start_str = start.strftime("%I:%M %p").lstrip("0")
    end_str = end.strftime("%I:%M %p").lstrip("0")
    return f"{start_str} - {end_str}"

