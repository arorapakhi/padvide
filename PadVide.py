"""PadVide - menstrual product accessibility and inventory monitoring."""

import io
import os
import random
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

st.set_page_config(page_title="PadVide", page_icon="*", layout="wide")

# ---------------- palette ----------------
CREAM = "#FDF6EC"
CARD = "#FFFBF5"
ROSE = "#C98A94"
SAGE = "#9CAF95"
CORAL = "#E09383"
LAVENDER = "#C5BBD6"
PLUM = "#4A3B45"
GRAY = "#8C8289"
TAN = "#E8DCCA"

ILLUS_DIR = "assets/illustrations"

STATUS_COLOR = {
    "Stocked": SAGE, "Low inventory": CORAL, "Empty": ROSE,
    "Sensor offline": GRAY, "Needs repair": LAVENDER,
}
STATUS_RANK = {
    "Empty": 0, "Needs repair": 1, "Sensor offline": 2,
    "Low inventory": 3, "Stocked": 4,
}

st.markdown("""
<style>
.stApp { background-color: #FDF6EC; }
h1, h2, h3, h4 { color: #4A3B45; font-family: Georgia, serif; }
section[data-testid="stSidebar"] { background-color: #FFFBF5; }
.pv-card { background:#FFFBF5; border:1.5px solid #E8DCCA; border-radius:18px;
  padding:16px 12px; text-align:center; }
.pv-val { font-size:2rem; font-weight:700; font-family:Georgia,serif; line-height:1.1; }
.pv-lab { font-size:.72rem; color:#8C8289; letter-spacing:1px; margin-top:4px; }
.pv-row { background:#FFFBF5; border-left:6px solid #C98A94; border-radius:12px;
  padding:12px 16px; margin-bottom:8px; }
.pv-pill { display:inline-block; padding:2px 11px; border-radius:999px;
  font-size:.74rem; font-weight:600; color:white; margin-right:8px; }
.pv-ph { border:2.5px dashed #C98A94; border-radius:18px; background:#FFFBF5;
  padding:26px 16px; text-align:center; color:#8C8289; font-style:italic;
  font-size:.88rem; }
.pv-note { background:#FFFBF5; border:1.5px solid #E8DCCA; border-radius:14px;
  padding:14px 18px; }
.stButton>button { background:#9CAF95; color:white; border:none;
  border-radius:999px; padding:7px 20px; font-weight:600; }
.stButton>button:hover { background:#C98A94; color:white; }
</style>
""", unsafe_allow_html=True)


# ---------------- helpers ----------------
def card(value, label, color):
    st.markdown(
        f'<div class="pv-card"><div class="pv-val" style="color:{color};">{value}</div>'
        f'<div class="pv-lab">{label.upper()}</div></div>',
        unsafe_allow_html=True,
    )


def pill(status):
    return (f'<span class="pv-pill" style="background:{STATUS_COLOR[status]};">'
            f'{status}</span>')


def illustration(filename, caption, height=190):
    """Show the user's drawing if present, else a labelled placeholder."""
    path = os.path.join(ILLUS_DIR, filename)
    if os.path.exists(path):
        st.image(path, caption=caption)
    else:
        st.markdown(
            f'<div class="pv-ph" style="min-height:{height}px;display:flex;'
            f'flex-direction:column;justify-content:center;">'
            f'<div style="font-size:1.5rem;">&#9998;</div>'
            f'<div><strong>Illustration placeholder</strong></div>'
            f'<div style="margin-top:6px;">{caption}</div>'
            f'<div style="margin-top:8px;font-size:.76rem;">save as '
            f'<code>{ILLUS_DIR}/{filename}</code></div></div>',
            unsafe_allow_html=True,
        )


# ---------------- seed data ----------------
DISPENSERS = [
    # id, building, floor, restroom, capacity, inventory, traffic, sensor_ok, mins_since_reading
    ("A-101", "Building A", "1st Floor", "Girls' Restroom East", 40, 36, 1.3, 1, 4),
    ("A-102", "Building A", "1st Floor", "Girls' Restroom West", 40, 9, 1.3, 1, 7),
    ("A-201", "Building A", "2nd Floor", "Girls' Restroom East", 40, 28, 1.2, 1, 3),
    ("A-202", "Building A", "2nd Floor", "All-Gender Restroom", 25, 1, 0.9, 1, 6),
    ("B-101", "Building B", "1st Floor", "Girls' Restroom North", 40, 40, 1.2, 1, 5),
    ("B-102", "Building B", "1st Floor", "Nurse's Office", 30, 22, 0.6, 1, 9),
    ("B-201", "Building B", "2nd Floor", "Girls' Restroom North", 40, 11, 1.2, 1, 2),
    ("B-202", "Building B", "2nd Floor", "Girls' Restroom South", 40, 31, 1.1, 0, 12),
    ("C-101", "Building C", "1st Floor", "Gym Locker Room", 50, 0, 1.9, 1, 8),
    ("C-102", "Building C", "1st Floor", "All-Gender Restroom", 25, 18, 0.9, 1, 240),
    ("C-201", "Building C", "2nd Floor", "Girls' Restroom Main", 40, 34, 1.6, 1, 5),
    ("C-202", "Building C", "2nd Floor", "Library Restroom", 25, 6, 0.7, 1, 1),
]