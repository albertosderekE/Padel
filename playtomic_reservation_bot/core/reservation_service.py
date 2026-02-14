from __future__ import annotations

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from core.playtomic_bot import PlaytomicBot
from core.time_controller import TimeController
from core.time_converter import TimeZoneConverter
from database.db import Database


class ReservationService:
    """Domain service for reservation lifecycle management."""

    VALID_STATUSES = {"Pending", "Waiting", "Running", "Success", "Failed", "Cancelled"}

    def __init__(
        self,
        db: Database,
        logger: logging.Logger,
        local_tz: str,
        target_tz: str,
    ) -> None:
        self.db = db
        self.logger = logger
        self.local_tz = local_tz
        self.target_tz = target_tz
        self.converter = TimeZoneConverter(local_tz=local_tz, target_tz=target_tz)
        self.timer = TimeController(local_tz=local_tz)
        self.bot = PlaytomicBot(logger=logger)
        self._zone = ZoneInfo(local_tz)

    def refresh_timezones(self, local_tz: str, target_tz: str) -> None:
        self.local_tz = local_tz
        self.target_tz = target_tz
        self.converter = TimeZoneConverter(local_tz=local_tz, target_tz=target_tz)
        self.timer = TimeController(local_tz=local_tz)
        self._zone = ZoneInfo(local_tz)

    def create_reservation(self, court_id: int, account_id: int, play_dt_local: datetime) -> int:
        if play_dt_local.tzinfo is None:
            play_dt_local = play_dt_local.replace(tzinfo=self._zone)
        execution_dt = play_dt_local - timedelta(days=2)

        duplicate = self.db.fetchone(
            """
            SELECT id FROM reservations
            WHERE court_id = ? AND account_id = ? AND play_datetime_local = ?
            """,
            (court_id, account_id, play_dt_local.isoformat()),
        )
        if duplicate:
            raise ValueError("Duplicate reservation for same account, court and datetime")

        return self.db.execute(
            """
            INSERT INTO reservations (court_id, account_id, play_datetime_local, execution_datetime_local, status)
            VALUES (?, ?, ?, ?, 'Pending')
            """,
            (court_id, account_id, play_dt_local.isoformat(), execution_dt.isoformat()),
        )

    def list_reservations(self) -> list[dict]:
        rows = self.db.fetchall(
            """
            SELECT r.id, c.name AS court_name, a.email, r.play_datetime_local,
                   r.execution_datetime_local, r.status, r.created_at
            FROM reservations r
            JOIN courts c ON c.id = r.court_id
            JOIN accounts a ON a.id = r.account_id
            ORDER BY r.execution_datetime_local ASC
            """
        )
        return [dict(row) for row in rows]

    def set_status(self, reservation_id: int, status: str) -> None:
        if status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid reservation status {status}")
        self.db.execute("UPDATE reservations SET status = ? WHERE id = ?", (status, reservation_id))

    def cancel_reservation(self, reservation_id: int) -> None:
        self.set_status(reservation_id, "Cancelled")

    def execute_reservation(self, reservation_id: int, cancel_check: callable) -> None:
        row = self.db.fetchone(
            """
            SELECT r.id, r.play_datetime_local, r.execution_datetime_local,
                   c.booking_fragment_url, cl.base_url,
                   a.email, a.password, a.active
            FROM reservations r
            JOIN courts c ON c.id = r.court_id
            JOIN clubs cl ON cl.id = c.club_id
            JOIN accounts a ON a.id = r.account_id
            WHERE r.id = ?
            """,
            (reservation_id,),
        )
        if not row:
            self.logger.error("Reservation %s not found", reservation_id)
            return

        if row["active"] == 0:
            self.logger.error("Reservation %s failed: account inactive", reservation_id)
            self.set_status(reservation_id, "Failed")
            return

        play_dt = datetime.fromisoformat(row["play_datetime_local"])
        execution_dt = datetime.fromisoformat(row["execution_datetime_local"])

        self.logger.info("Reservation %s waiting until %s", reservation_id, execution_dt.isoformat())
        self.set_status(reservation_id, "Waiting")

        wait_ok = self.timer.wait_until(execution_dt, cancel_check=cancel_check)
        if not wait_ok:
            self.logger.info("Reservation %s cancelled before execution", reservation_id)
            self.set_status(reservation_id, "Cancelled")
            return

        self.set_status(reservation_id, "Running")
        booking_code = self.converter.generate_booking_code(play_dt)
        self.logger.info(
            "Reservation %s timezone conversion local=%s booking_code=%s",
            reservation_id,
            play_dt.isoformat(),
            booking_code,
        )

        result = self.bot.reserve(
            email=row["email"],
            password=row["password"],
            base_url=row["base_url"],
            booking_fragment_url=row["booking_fragment_url"],
            play_datetime_local=play_dt,
            booking_code=booking_code,
        )

        self.set_status(reservation_id, "Success" if result.ok else "Failed")
        self.logger.info("Reservation %s result: %s", reservation_id, result.message)
