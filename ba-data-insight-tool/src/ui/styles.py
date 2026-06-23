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
    <style>
    /* Fonts loaded via CSS @import, not an HTML link element, because
       Streamlit's markdown sanitizer strips resource-loading HTML tags
       from unsafe_allow_html content, which previously broke the whole
       style block and rendered the raw CSS as visible page text. */
    @import url('https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

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
    [data-testid="stHeader"] {
        height: 0;
        min-height: 0;
        background: transparent;
        visibility: hidden;
    }
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] {
        display: none !important;
    }
    /* No font-family override here: it already inherits from the html/body
       rule above, and re-asserting it on every span (including Streamlit's
       own icon spans, which rely on a Material Symbols ligature font) wins
       by specificity and breaks icon rendering - e.g. the sidebar collapse
       arrow showing the literal text "keyboard_double_arrow_left" instead
       of the icon glyph. */
    .stApp, .stApp p, .stApp span, .stApp label, .stApp li {
        color: var(--text-main);
    }
    .main .block-container {
        max-width: 1210px;
        padding-top: 0.25rem;
        padding-bottom: 3rem;
    }
    section[data-testid="stMain"] > div[data-testid="stMainBlockContainer"],
    .stMainBlockContainer.block-container,
    [data-testid="stMainBlockContainer"] {
        max-width: 1210px;
        padding-top: 0 !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-bottom: 3rem !important;
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
        margin: 10px 0;
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
    div[data-testid="stDownloadButton"] button {
        background-color: var(--bg-panel);
        border: 1px solid var(--border-soft);
        border-radius: 9px;
        color: var(--text-main);
        font-weight: 600;
        transition: background-color 0.15s ease, border-color 0.15s ease;
    }
    div[data-testid="stDownloadButton"] button:hover:not(:disabled) {
        background-color: rgba(91, 141, 239, 0.10);
        border-color: var(--border-blue);
        color: var(--primary-blue);
    }

    /* Boton fantasma "Probar con datos de ejemplo" */
    .st-key-btn_cta_demo .stButton button {
        background-color: transparent;
        border-color: var(--border-soft);
        color: var(--text-secondary);
        box-shadow: none;
    }
    .st-key-btn_cta_demo .stButton button:hover:not(:disabled) {
        background-color: rgba(255, 255, 255, 0.05);
        border-color: var(--border-soft);
        color: var(--text-main);
    }
    .st-key-btn_cta_cargar .stButton button,
    .st-key-btn_cta_demo .stButton button {
        min-height: 48px;
        font-size: 14px;
    }
    .st-key-btn_cta_cargar,
    .st-key-btn_cta_demo {
        margin-top: -88px;
        position: relative;
        z-index: 2;
    }
    .st-key-btn_cta_cargar .stButton button,
    .st-key-btn_cta_demo .stButton button {
        justify-content: center;
        padding-left: 18px;
        padding-right: 18px;
    }
    .st-key-btn_header_exportar .stButton button {
        min-height: 36px;
        height: 36px;
        border-radius: 8px;
        padding-left: 12px;
        padding-right: 12px;
    }
    .st-key-run_analysis_button .stButton button {
        min-height: 48px;
        border-radius: 10px;
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
    .stRadio[data-testid="stRadio"] > div[role="radiogroup"] label > div:first-child {
        display: none !important;
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
        background: var(--bg-panel);
    }
    div[data-testid="stTable"] {
        border: 1px solid var(--border-soft);
        border-radius: 13px;
        overflow: hidden;
        background: var(--bg-panel);
    }

    /* ============ Plotly surfaces ============ */
    div[data-testid="stPlotlyChart"] {
        background: var(--bg-card);
        border: 1px solid var(--border-soft);
        border-radius: 14px;
        padding: 8px;
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

    /* ============ Cargar datos ============ */
    .load-kicker {
        margin-top: 26px;
        margin-bottom: 12px;
    }
    .load-source-caption {
        color: var(--text-muted);
        font-size: 12.5px;
        margin: 2px 0 12px 2px;
        min-height: 18px;
    }
    .upload-intro,
    .sample-data-card {
        min-height: 218px;
        border-radius: 18px 18px 0 0;
        border: 1px dashed rgba(154, 165, 184, 0.26);
        border-bottom: 0;
        background: #0F1420;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 34px 28px 22px 28px;
    }
    .sample-data-card {
        border: 1px solid var(--border-soft);
        border-radius: 18px;
        min-height: 292px;
    }
    .upload-icon-large {
        width: 62px;
        height: 62px;
        border-radius: 16px;
        background: rgba(91, 141, 239, 0.16);
        color: var(--primary-blue);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-family: var(--font-mono);
        font-size: 26px;
        margin-bottom: 18px;
    }
    .upload-title {
        color: var(--text-main);
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .upload-desc {
        color: var(--text-secondary);
        font-size: 13.5px;
        line-height: 1.5;
        max-width: 480px;
    }
    .upload-formats {
        color: var(--text-muted);
        font-family: var(--font-mono);
        font-size: 10px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-top: 22px;
    }
    .st-key-uploaded_data_file div[data-testid="stFileUploader"],
    .st-key-batch_uploader div[data-testid="stFileUploader"] {
        background: #0F1420;
        border: 1px dashed rgba(154, 165, 184, 0.26);
        border-top: 0;
        border-radius: 0 0 18px 18px;
        padding: 12px 24px 24px 24px;
        margin-bottom: 10px;
    }
    .st-key-batch_uploader div[data-testid="stFileUploader"] {
        border-top: 1px dashed rgba(154, 165, 184, 0.26);
        border-radius: 18px;
        margin-top: 12px;
        padding-top: 22px;
    }
    .st-key-uploaded_data_file div[data-testid="stFileUploaderDropzone"],
    .st-key-batch_uploader div[data-testid="stFileUploaderDropzone"] {
        min-height: 78px;
        background: transparent;
        border: 0;
        justify-content: center;
    }
    .st-key-uploaded_data_file div[data-testid="stFileUploader"] button,
    .st-key-batch_uploader div[data-testid="stFileUploader"] button,
    .st-key-btn_source_demo .stButton button {
        background: var(--primary-blue) !important;
        border-color: var(--primary-blue) !important;
        color: #fff !important;
        border-radius: 11px !important;
        min-height: 44px;
        padding-left: 20px;
        padding-right: 20px;
        font-weight: 700;
    }
    .st-key-uploaded_data_file div[data-testid="stFileUploader"] button,
    .st-key-batch_uploader div[data-testid="stFileUploader"] button {
        font-size: 0 !important;
    }
    .st-key-uploaded_data_file div[data-testid="stFileUploader"] button [data-testid="stMarkdownContainer"],
    .st-key-batch_uploader div[data-testid="stFileUploader"] button [data-testid="stMarkdownContainer"] {
        display: none !important;
    }
    .st-key-uploaded_data_file div[data-testid="stFileUploader"] button::after {
        content: "Seleccionar archivo";
        font-size: 13px;
    }
    .st-key-batch_uploader div[data-testid="stFileUploader"] button::after {
        content: "Seleccionar archivos";
        font-size: 13px;
    }
    .connector-card {
        min-height: 110px;
        background: var(--bg-card);
        border: 1px solid var(--border-soft);
        border-radius: 18px;
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 22px;
        margin-bottom: 14px;
    }
    .connector-icon {
        width: 48px;
        height: 48px;
        border-radius: 14px;
        background: rgba(91, 141, 239, 0.14);
        color: var(--primary-blue);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-family: var(--font-mono);
        font-weight: 700;
        flex: none;
    }
    .connector-title {
        color: var(--text-main);
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .connector-desc {
        color: var(--text-secondary);
        font-size: 13px;
        line-height: 1.45;
    }
    .recent-files-card {
        background: var(--bg-card);
        border: 1px solid var(--border-soft);
        border-radius: 18px;
        padding: 22px;
        min-height: 184px;
        margin-bottom: 16px;
    }
    .section-kicker.compact {
        margin: 0 0 18px 0;
    }
    .recent-file-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-top: 15px;
    }
    .recent-file-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex: none;
        font-family: var(--font-mono);
        font-size: 9px;
        font-weight: 700;
    }
    .recent-file-icon.green {
        background: rgba(69, 192, 138, 0.15);
        color: var(--accent-green);
    }
    .recent-file-icon.blue {
        background: rgba(91, 141, 239, 0.15);
        color: var(--primary-blue);
    }
    .recent-file-name {
        color: var(--text-main);
        font-size: 13px;
        font-weight: 700;
        line-height: 1.2;
    }
    .recent-file-meta {
        color: var(--text-muted);
        font-family: var(--font-mono);
        font-size: 10.5px;
        margin-top: 2px;
    }
    .load-tip-card {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        background: rgba(91, 141, 239, 0.12);
        border: 1px solid rgba(91, 141, 239, 0.28);
        border-radius: 14px;
        padding: 16px 18px;
        color: var(--text-secondary);
        font-size: 13px;
        line-height: 1.55;
    }
    .load-tip-card strong {
        color: var(--text-main);
    }
    .load-tip-card span:not(.info-dot) {
        color: var(--text-secondary);
    }

    /* ============ Alert boxes: borde izq acento ============ */
    div[data-testid="stAlertContainer"] {
        background: var(--bg-panel);
        border-radius: 12px;
        border-left: 3px solid currentColor;
    }

    /* ============ Header bar ============ */
    .app-page-header {
        background: transparent;
        border: 0;
        border-radius: 0;
        padding: 0;
        margin: 0 0 10px 0;
    }
    .app-header-kicker {
        display: none;
    }
    h1.app-header-title,
    .stMarkdown h1.app-header-title,
    .app-header-title {
        margin: 0;
        padding: 0 !important;
        color: var(--text-main);
        font-size: 20px !important;
        line-height: 1.14 !important;
        font-weight: 700;
        letter-spacing: -0.01em;
    }
    .app-header-subtitle {
        margin-top: 4px;
        color: var(--text-secondary);
        font-size: 13px;
        line-height: 1.45;
    }
    .readonly-tabs {
        display: flex;
        gap: 28px;
        align-items: flex-end;
        border-bottom: 0;
        margin-top: 14px;
    }
    .readonly-tabs span {
        display: inline-flex;
        align-items: center;
        min-height: 42px;
        color: var(--text-secondary);
        font-weight: 600;
        font-size: 14px;
    }

    /* ============ Sidebar ============ */
    section[data-testid="stSidebar"] {
        background-color: var(--bg-sidebar);
        border-right: 1px solid var(--border-soft);
        width: 296px !important;
        min-width: 296px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        padding: 0 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
        height: 0 !important;
        min-height: 0 !important;
        margin: 0 !important;
        overflow: hidden !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] {
        display: none !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
        padding: 1.25rem 1.25rem 2rem 1.25rem !important;
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
        font-size: 20px;
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
        border: 1px solid rgba(91, 141, 239, 0.22);
        padding: 38px 40px 98px 40px;
        text-align: left;
        border-radius: 18px;
        min-height: 284px;
    }
    .hero-card:hover {
        border-color: var(--border-soft);
        background: linear-gradient(135deg, rgba(91, 141, 239, 0.16) 0%, #0E1422 60%);
    }
    .hero-card h2 {
        margin: 0 0 14px 0;
        font-size: 32px;
        line-height: 1.22;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: var(--text-main);
        max-width: 720px;
    }
    .hero-card .accent {
        color: var(--primary-blue);
        background: none;
        -webkit-background-clip: initial;
        background-clip: initial;
    }
    .hero-card .hero-subtitle {
        font-size: 16px;
        color: var(--text-secondary);
        margin: 0;
        max-width: 690px;
        line-height: 1.55;
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
    .detect-card-premium {
        min-height: 102px;
        padding: 18px 18px;
    }
    .detect-card-premium .detect-title {
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .detect-dot {
        width: 8px;
        height: 8px;
        border-radius: 2px;
        display: inline-block;
    }
    .detect-dot.blue { background: var(--primary-blue); }
    .detect-dot.green { background: var(--accent-green); }
    .detect-dot.purple { background: var(--accent-purple); }
    .detect-dot.amber { background: var(--accent-amber); }
    .detect-card .detect-meta {
        color: var(--text-muted);
        font-size: 12px;
        margin-top: 5px;
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

    /* ============ Hero: etiqueta superior + blur decorativo ============ */
    .hero-card {
        position: relative;
        overflow: hidden;
    }
    .hero-card::before {
        display: none;
    }
    .hero-card .eyebrow {
        position: relative;
        font-family: var(--font-mono);
        font-size: 11px;
        letter-spacing: 0.1em;
        color: var(--primary-blue);
        margin-bottom: 10px;
    }
    .hero-card h2, .hero-card .hero-subtitle {
        position: relative;
    }

    /* ============ Sidebar: flujo de analisis (nav con icono + paso) ============ */
    .sidebar-eyebrow {
        font-family: var(--font-mono);
        font-size: 10px;
        letter-spacing: 0.13em;
        text-transform: uppercase;
        color: var(--text-muted);
        padding: 6px 8px 8px 2px;
    }
    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 11px;
        padding: 0 2px 26px 2px;
    }
    .sidebar-brand-icon {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        background: var(--primary-blue);
        color: #fff;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        flex: none;
        font-family: var(--font-mono);
        font-weight: 700;
        box-shadow: 0 6px 18px rgba(91, 141, 239, 0.32);
    }
    .sidebar-brand-title {
        font-size: 14.5px;
        font-weight: 700;
        line-height: 1.1;
        color: var(--text-main);
    }
    .sidebar-brand-subtitle {
        font-family: var(--font-mono);
        font-size: 10px;
        color: var(--text-muted);
        letter-spacing: 0.04em;
        margin-top: 2px;
    }
    section[data-testid="stSidebar"] div[class*="st-key-wizard_btn_"] .stButton button {
        justify-content: flex-start;
        text-align: left;
        position: relative;
        padding-left: 13px;
        padding-right: 34px;
        font-weight: 500;
        min-height: 40px;
        gap: 12px;
    }
    section[data-testid="stSidebar"] div[class*="st-key-wizard_btn_"] .stButton button::before {
        display: none;
    }
    section[data-testid="stSidebar"] div[class*="st-key-wizard_btn_"] .stButton button [data-testid="stIconMaterial"] {
        color: currentColor !important;
        font-size: 18px !important;
    }
    section[data-testid="stSidebar"] div[class*="st-key-wizard_btn_"] .stButton button p {
        font-size: 14px;
        font-weight: 600;
        line-height: 1.2;
    }
    section[data-testid="stSidebar"] div[class*="st-key-wizard_btn_"] .stButton button[kind="secondary"] {
        background-color: transparent;
        border-color: transparent;
        color: var(--text-secondary);
    }
    section[data-testid="stSidebar"] div[class*="st-key-wizard_btn_"] .stButton button[kind="secondary"]:hover:not(:disabled) {
        background-color: rgba(255, 255, 255, 0.04);
        border-color: transparent;
        color: var(--text-main);
    }
    section[data-testid="stSidebar"] div[class*="st-key-wizard_btn_"] .stButton button[kind="primary"] {
        background-color: rgba(91, 141, 239, 0.13);
        border-color: transparent;
        box-shadow: inset 2px 0 0 var(--primary-blue);
        color: var(--primary-blue);
    }
    .st-key-wizard_btn_inicio .stButton button::after { content: "01"; }
    .st-key-wizard_btn_cargar .stButton button::after { content: "02"; }
    .st-key-wizard_btn_columnas .stButton button::after { content: "03"; }
    .st-key-wizard_btn_resumen .stButton button::after { content: "04"; }
    section[data-testid="stSidebar"] div[class*="st-key-wizard_btn_"] .stButton button::after {
        position: absolute;
        right: 12px;
        top: 50%;
        transform: translateY(-50%);
        font-family: var(--font-mono);
        font-size: 10px;
        color: var(--text-muted);
    }

    /* ============ Sidebar: tarjeta de fuente de datos ============ */
    .source-card {
        margin: 0 4px;
        padding: 11px 12px;
        border-radius: 11px;
        background: var(--bg-panel);
        border: 1px solid var(--border-soft);
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .source-card .source-icon {
        width: 30px;
        height: 30px;
        border-radius: 8px;
        background: rgba(69, 192, 138, 0.16);
        color: var(--accent-green);
        display: flex;
        align-items: center;
        justify-content: center;
        flex: none;
        font-family: var(--font-mono);
        font-size: 10px;
        font-weight: 700;
    }
    .source-card .source-label {
        font-family: var(--font-mono);
        font-size: 9.5px;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin-bottom: 2px;
    }
    .source-card .source-info {
        flex: 1;
        min-width: 0;
    }
    .source-card .source-name {
        font-size: 12.5px;
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .source-card .source-meta {
        font-family: var(--font-mono);
        font-size: 10px;
        color: var(--text-muted);
        margin-top: 1px;
    }

    /* ============ Header: badge de archivo activo ============ */
    .file-badge {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 6px 12px;
        border-radius: 8px;
        background: var(--bg-panel);
        border: 1px solid var(--border-soft);
        font-family: var(--font-mono);
        font-size: 11.5px;
        color: var(--text-secondary);
        margin-bottom: 6px;
        max-width: 100%;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .file-badge .dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--accent-green);
        display: inline-block;
        flex: none;
    }

    /* ============ Subtabs de Resumen ejecutivo (radio -> tabs con subrayado) ============ */
    .st-key-active_subtab div[role="radiogroup"] {
        gap: 4px;
        border-bottom: 1px solid var(--border-soft);
        flex-wrap: wrap;
        margin-top: 2px;
    }
    .st-key-active_subtab div[role="radiogroup"] label {
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        padding: 9px 16px 11px 16px !important;
        margin: 0 2px 0 0 !important;
        font-size: 14px;
        font-weight: 600;
        color: var(--text-secondary);
        transition: color 0.15s ease;
    }
    .st-key-active_subtab div[role="radiogroup"] label:hover {
        background: transparent !important;
        color: var(--text-main);
    }
    .st-key-active_subtab div[role="radiogroup"] label[data-checked="true"],
    .st-key-active_subtab div[role="radiogroup"] label:has(input:checked) {
        background: transparent !important;
        color: var(--primary-blue) !important;
        box-shadow: inset 0 -2px 0 var(--primary-blue);
    }
    .st-key-active_subtab div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }

    /* ============ Calidad: anillo circular de score ============ */
    .quality-ring-card {
        display: flex;
        align-items: center;
        gap: 22px;
        flex-wrap: wrap;
    }
    .quality-ring-wrap {
        position: relative;
        width: 110px;
        height: 110px;
        flex: none;
    }
    .quality-ring-wrap .ring-value {
        position: absolute;
        inset: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .quality-ring-wrap .ring-score {
        font-family: var(--font-mono);
        font-size: 28px;
        font-weight: 600;
        line-height: 1;
        color: var(--text-main);
    }
    .quality-ring-wrap .ring-max {
        font-size: 10.5px;
        color: var(--text-muted);
    }
    .quality-copy-title {
        font-size: 16px;
        font-weight: 600;
        color: var(--text-main);
        margin-bottom: 5px;
    }
    .quality-copy-desc {
        font-size: 13px;
        line-height: 1.55;
        color: var(--text-secondary);
        max-width: 560px;
    }
    .quality-counts {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        margin-top: 14px;
    }
    .quality-count {
        font-size: 12px;
        color: var(--text-muted);
    }
    .quality-count strong {
        font-family: var(--font-mono);
        font-size: 18px;
        margin-right: 6px;
    }
    .quality-count.high strong { color: var(--accent-red); }
    .quality-count.medium strong { color: var(--accent-amber); }
    .quality-count.low strong { color: var(--accent-green); }

    /* ============ Section and content cards ============ */
    .section-kicker {
        font-family: var(--font-mono);
        font-size: 11px;
        letter-spacing: 0.10em;
        text-transform: uppercase;
        color: var(--text-muted);
        margin: 18px 0 12px 2px;
    }
    .section-card {
        background: var(--bg-card);
        border: 1px solid var(--border-soft);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 14px;
    }
    .info-banner {
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(91, 141, 239, 0.14);
        border: 1px solid rgba(91, 141, 239, 0.32);
        border-radius: 11px;
        padding: 14px 18px;
        color: var(--text-main);
        margin: 4px 0 20px 0;
        font-size: 14px;
    }
    .info-dot {
        width: 18px;
        height: 18px;
        border-radius: 50%;
        border: 1px solid var(--primary-blue);
        color: var(--primary-blue);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-family: var(--font-mono);
        font-size: 11px;
        flex: none;
    }
    .preview-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
        color: var(--text-muted);
        font-family: var(--font-mono);
        font-size: 11px;
        letter-spacing: 0.10em;
        text-transform: uppercase;
        margin: 28px 0 12px 0;
    }
    .dark-table-wrap {
        overflow: hidden;
        border: 1px solid var(--border-soft);
        border-radius: 14px;
        background: #101722;
        margin-bottom: 18px;
    }
    .dark-preview-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
    }
    .dark-preview-table th {
        background: var(--bg-card);
        color: var(--text-secondary);
        font-family: var(--font-mono);
        font-size: 11px;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        text-align: left;
        padding: 13px 18px;
        border-bottom: 1px solid var(--border-soft);
    }
    .dark-preview-table td {
        color: var(--text-main);
        padding: 12px 18px;
        border-bottom: 1px solid rgba(255,255,255,0.055);
    }
    .dark-preview-table tr:last-child td {
        border-bottom: none;
    }
    .quality-table td:nth-child(3),
    .quality-table th:nth-child(3) {
        text-align: right;
        font-family: var(--font-mono);
    }
    .severity-badge {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 999px;
        padding: 4px 11px;
        font-size: 11px;
        font-weight: 700;
    }
    .severity-badge.high { background: rgba(232, 115, 107, 0.18); color: var(--accent-red); }
    .severity-badge.medium { background: rgba(233, 169, 74, 0.18); color: var(--accent-amber); }
    .severity-badge.low { background: rgba(69, 192, 138, 0.16); color: var(--accent-green); }
    .dashboard-kpi-card {
        min-height: 128px;
        background: var(--bg-card);
        border: 1px solid var(--border-soft);
        border-radius: 14px;
        padding: 20px;
    }
    .dashboard-kpi-title {
        color: var(--text-secondary);
        font-size: 13px;
        margin-bottom: 10px;
    }
    .dashboard-kpi-value {
        color: var(--text-main);
        font-family: var(--font-mono);
        font-size: 30px;
        line-height: 1.1;
        font-weight: 700;
        letter-spacing: 0;
    }
    .dashboard-kpi-delta {
        margin-top: 10px;
        font-size: 12px;
    }
    .dashboard-kpi-delta.positive { color: var(--accent-green); }
    .dashboard-kpi-delta.muted { color: var(--text-muted); }
    .chart-panel-title {
        background: var(--bg-card);
        border: 1px solid var(--border-soft);
        border-bottom: none;
        border-radius: 14px 14px 0 0;
        padding: 18px 20px 0 20px;
        color: var(--text-main);
        font-size: 15px;
        font-weight: 700;
        margin-bottom: -2px;
    }
    .analysis-summary-card {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 18px;
        background: linear-gradient(135deg, rgba(91, 141, 239, 0.12), #0E1422 70%);
        border: 1px solid rgba(91, 141, 239, 0.22);
        border-radius: 15px;
        padding: 18px 20px;
        margin-bottom: 18px;
    }
    .analysis-summary-title {
        color: var(--text-main);
        font-weight: 700;
        font-size: 17px;
        margin-bottom: 3px;
    }
    .analysis-summary-meta {
        color: var(--text-secondary);
        font-size: 13px;
    }
    .analysis-summary-score {
        font-family: var(--font-mono);
        font-size: 24px;
        font-weight: 600;
        color: var(--primary-blue);
        white-space: nowrap;
    }
    .insight-summary-card {
        background: linear-gradient(135deg, rgba(91, 141, 239, 0.12), #0E1422 70%);
        border: 1px solid rgba(91, 141, 239, 0.22);
        border-radius: 15px;
        padding: 22px 24px;
        margin-bottom: 22px;
    }
    .insight-summary-card .summary-text {
        color: #E3E8F1;
        font-size: 15px;
        line-height: 1.6;
    }
    .insight-card {
        background: var(--bg-card);
        border: 1px solid var(--border-soft);
        border-radius: 14px;
        padding: 18px 20px;
        margin-bottom: 12px;
    }
    .insight-card-head {
        display: flex;
        align-items: center;
        gap: 11px;
        margin-bottom: 12px;
    }
    .insight-number {
        width: 28px;
        height: 28px;
        border-radius: 8px;
        background: rgba(91, 141, 239, 0.14);
        color: var(--primary-blue);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-family: var(--font-mono);
        font-size: 12px;
        font-weight: 600;
        flex: none;
    }
    .insight-title {
        color: var(--text-main);
        font-size: 14.5px;
        font-weight: 600;
        line-height: 1.35;
    }
    .insight-grid {
        display: grid;
        grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
        gap: 18px;
        padding-left: 39px;
    }
    .insight-label {
        font-family: var(--font-mono);
        font-size: 10px;
        letter-spacing: 0.06em;
        color: var(--text-muted);
        margin-bottom: 4px;
        text-transform: uppercase;
    }
    .insight-copy {
        color: var(--text-secondary);
        font-size: 12.5px;
        line-height: 1.5;
    }
    .recommendation-list {
        background: var(--bg-card);
        border: 1px solid var(--border-soft);
        border-radius: 14px;
        padding: 8px 20px;
    }
    .recommendation-item {
        display: flex;
        align-items: flex-start;
        gap: 11px;
        padding: 13px 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        color: var(--text-secondary);
        font-size: 13px;
        line-height: 1.5;
    }
    .recommendation-item:last-child {
        border-bottom: none;
    }
    .recommendation-check {
        color: var(--accent-green);
        font-weight: 700;
        flex: none;
    }
    .export-card {
        background: var(--bg-card);
        border: 1px solid var(--border-soft);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 10px;
        min-height: 164px;
    }
    .export-icon {
        width: 42px;
        height: 42px;
        border-radius: 11px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 14px;
        font-size: 19px;
    }
    .export-icon.green { background: rgba(69, 192, 138, 0.15); color: var(--accent-green); }
    .export-icon.red { background: rgba(232, 115, 107, 0.15); color: var(--accent-red); }
    .export-icon.amber { background: rgba(233, 169, 74, 0.15); color: var(--accent-amber); }
    .export-title {
        color: var(--text-main);
        font-size: 15px;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .export-desc {
        color: var(--text-muted);
        font-size: 12.5px;
        line-height: 1.5;
        margin-bottom: 14px;
    }

    @media (max-width: 900px) {
        section[data-testid="stMain"] > div[data-testid="stMainBlockContainer"],
        .stMainBlockContainer.block-container,
        [data-testid="stMainBlockContainer"] {
            padding-left: 0.9rem !important;
            padding-right: 0.9rem !important;
        }
        .analysis-summary-card {
            align-items: flex-start;
            flex-direction: column;
        }
        .insight-grid {
            grid-template-columns: 1fr;
            padding-left: 0;
        }
    }
    </style>
    """, unsafe_allow_html=True)
