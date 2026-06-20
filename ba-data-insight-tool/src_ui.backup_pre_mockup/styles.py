"""Custom CSS for BA Data Insight Tool."""
from __future__ import annotations

import streamlit as st


def inject_custom_css() -> None:
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
    }
    div[data-testid="stMetric"] {
        background-color: rgba(127, 127, 127, 0.06);
        border-radius: 8px;
        padding: 10px 12px;
    }

    /* Header bar with navy background behind the title */
    .main .block-container h1:first-of-type {
        background: linear-gradient(90deg, #1E3A5F 0%, #2E6DA4 100%);
        color: white !important;
        padding: 20px 24px;
        border-radius: 10px;
        margin-bottom: 8px;
    }

    /* Sidebar background slightly distinct from main area */
    section[data-testid="stSidebar"] {
        background-color: var(--secondary-background-color);
        border-right: 1px solid rgba(128, 128, 128, 0.25);
    }

    /* Primary buttons in brand navy */
    .stButton button[kind="primary"] {
        background-color: #1E3A5F;
        border-color: #1E3A5F;
    }
    .stButton button[kind="primary"]:hover {
        background-color: #2E6DA4;
        border-color: #2E6DA4;
    }

    /* Dividers more subtle */
    hr {
        border-color: rgba(128, 128, 128, 0.25) !important;
    }

    /* Radio buttons in sidebar navigation, more spacing */
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 4px 0;
    }

    /* Captions slightly larger and softer color for readability */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #5A6B7D !important;
        font-size: 13px !important;
    }

    /* Wizard step list in sidebar */
    .wizard-step {
        padding: 6px 10px;
        border-radius: 6px;
        margin-bottom: 2px;
        font-size: 14px;
    }
    .wizard-step.done {
        color: #2E7D32;
    }
    .wizard-step.active {
        background-color: rgba(46, 109, 164, 0.15);
        font-weight: 600;
    }
    .wizard-step.pending {
        opacity: 0.55;
    }
    </style>
    """, unsafe_allow_html=True)
