"""Administrator dashboard — the main screen."""

import streamlit as st
import plotly.express as px
import pv_config as config
import theme
from services import database, dispenser_service

st.set_page_config(page_title=f"Dashboard · {config.APP_NAME}",
                   page_icon="🌸", layout="wide")

database.init_database()
theme.apply_theme()

st.title("Dispenser Dashboard")
st.caption(config.SCHOOL_NAME)

df = dispenser_service.get_dispensers()

if df.empty:
    st.warning("No dispensers found.")
    st.stop()

# ---------- Summary cards ----------
counts = dispenser_service.get_status_counts(df)
cards = [
    (len(df),                        "Total",        config.COLORS["deep_plum"]),
    (counts[config.STATUS_STOCKED],  "Stocked",      config.COLORS["sage_green"]),
    (counts[config.STATUS_LOW],      "Low",          config.COLORS["muted_coral"]),
    (counts[config.STATUS_EMPTY],    "Empty",        config.COLORS["dusty_rose"]),
    (counts[config.STATUS_OFFLINE],  "Offline",      config.COLORS["soft_gray"]),
    (counts[config.STATUS_FAULTY],   "Needs repair", config.COLORS["soft_lavender"]),
]

for col, (value, label, color) in zip(st.columns(6), cards):
    with col:
        st.markdown(theme.summary_card(value, label, color), unsafe_allow_html=True)

st.write("")

# ---------- Needs attention ----------
st.subheader("Needs attention")
attention = dispenser_service.get_needs_attention(df)

if attention.empty:
    st.success("Every dispenser is stocked and reporting normally.")
else:
    st.write(f"**{len(attention)}** dispensers need a look, most urgent first.")
    for _, row in attention.iterrows():
        info_col, btn_col = st.columns([5, 1])
        with info_col:
            age = row.get("minutes_since_reading")
            age_text = f"{age} min ago" if age is not None else "unknown"
            st.markdown(
                f"""
                <div class="pv-attention">
                    {theme.status_pill(row['status'])}
                    <strong>{row['dispenser_id']}</strong> —
                    {row['building']}, {row['floor']}, {row['restroom']}<br>
                    <span style="color:{config.COLORS['soft_gray']}; font-size:0.86rem;">
                        {row['inventory']} of {row['capacity']} items
                        ({row['fill_pct']}%) · last reading {age_text}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with btn_col:
            if row["status"] in (config.STATUS_FAULTY, config.STATUS_OFFLINE):
                if st.button("Fix sensor", key=f"fix_{row['dispenser_id']}"):
                    dispenser_service.mark_sensor_fixed(row["dispenser_id"])
                    st.rerun()
            else:
                if st.button("Restock", key=f"re_{row['dispenser_id']}"):
                    dispenser_service.restock_dispenser(row["dispenser_id"])
                    st.rerun()

st.write("---")

# ---------- Filters + table ----------
st.subheader("All dispensers")

f1, f2, f3 = st.columns([2, 1.5, 1.5])
with f1:
    search = st.text_input("Search", placeholder="ID, restroom, or building…")
with f2:
    buildings = st.multiselect("Building", sorted(df["building"].unique()))
with f3:
    statuses = st.multiselect(
        "Status",
        options=list(config.STATUS_LABELS.keys()),
        format_func=lambda s: config.STATUS_LABELS[s],
    )

view = df.copy()
if search:
    q = search.lower()
    view = view[
        view["dispenser_id"].str.lower().str.contains(q)
        | view["restroom"].str.lower().str.contains(q)
        | view["building"].str.lower().str.contains(q)
        | view["floor"].str.lower().str.contains(q)
    ]
if buildings:
    view = view[view["building"].isin(buildings)]
if statuses:
    view = view[view["status"].isin(statuses)]

st.caption(f"Showing {len(view)} of {len(df)} dispensers")

table = view[[
    "dispenser_id", "building", "floor", "restroom",
    "inventory", "capacity", "fill_pct", "status_label",
]].rename(columns={
    "dispenser_id": "ID",
    "building": "Building",
    "floor": "Floor",
    "restroom": "Restroom",
    "inventory": "Stock",
    "capacity": "Capacity",
    "fill_pct": "Fill %",
    "status_label": "Status",
})


def tint_row(row):
    status = view.loc[row.name, "status"]
    return [f"background-color: {config.STATUS_TINTS[status]}"] * len(row)


st.dataframe(
    table.style.apply(tint_row, axis=1),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Fill %": st.column_config.ProgressColumn(
            "Fill %", min_value=0, max_value=100, format="%d%%"
        )
    },
)

st.write("---")

# ---------- Charts ----------
c1, c2 = st.columns(2)

with c1:
    st.subheader("Status breakdown")
    pie_data = (
        df["status"].value_counts().rename_axis("status").reset_index(name="count")
    )
    pie_data["label"] = pie_data["status"].map(config.STATUS_LABELS)
    fig = px.pie(
        pie_data, names="label", values="count", hole=0.45,
        color="label",
        color_discrete_map={
            config.STATUS_LABELS[s]: config.STATUS_COLORS[s]
            for s in config.STATUS_LABELS
        },
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=10, r=10), height=320,
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Fill level by dispenser")
    bar = df.sort_values("fill_pct")
    fig2 = px.bar(
        bar, x="fill_pct", y="dispenser_id", orientation="h",
        color="status_label",
        color_discrete_map={
            config.STATUS_LABELS[s]: config.STATUS_COLORS[s]
            for s in config.STATUS_LABELS
        },
        labels={"fill_pct": "Fill %", "dispenser_id": ""},
    )
    fig2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10, l=10, r=10), height=320,
        showlegend=False,
    )
    st.plotly_chart(fig2, use_container_width=True)

st.write("---")

# ---------- Illustration placeholders ----------
i1, i2 = st.columns(2)
with i1:
    theme.illustration_slot(
        "school_map.png",
        "Hand-drawn map of the three buildings with dispenser pins",
        height=200,
    )
with i2:
    theme.illustration_slot(
        "dispenser_sketch.png",
        "Sketch of a dispenser with its sensor and QR code",
        height=200,
    )