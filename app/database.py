"""SQLite-Zugriffsschicht für den Prototyp.

Bewusst ohne ORM gehalten (plain sqlite3), um die Struktur so einfach wie möglich
nachvollziehbar zu halten.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path

from app.models import Ampel, Fall, FallStatus, GestattungsbeschlussStatus

DB_PATH = Path(__file__).resolve().parent.parent / "massenverfahren.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS faelle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_adresse TEXT NOT NULL,
    werk TEXT NOT NULL,
    mandant TEXT NOT NULL,
    zeitstempel TEXT NOT NULL,
    gestattungsbeschluss_status TEXT NOT NULL,
    forderungshoehe_euro REAL NOT NULL,
    status TEXT NOT NULL,
    ampel TEXT NOT NULL,
    frist_datum TEXT,
    reaktion_text TEXT,
    abmahnung_pfad TEXT,
    eskalationsstufe INTEGER NOT NULL DEFAULT 0,
    notiz TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(SCHEMA)


def _row_to_fall(row: sqlite3.Row) -> Fall:
    return Fall(
        id=row["id"],
        ip_adresse=row["ip_adresse"],
        werk=row["werk"],
        mandant=row["mandant"],
        zeitstempel=datetime.fromisoformat(row["zeitstempel"]),
        gestattungsbeschluss_status=GestattungsbeschlussStatus(row["gestattungsbeschluss_status"]),
        forderungshoehe_euro=row["forderungshoehe_euro"],
        status=FallStatus(row["status"]),
        ampel=Ampel(row["ampel"]),
        frist_datum=date.fromisoformat(row["frist_datum"]) if row["frist_datum"] else None,
        reaktion_text=row["reaktion_text"],
        abmahnung_pfad=row["abmahnung_pfad"],
        eskalationsstufe=row["eskalationsstufe"],
        notiz=row["notiz"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )


def insert_fall(fall: Fall) -> Fall:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO faelle (
                ip_adresse, werk, mandant, zeitstempel, gestattungsbeschluss_status,
                forderungshoehe_euro, status, ampel, frist_datum, reaktion_text,
                abmahnung_pfad, eskalationsstufe, notiz, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fall.ip_adresse,
                fall.werk,
                fall.mandant,
                fall.zeitstempel.isoformat(),
                fall.gestattungsbeschluss_status.value,
                fall.forderungshoehe_euro,
                fall.status.value,
                fall.ampel.value,
                fall.frist_datum.isoformat() if fall.frist_datum else None,
                fall.reaktion_text,
                fall.abmahnung_pfad,
                fall.eskalationsstufe,
                fall.notiz,
                fall.created_at.isoformat(),
                fall.updated_at.isoformat(),
            ),
        )
        fall.id = cur.lastrowid
        return fall


def update_fall(fall: Fall) -> None:
    fall.updated_at = datetime.utcnow()
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE faelle SET
                ip_adresse=?, werk=?, mandant=?, zeitstempel=?, gestattungsbeschluss_status=?,
                forderungshoehe_euro=?, status=?, ampel=?, frist_datum=?, reaktion_text=?,
                abmahnung_pfad=?, eskalationsstufe=?, notiz=?, updated_at=?
            WHERE id=?
            """,
            (
                fall.ip_adresse,
                fall.werk,
                fall.mandant,
                fall.zeitstempel.isoformat(),
                fall.gestattungsbeschluss_status.value,
                fall.forderungshoehe_euro,
                fall.status.value,
                fall.ampel.value,
                fall.frist_datum.isoformat() if fall.frist_datum else None,
                fall.reaktion_text,
                fall.abmahnung_pfad,
                fall.eskalationsstufe,
                fall.notiz,
                fall.updated_at.isoformat(),
                fall.id,
            ),
        )


def get_fall(fall_id: int) -> Fall | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM faelle WHERE id=?", (fall_id,)).fetchone()
        return _row_to_fall(row) if row else None


def list_faelle() -> list[Fall]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM faelle ORDER BY frist_datum IS NULL, frist_datum ASC, id ASC").fetchall()
        return [_row_to_fall(row) for row in rows]


def reset_db() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()
