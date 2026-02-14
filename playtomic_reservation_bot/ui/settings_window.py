from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox

from database.db import Database


class SettingsWindow(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk, db: Database, on_change: callable) -> None:
        super().__init__(parent)
        self.db = db
        self.on_change = on_change
        self.title("Configuración")
        self.geometry("720x520")

        self.grid_columnconfigure((0, 1), weight=1)

        self.club_name = ctk.CTkEntry(self, placeholder_text="Nombre club")
        self.club_url = ctk.CTkEntry(self, placeholder_text="Base URL club")
        self.court_club = ctk.CTkEntry(self, placeholder_text="ID club")
        self.court_name = ctk.CTkEntry(self, placeholder_text="Nombre cancha")
        self.court_fragment = ctk.CTkEntry(self, placeholder_text="booking fragment URL")
        self.acc_email = ctk.CTkEntry(self, placeholder_text="Email")
        self.acc_pass = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.local_tz = ctk.CTkEntry(self, placeholder_text="Zona local, e.g. Europe/Madrid")
        self.target_tz = ctk.CTkEntry(self, placeholder_text="Zona Playtomic, e.g. UTC")

        widgets = [
            (ctk.CTkLabel(self, text="Club"), 0, 0),
            (self.club_name, 1, 0),
            (self.club_url, 2, 0),
            (ctk.CTkButton(self, text="Agregar Club", command=self.add_club), 3, 0),
            (ctk.CTkLabel(self, text="Cancha"), 4, 0),
            (self.court_club, 5, 0),
            (self.court_name, 6, 0),
            (self.court_fragment, 7, 0),
            (ctk.CTkButton(self, text="Agregar Cancha", command=self.add_court), 8, 0),
            (ctk.CTkLabel(self, text="Cuenta"), 0, 1),
            (self.acc_email, 1, 1),
            (self.acc_pass, 2, 1),
            (ctk.CTkButton(self, text="Agregar Cuenta", command=self.add_account), 3, 1),
            (ctk.CTkLabel(self, text="Zona horaria"), 4, 1),
            (self.local_tz, 5, 1),
            (self.target_tz, 6, 1),
            (ctk.CTkButton(self, text="Guardar Zonas Horarias", command=self.save_tz), 7, 1),
        ]
        for widget, row, col in widgets:
            widget.grid(row=row, column=col, padx=10, pady=6, sticky="ew")

    def _upsert_setting(self, key: str, value: str) -> None:
        self.db.execute(
            """
            INSERT INTO app_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )

    def add_club(self) -> None:
        try:
            self.db.execute(
                "INSERT INTO clubs (name, base_url) VALUES (?, ?)",
                (self.club_name.get().strip(), self.club_url.get().strip()),
            )
            self.on_change()
            messagebox.showinfo("OK", "Club agregado")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))

    def add_court(self) -> None:
        try:
            self.db.execute(
                "INSERT INTO courts (club_id, name, booking_fragment_url) VALUES (?, ?, ?)",
                (int(self.court_club.get()), self.court_name.get().strip(), self.court_fragment.get().strip()),
            )
            self.on_change()
            messagebox.showinfo("OK", "Cancha agregada")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))

    def add_account(self) -> None:
        try:
            self.db.execute(
                "INSERT INTO accounts (email, password, active) VALUES (?, ?, 1)",
                (self.acc_email.get().strip(), self.acc_pass.get().strip()),
            )
            self.on_change()
            messagebox.showinfo("OK", "Cuenta agregada")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))

    def save_tz(self) -> None:
        try:
            self._upsert_setting("local_tz", self.local_tz.get().strip())
            self._upsert_setting("target_tz", self.target_tz.get().strip())
            self.on_change()
            messagebox.showinfo("OK", "Zonas horarias guardadas")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))
