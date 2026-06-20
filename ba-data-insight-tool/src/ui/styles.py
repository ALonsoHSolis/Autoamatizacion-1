"""Custom CSS for BA Data Insight Tool."""
from __future__ import annotations

import streamlit as st


def inject_custom_css() -> None:
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid rgba(128, 128, 128, 0.25);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        padding: 10px 18px;
        margin-right: 2px;
        font-size: 15px;
        font-weight: 500;
        color: #5A6B7D;
    }
    .stTabs [data-baseweb="tab"] p {
        font-size: 15px;
        font-weight: 500;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(46, 109, 164, 0.08);
        color: #2E6DA4;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(46, 109, 164, 0.12);
        color: #2E6DA4 !important;
        font-weight: 700;
    }
    .stTabs [aria-selected="true"] p {
        color: #2E6DA4 !important;
        font-weight: 700;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #2E6DA4;
        height: 3px;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 20px;
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

    /* Generic card used across onboarding, dashboard, and column detection */
    .card {
        background-color: rgba(127, 127, 127, 0.06);
        border: 1px solid rgba(128, 128, 128, 0.2);
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 8px;
        height: 100%;
    }

    .hero-card {
        background: linear-gradient(135deg, rgba(30, 58, 95, 0.10) 0%, rgba(46, 109, 164, 0.06) 100%);
        border: none;
        padding: 28px 24px;
        text-align: left;
    }
    .hero-card h2 {
        margin: 0 0 8px 0;
        font-size: 28px;
        line-height: 1.25;
    }
    .hero-card .accent {
        color: #2E6DA4;
    }
    .hero-card .hero-subtitle {
        font-size: 15px;
        color: #5A6B7D;
        margin: 0;
    }

    .step-card {
        text-align: center;
    }
    .step-card .step-num {
        display: inline-block;
        width: 28px;
        height: 28px;
        line-height: 28px;
        border-radius: 50%;
        background-color: #2E6DA4;
        color: white;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .step-card .step-title {
        font-weight: 600;
        margin-bottom: 4px;
    }
    .step-card .step-desc {
        font-size: 13px;
        color: #5A6B7D;
    }

    .feature-card {
        text-align: center;
    }
    .feature-card .feature-title {
        font-weight: 600;
        margin-bottom: 4px;
        font-size: 14px;
    }
    .feature-card .feature-desc {
        font-size: 13px;
        color: #5A6B7D;
    }

    .detect-card .detect-title {
        font-size: 12px;
        color: #5A6B7D;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 4px;
    }
    .detect-card .detect-value {
        font-weight: 600;
        font-size: 14px;
    }

    .alert-card .card-header {
        margin-bottom: 6px;
    }
    .alert-card .card-title {
        font-weight: 600;
        margin-bottom: 4px;
    }
    .alert-card .card-desc {
        font-size: 13px;
        color: #5A6B7D;
    }

    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-high {
        background-color: rgba(211, 47, 47, 0.15);
        color: #D32F2F;
    }
    .badge-medium {
        background-color: rgba(245, 166, 35, 0.18);
        color: #B26A00;
    }
    .badge-low {
        background-color: rgba(46, 125, 50, 0.15);
        color: #2E7D32;
    }
    </style>
    """, unsafe_allow_html=True)
