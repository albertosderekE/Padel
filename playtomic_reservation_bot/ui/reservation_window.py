from __future__ import annotations

from datetime import datetime

import customtkinter as ctk
from tkcalendar import DateEntry
from tkinter import messagebox


class ReservationDialog(ctk.CTkToplevel):
    def __init__(self, parent: ctk.CTk, accounts: list[dict], on_submit: callable) -> None:
        super().__init__(parent)
        self.title("Nueva Reserva")
        self.geometry("420x280")
        self.accounts = accounts
        self.on_submit = on_submit

        ctk.CTkLabel(self, text="Fecha de juego").pack(pady=6)
        self.date_picker = DateEntry(self, date_pattern="yyyy-mm-dd")
        self.date_picker.pack(pady=6)

        ctk.CTkLabel(self, text="Hora (HH:MM)").pack(pady=6)
        self.hour_entry = ctk.CTkEntry(self, placeholder_text="07:00")
        self.hour_entry.pack(pady=6)

        ctk.CTkLabel(self, text="Cuenta").pack(pady=6)
        self.acc_menu = ctk.CTkOptionMenu(self, values=[f"{a['id']}|{a['email']}" for a in accounts])
        self.acc_menu.pack(pady=6)

        ctk.CTkButton(self, text="Guardar", command=self.submit).pack(pady=10)

    def submit(self) -> None:
        try:
            date_value = self.date_picker.get_date().strftime("%Y-%m-%d")
            hour_value = self.hour_entry.get().strip()
            dt = datetime.fromisoformat(f"{date_value}T{hour_value}:00")
            account_id = int(self.acc_menu.get().split("|")[0])
            self.on_submit(dt, account_id)
            self.destroy()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", f"Datos inválidos: {exc}")
