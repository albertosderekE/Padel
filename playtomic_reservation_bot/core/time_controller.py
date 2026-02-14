from __future__ import annotations

import time
from datetime import datetime
from core.tz_utils import load_timezone


class TimeController:
    """Wait helper with adaptive precision until target datetime."""

    def __init__(self, local_tz: str) -> None:
        self.zone = load_timezone(local_tz)

    def now(self) -> datetime:
        return datetime.now(self.zone)

    def wait_until(self, target: datetime, cancel_check: callable) -> bool:
        if target.tzinfo is None:
            target = target.replace(tzinfo=self.zone)
        else:
            target = target.astimezone(self.zone)

        while True:
            if cancel_check():
                return False

            delta = (target - self.now()).total_seconds()
            if delta <= 0:
                return True
            if delta > 60:
                time.sleep(30)
            elif delta > 10:
                time.sleep(1)
            else:
                time.sleep(0.1)
