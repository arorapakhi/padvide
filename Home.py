import streamlit as st
import pv_config as config
import theme
from services import database

st.set_page_config(page_title="PadVide", layout="wide")
database.init_database()
theme.apply_theme()

st.title("PadVide")
st.caption(config.APP_TAGLINE)
st.write("")
c1, c2 = st.columns([1.3, 1])
with c1:
    st.subheader("Welcome")
    st.write(f"**{config.SCHOOL_NAME}**")
    st.write("PadVide monitors every menstrual product dispenser in a school, "
             "so no student finds an empty box. Open the Dashboard in the sidebar.")
    st.info("Sensor data is simulated in software. No student data is collected.")
with c2:
    theme.illustration_slot("welcome_hero.png", "Illustration: Rawpixel (rawpixel.com)", height=240)
st.write("---")
st.caption("PadVide prototype.")
