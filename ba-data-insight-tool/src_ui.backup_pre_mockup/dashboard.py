"""Dashboard rendering helpers for BA Data Insight Tool.

Reusable blocks (KPI cards, quality overview, dataset preview,
executive dashboard, insights, recommendations) composed together
by src/ui/tabs.py.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

PREVIEW_ROWS = 20


def render_executive_dashboard(quality_score: dict, warnings: list) -> None:
    """Render the 'Qué revisar primero' executive snapshot."""
    st.markdown("#### 🎯 Qué revisar primero")

    qc1, qc2, qc3 = st.columns(3)
    if quality_score:
        score = quality_score.get("score", 0)
        label = quality_score.get("label", "")
        color = ("🟢" if score >= 80 else
                 "🟡" if score >= 55 else "🔴")
        qc1.metric("Calidad de datos", f"{score}/100",
                   delta=f"{color} {label}")

    if warnings:
        high_warnings = [w for w in warnings if w.severity == "Alta"]
        top_warning = (high_warnings[0] if high_warnings else warnings[0])
        qc2.metric("Alerta principal", top_warning.issue,
                   help=top_warning.detail)
    else:
        qc2.metric("Alerta principal", "Sin alertas")

    if quality_score and quality_score.get("score", 100) < 70:
        recommendation = (
            "Revisar y corregir datos antes de presentar "
            "resultados a stakeholders."
        )
    elif warnings and any(w.severity == "Alta" for w in warnings):
        recommendation = "Resolver advertencias de severidad alta primero."
    else:
        recommendation = "Datos listos para análisis y presentación."
    qc3.metric("Recomendación", "Ver detalle", help=recommendation)

    st.caption(f"💬 {recommendation}")
    st.divider()


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
