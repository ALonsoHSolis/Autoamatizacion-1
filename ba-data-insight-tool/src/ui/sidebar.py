"""Sidebar rendering for BA Data Insight Tool.

Handles: the 8-step wizard navigation, data source selection
(file / Google Sheets / batch), analysis type, advanced settings,
and column confirmation controls.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.batch_processor import batch_summary, consolidate_files, validate_compatible_schemas
from src.data_loader import get_excel_sheets, load_google_sheet

ANALYSIS_TYPES = [
    "Análisis general",
    "Análisis de ventas",
    "Análisis de pagos",
    "Análisis de conciliaciones",
    "Análisis de registros/personas",
    "Análisis financiero simple",
]

WIZARD_STEPS = [
    ("inicio", "1. Inicio"),
    ("cargar", "2. Cargar datos"),
    ("columnas", "3. Confirmar columnas"),
    ("resumen", "4. Resumen ejecutivo"),
    ("calidad", "5. Calidad de datos"),
    ("analisis", "6. Análisis"),
    ("insights", "7. Insights y recomendaciones"),
    ("exportar", "8. Exportar"),
]


def select_default(options: list[str], suggestions: list[str]) -> int:
    for suggestion in suggestions:
        if suggestion in options:
            return options.index(suggestion)
    return 0


def clean_selection(value: str) -> str | None:
    return None if value == "Ninguna" else value


def render_wizard_nav(file_loaded: bool, analysis_ready: bool) -> str:
    """Render the 8-step wizard navigation in the sidebar.

    Steps 3-8 are disabled (shown but not selectable) until a file is
    loaded; steps 6-8 stay reachable once a file is loaded so the user
    can see the "ejecuta el análisis" prompts, matching prior behavior.

    Returns the key of the active step (e.g. "resumen", "analisis").
    """
    st.sidebar.markdown("### 🧭 Tu progreso")

    available_keys = ["inicio", "cargar"]
    if file_loaded:
        available_keys += ["columnas", "resumen", "calidad", "analisis", "insights", "exportar"]

    current = st.session_state.get("wizard_step", "inicio")
    if current not in available_keys:
        current = available_keys[-1] if file_loaded else "cargar"

    completed_keys = {"inicio", "cargar"}
    if file_loaded:
        completed_keys.add("columnas")
    if analysis_ready:
        completed_keys |= {"resumen", "calidad", "analisis", "insights", "exportar"}

    labels = []
    label_to_key = {}
    for key, label in WIZARD_STEPS:
        if key not in available_keys:
            display = f"🔒 {label}"
        elif key == current:
            display = f"➡️ {label}"
        elif key in completed_keys:
            display = f"✅ {label}"
        else:
            display = f"⬜ {label}"
        labels.append(display)
        label_to_key[display] = key

    default_index = next((i for i, (k, _) in enumerate(WIZARD_STEPS) if k == current), 0)

    selected_label = st.sidebar.radio(
        "Pasos",
        labels,
        index=default_index,
        key="wizard_nav_radio",
        label_visibility="collapsed",
    )
    selected_key = label_to_key[selected_label]

    if selected_key not in available_keys:
        selected_key = current

    st.session_state["wizard_step"] = selected_key
    st.sidebar.divider()
    return selected_key


def render_sidebar_source(load_data) -> dict:
    """Render data-source controls for the 'Cargar datos' step.

    Args:
        load_data: the load_data() function from src.data_loader,
            passed in to avoid circular imports.

    Returns a dict with: uploaded, sheet_name, gs_df, gs_url, batch_df.
    """
    with st.sidebar:
        st.subheader("Cargar archivo")
        st.caption("Formatos soportados: CSV, XLSX y XLS.")

        st.markdown("### Fuente de datos")
        data_source = st.radio(
            "Tipo de entrada",
            ["Subir archivo", "Google Sheets URL",
             "Múltiples archivos (batch)"],
            key="data_source",
            horizontal=True,
        )

        gs_df = None
        batch_df = None
        if data_source == "Google Sheets URL":
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
                    st.error(str(exc))
                    gs_df = None
            uploaded = None
            sheet_name = None
        elif data_source == "Múltiples archivos (batch)":
            batch_files = st.sidebar.file_uploader(
                "Sube varios archivos (misma estructura)",
                type=["csv", "xlsx", "xls"],
                accept_multiple_files=True,
                key="batch_uploader",
            )
            df = None
            uploaded = None
            sheet_name = None
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
                    st.sidebar.success(f"{len(batch_files)} archivos · {total_rows} filas totales")

                    if not validation["is_compatible"]:
                        st.sidebar.warning(
                            "⚠️ Estructuras muy distintas entre archivos. "
                            "Revisa el detalle antes de continuar."
                        )

                    df = consolidate_files(loaded_dfs, filenames)
                except Exception as e:
                    st.sidebar.error(f"Error al procesar archivos: {e}")
            batch_df = df
        else:
            uploaded = st.file_uploader("Sube tu archivo", type=["csv", "xlsx", "xls"], key="uploaded_data_file")

            sheet_name = None
            if uploaded and uploaded.name.lower().endswith((".xlsx", ".xls")):
                try:
                    sheets = get_excel_sheets(uploaded)
                    uploaded.seek(0)
                    sheet_name = st.selectbox("Hoja de Excel", sheets, key="excel_sheet_name")
                except ValueError as exc:
                    st.error("No pudimos leer las hojas del archivo Excel.")
                    with st.expander("Ver detalle técnico"):
                        st.code(str(exc))

        return {
            "uploaded": uploaded,
            "sheet_name": sheet_name,
            "gs_df": gs_df,
            "gs_url": st.session_state.get("gs_url"),
            "batch_df": batch_df,
        }


def render_sidebar_analysis_config() -> dict:
    """Render analysis-type + advanced settings (shown alongside loading)."""
    with st.sidebar:
        st.divider()
        st.subheader("Configurar análisis")
        analysis_type = st.selectbox("Tipo de análisis", ANALYSIS_TYPES, key="analysis_type")

        with st.sidebar.expander("⚙️ Configuración avanzada", expanded=False):
            threshold = st.slider(
                "Sensibilidad para detectar valores atípicos",
                min_value=1.0,
                max_value=4.0,
                value=2.0,
                step=0.25,
                key="anomaly_threshold",
                help="Valores más bajos detectan más registros sospechosos.",
            )

        return {
            "analysis_type": analysis_type,
            "threshold": threshold,
        }


def render_sidebar_column_controls(df: pd.DataFrame, detected: dict) -> dict:
    """Render the column-confirmation controls and action buttons."""
    with st.sidebar:
        st.subheader("Confirmar columnas")
        st.caption("La app sugiere columnas automáticamente. Puedes cambiarlas si conoces mejor el archivo.")
        cols = ["Ninguna"] + list(df.columns)
        date_col = st.selectbox("Fecha", cols, index=select_default(cols, detected.get("date", [])), key="date_column")
        amount_col = st.selectbox("Monto principal", cols, index=select_default(cols, detected.get("amount", []) or detected.get("numeric", [])), key="amount_column")
        category_col = st.selectbox("Categoría", cols, index=select_default(cols, detected.get("category", [])), key="category_column")
        status_col = st.selectbox("Estado", cols, index=select_default(cols, detected.get("status", [])), key="status_column")

        st.divider()
        run_analysis = st.button("Ejecutar análisis", type="primary", width="stretch", key="run_analysis_button")
        if st.button("Limpiar / reiniciar", width="stretch", key="reset_button"):
            st.session_state.clear()
            st.rerun()

    return {
        "date_col": date_col,
        "amount_col": amount_col,
        "category_col": category_col,
        "status_col": status_col,
        "run_analysis": run_analysis,
    }
