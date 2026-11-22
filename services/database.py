"""The only file that talks to SQLite directly."""

import os
import sqlite3
from datetime import datetime, timedelta
import pv_config as config

SEED_DISPENSERS = [
    # (id, building, floor, restroom, capacity, inventory, sensor_ok, minutes_since_reading)
    ("A-101", "Building A", "1st Floor", "Girls' Restroom - East",   40, 36, 1, 4),
    ("A-102", "Building A", "1st Floor", "Girls' Restroom - West",   40,  9, 1, 7),
    ("A-201", "Building A", "2nd Floor", "Girls' Restroom - East",   40, 28, 1, 3),
    ("A-202", "Building A", "2nd Floor", "All-Gender Restroom",      25,  1, 1, 6),
    ("B-101", "Building B", "1st Floor", "Girls' Restroom - North",  40, 40, 1, 5),
    ("B-102", "Building B", "1st Floor", "Nurse's Office",           30, 22, 1, 9),
    ("B-201", "Building B", "2nd Floor", "Girls' Restroom - North",  40, 11, 1, 2),
    ("B-202", "Building B", "2nd Floor", "Girls' Restroom - South",  40, 31, 0, 12),
    ("C-101", "Building C", "1st Floor", "Gym Locker Room",          50,  0, 1, 8),
    ("C-102", "Building C", "1st Floor", "All-Gender Restroom",      25, 18, 1, 240),
    ("C-201", "Building C", "2nd Floor", "Girls' Restroom - Main",   40, 34, 1, 5),
    ("C-202", "Building C", "2nd Floor", "Library Restroom",         25,  6, 1, 1),
]


def get_connection():
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Create tables and seed data on first run. Safe to call every time."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS dispensers (
            dispenser_id    TEXT PRIMARY KEY,
            building        TEXT NOT NULL,
            floor           TEXT NOT NULL,
            restroom        TEXT NOT NULL,
            capacity        INTEGER NOT NULL,
            inventory       INTEGER NOT NULL,
            sensor_ok       INTEGER NOT NULL DEFAULT 1,
            last_reading_at TEXT,
            last_restocked  TEXT
        )
    """)

    cur.execute("SELECT COUNT(*) FROM dispensers")
    if cur.fetchone()[0] == 0:
        now = datetime.now()
        for d in SEED_DISPENSERS:
            did, bldg, flr, room, cap, inv, ok, mins = d
            cur.execute("""
                INSERT INTO dispensers
                (dispenser_id, building, floor, restroom, capacity,
                 inventory, sensor_ok, last_reading_at, last_restocked)
                VALUES (?,?,?,?,?,?,?,?,?)
            """, (
                did, bldg, flr, room, cap, inv, ok,
                (now - timedelta(minutes=mins)).isoformat(),
                (now - timedelta(days=3)).isoformat(),
            ))

    conn.commit()
    conn.close()