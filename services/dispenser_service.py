"""Turns raw dispenser facts into statuses the dashboard can show."""

from datetime import datetime
import pandas as pd
import pv_config as config
from services import database


def compute_status(inventory, capacity, sensor_ok, last_reading_at):
    """
    One rulebook for status. Order matters: hardware problems
    outrank inventory, because we can't trust the number.
    """
    if not sensor_ok:
        return config.STATUS_FAULTY

    if last_reading_at:
        try:
            last = datetime.fromisoformat(last_reading_at)
            age_min = (datetime.now() - last).total_seconds() / 60
            if age_min > config.OFFLINE_AFTER_MINUTES:
                return config.STATUS_OFFLINE
        except ValueError:
            return config.STATUS_OFFLINE
    else:
        return config.STATUS_OFFLINE

    fill_pct = (inventory / capacity * 100) if capacity else 0
    if fill_pct <= config.EMPTY_THRESHOLD:
        return config.STATUS_EMPTY
    if fill_pct <= config.LOW_THRESHOLD:
        return config.STATUS_LOW
    return config.STATUS_STOCKED


def get_dispensers():
    """Every dispenser as a DataFrame, with status and fill % added."""
    conn = database.get_connection()
    df = pd.read_sql_query("SELECT * FROM dispensers ORDER BY dispenser_id", conn)
    conn.close()

    if df.empty:
        return df

    df["fill_pct"] = (df["inventory"] / df["capacity"] * 100).round(0).astype(int)
    df["status"] = df.apply(
        lambda r: compute_status(
            r["inventory"], r["capacity"], r["sensor_ok"], r["last_reading_at"]
        ),
        axis=1,
    )
    df["status_label"] = df["status"].map(config.STATUS_LABELS)
    df["priority"] = df["status"].map(config.STATUS_PRIORITY)

    def minutes_ago(ts):
        try:
            return int((datetime.now() - datetime.fromisoformat(ts)).total_seconds() / 60)
        except (TypeError, ValueError):
            return None

        df["minutes_since_reading"] = df["last_reading_at"].apply(minutes_ago)
    return df


def get_status_counts(df):
    """Dict of status -> count, including zeros so cards never go blank."""
    counts = {s: 0 for s in config.STATUS_LABELS}
    if not df.empty:
        for status, n in df["status"].value_counts().items():
            counts[status] = int(n)
    return counts


def get_needs_attention(df):
    """
    Anything not 'stocked', most urgent first.
    Within the same status, emptier dispensers come first.
    """
    if df.empty:
        return df
    flagged = df[df["status"] != config.STATUS_STOCKED].copy()
    return flagged.sort_values(["priority", "fill_pct"], ascending=[True, True])


def restock_dispenser(dispenser_id):
    """Refill to capacity and timestamp it."""
    now = datetime.now().isoformat()
    conn = database.get_connection()
    conn.execute("""
        UPDATE dispensers
           SET inventory = capacity,
               last_restocked = ?,
               last_reading_at = ?
         WHERE dispenser_id = ?
    """, (now, now, dispenser_id))
    conn.commit()
    conn.close()


def mark_sensor_fixed(dispenser_id):
    """Clear a faulty/offline sensor flag."""
    now = datetime.now().isoformat()
    conn = database.get_connection()
    conn.execute("""
        UPDATE dispensers
           SET sensor_ok = 1,
               last_reading_at = ?
         WHERE dispenser_id = ?
    """, (now, dispenser_id))
    conn.commit()
    conn.close()