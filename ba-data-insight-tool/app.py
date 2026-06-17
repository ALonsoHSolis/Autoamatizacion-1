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
    create_boxplot,
    create_category_chart,
    create_correlation_heatmap,
    create_null_heatmap,
    create_pareto_chart,
    create_status_chart,
    create_temporal_chart,
    create_treemap,
    create_waterfall,
)
from src.data_loader import get_excel_sheets, load_data, load_google_sheet
from src.data_profiler import calculate_quality_score, profile_dataset, quality_warnings, warnings_to_frame
from src.export_utils import export_excel, export_pdf
from src.kpi_engine import (
    calculate_kpis,
    category_ranking,
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
            ["Subir archivo", "Google Sheets URL"],
            key="data_source",
            horizontal=True,
        )

        gs_df = None
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
        threshold = st.slider(
            "Sensibilidad de anomalías",
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
    st.dataframe(display, width="stretch", hide_index=True)


def render_detected_columns(profile: dict) -> None:
    detected = {key: value for key, value in profile["detected"].items() if value}
    if not detected:
        st.info("No se detectaron columnas especiales automáticamente.")
        return
    rows = [{"tipo": key, "columnas": ", ".join(value)} for key, value in detected.items()]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)


def render_preview(uploaded, df: pd.DataFrame, profile: dict) -> None:
    st.subheader("Archivo cargado")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Nombre", uploaded.name if uploaded is not None else "Archivo")
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
    render_header()

    initial_controls = render_sidebar_base()
    uploaded = initial_controls["uploaded"]
    sheet_name = initial_controls["sheet_name"]
    analysis_type = initial_controls["analysis_type"]
    threshold = initial_controls["threshold"]
    gs_df = initial_controls["gs_df"]
    gs_url = initial_controls["gs_url"]

    if gs_df is not None:
        signature = f"gsheet:{gs_url}"
        if st.session_state.get("active_file_signature") != signature:
            st.session_state["active_file_signature"] = signature
            st.session_state["analysis_has_run"] = False
            for key in ["date_column", "amount_column", "category_column", "status_column"]:
                st.session_state.pop(key, None)
        df = gs_df
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

    profile = cached_profile(df)
    detected = profile["detected"]
    st.success("Archivo cargado correctamente.")

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

    (
        summary_tab,
        quality_tab,
        numeric_tab,
        category_tab,
        pivot_tab,
        pareto_tab,
        advanced_tab,
        insights_tab,
        recommendations_tab,
        downloads_tab,
    ) = st.tabs(
        [
            "Resumen",
            "Calidad de datos",
            "Análisis numérico",
            "Categorías y estados",
            "Tabla pivot",
            "Pareto / ABC",
            "Análisis avanzado",
            "Insights automáticos",
            "Recomendaciones",
            "Descargas",
        ]
    )

    with summary_tab:
        st.subheader("Resumen del dataset")
        st.caption("Vista general para confirmar que el archivo se cargó como esperabas.")
        render_summary_metrics(profile, warnings_df)
        st.divider()
        render_preview(uploaded, df, profile)

    with quality_tab:
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

    with numeric_tab:
        st.subheader("KPIs y análisis numérico")
        if not analysis_ready:
            st.info("Ejecuta el análisis desde el panel lateral para ver KPIs, tendencias y anomalías.")
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

    with category_tab:
        st.subheader("Análisis por categorías y estados")
        if not analysis_ready:
            st.info("Ejecuta el análisis para ver rankings, participación y distribución por estados.")
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

    with pivot_tab:
        st.subheader("Tabla pivot dinámica")
        st.caption(
            "Cruza dos dimensiones y agrega un valor numérico. "
            "Ideal para comparar categorías por período o estado."
        )
        if not analysis_ready:
            st.info("Ejecuta el análisis para usar la tabla pivot.")
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

    with pareto_tab:
        st.subheader("Análisis de Pareto / ABC")
        st.caption(
            "Identifica automáticamente qué categorías concentran el 80 % (segmento A), "
            "el 15 % (B) y el 5 % (C) del valor. Útil para priorizar revisión y recursos."
        )
        if not analysis_ready:
            st.info("Ejecuta el análisis desde el panel lateral para ver el Pareto.")
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

    with advanced_tab:
        st.subheader("Análisis avanzado")
        if not analysis_ready:
            st.info("Ejecuta el análisis desde el panel lateral para ver las visualizaciones avanzadas.")
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

    with insights_tab:
        st.subheader("Insights automáticos")
        if not analysis_ready:
            st.info("Ejecuta el análisis para generar conclusiones ejecutivas.")
        else:
            render_insights(insights, kpis_df, profile, anomalies)
            with st.expander("Ver texto completo de insights", expanded=False):
                st.text_area("Resumen generado", insights_text, height=360, key="executive_insights_text")

    with recommendations_tab:
        if not analysis_ready:
            st.info("Ejecuta el análisis para ver recomendaciones iniciales.")
        else:
            default_recommendations = build_default_recommendations(profile, warnings_df, anomalies, amount_col, category_col, date_col)
            render_recommendations(insights, default_recommendations)

    with downloads_tab:
        st.subheader("Descargar resultados")
        if not analysis_ready:
            st.info("Ejecuta el análisis para habilitar las descargas.")
        else:
            export_sheets = {
                "Resumen": pd.DataFrame(
                    [
                        {
                            "archivo": uploaded.name,
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
            pdf_bytes = export_pdf(
                APP_TITLE, profile, kpis_df, insights,
                figures=st.session_state.get("figures_for_pdf", {}))
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


if __name__ == "__main__":
    main()
