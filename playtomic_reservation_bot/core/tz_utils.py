from __future__ import annotations

from datetime import tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def load_timezone(name: str) -> tzinfo:
    """Load timezone using zoneinfo, then pytz fallback when tzdata/system DB is missing."""
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        try:
            import pytz
            from pytz.exceptions import UnknownTimeZoneError

            try:
                return pytz.timezone(name)
            except UnknownTimeZoneError as exc:
                raise ValueError(
                    f"Invalid timezone '{name}'. Use an IANA timezone (e.g. Europe/Madrid, UTC)."
                ) from exc
        except ModuleNotFoundError as exc:
            raise ValueError(
                "Timezone database not available. Install tzdata (and optionally pytz) and retry."
            ) from exc
