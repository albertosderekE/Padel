from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Any, Iterable


class Database:
    """SQLite access layer with thread-safe helpers."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._initialize()

    @contextmanager
    def _connection(self) -> Iterable[sqlite3.Connection]:
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            finally:
                conn.close()

    def _initialize(self) -> None:
        with self._connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS clubs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    base_url TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS courts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    club_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    booking_fragment_url TEXT NOT NULL,
                    UNIQUE (club_id, name),
                    FOREIGN KEY (club_id) REFERENCES clubs(id)
                );

                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1
                );

                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    court_id INTEGER NOT NULL,
                    account_id INTEGER NOT NULL,
                    play_datetime_local TEXT NOT NULL,
                    execution_datetime_local TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (court_id) REFERENCES courts(id),
                    FOREIGN KEY (account_id) REFERENCES accounts(id),
                    UNIQUE (court_id, account_id, play_datetime_local)
                );
                """
            )

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> int:
        with self._connection() as conn:
            cursor = conn.execute(query, params)
            return cursor.lastrowid

    def fetchone(self, query: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        with self._connection() as conn:
            return conn.execute(query, params).fetchone()

    def fetchall(self, query: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with self._connection() as conn:
            return conn.execute(query, params).fetchall()
