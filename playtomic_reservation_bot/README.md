# Playtomic Reservation Bot

Aplicación de escritorio para automatizar reservas de canchas en Playtomic con ejecución exacta **2 días antes** a la misma hora, control por segundos, Selenium y SQLite.

## Instalación

```bash
cd playtomic_reservation_bot
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

## Flujo de uso

1. Abra **Configuración** y agregue clubs, canchas y cuentas.
2. Configure zona horaria local y zona horaria objetivo (Playtomic).
3. En la ventana principal seleccione club/cancha y agregue reservas.
4. Inicie automatización para ejecutar las reservas pendientes.
5. Revise estados en tiempo real y logs en `logs/app.log`.

## Notas

- `execution_datetime_local = play_datetime_local - 2 días`.
- `booking_code` se genera en zona objetivo con `TimeZoneConverter`.
- Evita duplicados por `(court_id, account_id, play_datetime_local)`.
- En Windows, `tzdata` se instala como dependencia para evitar errores de `zoneinfo`.
