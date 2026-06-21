"""Custom CSS for BA Data Insight Tool.

Dark-mode premium palette (forced regardless of browser/OS theme),
inspired by financial/data dashboard UIs: navy-black backgrounds,
glassmorphism cards, blue->cyan->violet gradients.
"""
from __future__ import annotations

import streamlit as st


def inject_custom_css() -> None:
    st.markdown("""
    <style>
    :root {
        --bg-main: #050A13;
        --bg-sidebar: #07101F;
        --bg-panel: #0B1324;
        --bg-card: rgba(15, 23, 42, 0.78);
        --bg-card-hover: rgba(30, 41, 59, 0.9);

        --primary-blue: #2563EB;
        --primary-blue-hover: #1D4ED8;
        --accent-cyan: #38BDF8;
        --accent-purple: #7C3AED;
        --accent-green: #22C55E;
        --accent-amber: #F59E0B;
        --accent-red: #EF4444;

        --text-main: #F8FAFC;
        --text-secondary: #CBD5E1;
        --text-muted: #64748B;

        --border-soft: rgba(148, 163, 184, 0.18);
        --border-blue: rgba(59, 130, 246, 0.35);

        --shadow-card: 0 18px 45px rgba(0, 0, 0, 0.35);
        --shadow-blue: 0 0 28px rgba(37, 99, 235, 0.22);

        --gradient-brand: linear-gradient(135deg, var(--primary-blue) 0%, var(--accent-cyan) 50%, var(--accent-purple) 100%);
    }

    /* ============ Global dark background (forced) ============ */
    .stApp, .main, .main .block-container {
        background-color: var(--bg-main);
    }
    .stApp, .stApp p, .stApp span, .stApp label, .stApp li {
        color: var(--text-main);
    }

    /* Streamlit's default top padding is very tall; tighten it so page
       titles sit close to the top instead of floating mid-screen. */
    .main .block-container {
        padding-top: 1.6rem;
    }

    /* ============ Typography ============ */
    h1, h2, h3 {
        letter-spacing: -0.01em;
        color: var(--text-main);
    }
    .main .block-container h2,
    .main .block-container h3 {
        font-weight: 600;
        margin-top: 28px;
        margin-bottom: 8px;
    }
    .main .block-container p,
    .main .block-container li {
        line-height: 1.6;
        color: var(--text-secondary);
    }

    /* ============ Vertical rhythm ============ */
    .main .block-container hr {
        margin: 20px 0;
        border-color: var(--border-soft) !important;
    }

    /* ============ Buttons ============ */
    .stButton button {
        transition: box-shadow 0.15s ease, transform 0.15s ease, background-color 0.15s ease, border-color 0.15s ease;
        background-color: var(--bg-panel);
        border-color: var(--border-soft);
        color: var(--text-main);
    }
    .stButton button:hover:not(:disabled) {
        box-shadow: var(--shadow-blue);
        transform: translateY(-1px);
        border-color: var(--border-blue);
    }
    .stButton button:active:not(:disabled) {
        transform: translateY(0);
    }
    .stButton button:disabled {
        opacity: 0.4;
        cursor: not-allowed;
        color: var(--text-muted);
    }

    /* Primary buttons in brand blue with glow */
    .stButton button[kind="primary"] {
        background-color: var(--primary-blue);
        border-color: var(--primary-blue);
        color: var(--text-main);
    }
    .stButton button[kind="primary"]:hover:not(:disabled) {
        background-color: var(--primary-blue-hover);
        border-color: var(--primary-blue-hover);
        box-shadow: var(--shadow-blue);
    }

    /* Secondary buttons (wizard steps, source selector) get a brand-tinted hover */
    .stButton button[kind="secondary"]:hover:not(:disabled) {
        background-color: rgba(37, 99, 235, 0.12);
        border-color: var(--border-blue);
        color: var(--accent-cyan);
    }

    /* ============ Pills (data-source selector and similar compact radios) ============ */
    .stRadio[data-testid="stRadio"] > div[role="radiogroup"] {
        gap: 6px;
        flex-wrap: wrap;
    }
    .stRadio[data-testid="stRadio"] > div[role="radiogroup"] label {
        background-color: var(--bg-panel);
        border: 1px solid var(--border-soft);
        border-radius: 999px;
        padding: 5px 14px;
        margin: 0;
        font-size: 13px;
        transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
    }
    .stRadio[data-testid="stRadio"] > div[role="radiogroup"] label:hover {
        border-color: var(--border-blue);
        background-color: rgba(37, 99, 235, 0.10);
    }
    .stRadio[data-testid="stRadio"] > div[role="radiogroup"] label[data-checked="true"],
    .stRadio[data-testid="stRadio"] > div[role="radiogroup"] label:has(input:checked) {
        background: var(--gradient-brand);
        border-color: transparent;
    }
    .stRadio[data-testid="stRadio"] svg {
        display: none;
    }

    /* ============ Tabs ============ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid var(--border-soft);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px 6px 0 0;
        padding: 10px 18px;
        margin-right: 2px;
        font-size: 15px;
        font-weight: 500;
        color: var(--text-muted);
        transition: background-color 0.15s ease, color 0.15s ease;
    }
    .stTabs [data-baseweb="tab"] p {
        font-size: 15px;
        font-weight: 500;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(37, 99, 235, 0.10);
        color: var(--accent-cyan);
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(37, 99, 235, 0.16);
        color: var(--accent-cyan) !important;
        font-weight: 700;
    }
    .stTabs [aria-selected="true"] p {
        color: var(--accent-cyan) !important;
        font-weight: 700;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background: var(--gradient-brand);
        height: 3px;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 20px;
    }

    /* ============ Metrics ============ */
    div[data-testid="stMetric"] {
        background: var(--bg-card);
        backdrop-filter: blur(12px);
        border: 1px solid var(--border-soft);
        border-radius: 8px;
        padding: 12px 14px;
        transition: box-shadow 0.15s ease, border-color 0.15s ease, background 0.15s ease;
    }
    div[data-testid="stMetric"]:hover {
        background: var(--bg-card-hover);
        box-shadow: var(--shadow-blue);
        border-color: var(--border-blue);
    }
    div[data-testid="stMetricLabel"] {
        color: var(--text-secondary);
    }
    div[data-testid="stMetricValue"] {
        color: var(--text-main);
    }

    /* ============ Dataframes / tables ============ */
    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border-soft);
        border-radius: 8px;
        overflow: hidden;
    }

    /* ============ Expanders ============ */
    div[data-testid="stExpander"] {
        background: var(--bg-panel);
        border: 1px solid var(--border-soft);
        border-radius: 8px;
    }
    div[data-testid="stExpander"] summary {
        background-color: rgba(148, 163, 184, 0.04);
        border-radius: 8px;
        transition: background-color 0.15s ease;
        color: var(--text-main);
    }
    div[data-testid="stExpander"] summary:hover {
        background-color: rgba(37, 99, 235, 0.10);
    }

    /* ============ Inputs: brand-colored focus ring ============ */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > input,
    div[data-baseweb="base-input"] {
        border-radius: 6px !important;
        background-color: var(--bg-panel) !important;
        border-color: var(--border-soft) !important;
        color: var(--text-main) !important;
    }
    div[data-baseweb="select"]:focus-within > div,
    div[data-baseweb="base-input"]:focus-within {
        border-color: var(--primary-blue) !important;
        box-shadow: 0 0 0 1px var(--primary-blue) !important;
    }
    .stSlider [data-baseweb="slider"] div[role="slider"] {
        background-color: var(--primary-blue) !important;
        border-color: var(--primary-blue) !important;
        box-shadow: var(--shadow-blue);
    }
    .stSlider [data-baseweb="slider"] > div > div {
        background: var(--gradient-brand) !important;
    }
    div[data-testid="stFileUploaderDropzone"] {
        background-color: var(--bg-panel);
        border-radius: 8px;
        border-color: var(--border-soft);
        transition: border-color 0.15s ease, background-color 0.15s ease;
    }
    div[data-testid="stFileUploaderDropzone"]:hover {
        border-color: var(--primary-blue) !important;
        background-color: rgba(37, 99, 235, 0.06);
    }

    /* ============ Alert boxes: accent left border ============ */
    div[data-testid="stAlertContainer"] {
        background: var(--bg-panel);
        border-radius: 8px;
        border-left: 4px solid currentColor;
    }

    /* ============ Header bar: blue -> cyan -> violet gradient ============ */
    .main .block-container h1:first-of-type {
        background: var(--gradient-brand);
        color: var(--text-main) !important;
        padding: 16px 24px;
        border-radius: 12px;
        margin-top: 0;
        margin-bottom: 6px;
        letter-spacing: -0.01em;
        font-size: 1.7rem;
        box-shadow: var(--shadow-card);
    }
    /* The caption right under the header banner and the divider after it
       don't need much breathing room before the page content starts. */
    .main .block-container h1:first-of-type + div [data-testid="stCaptionContainer"] {
        margin-bottom: 0;
    }
    .main .block-container h1:first-of-type ~ hr:first-of-type {
        margin: 10px 0 18px 0;
    }

    /* ============ Sidebar ============ */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-sidebar);
        border-right: 1px solid var(--border-soft);
    }
    section[data-testid="stSidebar"] * {
        color: var(--text-main);
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        padding: 4px 0;
    }

    /* Progress-complete badge shown under the wizard once analysis has run */
    .progress-complete {
        background: var(--bg-card);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(34, 197, 94, 0.35);
        border-radius: 10px;
        padding: 14px;
        text-align: center;
        margin-top: 8px;
    }
    .progress-complete .progress-ring {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: rgba(34, 197, 94, 0.15);
        border: 2px solid var(--accent-green);
        color: var(--accent-green);
        font-weight: 700;
        font-size: 12px;
        margin-bottom: 6px;
    }
    .progress-complete .progress-title {
        font-weight: 600;
        color: var(--accent-green);
        font-size: 13px;
    }
    .progress-complete .progress-desc {
        font-size: 12px;
        color: var(--text-muted);
        margin-top: 2px;
    }

    /* ============ Captions ============ */
    .stCaption, [data-testid="stCaptionContainer"] {
        color: var(--text-secondary) !important;
        font-size: 13px !important;
        line-height: 1.5;
    }

    /* ============ Generic card: glassmorphism ============ */
    .card {
        background: var(--bg-card);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid var(--border-soft);
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 8px;
        height: 100%;
        box-shadow: var(--shadow-card);
        transition: box-shadow 0.2s ease, border-color 0.2s ease, background 0.2s ease;
    }
    .card:hover {
        background: var(--bg-card-hover);
        box-shadow: var(--shadow-blue), var(--shadow-card);
        border-color: var(--border-blue);
    }

    .hero-card {
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.18) 0%, rgba(56, 189, 248, 0.10) 50%, rgba(124, 58, 237, 0.16) 100%);
        border: 1px solid var(--border-blue);
        padding: 30px 26px;
        text-align: left;
    }
    .hero-card:hover {
        box-shadow: var(--shadow-card);
        border-color: var(--border-blue);
        background: linear-gradient(135deg, rgba(37, 99, 235, 0.18) 0%, rgba(56, 189, 248, 0.10) 50%, rgba(124, 58, 237, 0.16) 100%);
    }
    .hero-card h2 {
        margin: 0 0 8px 0;
        font-size: 30px;
        line-height: 1.25;
        color: var(--text-main);
    }
    .hero-card .accent {
        background: var(--gradient-brand);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }
    .hero-card .hero-subtitle {
        font-size: 15px;
        color: var(--text-secondary);
        margin: 0;
    }

    /* ============ Icon badges (circular, gradient) ============ */
    .icon-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 44px;
        height: 44px;
        border-radius: 50%;
        background: var(--gradient-brand);
        box-shadow: var(--shadow-blue);
        font-size: 20px;
        margin-bottom: 10px;
    }

    .step-card {
        text-align: center;
    }
    .step-card .step-num {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: var(--gradient-brand);
        color: var(--text-main);
        font-weight: 700;
        margin-bottom: 10px;
        box-shadow: var(--shadow-blue);
    }
    .step-card .step-title {
        font-weight: 600;
        margin-bottom: 4px;
        color: var(--text-main);
    }
    .step-card .step-desc {
        font-size: 13px;
        color: var(--text-muted);
        line-height: 1.5;
    }

    .feature-card {
        text-align: center;
    }
    .feature-card .feature-title {
        font-weight: 600;
        margin-bottom: 4px;
        font-size: 14px;
        color: var(--text-main);
    }
    .feature-card .feature-desc {
        font-size: 13px;
        color: var(--text-muted);
        line-height: 1.5;
    }

    .detect-card .detect-title {
        font-size: 12px;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.03em;
        margin-bottom: 4px;
    }
    .detect-card .detect-value {
        font-weight: 600;
        font-size: 14px;
        color: var(--text-main);
    }

    .alert-card .card-header {
        margin-bottom: 6px;
    }
    .alert-card .card-title {
        font-weight: 600;
        margin-bottom: 4px;
        color: var(--text-main);
    }
    .alert-card .card-desc {
        font-size: 13px;
        color: var(--text-muted);
        line-height: 1.5;
    }

    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-high {
        background-color: rgba(239, 68, 68, 0.16);
        color: var(--accent-red);
    }
    .badge-medium {
        background-color: rgba(245, 158, 11, 0.18);
        color: var(--accent-amber);
    }
    .badge-low {
        background-color: rgba(34, 197, 94, 0.16);
        color: var(--accent-green);
    }
    </style>
    """, unsafe_allow_html=True)
