from __future__ import annotations

import threading
import time
from collections.abc import Callable

from core.reservation_service import ReservationService


class ReservationScheduler:
    """Thread-based scheduler for pending reservations."""

    def __init__(self, service: ReservationService) -> None:
        self.service = service
        self._worker_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._running_jobs: dict[int, tuple[threading.Thread, threading.Event]] = {}
        self._lock = threading.RLock()
        self._status_callback: Callable[[], None] | None = None

    def set_status_callback(self, callback: Callable[[], None]) -> None:
        self._status_callback = callback

    def start(self) -> None:
        if self._worker_thread and self._worker_thread.is_alive():
            return
        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._worker_thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        with self._lock:
            for _, cancel_event in self._running_jobs.values():
                cancel_event.set()

    def cancel_reservation(self, reservation_id: int) -> None:
        self.service.cancel_reservation(reservation_id)
        with self._lock:
            job = self._running_jobs.get(reservation_id)
            if job:
                job[1].set()

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            reservations = self.service.list_reservations()
            for row in reservations:
                res_id = row["id"]
                status = row["status"]
                if status != "Pending":
                    continue
                with self._lock:
                    if res_id in self._running_jobs:
                        continue
                    cancel_event = threading.Event()
                    thread = threading.Thread(
                        target=self._run_reservation,
                        args=(res_id, cancel_event),
                        daemon=True,
                    )
                    self._running_jobs[res_id] = (thread, cancel_event)
                    thread.start()
            if self._status_callback:
                self._status_callback()
            time.sleep(1)

    def _run_reservation(self, reservation_id: int, cancel_event: threading.Event) -> None:
        try:
            self.service.execute_reservation(reservation_id, cancel_check=cancel_event.is_set)
        finally:
            with self._lock:
                self._running_jobs.pop(reservation_id, None)
            if self._status_callback:
                self._status_callback()
