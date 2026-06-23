"""Custom CSS for BA Data Insight Tool.

Dark-mode premium palette (forced regardless of browser/OS theme).
v2 — "premium fintech, foco en datos": acento azul UNICO (sin degradado
arcoiris), tarjetas planas con borde fino (menos glassmorphism/glow),
tipografia Hanken Grotesk (UI) + JetBrains Mono (cifras/etiquetas).

Drop-in replacement: misma firma `inject_custom_css()` y mismos nombres de
clase que la version anterior (.card, .hero-card, .badge, .step-card,
.feature-card, .detect-card, .alert-card, .icon-badge, .progress-complete),
asi que el resto del codigo (dashboard.py, tabs.py, sidebar.py...) no cambia.
"""
from __future__ import annotations

import streamlit as st


def inject_custom_css() -> None:
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
    :root {
        /* ---- Lienzo ---- */
        --bg-main: #0A0E17;
        --bg-sidebar: #0B1019;
        --bg-panel: #0F1420;
        --bg-card: #131A26;
        --bg-card-hover: #161E2C;

        /* ---- Acento unico (sin degradado) ---- */
        --primary-blue: #5B8DEF;
        --primary-blue-hover: #4A7BDD;
        --accent-cyan: #5B8DEF;      /* alias: antes era cian, ahora = acento */
        --accent-purple: #A78BFA;
        --accent-green: #45C08A;
        --accent-amber: #E9A94A;
        --accent-red: #E8736B;

        /* ---- Texto ---- */
        --text-main: #EEF2F9;
        --text-secondary: #9AA5B8;
        --text-muted: #5E6A7E;

        /* ---- Bordes / sombras (finos, sin glow) ---- */
        --border-soft: rgba(255, 255, 255, 0.07);
        --border-blue: rgba(91, 141, 239, 0.45);

        --shadow-card: 0 1px 0 rgba(255, 255, 255, 0.02);
        --shadow-blue: 0 0 0 1px rgba(91, 141, 239, 0.18);

        /* Mantengo el nombre por compatibilidad, pero ahora es color plano */
        --gradient-brand: var(--primary-blue);

        --font-ui: 'Hanken Grotesk', system-ui, -apple-system, sans-serif;
        --font-mono: 'JetBrains Mono', ui-monospace, monospace;
    }

    /* ============ Global dark background (forced) ============ */
    html, body, .stApp, .main, .main .block-container {
        background-color: var(--bg-main);
        font-family: var(--font-ui);
    }
    .stApp, .stApp p, .stApp span, .stApp label, .stApp li {
        color: var(--text-main);
        font-family: var(--font-ui);
    }
    .main .block-container {
        padding-top: 1.6rem;
    }

    /* Cifras de metricas y badges en monoespaciada */
    div[data-testid="stMetricValue"] {
        font-family: var(--font-mono);
        font-weight: 600;
        letter-spacing: -0.02em;
    }

    /* ============ Typography ============ */
    h1, h2, h3 {
        letter-spacing: -0.01em;
        color: var(--text-main);
        font-family: var(--font-ui);
    }
    .main .block-container h2,
    .main .block-container h3 {
        font-weight: 600;
        margin-top: 12px;
        margin-bottom: 8px;
    }
    .main .block-container p,
    .main .block-container li {
        line-height: 1.6;
        color: var(--text-secondary);
    }

    /* ============ Vertical rhythm ============ */
    .main .block-container hr {
        margin: 12px 0;
        border-color: var(--border-soft) !important;
    }

    /* ============ Buttons ============ */
    .stButton button {
        transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
        background-color: var(--bg-panel);
        border: 1px solid var(--border-soft);
        color: var(--text-main);
        border-radius: 9px;
        font-weight: 600;
    }
    .stButton button:hover:not(:disabled) {
        background-color: var(--bg-card-hover);
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

    /* Primary: acento solido (sin glow) */
    .stButton button[kind="primary"] {
        background-color: var(--primary-blue);
        border-color: var(--primary-blue);
        color: #ffffff;
    }
    .stButton button[kind="primary"]:hover:not(:disabled) {
        background-color: var(--primary-blue-hover);
        border-color: var(--primary-blue-hover);
    }

    /* Boton fantasma "Probar con datos de ejemplo" */
    .st-key-btn_cta_demo .stButton button {
        background-color: transparent;
        border-color: transparent;
        color: var(--text-secondary);
        box-shadow: none;
    }
    .st-key-btn_cta_demo .stButton button:hover:not(:disabled) {
        background-color: rgba(255, 255, 255, 0.05);
        border-color: var(--border-soft);
        color: var(--text-main);
    }

    /* Secondary (wizard / source selector) */
    .stButton button[kind="secondary"]:hover:not(:disabled) {
        background-color: rgba(91, 141, 239, 0.10);
        border-color: var(--border-blue);
        color: var(--primary-blue);
    }

    /* ============ Pills (selector de fuente y radios compactos) ============ */
    .stRadio[data-testid="stRadio"] > div[role="radiogroup"] {
        gap: 8px;
        flex-wrap: wrap;
    }
    .stRadio[data-testid="stRadio"] > div[role="radiogroup"] label {
        background-color: var(--bg-panel);
        border: 1px solid var(--border-soft);
        border-radius: 999px;
        padding: 6px 16px;
        margin: 0;
        font-size: 13px;
        font-weight: 500;
        transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
    }
    .stRadio[data-testid="stRadio"] > div[role="radiogroup"] label:hover {
        border-color: var(--border-blue);
        background-color: rgba(91, 141, 239, 0.08);
    }
    .stRadio[data-testid="stRadio"] > div[role="radiogroup"] label[data-checked="true"],
    .stRadio[data-testid="stRadio"] > div[role="radiogroup"] label:has(input:checked) {
        background: var(--primary-blue);
        border-color: transparent;
        color: #ffffff;
    }
    .stRadio[data-testid="stRadio"] svg {
        display: none;
    }

    /* ============ Tabs: subrayado (sin relleno) ============ */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 1px solid var(--border-soft);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 0;
        padding: 9px 16px;
        margin-right: 2px;
        font-size: 14px;
        font-weight: 600;
        color: var(--text-secondary);
        background-color: transparent;
        transition: color 0.15s ease;
    }
    .stTabs [data-baseweb="tab"] p {
        font-size: 14px;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: transparent;
        color: var(--text-main);
    }
    .stTabs [aria-selected="true"] {
        background-color: transparent;
        color: var(--primary-blue) !important;
    }
    .stTabs [aria-selected="true"] p {
        color: var(--primary-blue) !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background: var(--primary-blue);
        height: 2px;
    }
    .stTabs [data-baseweb="tab-panel"] {
        padding-top: 16px;
    }

    /* ============ Metrics (KPI cards planas) ============ */
    div[data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid var(--border-soft);
        border-radius: 14px;
        padding: 16px 17px;
        transition: border-color 0.15s ease, background 0.15s ease;
    }
    div[data-testid="stMetric"]:hover {
        background: var(--bg-card-hover);
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
        border-radius: 13px;
        overflow: hidden;
    }

    /* ============ Expanders ============ */
    div[data-testid="stExpander"] {
        background: var(--bg-panel);
        border: 1px solid var(--border-soft);
        border-radius: 12px;
    }
    div[data-testid="stExpander"] summary {
        background-color: transparent;
        border-radius: 12px;
        transition: background-color 0.15s ease;
        color: var(--text-main);
    }
    div[data-testid="stExpander"] summary:hover {
        background-color: rgba(91, 141, 239, 0.08);
    }

    /* ============ Inputs: focus ring acento ============ */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > input,
    div[data-baseweb="base-input"] {
        border-radius: 8px !important;
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
        box-shadow: none;
    }
    .stSlider [data-baseweb="slider"] > div > div {
        background: var(--primary-blue) !important;
    }
    div[data-testid="stFileUploaderDropzone"] {
        background-color: var(--bg-panel);
        border-radius: 12px;
        border-color: var(--border-soft);
        transition: border-color 0.15s ease, background-color 0.15s ease;
    }
    div[data-testid="stFileUploaderDropzone"]:hover {
        border-color: var(--primary-blue) !important;
        background-color: rgba(91, 141, 239, 0.06);
    }

    /* ============ Alert boxes: borde izq acento ============ */
    div[data-testid="stAlertContainer"] {
        background: var(--bg-panel);
        border-radius: 12px;
        border-left: 3px solid currentColor;
    }

    /* ============ Header bar: panel plano con acento (sin arcoiris) ============ */
    .main .block-container h1:first-of-type {
        background: linear-gradient(135deg, rgba(91, 141, 239, 0.16) 0%, #0E1422 60%);
        border: 1px solid var(--border-soft);
        color: var(--text-main) !important;
        padding: 18px 24px;
        border-radius: 16px;
        margin-top: 0;
        margin-bottom: 6px;
        letter-spacing: -0.02em;
        font-size: 1.7rem;
        font-weight: 700;
        box-shadow: none;
    }
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

    /* Badge de progreso completado */
    .progress-complete {
        background: linear-gradient(135deg, rgba(69, 192, 138, 0.09), var(--bg-panel));
        border: 1px solid rgba(69, 192, 138, 0.28);
        border-radius: 12px;
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
        background: rgba(69, 192, 138, 0.16);
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

    /* ============ Card generica: plana ============ */
    .card {
        background: var(--bg-card);
        border: 1px solid var(--border-soft);
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 8px;
        height: 100%;
        box-shadow: none;
        transition: border-color 0.2s ease, background 0.2s ease;
    }
    .card:hover {
        background: var(--bg-card-hover);
        border-color: var(--border-blue);
    }

    .hero-card {
        background: linear-gradient(135deg, rgba(91, 141, 239, 0.16) 0%, #0E1422 60%);
        border: 1px solid var(--border-soft);
        padding: 22px 24px;
        text-align: left;
    }
    .hero-card:hover {
        border-color: var(--border-soft);
        background: linear-gradient(135deg, rgba(91, 141, 239, 0.16) 0%, #0E1422 60%);
    }
    .hero-card h2 {
        margin: 0 0 4px 0;
        font-size: 22px;
        line-height: 1.2;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: var(--text-main);
    }
    .hero-card .accent {
        color: var(--primary-blue);
        background: none;
        -webkit-background-clip: initial;
        background-clip: initial;
    }
    .hero-card .hero-subtitle {
        font-size: 14px;
        color: var(--text-secondary);
        margin: 0;
    }

    /* ============ Icon badges (cuadrado redondeado, color plano) ============ */
    .icon-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        border-radius: 11px;
        background: rgba(91, 141, 239, 0.14);
        color: var(--primary-blue);
        box-shadow: none;
        font-size: 19px;
        margin-bottom: 11px;
    }

    .step-card {
        text-align: left;
    }
    .step-card .step-num {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 30px;
        height: 30px;
        border-radius: 9px;
        background: rgba(91, 141, 239, 0.14);
        color: var(--primary-blue);
        font-family: var(--font-mono);
        font-weight: 600;
        margin-bottom: 12px;
        box-shadow: none;
    }
    .step-card .step-title {
        font-weight: 600;
        margin-bottom: 5px;
        color: var(--text-main);
    }
    .step-card .step-desc {
        font-size: 13px;
        color: var(--text-muted);
        line-height: 1.5;
    }

    .feature-card {
        text-align: left;
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
        line-height: 1.45;
    }

    .detect-card .detect-title {
        font-size: 11px;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 5px;
        font-family: var(--font-mono);
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

    /* Variante opcional: acento de severidad a la izquierda de la alerta.
       Anade class="alert-card alert-high" (o -medium/-low) en tu markup. */
    .alert-card.alert-high { border-left: 3px solid var(--accent-red); }
    .alert-card.alert-medium { border-left: 3px solid var(--accent-amber); }
    .alert-card.alert-low { border-left: 3px solid var(--accent-green); }

    .badge {
        display: inline-block;
        padding: 3px 11px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 600;
    }
    .badge-high {
        background-color: rgba(232, 115, 107, 0.16);
        color: var(--accent-red);
    }
    .badge-medium {
        background-color: rgba(233, 169, 74, 0.18);
        color: var(--accent-amber);
    }
    .badge-low {
        background-color: rgba(69, 192, 138, 0.16);
        color: var(--accent-green);
    }
    </style>
    """, unsafe_allow_html=True)
