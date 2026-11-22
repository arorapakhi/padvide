"""Visual styling and illustration placeholders for PadVide."""

import os
import streamlit as st
import pv_config as config


def apply_theme():
    """Inject CSS so Streamlit feels warm and handmade instead of corporate."""
    c = config.COLORS
    css = f"""
    <style>
    .stApp {{ background-color: {c['warm_cream']}; }}
    h1, h2, h3, h4 {{
        color: {c['deep_plum']};
        font-family: "Georgia", "Palatino", serif;
        letter-spacing: 0.3px;
    }}
    p, span, label {{ color: {c['deep_plum']}; }}
    section[data-testid="stSidebar"] {{
        background-color: {c['card_cream']};
        border-right: 2px solid {c['border_tan']};
    }}
    .pv-card {{
        background-color: {c['card_cream']};
        border: 1.5px solid {c['border_tan']};
        border-radius: 18px;
        padding: 18px 20px;
        box-shadow: 0 2px 6px rgba(74, 59, 69, 0.07);
        text-align: center;
        height: 118px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}
    .pv-card-value {{
        font-size: 2.1rem;
        font-weight: 700;
        font-family: "Georgia", serif;
        line-height: 1.1;
    }}
    .pv-card-label {{
        font-size: 0.82rem;
        color: {c['soft_gray']};
        text-transform: uppercase;
        letter-spacing: 1.1px;
        margin-top: 6px;
    }}
    .pv-pill {{
        display: inline-block;
        padding: 3px 12px;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        color: white;
        margin-right: 6px;
    }}
    .pv-attention {{
        background-color: {c['card_cream']};
        border-left: 6px solid {c['dusty_rose']};
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        box-shadow: 0 1px 4px rgba(74, 59, 69, 0.06);
    }}
    .pv-placeholder {{
        border: 2.5px dashed {c['dusty_rose']};
        border-radius: 18px;
        background-color: {c['card_cream']};
        padding: 28px 18px;
        text-align: center;
        color: {c['soft_gray']};
        font-style: italic;
        font-size: 0.9rem;
    }}
    .stButton > button {{
        background-color: {c['sage_green']};
        color: white;
        border: none;
        border-radius: 999px;
        padding: 8px 22px;
        font-weight: 600;
    }}
    .stButton > button:hover {{
        background-color: {c['dusty_rose']};
        color: white;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def summary_card(value, label, color):
    """One rounded stat card."""
    return f"""
    <div class="pv-card">
        <div class="pv-card-value" style="color:{color};">{value}</div>
        <div class="pv-card-label">{label}</div>
    </div>
    """


def status_pill(status):
    """Colored pill showing a dispenser's status."""
    color = config.STATUS_COLORS[status]
    label = config.STATUS_LABELS[status]
    return f'<span class="pv-pill" style="background-color:{color};">{label}</span>'


def illustration_slot(filename, caption, height=200):
    """
    Show your hand-drawn art if the file exists, otherwise a dashed placeholder.
    Drop a PNG into assets/illustrations/ with the matching name and it appears.
    """
    path = os.path.join(config.ILLUSTRATION_DIR, filename)
    if os.path.exists(path):
        st.image(path, caption=caption)
    else:
        st.markdown(
            f"""
            <div class="pv-placeholder" style="min-height:{height}px;
                 display:flex; flex-direction:column; justify-content:center;">
                <div style="font-size:1.6rem; margin-bottom:8px;">&#9999;</div>
                <div><strong>Illustration placeholder</strong></div>
                <div style="margin-top:6px;">{caption}</div>
                <div style="margin-top:10px; font-size:0.78rem;">
                    Save as <code>{config.ILLUSTRATION_DIR}/{filename}</code>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )