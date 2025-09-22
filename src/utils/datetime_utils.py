"""
Datetime utility functions for timezone-aware operations.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def utc_now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime.

    Returns:
        datetime: Current UTC time with timezone info
    """
    return datetime.now(timezone.utc)


def utc_now_isoformat() -> str:
    """
    Get current UTC time as ISO format string.

    Returns:
        str: Current UTC time in ISO format
    """
    return utc_now().isoformat()


def utc_now_timestamp() -> float:
    """
    Get current UTC time as Unix timestamp.

    Returns:
        float: Current UTC time as Unix timestamp
    """
    return utc_now().timestamp()


def utc_now_date():
    """
    Get current UTC date.

    Returns:
        date: Current UTC date
    """
    return utc_now().date()


def parse_datetime(datetime_str: str) -> datetime:
    """
    Parse datetime string to timezone-aware datetime.

    Args:
        datetime_str: Datetime string (ISO format)

    Returns:
        datetime: Parsed datetime with timezone info
    """
    # Remove 'Z' suffix if present and parse
    clean_str = datetime_str.replace("Z", "")
    dt = datetime.fromisoformat(clean_str)

    # If the parsed datetime is naive, make it UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt


def to_tz_iso(dt_or_str, tz_name: str) -> str:
    """
    Convert a datetime (or ISO string) to a specific IANA timezone and return ISO.

    Args:
        dt_or_str: datetime or ISO string
        tz_name: e.g. 'America/New_York'

    Returns:
        str: ISO string in requested timezone
    """
    if isinstance(dt_or_str, str):
        dt = parse_datetime(dt_or_str)
    else:
        dt = dt_or_str
    return dt.astimezone(ZoneInfo(tz_name)).isoformat()
