"""Usage history, weekly trend recalculation, and restock timing."""

import random
from datetime import datetime, timedelta
import pandas as pd
import pv_config as config
from services import database, dispenser_service

# Traffic weight by restroom type. Gym and main halls drain fastest.
TRAFFIC_WEIGHTS = {
    "gym": 1.9, "main": 1.6, "east": 1.3, "west": 1.3,
    "north": 1.2, "south": 1.1, "library": 0.7,
    "nurse": 0.6, "all-gender": 0.9,
}


def traffic_weight(restroom):
    name = restroom.lower()
    for key, w in TRAFFIC_WEIGHTS.items():
        if key in name:
            return w
    return 1.0


def init_usage_tables():
    conn = database.get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usage_history (
            reading_id INTEGER PRIMARY KEY AUTOINCREMENT,
            dispenser_id TEXT, date TEXT, units_used INTEGER
        )
    """)
    conn.commit()
    conn.close()


def has_history():
    conn = database.get_connection()
    n = conn.execute("SELECT COUNT(*) FROM usage_history").fetchone()[0]
    conn.close()
    return n > 0


def backfill_history(days=14, seed=42):
    """
    Generate the two-week monitoring period instantly.
    Weekdays only, with realistic traffic and day-of-week variation.
    """
    random.seed(seed)
    df = dispenser_service.get_dispensers()
    if df.empty:
        return 0

    conn = database.get_connection()
    conn.execute("DELETE FROM usage_history")
    today = datetime.now().date()
    rows = []

    for _, d in df.iterrows():
        base = d["capacity"] * 0.09 * traffic_weight(d["restroom"])
        for i in range(days, 0, -1):
            day = today - timedelta(days=i)
            if day.weekday() >= 5:          # skip weekends
                continue
            # Mondays and Fridays run slightly lower
            dow_factor = {0: 0.9, 1: 1.05, 2: 1.1, 3: 1.05, 4: 0.85}[day.weekday()]
            used = max(0, int(random.gauss(base * dow_factor, base * 0.22)))
            rows.append((d["dispenser_id"], day.isoformat(), used))

    conn.executemany(
        "INSERT INTO usage_history (dispenser_id, date, units_used) VALUES (?,?,?)",
        rows,
    )
    conn.commit()
    conn.close()
    return len(rows)


def get_usage_df():
    conn = database.get_connection()
    df = pd.read_sql_query("SELECT * FROM usage_history ORDER BY date", conn)
    conn.close()
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


def weekly_trends():
    """
    Compare the most recent 7 days to the 7 before it.
    This is the weekly readjustment the spec asks for.
    """
    usage = get_usage_df()
    if usage.empty:
        return pd.DataFrame()

    latest = usage["date"].max()
    recent = usage[usage["date"] > latest - timedelta(days=7)]
    prior = usage[(usage["date"] <= latest - timedelta(days=7)) &
                  (usage["date"] > latest - timedelta(days=14))]

    r = recent.groupby("dispenser_id")["units_used"].mean().rename("recent_avg")
    p = prior.groupby("dispenser_id")["units_used"].mean().rename("prior_avg")
    out = pd.concat([r, p], axis=1).fillna(0).reset_index()
    out["change_pct"] = (
        (out["recent_avg"] - out["prior_avg"]) /
        out["prior_avg"].replace(0, pd.NA) * 100
    ).fillna(0).round(0)
    out["recent_avg"] = out["recent_avg"].round(1)
    out["prior_avg"] = out["prior_avg"].round(1)
    return out


def restock_plan(buffer_days=2):
    """
    For each dispenser: average daily usage, days until empty,
    the date to restock by, and how many units to bring.
    """
    disp = dispenser_service.get_dispensers()
    trends = weekly_trends()
    if disp.empty or trends.empty:
        return pd.DataFrame()

    plan = disp.merge(trends, on="dispenser_id", how="left")
    plan["recent_avg"] = plan["recent_avg"].fillna(1).replace(0, 0.5)

    plan["days_to_empty"] = (plan["inventory"] / plan["recent_avg"]).round(1)
    plan["days_to_full_cycle"] = (plan["capacity"] / plan["recent_avg"]).round(1)
    plan["restock_in_days"] = (plan["days_to_empty"] - buffer_days).round(1)
    plan["restock_by"] = plan["restock_in_days"].apply(
        lambda d: (datetime.now() + timedelta(days=max(0, d))).strftime("%b %d")
    )
    plan["units_needed"] = (plan["capacity"] - plan["inventory"]).astype(int)

    def urgency(row):
        if row["status"] in (config.STATUS_FAULTY, config.STATUS_OFFLINE):
            return "Check sensor"
        if row["restock_in_days"] <= 0:
            return "Restock now"
        if row["restock_in_days"] <= 2:
            return "Restock soon"
        return "On track"

    plan["urgency"] = plan.apply(urgency, axis=1)
    order = {"Restock now": 0, "Check sensor": 1, "Restock soon": 2, "On track": 3}
    plan["urgency_rank"] = plan["urgency"].map(order)
    return plan.sort_values(["urgency_rank", "days_to_empty"])


def agent_message(row, restocker, school):
    """The message the AI agent would send to the restocker."""
    name = restocker.get("name", "there") if restocker else "there"
    school_name = school.get("school_name", "the school") if school else "the school"
    return (
        f"Hi {name} — PadVide restock request for {school_name}.\n\n"
        f"Dispenser {row['dispenser_id']}\n"
        f"Location: {row['building']}, {row['floor']}, {row['restroom']}\n"
        f"Current stock: {row['inventory']} of {row['capacity']} units\n"
        f"Average daily use: {row['recent_avg']} units\n"
        f"Projected empty in: {row['days_to_empty']} days\n"
        f"Please bring: {row['units_needed']} units\n"
        f"Restock by: {row['restock_by']}\n\n"
        f"Reply DONE when complete. Thank you."
    )