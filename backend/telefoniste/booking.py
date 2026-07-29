"""
Multi-tenant SQLite kalender voor kapperszaken.
Elke afspraak heeft een business_id.
"""

import sqlite3
import os
from datetime import datetime, timedelta
from config import get_business

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "appointments.db")


def init_db():
    """Maak de appointments tabel aan met business_id."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT DEFAULT '',
            service TEXT NOT NULL,
            stylist TEXT DEFAULT '',
            appointment_datetime TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    # Index voor snelle lookups per business
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_business_date 
        ON appointments(business_id, appointment_datetime)
    """)
    conn.commit()
    conn.close()


def _next_date_for_day(day_of_week: str) -> str:
    """Eerstvolgende datum voor een dag (Engels, lowercase)."""
    day_map = {
        "monday": 0, "tuesday": 1, "wednesday": 2,
        "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
    }
    target = day_map[day_of_week]
    today = datetime.now().date()
    days_ahead = target - today.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return (today + timedelta(days=days_ahead)).isoformat()


def get_availability(business_id: str, day_of_week: str) -> dict:
    """
    Geef beschikbare tijdslots voor een business op een dag.
    Return: {"day": "woensdag 30 juli", "date": "2026-07-30", "slots": ["09:00", "09:30", ...]}
    """
    business = get_business(business_id)
    if not business:
        return {"error": f"Onbekende zaak: {business_id}"}

    date_str = _next_date_for_day(day_of_week)
    day_info = business["opening_hours"].get(day_of_week)

    if day_info is None:
        return {
            "business": business["name"],
            "day": f"{day_of_week} {date_str}",
            "date": date_str,
            "slots": [],
            "message": f"Wij zijn gesloten op {day_of_week}."
        }

    open_time = datetime.strptime(day_info["open"], "%H:%M").time()
    close_time = datetime.strptime(day_info["close"], "%H:%M").time()
    interval = business["slot_interval_min"]

    # Genereer alle slots
    all_slots = []
    current = datetime.combine(datetime.now().date(), open_time)
    end = datetime.combine(datetime.now().date(), close_time)

    while current + timedelta(minutes=30) <= end:
        slot_time = current.strftime("%H:%M")
        all_slots.append(slot_time)
        current += timedelta(minutes=interval)

    # Filter verleden slots
    now = datetime.now()
    if date_str == now.strftime("%Y-%m-%d"):
        now_time = now.strftime("%H:%M")
        all_slots = [s for s in all_slots if s > now_time]

    # Filter geboekte slots
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT appointment_datetime FROM appointments WHERE business_id = ? AND date(appointment_datetime) = ?",
        (business_id, date_str),
    )
    booked = {row[0] for row in cur.fetchall()}
    conn.close()

    available = [s for s in all_slots if f"{date_str}T{s}:00" not in booked]

    # Nederlandse dag vertaling
    day_nl = {
        "monday": "maandag", "tuesday": "dinsdag", "wednesday": "woensdag",
        "thursday": "donderdag", "friday": "vrijdag", "saturday": "zaterdag", "sunday": "zondag",
    }

    return {
        "business": business["name"],
        "day": f"{day_nl.get(day_of_week, day_of_week)} {date_str}",
        "date": date_str,
        "slots": available,
        "total": len(available),
    }


def book_appointment(
    business_id: str = "",
    day_of_week: str = "",
    time_str: str = "",
    customer_name: str = "",
    service: str = "",
    customer_phone: str = "",
    stylist: str = "",
) -> dict:
    """Boek een afspraak voor een specifieke business."""
    business = get_business(business_id)
    if not business:
        return {"success": False, "error": f"Onbekende zaak: {business_id}"}

    date = _next_date_for_day(day_of_week)
    appointment_iso = f"{date}T{time_str}:00"

    # Check of slot in de toekomst ligt
    try:
        slot_dt = datetime.fromisoformat(appointment_iso)
        if slot_dt <= datetime.now():
            return {"success": False, "error": "Dit tijdstip ligt in het verleden."}
    except ValueError:
        return {"success": False, "error": "Ongeldige datum of tijd."}

    # Valideer service
    valid_services = [s["name"] for s in business["services"]]
    if service not in valid_services:
        return {"success": False, "error": f"Ongeldige behandeling. Kies uit: {', '.join(valid_services)}"}

    # Valideer stylist (indien opgegeven)
    if stylist and stylist not in business.get("stylists", []):
        return {"success": False, "error": f"Ongeldige stylist. Kies uit: {', '.join(business['stylists'])}"}

    # Race condition check
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM appointments WHERE business_id = ? AND appointment_datetime = ?",
        (business_id, appointment_iso),
    )
    if cur.fetchone():
        conn.close()
        return {"success": False, "error": "Dit tijdstip is helaas net geboekt. Kies een ander tijdstip."}

    cur.execute(
        "INSERT INTO appointments (business_id, customer_name, customer_phone, service, stylist, appointment_datetime) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (business_id, customer_name, customer_phone, service, stylist, appointment_iso),
    )
    conn.commit()
    conn.close()

    service_info = next((s for s in business["services"] if s["name"] == service), {})
    return {
        "success": True,
        "appointment": {
            "business": business["name"],
            "customer_name": customer_name,
            "service": service,
            "price": service_info.get("price", 0),
            "duration": service_info.get("duration_min", 0),
            "stylist": stylist if stylist else "geen voorkeur",
            "datetime": appointment_iso,
            "day": day_of_week,
            "time": time_str,
        },
    }


init_db()
