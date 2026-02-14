from __future__ import annotations

from datetime import datetime


from core.tz_utils import load_timezone


class TimeZoneConverter:
    """Converts local datetimes to target timezone datetimes and booking codes."""

    def __init__(self, local_tz: str, target_tz: str):
        self.local_zone = load_timezone(local_tz)
        self.target_zone = load_timezone(target_tz)

    def local_to_target_hour(self, dt_local: datetime) -> datetime:
        if dt_local.tzinfo is None:
            dt_local = dt_local.replace(tzinfo=self.local_zone)
        else:
            dt_local = dt_local.astimezone(self.local_zone)
        return dt_local.astimezone(self.target_zone)

    def generate_booking_code(self, dt_local: datetime) -> str:
        dt_target = self.local_to_target_hour(dt_local)
        normalized_hour = dt_target.hour % 24
        return f"T{normalized_hour:02d}%3A00~60"
