import streamlit as st
import plotly.express as px
import pv_config as config
import theme
from services import database, setup_service, usage_service

st.set_page_config(page_title="Restock Agent | PadVide", layout="wide")
database.init_database()
setup_service.init_setup_tables()
usage_service.init_usage_tables()
theme.apply_theme()

st.title("Restock Agent")

school = setup_service.get_school()
restocker = setup_service.get_restocker()
buffer_days = school["buffer_days"] if school else 2

if not usage_service.has_history():
    st.warning("No usage data yet. Go to **Setup -> Monitoring** and generate the "
               "14-day monitoring period first.")
    st.stop()

plan = usage_service.restock_plan(buffer_days=buffer_days)

t1, t2, t3 = st.tabs(["Restock plan", "Usage trends", "Agent log"])

with t1:
    tier = school["poverty_tier"] if school else "not set"
    st.caption(f"Safety buffer: {buffer_days} days ({tier})")

    counts = plan["urgency"].value_counts()
    cards = [
        (int(counts.get("Restock now", 0)), "Restock now", config.COLORS["dusty_rose"]),
        (int(counts.get("Restock soon", 0)), "Restock soon", config.COLORS["muted_coral"]),
        (int(counts.get("Check sensor", 0)), "Check sensor", config.COLORS["soft_lavender"]),
        (int(counts.get("On track", 0)), "On track", config.COLORS["sage_green"]),
    ]
    for col, (v, l, c) in zip(st.columns(4), cards):
        with col:
            st.markdown(theme.summary_card(v, l, c), unsafe_allow_html=True)

    st.write("")
    show = plan[["dispenser_id", "building", "restroom", "inventory", "capacity",
                 "recent_avg", "days_to_empty", "restock_by", "units_needed",
                 "urgency"]].rename(columns={
        "dispenser_id": "ID", "building": "Building", "restroom": "Restroom",
        "inventory": "Stock", "capacity": "Cap", "recent_avg": "Daily use",
        "days_to_empty": "Days left", "restock_by": "Restock by",
        "units_needed": "Bring", "urgency": "Action"})
    st.dataframe(show, use_container_width=True, hide_index=True)

    st.subheader("Send restock requests")
    urgent = plan[plan["urgency"].isin(["Restock now", "Restock soon"])]
    if urgent.empty:
        st.success("Nothing needs restocking right now.")
    elif not (restocker and restocker.get("verified")):
        st.warning("Add a **verified** restocker in Setup before sending requests.")
    else:
        for _, row in urgent.iterrows():
            with st.expander(f"{row['urgency']} - {row['dispenser_id']} ({row['restroom']})"):
                msg = usage_service.agent_message(row, restocker, school)
                st.code(msg)
                if st.button("Send via agent", key=f"send_{row['dispenser_id']}"):
                    setup_service.log_agent_message(row["dispenser_id"], msg)
                    st.success(f"Sent to {restocker['name']} via {restocker['method']}.")

with t2:
    usage = usage_service.get_usage_df()
    daily = usage.groupby("date")["units_used"].sum().reset_index()
    st.subheader("School-wide daily usage")
    fig = px.line(daily, x="date", y="units_used", markers=True,
                  labels={"date": "", "units_used": "Units used"})
    fig.update_traces(line_color=config.COLORS["dusty_rose"])
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=300, margin=dict(t=20, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Week-over-week change by dispenser")
    trends = usage_service.weekly_trends()
    fig2 = px.bar(trends.sort_values("change_pct"), x="change_pct", y="dispenser_id",
                  orientation="h",
                  labels={"change_pct": "Change vs prior week (%)", "dispenser_id": ""})
    fig2.update_traces(marker_color=config.COLORS["sage_green"])
    fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                       height=360, margin=dict(t=20, b=10, l=10, r=10))
    st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(trends.rename(columns={
        "dispenser_id": "ID", "recent_avg": "This week avg",
        "prior_avg": "Last week avg", "change_pct": "Change %"}),
        use_container_width=True, hide_index=True)

    st.download_button("Download usage data (CSV)",
                       usage.to_csv(index=False).encode("utf-8"),
                       "padvide_usage.csv", "text/csv")

with t3:
    log = setup_service.get_agent_log()
    if not log:
        st.info("No messages sent yet. Send one from the Restock plan tab.")
    else:
        st.caption(f"{len(log)} messages sent.")
        for e in log:
            st.markdown(f"**{e['dispenser_id']}** - {e['sent_at'][:16]}")
            st.code(e["message"])