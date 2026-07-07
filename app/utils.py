"""Shared utility functions."""

from datetime import UTC, datetime


def parse_dt(dt_str: str | None) -> datetime | None:
    """Parse an ISO datetime string to timezone-aware datetime."""
    if not dt_str:
        return None
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except (ValueError, TypeError):
        return None
