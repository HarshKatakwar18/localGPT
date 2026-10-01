from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from langchain_core.tools import tool


@tool
def get_current_datetime(timezone_name: str = "UTC") -> str:
    """
    Get the current date and time for a specific IANA timezone.

    Use this tool whenever the user asks for the current date,
    current time, today's date, or the current date/time in a
    particular location.

    Examples of valid timezone names:
    UTC
    Asia/Kolkata
    America/New_York
    Europe/London
    Asia/Tokyo
    """

    timezone_name = timezone_name.strip()

    if not timezone_name:
        timezone_name = "UTC"

    try:
        timezone = ZoneInfo(timezone_name)

    except ZoneInfoNotFoundError:
        return (
            f"Error: Unknown timezone '{timezone_name}'. "
            "Use an IANA timezone such as Asia/Kolkata or UTC."
        )

    current_time = datetime.now(timezone)

    return (
        f"Current date and time in {timezone_name}: "
        f"{current_time.strftime('%A, %d %B %Y, %I:%M:%S %p %Z')}"
    )