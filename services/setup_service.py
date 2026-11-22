"""School setup, restocker info, and the agent message log."""

from datetime import datetime
import pv_config as config
from services import database

POVERTY_TIERS = {
    "Low need":      {"buffer_days": 1, "note": "Standard restock cadence."},
    "Moderate need": {"buffer_days": 2, "note": "Slightly earlier restocks to avoid gaps."},
    "High need":     {"buffer_days": 3, "note": "Restock early; dispensers are a primary source."},
}


def init_setup_tables():
    conn = database.get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS school_setup (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            school_name TEXT, city TEXT, state TEXT,
            enrollment INTEGER, poverty_tier TEXT,
            buffer_days INTEGER, monitoring_start TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS restocker (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            name TEXT, role TEXT, contact TEXT,
            method TEXT, verified INTEGER DEFAULT 0
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS agent_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sent_at TEXT, dispenser_id TEXT, message TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_school(school_name, city, state, enrollment, poverty_tier, buffer_days):
    conn = database.get_connection()
    conn.execute("""
        INSERT INTO school_setup
          (id, school_name, city, state, enrollment, poverty_tier, buffer_days, monitoring_start)
        VALUES (1,?,?,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
          school_name=excluded.school_name, city=excluded.city, state=excluded.state,
          enrollment=excluded.enrollment, poverty_tier=excluded.poverty_tier,
          buffer_days=excluded.buffer_days
    """, (school_name, city, state, enrollment, poverty_tier,
          buffer_days, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_school():
    conn = database.get_connection()
    row = conn.execute("SELECT * FROM school_setup WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else None


def save_restocker(name, role, contact, method, verified):
    conn = database.get_connection()
    conn.execute("""
        INSERT INTO restocker (id, name, role, contact, method, verified)
        VALUES (1,?,?,?,?,?)
        ON CONFLICT(id) DO UPDATE SET
          name=excluded.name, role=excluded.role, contact=excluded.contact,
          method=excluded.method, verified=excluded.verified
    """, (name, role, contact, method, int(verified)))
    conn.commit()
    conn.close()


def get_restocker():
    conn = database.get_connection()
    row = conn.execute("SELECT * FROM restocker WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else None


def set_capacity(dispenser_id, capacity):
    conn = database.get_connection()
    conn.execute("UPDATE dispensers SET capacity = ? WHERE dispenser_id = ?",
                 (capacity, dispenser_id))
    conn.commit()
    conn.close()


def log_agent_message(dispenser_id, message):
    conn = database.get_connection()
    conn.execute("INSERT INTO agent_log (sent_at, dispenser_id, message) VALUES (?,?,?)",
                 (datetime.now().isoformat(), dispenser_id, message))
    conn.commit()
    conn.close()


def get_agent_log(limit=30):
    conn = database.get_connection()
    rows = conn.execute(
        "SELECT * FROM agent_log ORDER BY log_id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]