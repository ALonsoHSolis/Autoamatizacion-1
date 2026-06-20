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
    create_boxplot,
    create_budget_chart,
    create_category_chart,
    create_cluster_profiles_chart,
    create_cluster_scatter,
    create_correlation_heatmap,
    create_elbow_chart,
    create_forecast_chart,
    create_fuzzy_groups_chart,
    create_null_heatmap,
    create_pareto_chart,
    create_rfm_scatter,
    create_rfm_segment_chart,
    create_status_chart,
    create_temporal_chart,
    create_treemap,
    create_waterfall,
)
from src.batch_processor import (validate_compatible_schemas,
                                 consolidate_files, batch_summary)
from src.clustering import auto_cluster
from src.data_loader import get_excel_sheets, load_data, load_google_sheet
from src.fuzzy_match import (find_similar_categories,
                             apply_consolidation,
                             build_mapping_from_groups)
from src.rfm import calculate_rfm, rfm_summary
from src.data_profiler import calculate_quality_score, profile_dataset, quality_warnings, warnings_to_frame
from src.export_utils import export_excel, export_pdf, export_pptx
from src.kpi_engine import (
    calculate_kpis,
    category_ranking,
    compare_vs_budget,
    forecast_kpis,
    forecast_trend,
    kpis_to_frame,
    pareto_analysis,
    period_comparison,
    status_summary,
    temporal_trend,
)


APP_TITLE = "Herramienta de análisis de datos de BA"
APP_SUBTITLE = "Análisis automático de datos para equipos de negocio, conciliaciones, pagos, ventas y operaciones."
PREVIEW_ROWS = 20

st.set_page_config(page_title=APP_TITLE, page_icon=":bar_chart:", layout="wide")

ANALYSIS_TYPES = [
    "Análisis general",
    "Análisis de ventas",
    "Análisis de pagos",
    "Análisis de conciliaciones",
    "Análisis de registros/personas",
    "Análisis financiero simple",
]

GROUPS = {
    "📊 Resumen ejecutivo": ["Resumen"],
    "🔍 Calidad de datos": ["Calidad de datos"],
    "📈 Análisis": [
        "Análisis numérico", "Categorías y estados", "Tabla pivot",
        "Pareto / ABC", "Análisis avanzado", "Clustering", "RFM",
        "Categorías",
    ],
    "💰 Comparaciones": ["vs Presupuesto"],
    "💡 Insights": ["Insights automáticos", "Recomendaciones"],
    "📥 Exportar": ["Descargas"],
}


@st.cache_data(show_spinner=False)
def cached_load(file_bytes: bytes, filename: str, sheet_name: str | None) -> pd.DataFrame:
    """Cache load_data per (file_bytes, filename, sheet_name)."""
    from io import BytesIO

    return load_data(BytesIO(file_bytes), filename, sheet_name)


@st.cache_data(show_spinner=False)
def cached_profile(df: pd.DataFrame):
    """Cache profile_dataset so it only runs when the DataFrame changes."""
    return profile_dataset(df)


def select_default(options: list[str], suggestions: list[str]) -> int:
    for suggestion in suggestions:
        if suggestion in options:
            return options.index(suggestion)
    return 0


def clean_selection(value: str) -> str | None:
    return None if value == "Ninguna" else value


def file_signature(uploaded) -> str:
    return f"{uploaded.name}:{uploaded.size}" if uploaded is not None else ""


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
    </style>
    """, unsafe_allow_html=True)


def render_header() -> None:
    st.title(APP_TITLE)
    st.caption(APP_SUBTITLE)
    file_loaded = st.session_state.get("df") is not None
    analysis_done = st.session_state.get("analysis_has_run", False)
    steps = [
        ("1", "Carga el archivo",    "CSV, XLSX o XLS",
         file_loaded),
        ("2", "Confirma columnas",   "Panel lateral",
         file_loaded),
        ("3", "Ejecuta el análisis", "Botón en sidebar",
         analysis_done),
        ("4", "Lee los resultados",  "Pestañas de abajo",
         analysis_done),
    ]
    cols = st.columns(4)
    for col, (num, title, sub, done) in zip(cols, steps):
        with col:
            icon  = "✅" if done else num
            color = "green" if done else ("orange" if num == "3" and file_loaded else "gray")
            st.markdown(
                f":{color}[**{icon} {title}**]",
                help=sub,
            )
            st.caption(sub)
    st.divider()


def render_empty_state() -> None:
    st.info("Carga un archivo Excel o CSV para comenzar el análisis.")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Formatos soportados")
        st.write("Puedes subir archivos `.csv`, `.xlsx` o `.xls` con encabezados en la primera fila.")
    with col_b:
        st.subheader("Datos de ejemplo")
        st.write("Si quieres probar la herramienta, usa los archivos disponibles en la carpeta `sample_data/`.")
    st.divider()
    st.subheader("Qué obtendrás")
    st.write("- Resumen del dataset y columnas detectadas.")
    st.write("- Revisión de calidad de datos y registros sospechosos.")
    st.write("- KPIs, gráficos, insights ejecutivos y exportaciones.")


def render_sidebar_base() -> dict:
    with st.sidebar:
        st.title("Panel de control")
        st.caption("Configura el archivo y las columnas principales antes de ejecutar el análisis.")

        st.subheader("1. Cargar archivo")
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
                type=["csv","xlsx","xls"],
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

                    validation = validate_compatible_schemas(
                        loaded_dfs, filenames)
                    summary = batch_summary(loaded_dfs, filenames)
                    st.session_state["batch_validation"] = validation
                    st.session_state["batch_summary"] = summary

                    total_rows = sum(len(d) for d in loaded_dfs)
                    st.sidebar.success(
                        f"{len(batch_files)} archivos · "
                        f"{total_rows} filas totales")

                    if not validation["is_compatible"]:
                        st.sidebar.warning(
                            "⚠️ Estructuras muy distintas entre archivos. "
                            "Revisa el detalle antes de continuar.")

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

        st.divider()
        st.subheader("2. Configurar análisis")
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
            "uploaded": uploaded,
            "sheet_name": sheet_name,
            "analysis_type": analysis_type,
            "threshold": threshold,
            "gs_df": gs_df,
            "gs_url": st.session_state.get("gs_url"),
            "batch_df": batch_df,
        }


def render_sidebar_column_controls(df: pd.DataFrame, detected: dict) -> dict:
    with st.sidebar:
        st.divider()
        st.subheader("3. Confirmar columnas")
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


def render_summary_metrics(profile: dict, warnings_df: pd.DataFrame) -> None:
    missing_warnings = 0 if warnings_df.empty else int(warnings_df["issue"].astype(str).str.contains("nulos|vacía|faltantes", case=False, regex=True).sum())
    metrics = [
        ("Total de filas", profile["rows"], "Registros cargados"),
        ("Total de columnas", profile["columns"], "Campos disponibles"),
        ("Columnas numéricas", len(profile["numeric_columns"]), "Valores analizables"),
        ("Columnas de texto", len(profile["categorical_columns"]), "Segmentos o categorías"),
        ("Valores nulos", f"{profile['missing_percent']}%", f"{missing_warnings} advertencias"),
        ("Duplicados", profile["duplicates"], "Filas repetidas"),
    ]
    for start in range(0, len(metrics), 3):
        cols = st.columns(3)
        for col, (label, value, help_text) in zip(cols, metrics[start : start + 3]):
            col.metric(label, value, help=help_text)


def render_business_kpis(kpis_df: pd.DataFrame) -> None:
    if kpis_df.empty:
        st.info("No hay KPIs disponibles con la configuración actual.")
        return
    for chunk_start in range(0, len(kpis_df), 4):
        cols = st.columns(4)
        for col, (_, row) in zip(cols, kpis_df.iloc[chunk_start : chunk_start + 4].iterrows()):
            col.metric(str(row["kpi"]), str(row["valor"]))
            col.caption(str(row["interpretacion"]))


def render_quality_overview(warnings_df: pd.DataFrame) -> None:
    if warnings_df.empty:
        st.success("No se detectaron advertencias relevantes con las reglas automáticas.")
        return

    severity_order = {"Alta": 0, "Media": 1, "Baja": 2}
    display = warnings_df.assign(_order=warnings_df["severity"].map(severity_order)).sort_values("_order").drop(columns="_order")
    high = int((display["severity"] == "Alta").sum())
    medium = int((display["severity"] == "Media").sum())
    low = int((display["severity"] == "Baja").sum())

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Alta", high)
    col_b.metric("Media", medium)
    col_c.metric("Baja", low)

    if high:
        st.warning("Hay advertencias de severidad alta. Revisa estos datos antes de tomar decisiones.")
    elif medium:
        st.info("Hay advertencias medias que conviene revisar antes de presentar resultados finales.")
    else:
        st.success("Solo se detectaron advertencias de baja severidad.")
    display_df = display.copy()
    display_df["severity"] = display_df["severity"].map({
        "Alta": "🔴 Alta",
        "Media": "🟡 Media",
        "Baja": "🟢 Baja",
    })
    st.dataframe(display_df, width="stretch", hide_index=True)


def render_detected_columns(profile: dict) -> None:
    detected = {key: value for key, value in profile["detected"].items() if value}
    if not detected:
        st.info("No se detectaron columnas especiales automáticamente.")
        return
    rows = [{"tipo": key, "columnas": ", ".join(value)} for key, value in detected.items()]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def render_preview(source_filename: str, df: pd.DataFrame, profile: dict) -> None:
    st.subheader("Archivo cargado")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Nombre", source_filename)
    col_b.metric("Filas", profile["rows"])
    col_c.metric("Columnas", profile["columns"])

    if profile["columns"] > 40:
        st.warning("El archivo tiene muchas columnas. Revisa las columnas detectadas antes de ejecutar el análisis.")
    if profile["missing_percent"] >= 30:
        st.warning("Se detecta un porcentaje alto de datos faltantes.")

    st.subheader("Primeras filas")
    st.caption(f"Se muestran las primeras {min(PREVIEW_ROWS, len(df))} filas para mantener la lectura simple.")
    st.dataframe(df.head(PREVIEW_ROWS), width="stretch")

    with st.expander("Columnas detectadas y tipos de datos", expanded=False):
        render_detected_columns(profile)
        st.dataframe(profile["dtypes"], width="stretch", hide_index=True)


def build_default_recommendations(profile: dict, warnings_df: pd.DataFrame, anomalies: pd.DataFrame, amount_col: str | None, category_col: str | None, date_col: str | None) -> list[str]:
    recommendations: list[str] = []
    if profile["duplicates"]:
        recommendations.append("Revisar registros duplicados antes de tomar decisiones.")
    if not warnings_df.empty:
        recommendations.append("Priorizar columnas con advertencias de calidad de severidad alta o media.")
    if not anomalies.empty:
        recommendations.append("Investigar valores atípicos en montos o fechas antes de cerrar conclusiones.")
    if amount_col:
        recommendations.append("Validar que la columna de monto seleccionada represente la métrica principal del negocio.")
    if category_col:
        recommendations.append("Separar el análisis por categoría para identificar concentración o segmentos críticos.")
    if date_col:
        recommendations.append("Comparar la tendencia contra periodos anteriores o eventos relevantes del negocio.")
    if not recommendations:
        recommendations.append("Documentar supuestos del análisis y validar resultados con el equipo dueño del dato.")
    return recommendations


def render_insights(insights: dict, kpis_df: pd.DataFrame, profile: dict, anomalies: pd.DataFrame) -> None:
    st.subheader("Resumen ejecutivo")
    st.info(str(insights.get("resumen_ejecutivo", "No hay resumen disponible.")))

    findings = insights.get("hallazgos", [])
    actions = insights.get("acciones_recomendadas", [])
    risks = insights.get("riesgos", [])

    if isinstance(findings, str):
        findings = [findings]
    if isinstance(actions, str):
        actions = [actions]
    if isinstance(risks, str):
        risks = [risks]

    if not findings:
        st.info("No se generaron hallazgos automáticos con la configuración actual.")
        return

    evidence = "KPIs calculados, revisión de calidad y registros analizados."
    if not kpis_df.empty:
        first_kpi = kpis_df.iloc[0]
        evidence = f"{first_kpi['kpi']}: {first_kpi['valor']}."
    if not anomalies.empty:
        evidence += f" Además, se detectaron {len(anomalies)} registros sospechosos."

    for idx, finding in enumerate(findings[:6], start=1):
        with st.expander(f"Insight {idx}: {str(finding)[:80]}", expanded=idx == 1):
            st.write("**Hallazgo principal**")
            st.write(finding)
            st.write("**Evidencia**")
            st.write(evidence)
            st.write("**Interpretación de negocio**")
            st.write("Este punto ayuda a priorizar revisión, seguimiento o segmentación antes de presentar conclusiones finales.")
            st.write("**Acción recomendada**")
            if actions:
                st.write(actions[min(idx - 1, len(actions) - 1)])
            elif risks:
                st.write(risks[min(idx - 1, len(risks) - 1)])
            else:
                st.write("Validar el hallazgo con el equipo dueño del proceso.")


def render_recommendations(insights: dict, default_recommendations: list[str]) -> None:
    st.subheader("Recomendaciones iniciales")
    actions = insights.get("acciones_recomendadas", [])
    risks = insights.get("riesgos", [])
    questions = insights.get("preguntas_negocio", [])

    if isinstance(actions, str):
        actions = [actions]
    if isinstance(risks, str):
        risks = [risks]
    if isinstance(questions, str):
        questions = [questions]

    for recommendation in list(actions) + default_recommendations:
        st.write(f"- {recommendation}")

    with st.expander("Riesgos y preguntas para profundizar", expanded=False):
        if risks:
            st.write("**Riesgos detectados**")
            for risk in risks:
                st.write(f"- {risk}")
        if questions:
            st.write("**Preguntas sugeridas**")
            for question in questions:
                st.write(f"- {question}")


def main() -> None:
    inject_custom_css()
    render_header()

    initial_controls = render_sidebar_base()
    uploaded = initial_controls["uploaded"]
    sheet_name = initial_controls["sheet_name"]
    analysis_type = initial_controls["analysis_type"]
    threshold = initial_controls["threshold"]
    gs_df = initial_controls["gs_df"]
    gs_url = initial_controls["gs_url"]
    batch_df = initial_controls["batch_df"]

    if gs_df is not None:
        signature = f"gsheet:{gs_url}"
        if st.session_state.get("active_file_signature") != signature:
            st.session_state["active_file_signature"] = signature
            st.session_state["analysis_has_run"] = False
            for key in ["date_column", "amount_column", "category_column", "status_column"]:
                st.session_state.pop(key, None)
        df = gs_df
    elif batch_df is not None:
        batch_summary_df = st.session_state.get("batch_summary")
        filenames = batch_summary_df["archivo"].tolist() if batch_summary_df is not None else []
        signature = "batch:" + ",".join(filenames)
        if st.session_state.get("active_file_signature") != signature:
            st.session_state["active_file_signature"] = signature
            st.session_state["analysis_has_run"] = False
            for key in ["date_column", "amount_column", "category_column", "status_column"]:
                st.session_state.pop(key, None)
        df = batch_df
    elif uploaded is not None:
        signature = file_signature(uploaded)
        if st.session_state.get("active_file_signature") != signature:
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
    else:
        render_empty_state()
        return

    data_source = st.session_state.get("data_source")
    batch_files = st.session_state.get("batch_uploader")
    source_filename = (
        uploaded.name if uploaded is not None
        else "Google Sheets" if data_source == "Google Sheets URL"
        else (
            "Batch: " + ", ".join(f.name for f in batch_files)
            if data_source == "Múltiples archivos (batch)" and batch_files
            else "archivo_desconocido"
        )
    )

    profile = cached_profile(df)
    detected = profile["detected"]
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

    controls = render_sidebar_column_controls(df, detected)
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

    if not st.session_state.get("analysis_has_run", False):
        st.info("Previsualiza los datos y revisa la calidad. Luego confirma las columnas en el panel lateral y presiona **Ejecutar análisis**.")

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

    st.sidebar.markdown("### 📋 Navegación")
    nav_category = st.sidebar.selectbox(
        "Categoría", list(GROUPS.keys()), key="nav_category")
    nav_selection = st.sidebar.radio(
        "Sección", GROUPS[nav_category], key="nav_section")

    if nav_selection == "Resumen":
        if analysis_ready:
            st.markdown("#### 🎯 Qué revisar primero")

            # Quality score card
            qc1, qc2, qc3 = st.columns(3)
            if quality_score:
                score = quality_score.get("score", 0)
                label = quality_score.get("label", "")
                color = ("🟢" if score >= 80 else
                         "🟡" if score >= 55 else "🔴")
                qc1.metric("Calidad de datos", f"{score}/100",
                           delta=f"{color} {label}")

            # Top alert: highest severity warning
            if warnings:
                high_warnings = [w for w in warnings
                                 if w.severity == "Alta"]
                top_warning = (high_warnings[0] if high_warnings
                               else warnings[0])
                qc2.metric("Alerta principal", top_warning.issue,
                           help=top_warning.detail)
            else:
                qc2.metric("Alerta principal", "Sin alertas")

            # Auto recommendation based on quality score
            if quality_score and quality_score.get("score", 100) < 70:
                recommendation = (
                    "Revisar y corregir datos antes de presentar "
                    "resultados a stakeholders."
                )
            elif warnings and any(w.severity == "Alta" for w in warnings):
                recommendation = (
                    "Resolver advertencias de severidad alta primero."
                )
            else:
                recommendation = (
                    "Datos listos para análisis y presentación."
                )
            qc3.metric("Recomendación", "Ver detalle",
                       help=recommendation)

            st.caption(f"💬 {recommendation}")
            st.divider()

        st.subheader("Resumen del dataset")
        st.caption("Vista general para confirmar que el archivo se cargó como esperabas.")
        render_summary_metrics(profile, warnings_df)
        st.divider()
        render_preview(source_filename, df, profile)

    if nav_selection == "Calidad de datos":
        st.subheader("Revisión de calidad")
        st.caption("Antes de tomar decisiones, revisa nulos, duplicados, formatos inválidos y valores sospechosos.")
        st.metric(
            label="Calidad del dataset",
            value=f"{quality_score['score']}/100",
            delta=quality_score['label'],
            delta_color=quality_score['color'],
        )
        render_quality_overview(warnings_df)
        with st.expander("Mapa simple de datos faltantes", expanded=False):
            st.plotly_chart(create_null_heatmap(df), width="stretch", key="null_heatmap_chart")

    if nav_selection == "Análisis numérico":
        st.subheader("KPIs y análisis numérico")
        if not analysis_ready:
            st.info("Ejecuta el análisis para ver tus KPIs principales, cómo evolucionan en el tiempo y qué valores se salen de lo normal.")
        else:
            render_business_kpis(kpis_df)
            st.divider()
            if date_col:
                st.subheader("Tendencia temporal")
                st.plotly_chart(create_temporal_chart(df, date_col, amount_col), width="stretch", key="temporal_chart")
                st.dataframe(temporal_trend(df, date_col, amount_col), width="stretch", hide_index=True)
            else:
                st.info("Selecciona una columna de fecha para ver tendencia temporal.")

            st.subheader("Distribución y anomalías")
            if amount_col:
                left, right = st.columns(2)
                left.plotly_chart(create_amount_distribution(df, amount_col), width="stretch", key="amount_distribution_chart")
                right.plotly_chart(create_boxplot(df, amount_col), width="stretch", key="amount_boxplot_chart")
            if anomalies.empty:
                st.success("No se detectaron anomalías con el umbral seleccionado.")
            else:
                st.warning(f"Se detectaron {len(anomalies)} registros sospechosos.")
                st.dataframe(anomalies, width="stretch")

    if nav_selection == "Categorías y estados":
        st.subheader("Análisis por categorías y estados")
        if not analysis_ready:
            st.info("Ejecuta el análisis para ver qué categorías y estados concentran más volumen y cómo se reparte el total entre ellos.")
        else:
            if category_col:
                st.subheader("Ranking por categoría")
                st.plotly_chart(create_category_chart(df, category_col, amount_col), width="stretch", key="category_chart")
                st.dataframe(category_ranking(df, category_col, amount_col), width="stretch", hide_index=True)
            else:
                st.info("Selecciona una columna de categoría para ver ranking.")

            if status_col:
                st.subheader("Distribución por estado")
                st.plotly_chart(create_status_chart(df, status_col, amount_col), width="stretch", key="status_chart")
                st.dataframe(status_summary(df, status_col, amount_col), width="stretch", hide_index=True)
            else:
                st.info("Selecciona una columna de estado para ver distribución.")

    if nav_selection == "Tabla pivot":
        st.subheader("Tabla pivot dinámica")
        st.caption(
            "Cruza dos dimensiones y agrega un valor numérico. "
            "Ideal para comparar categorías por período o estado."
        )
        if not analysis_ready:
            st.info("Ejecuta el análisis para cruzar tus datos como una tabla dinámica de Excel, sin fórmulas.")
        else:
            cat_cols = [c for c in df.columns if df[c].dtype == "object"]
            num_cols = [c for c in df.columns
                        if pd.api.types.is_numeric_dtype(df[c])]
            if len(cat_cols) < 2 or len(num_cols) < 1:
                st.info("Se necesitan al menos 2 columnas categóricas "
                        "y 1 numérica para la tabla pivot.")
            else:
                pc1, pc2, pc3 = st.columns(3)
                pivot_row = pc1.selectbox(
                    "Filas", cat_cols, key="pivot_row")
                pivot_col = pc2.selectbox(
                    "Columnas",
                    [c for c in cat_cols if c != pivot_row],
                    key="pivot_col")
                pivot_val = pc3.selectbox(
                    "Valor", num_cols, key="pivot_val")
                agg = st.radio(
                    "Agregación",
                    ["sum", "mean", "count"],
                    horizontal=True,
                    key="pivot_agg")
                try:
                    pivot_df = pd.pivot_table(
                        df,
                        values=pivot_val,
                        index=pivot_row,
                        columns=pivot_col,
                        aggfunc=agg,
                        fill_value=0,
                    ).round(2)
                    st.dataframe(
                        pivot_df,
                        width="stretch",
                        key="pivot_table")
                    buf = pivot_df.to_csv().encode("utf-8")
                    st.download_button(
                        "Descargar pivot CSV",
                        buf,
                        file_name="pivot.csv",
                        mime="text/csv",
                        key="pivot_download")
                except Exception as e:
                    st.warning(f"No se pudo generar el pivot: {e}")

    if nav_selection == "vs Presupuesto":
        st.subheader("Comparación Real vs Presupuesto")
        st.caption(
            "Sube un archivo de presupuesto con las mismas categorías "
            "que el dataset principal. La app compara montos reales vs esperados."
        )
        if not analysis_ready:
            st.info("Ejecuta primero el análisis del archivo principal.")
        else:
            budget_file = st.file_uploader(
                "Archivo de presupuesto (CSV o Excel)",
                type=["csv","xlsx","xls"],
                key="budget_uploader",
            )
            if budget_file:
                try:
                    df_budget = load_data(budget_file, budget_file.name)
                    st.success(f"Presupuesto cargado: {len(df_budget)} filas · "
                               f"{len(df_budget.columns)} columnas")

                    b1, b2, b3 = st.columns(3)
                    budget_group = b1.selectbox(
                        "Columna de agrupación (presupuesto)",
                        df_budget.columns.tolist(), key="bg_group")
                    budget_amount = b2.selectbox(
                        "Columna de monto (presupuesto)",
                        df_budget.columns.tolist(), key="bg_amount")
                    actual_group = b3.selectbox(
                        "Columna de agrupación (real)",
                        df.columns.tolist(),
                        index=df.columns.tolist().index(category_col)
                        if category_col in df.columns else 0,
                        key="bg_actual_group")

                    if st.button("Comparar", key="btn_compare"):
                        comparison = compare_vs_budget(
                            df, df_budget,
                            group_col=actual_group,
                            actual_amount_col=amount_col or df.select_dtypes(
                                include="number").columns[0],
                            budget_amount_col=budget_amount,
                        )
                        if not comparison.empty:
                            total_real  = comparison["real"].sum()
                            total_ppto  = comparison["presupuesto"].sum()
                            varianza    = total_real - total_ppto
                            cumplimiento = total_real/total_ppto*100 if total_ppto else 0

                            m1,m2,m3,m4 = st.columns(4)
                            m1.metric("Total real",       f"${total_real:,.0f}")
                            m2.metric("Total presupuesto",f"${total_ppto:,.0f}")
                            m3.metric("Varianza",
                                      f"${varianza:,.0f}",
                                      delta=f"{varianza/total_ppto*100:+.1f}%"
                                      if total_ppto else None)
                            m4.metric("Cumplimiento",     f"{cumplimiento:.1f}%")

                            st.plotly_chart(create_budget_chart(comparison),
                                            width="stretch", key="budget_chart")
                            st.dataframe(comparison, width="stretch",
                                         hide_index=True)
                        else:
                            st.warning("No se encontraron categorías comunes "
                                       "entre los dos archivos.")
                except Exception as e:
                    st.error(f"Error al cargar el presupuesto: {e}")
            else:
                st.info("Sube el archivo de presupuesto para comenzar.")

    if nav_selection == "Pareto / ABC":
        st.subheader("Análisis de Pareto / ABC")
        st.caption(
            "Identifica automáticamente qué categorías concentran el 80 % (segmento A), "
            "el 15 % (B) y el 5 % (C) del valor. Útil para priorizar revisión y recursos."
        )
        if not analysis_ready:
            st.info("Sube y analiza tus datos para descubrir qué categorías concentran el 80% del valor.")
        elif not category_col:
            st.info("Selecciona una columna de categoría para ver el análisis de Pareto.")
        else:
            st.plotly_chart(
                create_pareto_chart(df, category_col, amount_col),
                width='stretch',
                key="pareto_chart",
            )
            pareto_df = pareto_analysis(df, category_col, amount_col)
            if not pareto_df.empty:
                seg_a = pareto_df[pareto_df["segmento"] == "A"]
                seg_b = pareto_df[pareto_df["segmento"] == "B"]
                seg_c = pareto_df[pareto_df["segmento"] == "C"]
                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Segmento A - vital", len(seg_a), help="Concentran el 80 % del valor")
                col_b.metric("Segmento B - importante", len(seg_b), help="Llevan el acumulado al 95 %")
                col_c.metric("Segmento C - trivial", len(seg_c), help="El restante 5 %")
                with st.expander("Ver tabla Pareto completa", expanded=False):
                    st.dataframe(pareto_df, width='stretch', hide_index=True)

    if nav_selection == "Análisis avanzado":
        st.subheader("Análisis avanzado")
        if not analysis_ready:
            st.info("Ejecuta el análisis para desbloquear correlaciones, proyecciones y gráficos de composición.")
        else:
            if date_col:
                st.subheader("Comparación de períodos")
                comp_col1, comp_col2 = st.columns(2)

                with comp_col1:
                    mom = period_comparison(df, date_col, amount_col, periods=1)
                    if mom:
                        delta_str = f"{mom['percent_change']:+.1f} %" if mom["percent_change"] is not None else "N/A"
                        st.metric(
                            label=f"Último período ({mom['current_period']})",
                            value=f"${mom['current_value']:,.0f}",
                            delta=delta_str,
                            help=f"vs período anterior {mom['previous_period']}: ${mom['previous_value']:,.0f}",
                        )

                with comp_col2:
                    yoy = period_comparison(df, date_col, amount_col, periods=12)
                    if yoy:
                        delta_str = f"{yoy['percent_change']:+.1f} %" if yoy["percent_change"] is not None else "N/A"
                        st.metric(
                            label=f"Variación anual ({yoy['current_period']} vs {yoy['previous_period']})",
                            value=f"${yoy['current_value']:,.0f}",
                            delta=delta_str,
                        )
                st.divider()

            if date_col:
                st.subheader("Proyección de tendencia")
                st.caption(
                    "Regresión lineal sobre los períodos históricos. "
                    "La banda sombreada representa el intervalo de confianza del 95%."
                )
                periods_ahead = st.slider(
                    "Períodos a proyectar",
                    min_value=1, max_value=12, value=3,
                    key="forecast_periods",
                )
                forecast = forecast_trend(
                    df, date_col, amount_col, periods_ahead=periods_ahead
                )
                if forecast:
                    st.session_state["forecast"] = forecast
                    f_kpis = forecast_kpis(forecast)
                    if f_kpis:
                        k_cols = st.columns(min(len(f_kpis), 3))
                        for i, kpi in enumerate(f_kpis[:3]):
                            k_cols[i].metric(
                                label=kpi["kpi"],
                                value=kpi["valor"],
                                help=kpi["interpretacion"],
                            )
                    st.plotly_chart(
                        create_forecast_chart(forecast),
                        width="stretch",
                        key="forecast_chart",
                    )
                    if len(f_kpis) > 3:
                        with st.expander("Ver todas las proyecciones", expanded=False):
                            proj_df = pd.DataFrame(forecast["projected"])
                            proj_df.columns = ["Período","Valor proyectado",
                                               "Límite inferior","Límite superior"]
                            st.dataframe(proj_df, width="stretch", hide_index=True)
                else:
                    st.info("Se necesitan al menos 3 períodos históricos para proyectar.")
                st.divider()

            st.subheader("Matriz de correlación")
            st.caption(
                "Detecta relaciones lineales entre columnas numéricas. "
                "Valores cercanos a 1 o -1 indican correlación fuerte."
            )
            st.plotly_chart(
                create_correlation_heatmap(df),
                width='stretch',
                key="correlation_heatmap",
            )
            st.divider()

            if category_col and amount_col:
                st.subheader("Waterfall por categoría")
                st.caption(
                    "Visualiza cómo cada categoría contribuye al total. "
                    "Ideal para análisis financiero y de ventas."
                )
                st.plotly_chart(
                    create_waterfall(df, category_col, amount_col),
                    width='stretch',
                    key="waterfall_chart",
                )
                st.divider()

            if category_col:
                st.subheader("Treemap de distribución")
                object_cols = [c for c in df.columns if c != category_col and df[c].dtype == "object"]
                sub_cat_choice = st.selectbox(
                    "Segunda dimensión (opcional)",
                    ["Ninguna"] + object_cols,
                    key="treemap_subcat",
                )
                sub_cat_col = None if sub_cat_choice == "Ninguna" else sub_cat_choice
                st.plotly_chart(
                    create_treemap(df, category_col, amount_col, sub_cat_col),
                    width='stretch',
                    key="treemap_chart",
                )

    if nav_selection == "Clustering":
        st.subheader("Clustering automático de segmentos")
        st.caption(
            "Agrupa automáticamente los registros en segmentos "
            "similares usando K-means. No requiere columna de "
            "categoría — detecta patrones ocultos en los datos."
        )
        if not analysis_ready:
            st.info("Ejecuta el análisis para descubrir grupos ocultos en tus datos, sin necesidad de definir categorías manualmente.")
        else:
            num_cols = [c for c in df.columns
                        if pd.api.types.is_numeric_dtype(df[c])]
            if len(num_cols) < 2:
                st.warning("Se necesitan al menos 2 columnas "
                           "numéricas para clustering.")
            else:
                c1, c2 = st.columns(2)
                k_mode = c1.radio(
                    "Número de clusters",
                    ["Automático (método del codo)", "Manual"],
                    key="k_mode", horizontal=True)
                k_manual = c2.slider(
                    "K manual", 2, 8, 3,
                    key="k_manual",
                    disabled=(k_mode == "Automático (método del codo)"))

                selected_cols = st.multiselect(
                    "Columnas para clustering",
                    num_cols, default=num_cols[:min(4, len(num_cols))],
                    key="cluster_cols")

                if st.button("Ejecutar clustering", key="btn_cluster"):
                    with st.spinner("Calculando segmentos..."):
                        n = ("auto" if "Automático" in k_mode
                             else k_manual)
                        result = auto_cluster(
                            df, n_clusters=n,
                            cols=selected_cols or None)

                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.session_state["cluster_result"] = result

                result = st.session_state.get("cluster_result")
                if result and "error" not in result:
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Segmentos detectados",
                              result["n_clusters"])
                    m2.metric("Silhouette score",
                              result["silhouette"] or "N/A",
                              help="Cercano a 1 = clusters bien separados")
                    m3.metric("Registros analizados",
                              len(result["labels"]))

                    st.plotly_chart(
                        create_elbow_chart(
                            result["k_range"], result["inertias"]),
                        width="stretch", key="elbow_chart")

                    num_cols_result = result["numeric_cols"]
                    if len(num_cols_result) >= 2:
                        st.subheader("Dispersión por segmento")
                        ea, eb = st.columns(2)
                        ax = ea.selectbox(
                            "Eje X", num_cols_result,
                            key="cl_x")
                        ay = eb.selectbox(
                            "Eje Y", num_cols_result,
                            index=min(1, len(num_cols_result)-1),
                            key="cl_y")
                        df_labeled = result["df_with_labels"]
                        st.plotly_chart(
                            create_cluster_scatter(
                                df_labeled, ax, ay),
                            width="stretch", key="cluster_scatter")

                    st.subheader("Perfil de cada segmento")
                    st.plotly_chart(
                        create_cluster_profiles_chart(
                            result["profiles"]),
                        width="stretch", key="cluster_profiles")

                    with st.expander("Ver tabla de perfiles",
                                     expanded=False):
                        st.dataframe(result["profiles"],
                                     width="stretch",
                                     hide_index=True)

    if nav_selection == "RFM":
        st.subheader("Segmentación RFM")
        st.caption(
            "Clasifica clientes según Recencia, Frecuencia y Monto. "
            "Requiere un archivo con una fila por transacción y una "
            "columna que identifique al cliente."
        )
        if not analysis_ready:
            st.info("Ejecuta el análisis para clasificar a tus clientes según qué tan recientes, frecuentes y valiosos son.")
        else:
            obj_cols = [c for c in df.columns if df[c].dtype == "object"]
            date_cols_all = [c for c in df.columns]

            rc1, rc2, rc3 = st.columns(3)
            rfm_id_col = rc1.selectbox(
                "Columna de cliente", df.columns.tolist(),
                key="rfm_id")
            rfm_date_col = rc2.selectbox(
                "Columna de fecha", date_cols_all,
                index=date_cols_all.index(date_col)
                if date_col in date_cols_all else 0,
                key="rfm_date")
            rfm_amount_col = rc3.selectbox(
                "Columna de monto", date_cols_all,
                index=date_cols_all.index(amount_col)
                if amount_col in date_cols_all else 0,
                key="rfm_amount")

            if st.button("Calcular RFM", key="btn_rfm"):
                rfm_df = calculate_rfm(
                    df, rfm_id_col, rfm_date_col, rfm_amount_col)
                if rfm_df.empty:
                    st.warning("No se pudo calcular RFM. Verifica que "
                              "el archivo tenga múltiples transacciones "
                              "por cliente.")
                else:
                    st.session_state["rfm_result"] = rfm_df

            rfm_result = st.session_state.get("rfm_result")
            if rfm_result is not None and not rfm_result.empty:
                summary = rfm_summary(rfm_result)
                m1, m2, m3 = st.columns(3)
                m1.metric("Clientes analizados", len(rfm_result))
                m2.metric("Segmentos detectados",
                          rfm_result["segmento"].nunique())
                top_seg = summary.iloc[0]["segmento"] if not summary.empty else "—"
                m3.metric("Segmento de mayor valor", top_seg)

                st.plotly_chart(
                    create_rfm_segment_chart(summary),
                    width="stretch", key="rfm_segment_chart")
                st.plotly_chart(
                    create_rfm_scatter(rfm_result),
                    width="stretch", key="rfm_scatter")

                with st.expander("Ver tabla completa de clientes",
                                 expanded=False):
                    st.dataframe(rfm_result, width="stretch",
                                 hide_index=True)
                with st.expander("Ver resumen por segmento",
                                 expanded=False):
                    st.dataframe(summary, width="stretch",
                                 hide_index=True)
                with st.expander("Ver criterios de clasificación", expanded=False):
                    st.markdown("""
**Cada cliente recibe 3 puntajes del 1 al 5** (por quintiles,
comparado contra el resto de los clientes):

| Puntaje | Qué mide |
|---|---|
| **R — Recencia** | Qué tan reciente fue su última compra. 5 = compró hace poco, 1 = hace mucho tiempo |
| **F — Frecuencia** | Cuántas veces compró en total. 5 = compra muy seguido, 1 = casi nunca |
| **M — Monto** | Cuánto ha gastado en total. 5 = alto gasto, 1 = bajo gasto |

**La combinación de los 3 puntajes define el segmento:**

| Segmento | Condición | Significado |
|---|---|---|
| 🏆 Champions | R≥4, F≥4, M≥4 | Compran seguido, recientemente y gastan mucho |
| 💚 Clientes leales | R≥3, F≥3, M≥3 | Buen comportamiento general |
| ⚠️ En riesgo | R≤2, F≥3, M≥3 | Antes compraban bien, hace tiempo no vuelven |
| 🆕 Nuevos | R≥4, F≤2 | Compraron hace poco, pocas veces |
| 💤 Perdidos | R≤2, F≤2, M≤2 | Hace mucho que no compran, bajo gasto |
| 🔹 Regulares | Otra combinación | No encaja claramente en las anteriores |
    """)

    if nav_selection == "Categorías":
        st.subheader("Limpieza de categorías duplicadas")
        st.caption(
            "Detecta variantes de texto que probablemente representan "
            "la misma categoría — mayúsculas, espacios extra, acentos "
            "faltantes o errores de tipeo — y sugiere unificarlas."
        )
        if not analysis_ready:
            st.info("Ejecuta el análisis para detectar y unificar categorías duplicadas por errores de tipeo o formato.")
        else:
            text_cols = [
                c for c in df.columns
                if not pd.api.types.is_numeric_dtype(df[c])
                and not pd.api.types.is_datetime64_any_dtype(df[c])
            ]
            if not text_cols:
                text_cols = df.columns.tolist()
            if not text_cols:
                st.info("No se encontraron columnas de texto para analizar.")
            else:
                cc1, cc2 = st.columns(2)
                cleanup_col = cc1.selectbox(
                    "Columna a revisar", text_cols,
                    index=text_cols.index(category_col)
                    if category_col in text_cols else 0,
                    key="cleanup_col")
                threshold = cc2.slider(
                    "Sensibilidad de similitud", 0.70, 1.00, 0.85,
                    step=0.01, key="cleanup_threshold",
                    help="Más alto = más estricto, solo detecta "
                         "variantes muy parecidas entre sí")

                if st.button("Detectar duplicados", key="btn_detect_fuzzy"):
                    groups = find_similar_categories(
                        df[cleanup_col], threshold=threshold)
                    st.session_state["fuzzy_groups"] = groups
                    st.session_state["fuzzy_col"] = cleanup_col

                groups = st.session_state.get("fuzzy_groups")
                stored_col = st.session_state.get("fuzzy_col")

                if groups is not None and stored_col == cleanup_col:
                    if groups.empty:
                        st.success(
                            "No se detectaron categorías duplicadas con "
                            "este nivel de sensibilidad.")
                    else:
                        n_groups = groups["grupo"].nunique()
                        n_variants = len(groups)
                        before_unique = df[cleanup_col].nunique()
                        st.warning(
                            f"Se detectaron **{n_groups} grupos** de "
                            f"categorías similares ({n_variants} "
                            f"variantes de {before_unique} valores "
                            "únicos totales).")

                        st.plotly_chart(
                            create_fuzzy_groups_chart(groups),
                            width="stretch", key="fuzzy_chart")

                        with st.expander(
                            "Ver tabla de grupos detectados",
                            expanded=True):
                            display_df = groups.copy()
                            display_df["es_canonico"] = display_df["es_canonico"].map({
                                True: "✅ Sugerido como canónico",
                                False: "🔁 Variante a reemplazar",
                            })
                            st.dataframe(display_df, width="stretch",
                                        hide_index=True)

                        if st.button("Aplicar consolidación",
                                     key="btn_apply_fuzzy"):
                            mapping = build_mapping_from_groups(groups)
                            cleaned_df = apply_consolidation(
                                df, cleanup_col, mapping)
                            after_unique = cleaned_df[cleanup_col].nunique()
                            st.session_state["cleaned_df"] = cleaned_df
                            st.success(
                                f"Consolidación aplicada: de "
                                f"**{before_unique}** a **{after_unique}** "
                                "valores únicos.")

                        cleaned_df = st.session_state.get("cleaned_df")
                        if cleaned_df is not None:
                            st.divider()
                            st.subheader(
                                "Comparación antes vs después")
                            comp_a, comp_b = st.columns(2)
                            with comp_a:
                                st.caption("Antes (top 10)")
                                st.dataframe(
                                    df[cleanup_col].value_counts()
                                    .head(10).rename("frecuencia"),
                                    width="stretch")
                            with comp_b:
                                st.caption("Después (top 10)")
                                st.dataframe(
                                    cleaned_df[cleanup_col].value_counts()
                                    .head(10).rename("frecuencia"),
                                    width="stretch")

                            csv_bytes = cleaned_df.to_csv(
                                index=False).encode("utf-8-sig")
                            st.download_button(
                                "Descargar dataset con categorías "
                                "unificadas",
                                csv_bytes,
                                file_name="dataset_categorias_limpias.csv",
                                mime="text/csv",
                                key="download_cleaned")

    if nav_selection == "Insights automáticos":
        st.subheader("Insights automáticos")
        if not analysis_ready:
            st.info("Ejecuta el análisis para generar un resumen ejecutivo con hallazgos y conclusiones listas para compartir.")
        else:
            render_insights(insights, kpis_df, profile, anomalies)
            with st.expander("Ver texto completo de insights", expanded=False):
                st.text_area("Resumen generado", insights_text, height=360, key="executive_insights_text")

    if nav_selection == "Recomendaciones":
        if not analysis_ready:
            st.info("Ejecuta el análisis para recibir sugerencias concretas sobre qué revisar o priorizar a continuación.")
        else:
            default_recommendations = build_default_recommendations(profile, warnings_df, anomalies, amount_col, category_col, date_col)
            render_recommendations(insights, default_recommendations)

    if nav_selection == "Descargas":
        st.subheader("Descargar resultados")
        if not analysis_ready:
            st.info("Ejecuta el análisis para descargar tus resultados en Excel, PDF o PowerPoint, listos para compartir.")
        else:
            export_sheets = {
                "Resumen": pd.DataFrame(
                    [
                        {
                            "archivo": source_filename,
                            "tipo_analisis": analysis_type,
                            "filas": profile["rows"],
                            "columnas": profile["columns"],
                            "faltantes_pct": profile["missing_percent"],
                            "duplicados": profile["duplicates"],
                        }
                    ]
                ),
                "KPIs": kpis_df,
                "Calidad de datos": warnings_df,
                "Anomalías": anomalies,
                "Ranking categoría": category_ranking(df, category_col, amount_col) if category_col else pd.DataFrame(),
                "Estados": status_summary(df, status_col, amount_col) if status_col else pd.DataFrame(),
                "Tendencia temporal": temporal_trend(df, date_col, amount_col) if date_col else pd.DataFrame(),
            }
            excel_bytes = export_excel(export_sheets, insights_text)
            pdf_figures = st.session_state.get("figures_for_pdf", {}).copy()
            saved_forecast = st.session_state.get("forecast")
            if saved_forecast:
                pdf_figures["Tendencia temporal"] = create_forecast_chart(
                    saved_forecast
                )
            pdf_bytes = export_pdf(
                APP_TITLE, profile, kpis_df, insights,
                figures=pdf_figures)
            col_a, col_b = st.columns(2)
            col_a.download_button(
                "Descargar Excel",
                excel_bytes,
                file_name="ba_data_insight_resultados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
                key="download_excel",
            )
            col_b.download_button(
                "Descargar PDF ejecutivo",
                pdf_bytes,
                file_name="ba_data_insight_resumen.pdf",
                mime="application/pdf",
                width="stretch",
                key="download_pdf",
            )

            st.divider()
            st.subheader("PowerPoint ejecutivo")
            st.caption("Presentación lista para compartir con stakeholders. "
                       "Incluye portada, KPIs, gráficos y insights.")
            if st.button("Generar PowerPoint", key="btn_pptx"):
                with st.spinner("Generando presentación..."):
                    try:
                        pptx_bytes = export_pptx(
                            title=APP_TITLE,
                            profile=profile,
                            kpis=kpis_df,
                            insights=insights,
                            figures=pdf_figures,
                            quality_score=st.session_state.get("quality_score"),
                        )
                        st.download_button(
                            label="Descargar .pptx",
                            data=pptx_bytes,
                            file_name="reporte_ba_insight.pptx",
                            mime="application/vnd.openxmlformats-officedocument"
                                 ".presentationml.presentation",
                            key="download_pptx",
                        )
                        st.success("Presentación lista. Haz clic en Descargar .pptx")
                    except Exception as e:
                        st.error(f"Error al generar PowerPoint: {e}")


if __name__ == "__main__":
    main()
