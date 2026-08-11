"""
SQLite database models for Yard Management System.
Uses threading.Lock per DC for race condition protection.
"""

import sqlite3
import uuid
import threading
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "yard.db"

# Per-DC locks for race condition protection.
# RLock (reentrant) zodat geneste lock-aanroepen niet deadlocken:
# call_next_driver → assign_driver_to_dock pakt dezelfde DC-lock nog eens.
_dc_locks: dict[str, threading.RLock] = {}
_global_lock = threading.RLock()


def _get_dc_lock(dc_id: str) -> threading.RLock:
    with _global_lock:
        if dc_id not in _dc_locks:
            _dc_locks[dc_id] = threading.RLock()
        return _dc_locks[dc_id]


def _lock_dc(dc_id: str):
    return _get_dc_lock(dc_id)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def dict_from_row(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    return dict(row)


def init_db():
    """Create all tables and seed data."""
    conn = get_connection()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS distribution_centers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                address TEXT NOT NULL,
                standby_slots INTEGER NOT NULL DEFAULT 2,
                reistijd_minuten INTEGER NOT NULL DEFAULT 8,
                timeout_standby_minuten INTEGER NOT NULL DEFAULT 15,
                timeout_dock_minuten INTEGER NOT NULL DEFAULT 10,
                no_show_limiet INTEGER NOT NULL DEFAULT 2,
                blokkade_uren INTEGER NOT NULL DEFAULT 24,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS docks (
                id TEXT PRIMARY KEY,
                dc_id TEXT NOT NULL,
                name TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (dc_id) REFERENCES distribution_centers(id)
            );

            CREATE TABLE IF NOT EXISTS drivers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT NOT NULL UNIQUE,
                dc_id TEXT NOT NULL,
                dock_id TEXT,
                name TEXT NOT NULL,
                license_plate TEXT NOT NULL,
                transporter TEXT NOT NULL,
                cmr_number TEXT NOT NULL,
                phone TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Ingecheckt',
                position_in_queue INTEGER NOT NULL DEFAULT 0,
                status_updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                no_show_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (dc_id) REFERENCES distribution_centers(id),
                FOREIGN KEY (dock_id) REFERENCES docks(id)
            );

            CREATE TABLE IF NOT EXISTS driver_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_plate TEXT NOT NULL,
                dc_id TEXT NOT NULL,
                status TEXT NOT NULL,
                completed_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS blocked_plates (
                license_plate TEXT PRIMARY KEY,
                blocked_until TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        conn.commit()

        # Seed DC Rotterdam if not exists
        existing = conn.execute(
            "SELECT id FROM distribution_centers WHERE id = ?", ("dc-rotterdam",)
        ).fetchone()

        if not existing:
            conn.execute("""
                INSERT INTO distribution_centers (id, name, address, standby_slots, reistijd_minuten,
                    timeout_standby_minuten, timeout_dock_minuten, no_show_limiet, blokkade_uren)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "dc-rotterdam",
                "Distributiecentrum Rotterdam Smirnoffweg",
                "Smirnoffweg 42, 3044 AP Rotterdam",
                2, 8, 15, 10, 2, 24,
            ))
            conn.commit()

        # Seed docks if not exists
        dock_count = conn.execute(
            "SELECT COUNT(*) FROM docks WHERE dc_id = ?", ("dc-rotterdam",)
        ).fetchone()[0]

        if dock_count == 0:
            for name in ["Dok A", "Dok B", "Dok C"]:
                dock_id = f"dc-rotterdam-{name.lower().replace(' ', '-')}"
                conn.execute(
                    "INSERT INTO docks (id, dc_id, name, active) VALUES (?, ?, ?, 1)",
                    (dock_id, "dc-rotterdam", name),
                )
            conn.commit()
    finally:
        conn.close()


# ─── Driver operations ───────────────────────────────────────────

def is_plate_blocked(plate: str) -> bool:
    conn = get_connection()
    try:
        now = datetime.utcnow().isoformat()
        row = conn.execute(
            "SELECT blocked_until FROM blocked_plates WHERE license_plate = ? AND blocked_until > ?",
            (plate.upper(), now),
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def get_next_position(dc_id: str, conn: sqlite3.Connection) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(position_in_queue), 0) + 1 FROM drivers WHERE dc_id = ?",
        (dc_id,),
    ).fetchone()
    return row[0]


def create_driver(dc_id: str, name: str, license_plate: str, transporter: str,
                  cmr: str, phone: str) -> dict:
    with _lock_dc(dc_id):
        conn = get_connection()
        try:
            ticket_id = str(uuid.uuid4())
            position = get_next_position(dc_id, conn)
            now = datetime.utcnow().isoformat()

            conn.execute("""
                INSERT INTO drivers (ticket_id, dc_id, name, license_plate, transporter,
                    cmr_number, phone, status, position_in_queue, status_updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Ingecheckt', ?, ?)
            """, (ticket_id, dc_id, name, license_plate.upper(), transporter, cmr, phone, position, now))
            conn.commit()

            return {
                "ticket_id": ticket_id,
                "position": position,
                "status": "Ingecheckt",
                "dc_id": dc_id,
            }
        finally:
            conn.close()


def get_driver_by_ticket(ticket_id: str) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM drivers WHERE ticket_id = ?", (ticket_id,)
        ).fetchone()
        return dict_from_row(row)
    finally:
        conn.close()


def update_driver_status(ticket_id: str, new_status: str, dock_id: str | None = None,
                         position: int | None = None) -> dict | None:
    driver = get_driver_by_ticket(ticket_id)
    if not driver:
        return None

    dc_id = driver["dc_id"]
    with _lock_dc(dc_id):
        conn = get_connection()
        try:
            now = datetime.utcnow().isoformat()
            old_updated = driver["status_updated_at"]

            # Optimistic locking check
            current_row = conn.execute(
                "SELECT status_updated_at FROM drivers WHERE ticket_id = ?",
                (ticket_id,),
            ).fetchone()
            if current_row and current_row["status_updated_at"] != old_updated:
                return {"error": "Conflict: status was modified by another request"}

            if dock_id is not None:
                conn.execute(
                    "UPDATE drivers SET status = ?, dock_id = ?, status_updated_at = ? WHERE ticket_id = ?",
                    (new_status, dock_id, now, ticket_id),
                )
            elif position is not None:
                conn.execute(
                    "UPDATE drivers SET status = ?, position_in_queue = ?, status_updated_at = ? WHERE ticket_id = ?",
                    (new_status, position, now, ticket_id),
                )
            else:
                conn.execute(
                    "UPDATE drivers SET status = ?, status_updated_at = ? WHERE ticket_id = ?",
                    (new_status, now, ticket_id),
                )
            conn.commit()

            row = conn.execute(
                "SELECT * FROM drivers WHERE ticket_id = ?", (ticket_id,)
            ).fetchone()
            return dict_from_row(row)
        finally:
            conn.close()


def move_position_back(ticket_id: str) -> dict | None:
    driver = get_driver_by_ticket(ticket_id)
    if not driver:
        return None

    dc_id = driver["dc_id"]
    current_pos = driver["position_in_queue"]

    with _lock_dc(dc_id):
        conn = get_connection()
        try:
            # Move this driver one position back in queue
            conn.execute("""
                UPDATE drivers
                SET position_in_queue = position_in_queue - 1
                WHERE dc_id = ? AND position_in_queue = ?
            """, (dc_id, current_pos + 1))
            conn.execute("""
                UPDATE drivers
                SET position_in_queue = position_in_queue + 1
                WHERE ticket_id = ?
            """, (ticket_id,))
            conn.commit()

            return dict_from_row(conn.execute(
                "SELECT * FROM drivers WHERE ticket_id = ?", (ticket_id,)
            ).fetchone())
        finally:
            conn.close()


def increment_no_show(ticket_id: str) -> dict | None:
    driver = get_driver_by_ticket(ticket_id)
    if not driver:
        return None

    dc_id = driver["dc_id"]
    with _lock_dc(dc_id):
        conn = get_connection()
        try:
            new_count = driver["no_show_count"] + 1
            now = datetime.utcnow().isoformat()

            conn.execute(
                "UPDATE drivers SET no_show_count = ?, status_updated_at = ? WHERE ticket_id = ?",
                (new_count, now, ticket_id),
            )

            # Record in history
            conn.execute(
                "INSERT INTO driver_history (license_plate, dc_id, status) VALUES (?, ?, ?)",
                (driver["license_plate"], dc_id, "No_Show"),
            )

            # Check if should be blocked
            dc = dict_from_row(conn.execute(
                "SELECT * FROM distribution_centers WHERE id = ?", (dc_id,)
            ).fetchone())

            if dc and new_count >= dc["no_show_limiet"]:
                block_until = datetime.utcnow() + timedelta(hours=dc["blokkade_uren"])
                conn.execute(
                    "INSERT OR REPLACE INTO blocked_plates (license_plate, blocked_until, created_at) VALUES (?, ?, ?)",
                    (driver["license_plate"], block_until.isoformat(), now),
                )
                conn.execute(
                    "UPDATE drivers SET status = 'Geblokkeerd', status_updated_at = ? WHERE ticket_id = ?",
                    (now, ticket_id),
                )
            else:
                # Return to waiting queue
                new_position = get_next_position(dc_id, conn)
                conn.execute(
                    "UPDATE drivers SET status = 'Wachtend', position_in_queue = ?, dock_id = NULL, status_updated_at = ? WHERE ticket_id = ?",
                    (new_position, now, ticket_id),
                )

            conn.commit()
            return dict_from_row(conn.execute(
                "SELECT * FROM drivers WHERE ticket_id = ?", (ticket_id,)
            ).fetchone())
        finally:
            conn.close()


def complete_driver(ticket_id: str) -> dict | None:
    driver = get_driver_by_ticket(ticket_id)
    if not driver:
        return None

    dc_id = driver["dc_id"]
    with _lock_dc(dc_id):
        conn = get_connection()
        try:
            now = datetime.utcnow().isoformat()
            conn.execute(
                "UPDATE drivers SET status = 'Voltooid', dock_id = NULL, status_updated_at = ? WHERE ticket_id = ?",
                (now, ticket_id),
            )
            conn.execute(
                "INSERT INTO driver_history (license_plate, dc_id, status) VALUES (?, ?, ?)",
                (driver["license_plate"], dc_id, "Voltooid"),
            )
            conn.commit()
            return dict_from_row(conn.execute(
                "SELECT * FROM drivers WHERE ticket_id = ?", (ticket_id,)
            ).fetchone())
        finally:
            conn.close()


# ─── Dashboard queries ───────────────────────────────────────────

def get_dc_dashboard(dc_id: str) -> dict:
    conn = get_connection()
    try:
        dc = dict_from_row(conn.execute(
            "SELECT * FROM distribution_centers WHERE id = ?", (dc_id,)
        ).fetchone())
        if not dc:
            return {"error": "DC not found"}

        docks = [dict(r) for r in conn.execute(
            "SELECT * FROM docks WHERE dc_id = ? ORDER BY name", (dc_id,)
        ).fetchall()]

        drivers = [dict(r) for r in conn.execute(
            "SELECT * FROM drivers WHERE dc_id = ? ORDER BY position_in_queue",
            (dc_id,)
        ).fetchall()]

        return {
            "dc": dc,
            "docks": docks,
            "drivers": drivers,
        }
    finally:
        conn.close()


def get_next_waiting_driver(dc_id: str) -> dict | None:
    with _lock_dc(dc_id):
        conn = get_connection()
        try:
            row = conn.execute("""
                SELECT * FROM drivers
                WHERE dc_id = ? AND status IN ('Ingecheckt', 'Wachtend', 'Truckparking')
                ORDER BY position_in_queue LIMIT 1
            """, (dc_id,)).fetchone()
            return dict_from_row(row)
        finally:
            conn.close()


def assign_driver_to_dock(dc_id: str) -> dict | None:
    with _lock_dc(dc_id):
        conn = get_connection()
        try:
            driver_row = conn.execute("""
                SELECT * FROM drivers
                WHERE dc_id = ? AND status IN ('Ingecheckt', 'Wachtend', 'Truckparking', 'Standby_Aangekomen')
                ORDER BY CASE WHEN status = 'Standby_Aangekomen' THEN 0 ELSE 1 END, position_in_queue
                LIMIT 1
            """, (dc_id,)).fetchone()

            if not driver_row:
                return None

            driver = dict(driver_row)

            # Find first available dock
            dock_row = conn.execute("""
                SELECT d.* FROM docks d
                WHERE d.dc_id = ? AND d.active = 1
                AND d.id NOT IN (
                    SELECT dock_id FROM drivers WHERE dc_id = ? AND dock_id IS NOT NULL AND status = 'Actief_Dok'
                )
                ORDER BY d.name LIMIT 1
            """, (dc_id, dc_id)).fetchone()

            if not dock_row:
                return None

            dock = dict(dock_row)
            now = datetime.utcnow().isoformat()

            conn.execute(
                "UPDATE drivers SET status = 'Actief_Dok', dock_id = ?, status_updated_at = ? WHERE ticket_id = ?",
                (dock["id"], now, driver["ticket_id"]),
            )
            conn.commit()

            driver["status"] = "Actief_Dok"
            driver["dock_id"] = dock["id"]
            return driver
        finally:
            conn.close()


def call_next_driver(dc_id: str) -> dict | None:
    with _lock_dc(dc_id):
        conn = get_connection()
        try:
            dc = dict_from_row(conn.execute(
                "SELECT * FROM distribution_centers WHERE id = ?", (dc_id,)
            ).fetchone())

            if not dc:
                return None

            # Count drivers in standby
            standby_count = conn.execute("""
                SELECT COUNT(*) FROM drivers
                WHERE dc_id = ? AND status IN ('Standby_Onderweg', 'Standby_Aangekomen')
            """, (dc_id,)).fetchone()[0]

            # Count free docks
            free_dock_count = conn.execute("""
                SELECT COUNT(*) FROM docks d
                WHERE d.dc_id = ? AND d.active = 1
                AND d.id NOT IN (
                    SELECT dock_id FROM drivers WHERE dc_id = ? AND dock_id IS NOT NULL AND status = 'Actief_Dok'
                )
            """, (dc_id, dc_id)).fetchone()[0]

            # Ready drivers (aangekomen op standby) get priority for a free dock,
            # even when standby is not full yet.
            ready_count = conn.execute("""
                SELECT COUNT(*) FROM drivers
                WHERE dc_id = ? AND status = 'Standby_Aangekomen'
            """, (dc_id,)).fetchone()[0]

            if ready_count and free_dock_count:
                return assign_driver_to_dock(dc_id)

            if standby_count >= dc["standby_slots"]:
                # Standby full → try direct to dock
                return assign_driver_to_dock(dc_id)

            # Call next waiting driver to standby
            driver_row = conn.execute("""
                SELECT * FROM drivers
                WHERE dc_id = ? AND status IN ('Ingecheckt', 'Wachtend', 'Truckparking')
                ORDER BY position_in_queue LIMIT 1
            """, (dc_id,)).fetchone()

            if not driver_row:
                return None

            driver = dict(driver_row)
            now = datetime.utcnow().isoformat()

            conn.execute(
                "UPDATE drivers SET status = 'Standby_Onderweg', status_updated_at = ? WHERE ticket_id = ?",
                (now, driver["ticket_id"]),
            )
            conn.commit()

            driver["status"] = "Standby_Onderweg"
            return driver
        finally:
            conn.close()


def reorder_queue(dc_id: str, ticket_ids: list[str]) -> dict:
    with _lock_dc(dc_id):
        conn = get_connection()
        try:
            now = datetime.utcnow().isoformat()
            for i, tid in enumerate(ticket_ids, start=1):
                conn.execute(
                    "UPDATE drivers SET position_in_queue = ?, status_updated_at = ? WHERE ticket_id = ? AND dc_id = ?",
                    (i, now, tid, dc_id),
                )
            conn.commit()
            return {"success": True, "reordered": len(ticket_ids)}
        finally:
            conn.close()


def get_blocked_plates(dc_id: str) -> list[dict]:
    conn = get_connection()
    try:
        now = datetime.utcnow().isoformat()
        rows = conn.execute(
            "SELECT * FROM blocked_plates WHERE blocked_until > ?",
            (now,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def unblock_plate(plate: str) -> dict:
    conn = get_connection()
    try:
        now = datetime.utcnow().isoformat()
        conn.execute(
            "UPDATE blocked_plates SET blocked_until = ? WHERE license_plate = ?",
            (now, plate.upper()),
        )
        conn.commit()
        return {"success": True, "plate": plate.upper()}
    finally:
        conn.close()


def get_standby_count(dc_id: str) -> int:
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT COUNT(*) FROM drivers
            WHERE dc_id = ? AND status IN ('Standby_Onderweg', 'Standby_Aangekomen')
        """, (dc_id,)).fetchone()
        return row[0]
    finally:
        conn.close()
