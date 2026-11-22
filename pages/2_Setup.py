import streamlit as st
import pv_config as config
import theme
from services import database, setup_service, usage_service, dispenser_service

st.set_page_config(page_title="Setup | PadVide", layout="wide")
database.init_database()
setup_service.init_setup_tables()
usage_service.init_usage_tables()
theme.apply_theme()

st.title("Setup")
st.caption("One-time configuration, then PadVide runs on its own.")

school = setup_service.get_school()
restocker = setup_service.get_restocker()
tiers = list(setup_service.POVERTY_TIERS.keys())

t1, t2, t3 = st.tabs(["School", "Restocker", "Monitoring"])

with t1:
    with st.form("school"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("School name",
                value=school["school_name"] if school else "Rosewood High School")
            city = st.text_input("City", value=school["city"] if school else "Austin")
        with c2:
            state = st.text_input("State", value=school["state"] if school else "TX")
            enroll = st.number_input("Enrollment", 50, 10000,
                value=school["enrollment"] if school else 1200, step=50)

        idx = tiers.index(school["poverty_tier"]) if school and school["poverty_tier"] in tiers else 1
        tier = st.selectbox("Community need level", tiers, index=idx)
        st.caption("In production this is pulled from U.S. Census poverty data by "
                   "ZIP code. Administrator-selected in this prototype.")
        buf = st.slider("Safety buffer (days before projected empty)", 0, 7,
                        value=school["buffer_days"] if school else 2)
        st.info("Higher-need schools get a larger buffer so dispensers never run dry.")
        if st.form_submit_button("Save school"):
            setup_service.save_school(name, city, state, enroll, tier, buf)
            st.success("Saved.")
            st.rerun()

with t2:
    with st.form("restocker"):
        c1, c2 = st.columns(2)
        with c1:
            rname = st.text_input("Restocker name",
                value=restocker["name"] if restocker else "Ms. Alvarez")
            rrole = st.selectbox("Role", ["Custodial staff", "Facilities manager",
                                          "Nurse", "Supply company"])
        with c2:
            rcontact = st.text_input("Contact",
                value=restocker["contact"] if restocker else "alvarez@rosewood.edu")
            rmethod = st.selectbox("Contact method", ["Email", "SMS", "In-app"])
        rver = st.checkbox("Contact verified",
            value=bool(restocker["verified"]) if restocker else True)
        st.caption("The agent only sends requests to a verified contact.")
        if st.form_submit_button("Save restocker"):
            setup_service.save_restocker(rname, rrole, rcontact, rmethod, rver)
            st.success("Saved.")
            st.rerun()

with t3:
    st.write("PadVide needs **two weeks of usage data** before predicting restock "
             "timing. Real deployments collect this automatically from sensors.")
    if usage_service.has_history():
        st.success(f"Monitoring complete - {len(usage_service.get_usage_df())} readings.")
    else:
        st.warning("No usage history yet.")
    if st.button("Generate 14-day monitoring period"):
        n = usage_service.backfill_history(days=14)
        st.success(f"Created {n} readings.")
        st.rerun()
    theme.illustration_slot("setup_sketch.jpg",
                            "Hand-drawn sensor installation sketch", height=160)