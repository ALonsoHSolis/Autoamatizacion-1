"""Sidebar rendering for BA Data Insight Tool.

Handles: the 4-step wizard navigation, data source selection
(file / Google Sheets / batch), analysis type, advanced settings,
and column confirmation controls. Calidad/Análisis/Insights/Exportar
live as subtabs inside the "Resumen ejecutivo" step (see src/ui/tabs.py).
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
    ("inicio", "Inicio"),
    ("cargar", "Cargar datos"),
    ("columnas", "Confirmar columnas"),
    ("resumen", "Resumen ejecutivo"),
]

DATA_SOURCE_OPTIONS = [
    ("Subir archivo", "Ideal para Excel o CSV local."),
    ("Google Sheets URL", "Usa una URL pública de Google Sheets."),
    ("Múltiples archivos (batch)", "Consolida varios archivos con estructura similar."),
]


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
    st.sidebar.markdown("### Tu progreso")

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

    for key, label in WIZARD_STEPS:
        locked = key not in available_keys
        is_current = key == current
        done = key in completed_keys and not is_current

        if done:
            icon = "✅"
        elif locked:
            icon = "🔒"
        else:
            icon = "⚪"

        button_type = "primary" if is_current else "secondary"
        if st.sidebar.button(
            f"{icon}  {label}",
            key=f"wizard_btn_{key}",
            width="stretch",
            type=button_type,
            disabled=locked,
        ):
            st.session_state["wizard_step"] = key
            st.rerun()

    if analysis_ready:
        st.sidebar.markdown(
            '<div class="progress-complete">'
            '<div class="progress-ring">100%</div>'
            '<div class="progress-title">Progreso completo</div>'
            '<div class="progress-desc">Listo para generar insights</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.sidebar.divider()
    return current


def render_sidebar_context_card(source_filename: str, profile: dict, analysis_type: str, quality_score: dict | None) -> None:
    """Compact read-only context shown in the sidebar for steps 4-8."""
    st.sidebar.markdown("### Archivo actual")
    st.sidebar.write(f"**{source_filename}**")
    st.sidebar.caption(f"{profile['rows']:,} filas · {profile['columns']} columnas")
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
        target.subheader("Cargar archivo")
        target.caption("Formatos soportados: CSV, XLSX y XLS.")

        target.markdown("### Fuente de datos")
        source_values = [value for value, _ in DATA_SOURCE_OPTIONS]
        source_descriptions = dict(DATA_SOURCE_OPTIONS)
        if "data_source" not in st.session_state:
            st.session_state["data_source"] = source_values[0]

        data_source = target.radio(
            "Fuente de datos",
            source_values,
            key="data_source",
            horizontal=True,
            label_visibility="collapsed",
        )
        target.caption(source_descriptions[data_source])

        gs_df = None
        batch_df = None
        if data_source == "Google Sheets URL":
            gs_url = target.text_input(
                "URL de Google Sheets",
                placeholder="https://docs.google.com/spreadsheets/d/...",
                key="gs_url",
            )
            if gs_url:
                try:
                    gs_df = load_google_sheet(gs_url)
                    target.success(f"Cargado: {len(gs_df)} filas · {len(gs_df.columns)} columnas")
                except ValueError as exc:
                    target.error("No pudimos cargar la hoja de Google Sheets.")
                    target.markdown(
                        "Revisa lo siguiente:\n"
                        "- El documento debe estar compartido como **\"Cualquier persona con el enlace\"**.\n"
                        "- La URL debe apuntar a un Google Sheet (no a Drive ni a otro tipo de archivo).\n"
                        "- La primera hoja debe tener encabezados de columna en la primera fila."
                    )
                    with target.expander("Ver detalle técnico"):
                        target.code(str(exc))
                    gs_df = None
            uploaded = None
            sheet_name = None
        elif data_source == "Múltiples archivos (batch)":
            batch_files = target.file_uploader(
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
                    target.success(f"{len(batch_files)} archivos · {total_rows} filas totales")

                    if not validation["is_compatible"]:
                        target.warning(
                            "⚠️ Estructuras muy distintas entre archivos. "
                            "Revisa el detalle antes de continuar."
                        )

                    df = consolidate_files(loaded_dfs, filenames)
                except Exception as e:
                    target.error("No pudimos consolidar los archivos.")
                    target.markdown(
                        "Revisa lo siguiente:\n"
                        "- Todos los archivos deben tener encabezados de columna en la primera fila.\n"
                        "- Deben compartir al menos algunas columnas en común para poder unirse.\n"
                        "- Ningún archivo debe estar vacío o dañado."
                    )
                    with target.expander("Ver detalle técnico"):
                        target.code(str(e))
            batch_df = df
        else:
            uploaded = target.file_uploader("Sube tu archivo", type=["csv", "xlsx", "xls"], key="uploaded_data_file")

            sheet_name = None
            if uploaded and uploaded.name.lower().endswith((".xlsx", ".xls")):
                try:
                    sheets = get_excel_sheets(uploaded)
                    uploaded.seek(0)
                    sheet_name = target.selectbox("Hoja de Excel", sheets, key="excel_sheet_name")
                except ValueError as exc:
                    target.error("No pudimos leer las hojas del archivo Excel.")
                    with target.expander("Ver detalle técnico"):
                        target.code(str(exc))

        return {
            "uploaded": uploaded,
            "sheet_name": sheet_name,
            "gs_df": gs_df,
            "gs_url": st.session_state.get("gs_url"),
            "batch_df": batch_df,
        }


def render_sidebar_analysis_config(container=None) -> dict:
    """Render analysis-type + advanced settings (shown in 'Confirmar columnas')."""
    target = container if container is not None else st

    with target.container():
        target.subheader("Configurar análisis")
        analysis_type = target.selectbox("Tipo de análisis", ANALYSIS_TYPES, key="analysis_type")

        with target.expander("⚙️ Configuración avanzada", expanded=False):
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


def render_sidebar_column_controls(df: pd.DataFrame, detected: dict, container=None) -> dict:
    """Render the column-confirmation controls and action buttons."""
    target = container if container is not None else st

    with target.container():
        target.subheader("Confirmar columnas")
        target.caption("La app sugiere columnas automáticamente. Puedes cambiarlas si conoces mejor el archivo.")
        cols = ["Ninguna"] + list(df.columns)
        col_a, col_b = target.columns(2)
        date_col = col_a.selectbox("Fecha", cols, index=select_default(cols, detected.get("date", [])), key="date_column")
        amount_col = col_b.selectbox("Monto principal", cols, index=select_default(cols, detected.get("amount", []) or detected.get("numeric", [])), key="amount_column")
        category_col = col_a.selectbox("Categoría", cols, index=select_default(cols, detected.get("category", [])), key="category_column")
        status_col = col_b.selectbox("Estado", cols, index=select_default(cols, detected.get("status", [])), key="status_column")

        target.divider()
        btn_col_a, btn_col_b = target.columns(2)
        run_analysis = btn_col_a.button("Ejecutar análisis", type="primary", width="stretch", key="run_analysis_button")
        with btn_col_b:
            render_reset_control(key_prefix="columnas")

    return {
        "date_col": date_col,
        "amount_col": amount_col,
        "category_col": category_col,
        "status_col": status_col,
        "run_analysis": run_analysis,
    }
