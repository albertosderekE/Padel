from __future__ import annotations

from datetime import datetime
from tkinter import messagebox, ttk

import customtkinter as ctk

from core.reservation_service import ReservationService
from core.scheduler import ReservationScheduler
from database.db import Database
from ui.reservation_window import ReservationDialog
from ui.settings_window import SettingsWindow


class MainWindow(ctk.CTk):
    def __init__(self, db: Database, service: ReservationService, scheduler: ReservationScheduler) -> None:
        super().__init__()
        self.db = db
        self.service = service
        self.scheduler = scheduler
        self.title("Playtomic Reservation Bot")
        self.geometry("1100x620")

        self.scheduler.set_status_callback(self._threadsafe_refresh)

        self.club_selector = ctk.CTkOptionMenu(self, values=[""], command=lambda _: self.refresh_courts())
        self.court_selector = ctk.CTkOptionMenu(self, values=[""])

        ctk.CTkLabel(self, text="Club").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.club_selector.grid(row=1, column=0, padx=8, pady=4, sticky="ew")
        ctk.CTkLabel(self, text="Cancha").grid(row=0, column=1, padx=8, pady=8, sticky="w")
        self.court_selector.grid(row=1, column=1, padx=8, pady=4, sticky="ew")

        ctk.CTkButton(self, text="Agregar Reserva", command=self.open_reservation_dialog).grid(row=1, column=2, padx=8)
        ctk.CTkButton(self, text="Configuración", command=self.open_settings).grid(row=1, column=3, padx=8)
        ctk.CTkButton(self, text="Iniciar Automatización", command=self.scheduler.start).grid(row=1, column=4, padx=8)
        ctk.CTkButton(self, text="Cancelar Reserva", command=self.cancel_selected).grid(row=1, column=5, padx=8)

        cols = ("id", "court", "email", "play_dt", "execution_dt", "status", "created")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=20)
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        self.tree.grid(row=2, column=0, columnspan=6, padx=10, pady=10, sticky="nsew")

        self.grid_rowconfigure(2, weight=1)
        for c in range(6):
            self.grid_columnconfigure(c, weight=1)

        self.refresh_selectors()
        self.refresh_reservations()
        self.after(1000, self._periodic_refresh)

    def _threadsafe_refresh(self) -> None:
        self.after(0, self.refresh_reservations)

    def _periodic_refresh(self) -> None:
        self.refresh_reservations()
        self.after(1500, self._periodic_refresh)

    def get_accounts(self) -> list[dict]:
        return [dict(r) for r in self.db.fetchall("SELECT id, email FROM accounts WHERE active = 1 ORDER BY email")]

    def refresh_selectors(self) -> None:
        clubs = [dict(r) for r in self.db.fetchall("SELECT id, name FROM clubs ORDER BY name")]
        values = [f"{c['id']}|{c['name']}" for c in clubs] or [""]
        self.club_selector.configure(values=values)
        self.club_selector.set(values[0])
        self.refresh_courts()

    def refresh_courts(self) -> None:
        club_value = self.club_selector.get()
        if "|" not in club_value:
            self.court_selector.configure(values=[""])
            self.court_selector.set("")
            return
        club_id = int(club_value.split("|")[0])
        courts = [dict(r) for r in self.db.fetchall("SELECT id, name FROM courts WHERE club_id = ?", (club_id,))]
        values = [f"{c['id']}|{c['name']}" for c in courts] or [""]
        self.court_selector.configure(values=values)
        self.court_selector.set(values[0])

    def open_settings(self) -> None:
        SettingsWindow(self, db=self.db, on_change=self._on_settings_change)

    def _on_settings_change(self) -> None:
        self.refresh_selectors()
        local_tz = self._get_setting("local_tz", "Europe/Madrid")
        target_tz = self._get_setting("target_tz", "UTC")
        self.service.refresh_timezones(local_tz, target_tz)

    def _get_setting(self, key: str, default: str) -> str:
        row = self.db.fetchone("SELECT value FROM app_settings WHERE key = ?", (key,))
        return row["value"] if row else default

    def open_reservation_dialog(self) -> None:
        accounts = self.get_accounts()
        if not accounts:
            messagebox.showerror("Error", "No hay cuentas activas")
            return
        ReservationDialog(self, accounts=accounts, on_submit=self._create_reservation)

    def _create_reservation(self, play_dt: datetime, account_id: int) -> None:
        court_value = self.court_selector.get()
        if "|" not in court_value:
            messagebox.showerror("Error", "Seleccione una cancha")
            return
        court_id = int(court_value.split("|")[0])
        try:
            self.service.create_reservation(court_id, account_id, play_dt)
            self.refresh_reservations()
            messagebox.showinfo("OK", "Reserva agregada")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))

    def refresh_reservations(self) -> None:
        for i in self.tree.get_children():
            self.tree.delete(i)
        for row in self.service.list_reservations():
            self.tree.insert(
                "",
                "end",
                values=(
                    row["id"],
                    row["court_name"],
                    row["email"],
                    row["play_datetime_local"],
                    row["execution_datetime_local"],
                    row["status"],
                    row["created_at"],
                ),
            )

    def cancel_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Seleccione una reserva")
            return
        reservation_id = int(self.tree.item(selected[0])["values"][0])
        self.scheduler.cancel_reservation(reservation_id)
        self.refresh_reservations()

    def on_close(self) -> None:
        self.scheduler.stop()
        self.destroy()
