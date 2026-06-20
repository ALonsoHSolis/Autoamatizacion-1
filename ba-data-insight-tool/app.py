from __future__ import annotations

import importlib
import sys
from pathlib import Path
from types import ModuleType

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import utils as _utils


REQUIRED_UTILS_API = (
    "format_currency",
    "format_number",
    "format_percent",
    "parse_numeric_series",
    "strip_accents",
)

REQUIRED_BUSINESS_INSIGHTS_API = (
    "build_insight_context",
    "enrich_context_for_app",
    "generate_insights",
    "insights_to_text",
)


def load_business_insights_module() -> ModuleType:
    """Reload dependent modules so Streamlit does not keep stale imports."""
    importlib.invalidate_caches()

    utils_module = importlib.reload(_utils)
    missing_utils = [name for name in REQUIRED_UTILS_API if not hasattr(utils_module, name)]
    if missing_utils:
        missing_text = ", ".join(missing_utils)
        raise ImportError(f"src.utils no expone las funciones requeridas: {missing_text}")

    kpi_module = importlib.import_module("src.kpi_engine")
    importlib.reload(kpi_module)

    if "src.charts" in sys.modules:
        importlib.reload(sys.modules["src.charts"])

    module = importlib.import_module("src.business_insights")
    module = importlib.reload(module)
    missing = [name for name in REQUIRED_BUSINESS_INSIGHTS_API if not hasattr(module, name)]
    if missing:
        missing_text = ", ".join(missing)
        raise ImportError(f"src.business_insights no expone las funciones requeridas: {missing_text}")

    if "src.export_utils" in sys.modules:
        importlib.reload(sys.modules["src.export_utils"])
    return module


business_insights = load_business_insights_module()

from src.anomaly_detection import detect_anomalies
from src.charts import (
    create_amount_distribution,
    create_batch_summary_chart,
    create_category_chart,
    create_correlation_heatmap,
    create_forecast_chart,
    create_status_chart,
    create_temporal_chart,
)
from src.data_loader import load_data
from src.data_profiler import calculate_quality_score, profile_dataset, quality_warnings, warnings_to_frame
from src.kpi_engine import calculate_kpis, forecast_trend, kpis_to_frame

from src.ui.styles import inject_custom_css
from src.ui.header import render_header
from src.ui.empty_state import render_empty_state
from src.ui.sidebar import (
    ANALYSIS_TYPES,
    clean_selection,
    render_sidebar_analysis_config,
    render_sidebar_column_controls,
    render_sidebar_context_card,
    render_sidebar_source,
    render_wizard_nav,
)
from src.ui.dashboard import render_column_detection_cards
from src.ui.tabs import (
    render_step_analisis,
    render_step_calidad,
    render_step_exportar,
    render_step_insights,
    render_step_resumen,
)


APP_TITLE = "Herramienta de análisis de datos de BA"
APP_SUBTITLE = "Análisis automático de datos para equipos de negocio, conciliaciones, pagos, ventas y operaciones."

st.set_page_config(page_title=APP_TITLE, page_icon=":bar_chart:", layout="wide")


@st.cache_data(show_spinner=False)
def cached_load(file_bytes: bytes, filename: str, sheet_name: str | None) -> pd.DataFrame:
    """Cache load_data per (file_bytes, filename, sheet_name)."""
    from io import BytesIO

    return load_data(BytesIO(file_bytes), filename, sheet_name)


@st.cache_data(show_spinner=False)
def cached_profile(df: pd.DataFrame):
    """Cache profile_dataset so it only runs when the DataFrame changes."""
    return profile_dataset(df)


def file_signature(uploaded) -> str:
    return f"{uploaded.name}:{uploaded.size}" if uploaded is not None else ""


def main() -> None:
    inject_custom_css()
    render_header(APP_TITLE, APP_SUBTITLE)

    # Peek at the wizard step before rendering the nav, so that a file
    # uploaded/selected in THIS render already unlocks "columnas" instead
    # of requiring an extra rerun.
    demo_df = st.session_state.get("demo_df")
    has_new_source = (
        demo_df is not None
        or st.session_state.get("gs_url")
        or st.session_state.get("uploaded_data_file") is not None
        or st.session_state.get("batch_uploader")
    )
    file_loaded = st.session_state.get("df_loaded", False) or bool(has_new_source)
    analysis_ready = st.session_state.get("analysis_has_run", False)
    step = render_wizard_nav(file_loaded, analysis_ready)

    if step == "inicio":
        render_empty_state(load_data)
        return

    if step == "cargar":
        source_controls = render_sidebar_source(load_data)
    else:
        source_controls = {"uploaded": None, "sheet_name": None, "gs_df": None, "gs_url": None, "batch_df": None}
    if step == "columnas":
        config_controls = render_sidebar_analysis_config()
    else:
        config_controls = {
            "analysis_type": st.session_state.get("analysis_type", ANALYSIS_TYPES[0]),
            "threshold": st.session_state.get("anomaly_threshold", 2.0),
        }

    uploaded = source_controls["uploaded"]
    sheet_name = source_controls["sheet_name"]
    gs_df = source_controls["gs_df"]
    gs_url = source_controls["gs_url"]
    batch_df = source_controls["batch_df"]
    analysis_type = config_controls["analysis_type"]
    threshold = config_controls["threshold"]

    new_source_filename = None

    if gs_df is not None:
        signature = f"gsheet:{gs_url}"
        if st.session_state.get("active_file_signature") != signature:
            st.session_state["active_file_signature"] = signature
            st.session_state["analysis_has_run"] = False
            for key in ["date_column", "amount_column", "category_column", "status_column"]:
                st.session_state.pop(key, None)
            st.session_state["wizard_step"] = "columnas"
            st.rerun()
        df = gs_df
        new_source_filename = "Google Sheets"
    elif batch_df is not None:
        batch_summary_df = st.session_state.get("batch_summary")
        filenames = batch_summary_df["archivo"].tolist() if batch_summary_df is not None else []
        signature = "batch:" + ",".join(filenames)
        if st.session_state.get("active_file_signature") != signature:
            st.session_state["active_file_signature"] = signature
            st.session_state["analysis_has_run"] = False
            for key in ["date_column", "amount_column", "category_column", "status_column"]:
                st.session_state.pop(key, None)
            st.session_state["wizard_step"] = "columnas"
            st.rerun()
        df = batch_df
        new_source_filename = "Batch: " + ", ".join(filenames)
    elif uploaded is not None:
        signature = file_signature(uploaded)
        is_new_file = st.session_state.get("active_file_signature") != signature
        if is_new_file:
            st.session_state["active_file_signature"] = signature
            st.session_state["analysis_has_run"] = False
            for key in ["date_column", "amount_column", "category_column", "status_column"]:
                st.session_state.pop(key, None)

        try:
            with st.spinner("Procesando archivo..."):
                uploaded.seek(0)
                file_bytes = uploaded.read()
                df = cached_load(file_bytes, uploaded.name, sheet_name)
        except ValueError as exc:
            st.error("No pudimos procesar el archivo. Revisa que tenga encabezados válidos y datos tabulares.")
            with st.expander("Ver detalle técnico"):
                st.code(str(exc))
            return
        new_source_filename = uploaded.name
        if is_new_file:
            st.session_state["df_loaded"] = True
            st.session_state["df"] = df
            st.session_state["source_filename"] = new_source_filename
            st.session_state["wizard_step"] = "columnas"
            st.rerun()
    elif demo_df is not None:
        signature = "demo:ventas_mensuales"
        if st.session_state.get("active_file_signature") != signature:
            st.session_state["active_file_signature"] = signature
            st.session_state["analysis_has_run"] = False
            for key in ["date_column", "amount_column", "category_column", "status_column"]:
                st.session_state.pop(key, None)
            st.session_state["wizard_step"] = "columnas"
            st.rerun()
        df = demo_df
        new_source_filename = "ventas_mensuales.csv (ejemplo)"
    elif step != "cargar":
        # Past the loading step with no fresh source pending: reuse the
        # already-loaded DataFrame so the source selector doesn't need to
        # re-render (and re-clear) on every step.
        df = st.session_state.get("df")
        new_source_filename = st.session_state.get("source_filename")
        if df is None:
            st.session_state["df_loaded"] = False
            render_empty_state(load_data)
            return
    else:
        st.session_state["df_loaded"] = False
        return

    st.session_state["df_loaded"] = True
    st.session_state["df"] = df
    if new_source_filename is not None:
        st.session_state["source_filename"] = new_source_filename
    source_filename = st.session_state.get("source_filename", "archivo_desconocido")

    profile = cached_profile(df)
    detected = profile["detected"]

    if step == "cargar":
        st.success("Archivo cargado correctamente.")

        if st.session_state.get("data_source") == "Múltiples archivos (batch)":
            batch_validation = st.session_state.get("batch_validation")
            batch_summary_df = st.session_state.get("batch_summary")
            if batch_validation and batch_summary_df is not None:
                with st.expander("Ver detalle de consolidación batch",
                                 expanded=not batch_validation["is_compatible"]):
                    st.plotly_chart(
                        create_batch_summary_chart(batch_summary_df),
                        width="stretch", key="batch_chart")
                    st.dataframe(batch_summary_df, width="stretch",
                                hide_index=True)
                    st.caption(
                        f"Columnas en común: "
                        f"{', '.join(batch_validation['common_columns'])}")
                    if batch_validation["per_file_missing"]:
                        st.warning("Columnas faltantes por archivo:")
                        for fname, missing in batch_validation[
                            "per_file_missing"].items():
                            st.write(f"**{fname}**: {', '.join(missing)}")

    if step == "columnas":
        st.subheader("Confirmar columnas clave")
        st.caption("Revisa las columnas detectadas y ajústalas si es necesario.")
        render_column_detection_cards(detected)
        st.divider()

    if step in ("resumen", "calidad", "analisis", "insights", "exportar"):
        render_sidebar_context_card(
            source_filename, profile, analysis_type,
            st.session_state.get("quality_score"),
        )

    controls = render_sidebar_column_controls(df, detected) if step == "columnas" else {
        "amount_col": st.session_state.get("amount_column", "Ninguna"),
        "date_col": st.session_state.get("date_column", "Ninguna"),
        "category_col": st.session_state.get("category_column", "Ninguna"),
        "status_col": st.session_state.get("status_column", "Ninguna"),
        "run_analysis": False,
    }
    amount_col = clean_selection(controls["amount_col"])
    date_col = clean_selection(controls["date_col"])
    category_col = clean_selection(controls["category_col"])
    status_col = clean_selection(controls["status_col"])

    if controls["run_analysis"]:
        st.session_state["analysis_has_run"] = True

    warnings = quality_warnings(df, detected)
    warnings_df = warnings_to_frame(warnings)
    quality_score = calculate_quality_score(profile, warnings)
    st.session_state["quality_score"] = quality_score

    if not st.session_state.get("analysis_has_run", False) and step == "columnas":
        st.info("Previsualiza los datos y revisa la calidad. Luego confirma las columnas y presiona **Ejecutar análisis**.")

    analysis_ready = st.session_state.get("analysis_has_run", False)
    kpis: list[dict] = []
    kpis_df = pd.DataFrame()
    anomalies = pd.DataFrame()
    insights: dict = {}
    insights_text = ""

    if analysis_ready:
        with st.spinner("Ejecutando análisis y generando insights..."):
            kpis = calculate_kpis(df, analysis_type, amount_col, date_col, category_col, status_col)
            kpis_df = kpis_to_frame(kpis)
            anomalies = detect_anomalies(df, amount_col, float(threshold))
            insight_context = business_insights.build_insight_context(df)
            insight_context = business_insights.enrich_context_for_app(
                insight_context,
                df,
                analysis_type,
                kpis,
                warnings_df,
                anomalies,
                amount_col,
                date_col,
                category_col,
                status_col,
            )
            insights = business_insights.generate_insights(df, context=insight_context)
            insights_text = business_insights.insights_to_text(insights)

            figures_for_pdf = {}
            if date_col:
                existing_forecast = st.session_state.get("forecast")
                if not existing_forecast:
                    existing_forecast = forecast_trend(df, date_col, amount_col, periods_ahead=3)
                    if existing_forecast:
                        st.session_state["forecast"] = existing_forecast
                if existing_forecast:
                    figures_for_pdf["Tendencia temporal"] = create_forecast_chart(existing_forecast)
                else:
                    figures_for_pdf["Tendencia temporal"] = create_temporal_chart(df, date_col, amount_col)
            if category_col:
                figures_for_pdf["Ranking por categoría"] = create_category_chart(df, category_col, amount_col)
            if status_col:
                figures_for_pdf["Distribución por estado"] = create_status_chart(df, status_col, amount_col)
            if amount_col:
                figures_for_pdf["Distribución de montos"] = create_amount_distribution(df, amount_col)
            if len(df.select_dtypes(include="number").columns) >= 2:
                figures_for_pdf["Matriz de correlación"] = create_correlation_heatmap(df)
            st.session_state["figures_for_pdf"] = figures_for_pdf

    ctx = {
        "analysis_ready": analysis_ready,
        "quality_score": quality_score,
        "warnings": warnings,
        "warnings_df": warnings_df,
        "profile": profile,
        "source_filename": source_filename,
        "df": df,
        "amount_col": amount_col,
        "date_col": date_col,
        "category_col": category_col,
        "status_col": status_col,
        "kpis_df": kpis_df,
        "anomalies": anomalies,
        "insights": insights,
        "insights_text": insights_text,
        "app_title": APP_TITLE,
        "analysis_type": analysis_type,
    }

    if step == "cargar":
        st.success("Archivo listo. Pasa a **Confirmar columnas** en el panel de progreso para continuar.")
    elif step == "resumen":
        render_step_resumen(ctx)
    elif step == "calidad":
        render_step_calidad(ctx)
    elif step == "analisis":
        render_step_analisis(ctx)
    elif step == "insights":
        render_step_insights(ctx)
    elif step == "exportar":
        render_step_exportar(ctx)


if __name__ == "__main__":
    main()
