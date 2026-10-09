"""The Konkur countdown shown in every panel (DES-API-04)."""

from datetime import date
from typing import Any

PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def countdown(exam_day: date, today: date) -> dict[str, Any]:
    """Days left until `exam_day`, with a Persian label. Days left is 0 on and after the day."""
    remaining = (exam_day - today).days
    if remaining > 0:
        state = "upcoming"
        label = f"{str(remaining).translate(PERSIAN_DIGITS)} روز تا کنکور"
    elif remaining == 0:
        state = "today"
        label = "امروز روز کنکور است"
    else:
        state = "past"
        label = "کنکور برگزار شده است"
    return {
        "date": exam_day.isoformat(),
        "state": state,
        "days_remaining": max(remaining, 0),
        "label": label,
    }
