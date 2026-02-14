from __future__ import annotations

import logging
from pathlib import Path

import customtkinter as ctk

from core.reservation_service import ReservationService
from core.scheduler import ReservationScheduler
from core.tz_utils import load_timezone
from database.db import Database
from ui.main_window import MainWindow


def configure_logging(base_dir: Path) -> logging.Logger:
    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("playtomic_bot")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(threadName)s %(message)s")
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    return logger


def get_setting(db: Database, key: str, default: str) -> str:
    row = db.fetchone("SELECT value FROM app_settings WHERE key = ?", (key,))
    return row["value"] if row else default


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    logger = configure_logging(base_dir)
    db = Database(base_dir / "database" / "playtomic.db")

    local_tz = get_setting(db, "local_tz", "Europe/Madrid")
    target_tz = get_setting(db, "target_tz", "UTC")

    try:
        load_timezone(local_tz)
        load_timezone(target_tz)
    except ValueError as exc:
        logger.warning("Invalid configured timezone(s): %s. Falling back to UTC.", exc)
        local_tz = "UTC"
        target_tz = "UTC"

    service = ReservationService(db=db, logger=logger, local_tz=local_tz, target_tz=target_tz)
    scheduler = ReservationScheduler(service=service)

    ctk.set_appearance_mode("system")
    app = MainWindow(db=db, service=service, scheduler=scheduler)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()


if __name__ == "__main__":
    main()
