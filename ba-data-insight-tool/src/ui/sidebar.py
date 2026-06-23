"""Sidebar rendering for BA Data Insight Tool.

Handles: the 4-step wizard navigation, data source selection
(file / Google Sheets / batch), analysis type, advanced settings,
and column confirmation controls. Calidad/Análisis/Insights/Exportar
live as subtabs inside the "Resumen ejecutivo" step (see src/ui/tabs.py).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.batch_processor import batch_summary, consolidate_files, validate_compatible_schemas
from src.data_loader import get_excel_sheets, load_google_sheet
from src.ui.dashboard import render_column_detection_cards, render_dark_preview_table

ANALYSIS_TYPES = [
    "Ventas",
    "General",
    "Pagos",
    "Conciliaciones",
    "Registros",
    "Financiero",
]

WIZARD_STEPS = [
    ("inicio", "Inicio", ":material/home:"),
    ("cargar", "Cargar datos", ":material/upload_file:"),
    ("columnas", "Confirmar columnas", ":material/check_box:"),
    ("resumen", "Resumen ejecutivo", ":material/monitoring:"),
]

DATA_SOURCE_OPTIONS = [
    ("Subir archivo", "Ideal para Excel o CSV local."),
    ("Google Sheets", "Conecta una hoja pública de Google Sheets."),
    ("Base de datos", "Consolida varias fuentes con estructura similar."),
    ("Datos de ejemplo", "Explora el flujo con una muestra lista."),
]

SAMPLE_FILE = Path(__file__).resolve().parent.parent.parent / "sample_data" / "ventas_mensuales.csv"


def select_default(options: list[str], suggestions: list[str]) -> int:
    for suggestion in suggestions:
        if suggestion in options:
            return options.index(suggestion)
    return 0


def clean_selection(value: str) -> str | None:
    return None if value == "Ninguna" else value


def render_wizard_nav(file_loaded: bool, analysis_ready: bool) -> str:
    """Render the 4-step wizard navigation in the sidebar as a vertical
    list of buttons with status (done / current / pending / locked).

    Returns the key of the active step (e.g. "resumen").
    """
    st.sidebar.markdown(
        '<div class="sidebar-brand">'
        '<div class="sidebar-brand-icon" aria-hidden="true">'
        '<svg width="19" height="19" viewBox="0 0 20 20" fill="none">'
        '<rect x="3" y="11" width="3.4" height="6" rx="1" fill="currentColor"/>'
        '<rect x="8.3" y="7" width="3.4" height="10" rx="1" fill="currentColor"/>'
        '<rect x="13.6" y="3" width="3.4" height="14" rx="1" fill="currentColor" opacity="0.88"/>'
        '</svg>'
        '</div>'
        '<div><div class="sidebar-brand-title">BA Insight</div>'
        '<div class="sidebar-brand-subtitle">DATA · TOOL</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown('<div class="sidebar-eyebrow">Flujo de análisis</div>', unsafe_allow_html=True)

    available_keys = ["inicio", "cargar"]
    if file_loaded:
        available_keys += ["columnas", "resumen"]

    current = st.session_state.get("wizard_step", "inicio")
    if current not in available_keys:
        current = available_keys[-1] if file_loaded else "cargar"
        st.session_state["wizard_step"] = current

    completed_keys = {"inicio"}
    if file_loaded:
        completed_keys.add("cargar")
        completed_keys.add("columnas")
    if analysis_ready:
        completed_keys.add("resumen")

    for key, label, type_icon in WIZARD_STEPS:
        locked = key not in available_keys
        is_current = key == current
        done = key in completed_keys and not is_current

        button_type = "primary" if is_current else "secondary"
        if st.sidebar.button(
            label,
            key=f"wizard_btn_{key}",
            width="stretch",
            type=button_type,
            icon=type_icon,
            disabled=locked,
        ):
            st.session_state["wizard_step"] = key
            st.rerun()

    if analysis_ready:
        st.sidebar.markdown(
            '<div class="progress-complete">'
            '<div class="progress-ring">✓</div>'
            '<div class="progress-title">Análisis completado</div>'
            '<div class="progress-desc">Listo para revisar y exportar</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.sidebar.divider()
    return current


def render_sidebar_context_card(source_filename: str, profile: dict, analysis_type: str, quality_score: dict | None) -> None:
    """Compact read-only context shown in the sidebar for steps 4-8."""
    st.sidebar.markdown('<div class="sidebar-eyebrow">Fuente de datos</div>', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<div class="source-card">'
        '<div class="source-icon">DOC</div>'
        '<div class="source-info">'
        '<div class="source-label">Archivo actual</div>'
        f'<div class="source-name">{source_filename}</div>'
        f'<div class="source-meta">{profile["rows"]:,} filas · {profile["columns"]} col.</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.caption(f"Tipo de análisis: {analysis_type}")
    if quality_score:
        st.sidebar.caption(f"Calidad de datos: {quality_score['score']}/100")

    with st.sidebar.expander("Cambiar archivo / Reiniciar"):
        render_reset_control(key_prefix="context")


def render_reset_control(container=None, key_prefix: str = "") -> None:
    """Render a 'Limpiar / reiniciar' button gated behind a confirmation
    popover, since session_state.clear() discards the loaded file and
    analysis irreversibly."""
    target = container if container is not None else st
    with target.popover("Limpiar / reiniciar", width="stretch"):
        st.warning("Se perderá el archivo cargado y el análisis actual. Esta acción no se puede deshacer.")
        if st.button("Sí, reiniciar todo", type="primary", width="stretch", key=f"confirm_reset_{key_prefix}"):
            st.session_state.clear()
            st.rerun()


def render_sidebar_source(load_data, container=None) -> dict:
    """Render data-source controls for the 'Cargar datos' step.

    Args:
        load_data: the load_data() function from src.data_loader,
            passed in to avoid circular imports.
        container: Streamlit container to render into (defaults to the
            main area). Pass st.sidebar to render in the sidebar instead.

    Returns a dict with: uploaded, sheet_name, gs_df, gs_url, batch_df.
    """
    target = container if container is not None else st

    with target.container():
        target.markdown('<div class="section-kicker load-kicker">Fuente de datos</div>', unsafe_allow_html=True)
        source_values = [value for value, _ in DATA_SOURCE_OPTIONS]
        source_descriptions = dict(DATA_SOURCE_OPTIONS)
        legacy_source_map = {
            "Google Sheets URL": "Google Sheets",
            "Múltiples archivos (batch)": "Base de datos",
        }
        if st.session_state.get("data_source") in legacy_source_map:
            st.session_state["data_source"] = legacy_source_map[st.session_state["data_source"]]
        if "data_source" not in st.session_state:
            st.session_state["data_source"] = source_values[0]
        if st.session_state["data_source"] not in source_values:
            st.session_state["data_source"] = source_values[0]

        data_source = target.radio(
            "Fuente de datos",
            source_values,
            key="data_source",
            horizontal=True,
            label_visibility="collapsed",
        )

        gs_df = None
        batch_df = None
        uploaded = None
        sheet_name = None

        left_col, right_col = target.columns([1.36, 0.98], gap="large")
        with left_col:
            st.markdown(
                f'<div class="load-source-caption">{source_descriptions[data_source]}</div>',
                unsafe_allow_html=True,
            )
            if data_source == "Google Sheets":
                st.markdown(
                    '<div class="connector-card">'
                    '<div class="connector-icon">GS</div>'
                    '<div><div class="connector-title">Conectar Google Sheets</div>'
                    '<div class="connector-desc">Pega una URL pública. La primera hoja debe contener encabezados.</div></div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                gs_url = st.text_input(
                    "URL de Google Sheets",
                    placeholder="https://docs.google.com/spreadsheets/d/...",
                    key="gs_url",
                )
                if gs_url:
                    try:
                        gs_df = load_google_sheet(gs_url)
                        st.success(f"Cargado: {len(gs_df)} filas · {len(gs_df.columns)} columnas")
                    except ValueError as exc:
                        st.error("No pudimos cargar la hoja de Google Sheets.")
                        st.markdown(
                            "Revisa lo siguiente:\n"
                            "- El documento debe estar compartido como **\"Cualquier persona con el enlace\"**.\n"
                            "- La URL debe apuntar a un Google Sheet (no a Drive ni a otro tipo de archivo).\n"
                            "- La primera hoja debe tener encabezados de columna en la primera fila."
                        )
                        with st.expander("Ver detalle técnico"):
                            st.code(str(exc))
                        gs_df = None
            elif data_source == "Base de datos":
                st.markdown(
                    '<div class="connector-card">'
                    '<div class="connector-icon">DB</div>'
                    '<div><div class="connector-title">Importación por lote</div>'
                    '<div class="connector-desc">Consolida varios archivos con la misma estructura mientras se habilitan conectores directos.</div></div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                batch_files = st.file_uploader(
                    "Seleccionar archivos",
                    type=["csv", "xlsx", "xls"],
                    accept_multiple_files=True,
                    key="batch_uploader",
                    label_visibility="collapsed",
                )
                df = None
                if batch_files:
                    try:
                        loaded_dfs = []
                        filenames = []
                        for f in batch_files:
                            loaded_dfs.append(load_data(f, f.name))
                            filenames.append(f.name)

                        validation = validate_compatible_schemas(loaded_dfs, filenames)
                        summary = batch_summary(loaded_dfs, filenames)
                        st.session_state["batch_validation"] = validation
                        st.session_state["batch_summary"] = summary

                        total_rows = sum(len(d) for d in loaded_dfs)
                        st.success(f"{len(batch_files)} archivos · {total_rows} filas totales")

                        if not validation["is_compatible"]:
                            st.warning(
                                "Estructuras muy distintas entre archivos. "
                                "Revisa el detalle antes de continuar."
                            )

                        df = consolidate_files(loaded_dfs, filenames)
                    except Exception as e:
                        st.error("No pudimos consolidar los archivos.")
                        st.markdown(
                            "Revisa lo siguiente:\n"
                            "- Todos los archivos deben tener encabezados de columna en la primera fila.\n"
                            "- Deben compartir al menos algunas columnas en común para poder unirse.\n"
                            "- Ningún archivo debe estar vacío o dañado."
                        )
                        with st.expander("Ver detalle técnico"):
                            st.code(str(e))
                batch_df = df
            elif data_source == "Datos de ejemplo":
                st.markdown(
                    '<div class="sample-data-card">'
                    '<div class="upload-icon-large">▶</div>'
                    '<div class="upload-title">Explora con ventas_mensuales.csv</div>'
                    '<div class="upload-desc">Dataset de muestra con fecha, categoría, canal, clientes, ticket promedio y venta total.</div>'
                    '<div class="upload-formats">Sin preparación · listo para confirmar columnas</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                if st.button(
                    "Cargar datos de ejemplo",
                    type="primary",
                    width="stretch",
                    key="btn_source_demo",
                    icon=":material/play_arrow:",
                ):
                    if SAMPLE_FILE.exists():
                        st.session_state["demo_df"] = load_data(str(SAMPLE_FILE), SAMPLE_FILE.name)
                        st.session_state["analysis_has_run"] = False
                        for key in ["date_column", "amount_column", "category_column", "status_column"]:
                            st.session_state.pop(key, None)
                        st.session_state["wizard_step"] = "columnas"
                        st.session_state["source_filename"] = f"{SAMPLE_FILE.name} (ejemplo)"
                        st.rerun()
                    else:
                        st.error("No se encontró el archivo de ejemplo.")
            else:
                st.markdown(
                    '<div class="upload-intro">'
                    '<div class="upload-icon-large">↑</div>'
                    '<div class="upload-title">Arrastra tu archivo aquí</div>'
                    '<div class="upload-desc">o haz clic para explorar — Excel, CSV o Google Sheet</div>'
                    '<div class="upload-formats">Formatos: .xlsx · .xls · .csv · máx. 200 MB</div>'
                    '</div>',
                    unsafe_allow_html=True,
                )
                uploaded = st.file_uploader(
                    "Seleccionar archivo",
                    type=["csv", "xlsx", "xls"],
                    key="uploaded_data_file",
                    label_visibility="collapsed",
                )

                if uploaded and uploaded.name.lower().endswith((".xlsx", ".xls")):
                    try:
                        sheets = get_excel_sheets(uploaded)
                        uploaded.seek(0)
                        sheet_name = st.selectbox("Hoja de Excel", sheets, key="excel_sheet_name")
                    except ValueError as exc:
                        st.error("No pudimos leer las hojas del archivo Excel.")
                        with st.expander("Ver detalle técnico"):
                            st.code(str(exc))

        with right_col:
            st.markdown(
                '<div class="recent-files-card">'
                '<div class="section-kicker compact">Archivos recientes</div>'
                '<div class="recent-file-row">'
                '<div class="recent-file-icon green">DOC</div>'
                '<div><div class="recent-file-name">ventas_mensuales.csv</div>'
                '<div class="recent-file-meta">hace 2 días · 3.867 filas</div></div>'
                '</div>'
                '<div class="recent-file-row">'
                '<div class="recent-file-icon blue">XLS</div>'
                '<div><div class="recent-file-name">pagos_q1.xlsx</div>'
                '<div class="recent-file-meta">hace 1 semana · 1.240 filas</div></div>'
                '</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="load-tip-card">'
                '<span class="info-dot">i</span>'
                '<div>La primera fila debe contener los <strong>nombres de columna</strong>.'
                '<br><span>Detectaremos tipos y columnas clave automáticamente.</span></div>'
                '</div>',
                unsafe_allow_html=True,
            )

        return {
            "uploaded": uploaded,
            "sheet_name": sheet_name,
            "gs_df": gs_df,
            "gs_url": st.session_state.get("gs_url"),
            "batch_df": batch_df,
        }


def render_sidebar_analysis_config(container=None) -> dict:
    """Render analysis-type + advanced settings (shown in 'Confirmar columnas')."""
    if st.session_state.get("analysis_type") not in ANALYSIS_TYPES:
        st.session_state["analysis_type"] = "Ventas"
    if "anomaly_threshold" not in st.session_state:
        st.session_state["anomaly_threshold"] = 2.0
    return {
        "analysis_type": st.session_state["analysis_type"],
        "threshold": st.session_state["anomaly_threshold"],
    }


def render_sidebar_column_controls(df: pd.DataFrame, detected: dict, container=None) -> dict:
    """Render the column-confirmation controls and action buttons."""
    target = container if container is not None else st

    with target.container():
        target.markdown(
            '<div class="info-banner">'
            '<span class="info-dot">i</span>'
            '<span>Detectamos automáticamente las columnas clave. '
            '<strong>Revisa y ajusta</strong> antes de ejecutar el análisis.</span>'
            '</div>',
            unsafe_allow_html=True,
        )
        target.markdown('<div class="section-kicker">Columnas detectadas</div>', unsafe_allow_html=True)
        render_column_detection_cards(detected, df)

        target.markdown('<div class="section-kicker">Tipo de análisis</div>', unsafe_allow_html=True)
        if st.session_state.get("analysis_type") not in ANALYSIS_TYPES:
            st.session_state["analysis_type"] = "Ventas"
        target.radio(
            "Tipo de análisis",
            ANALYSIS_TYPES,
            key="analysis_type",
            horizontal=True,
            label_visibility="collapsed",
        )

        render_dark_preview_table(df, max_rows=6)

        cols = ["Ninguna"] + list(df.columns)
        with target.expander("Ajustar columnas manualmente", expanded=False):
            col_a, col_b = target.columns(2)
            date_col = col_a.selectbox("Fecha", cols, index=select_default(cols, detected.get("date", [])), key="date_column")
            amount_col = col_b.selectbox("Monto principal", cols, index=select_default(cols, detected.get("amount", []) or detected.get("numeric", [])), key="amount_column")
            category_col = col_a.selectbox("Categoría", cols, index=select_default(cols, detected.get("category", [])), key="category_column")
            status_col = col_b.selectbox("Estado", cols, index=select_default(cols, detected.get("status", [])), key="status_column")
            threshold = target.slider(
                "Sensibilidad para detectar valores atípicos",
                min_value=1.0,
                max_value=4.0,
                value=float(st.session_state.get("anomaly_threshold", 2.0)),
                step=0.25,
                key="anomaly_threshold",
                help="Valores más bajos detectan más registros sospechosos.",
            )

        btn_spacer, btn_col = target.columns([4.2, 0.8])
        with btn_spacer:
            render_reset_control(key_prefix="columnas")
        run_analysis = btn_col.button(
            "Ejecutar análisis",
            type="primary",
            width="stretch",
            key="run_analysis_button",
            icon=":material/arrow_forward:",
            icon_position="right",
        )

    return {
        "date_col": date_col,
        "amount_col": amount_col,
        "category_col": category_col,
        "status_col": status_col,
        "run_analysis": run_analysis,
    }
