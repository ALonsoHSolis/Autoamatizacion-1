"""Dashboard rendering helpers for BA Data Insight Tool.

Reusable blocks (KPI cards, quality overview, dataset preview,
executive dashboard, insights, recommendations) composed together
by src/ui/tabs.py.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

PREVIEW_ROWS = 20


def render_column_detection_cards(detected: dict) -> None:
    """Show detected date/amount/category/status columns as cards."""
    labels = [
        ("date", "Fecha detectada"),
        ("amount", "Monto detectado"),
        ("category", "Categoría detectada"),
        ("status", "Estado detectado"),
    ]
    cols = st.columns(4)
    for col, (key, title) in zip(cols, labels):
        values = detected.get(key, [])
        value_text = ", ".join(values) if values else "No detectada"
        with col:
            st.markdown(
                f'<div class="card detect-card">'
                f'<div class="detect-title">{title}</div>'
                f'<div class="detect-value">{value_text}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def render_executive_dashboard(
    quality_score: dict,
    warnings: list,
    kpis_df: pd.DataFrame,
    source_filename: str,
    profile: dict,
    df: pd.DataFrame | None = None,
    date_col: str | None = None,
    amount_col: str | None = None,
    category_col: str | None = None,
) -> None:
    """Render the executive dashboard: KPI cards, quality, alert and charts."""
    st.subheader("📁 Archivo analizado")
    st.markdown(f"**{source_filename}**")
    st.caption(f"{profile['rows']:,} filas · {profile['columns']} columnas")
    st.divider()

    st.subheader("📊 KPIs principales")
    if not kpis_df.empty:
        kpi_rows = kpis_df.head(4).to_dict("records")
        cols = st.columns(len(kpi_rows))
        for col, row in zip(cols, kpi_rows):
            col.metric(str(row["kpi"]), str(row["valor"]))
    else:
        st.warning(
            "No se calcularon KPIs con la configuración actual. "
            "Revisa en **Confirmar columnas** que la columna de monto esté bien mapeada, "
            "y que el archivo tenga datos en esa columna."
        )
    st.divider()

    st.subheader("⚠️ Alertas y prioridades")
    st.caption("Lo más urgente a revisar antes de tomar decisiones con estos datos.")
    alert_col, priority_col = st.columns(2)
    with alert_col:
        if warnings:
            high_warnings = [w for w in warnings if w.severity == "Alta"]
            top_warning = (high_warnings[0] if high_warnings else warnings[0])
            badge_class, badge_icon = {
                "Alta": ("badge-high", "🔴"),
                "Media": ("badge-medium", "🟡"),
            }.get(top_warning.severity, ("badge-low", "🟢"))
            st.markdown(
                f'<div class="card alert-card">'
                f'<div class="card-header"><span class="badge {badge_class}">{badge_icon} {top_warning.severity} prioridad</span></div>'
                f'<div class="card-title">{top_warning.issue}</div>'
                f'<div class="card-desc">{top_warning.detail}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="card alert-card"><div class="card-title">Sin alertas</div>'
                '<div class="card-desc">No se detectaron advertencias relevantes.</div></div>',
                unsafe_allow_html=True,
            )

    with priority_col:
        if quality_score and quality_score.get("score", 100) < 70:
            action = "Revisar y corregir datos antes de presentar resultados a stakeholders."
            badge_class, badge_icon = "badge-high", "🔴"
        elif warnings and any(w.severity == "Alta" for w in warnings):
            action = "Resolver advertencias de severidad alta primero."
            badge_class, badge_icon = "badge-high", "🔴"
        else:
            action = "Datos listos para análisis y presentación."
            badge_class, badge_icon = "badge-low", "🟢"
        score = quality_score.get("score", 0) if quality_score else 0
        st.markdown(
            f'<div class="card alert-card">'
            f'<div class="card-header"><span class="badge {badge_class}">{badge_icon} Qué revisar primero</span></div>'
            f'<div class="card-title">Calidad de datos: {score}/100</div>'
            f'<div class="card-desc">{action}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if df is not None and (date_col or category_col):
        st.divider()
        with st.expander("📈 Tendencias", expanded=False):
            chart_cols = st.columns(2) if (date_col and category_col) else st.columns(1)
            idx = 0
            if date_col:
                from src.charts import create_temporal_chart
                with chart_cols[idx]:
                    st.caption("Tendencia temporal")
                    st.plotly_chart(create_temporal_chart(df, date_col, amount_col), width="stretch", key="exec_dashboard_temporal")
                idx += 1
            if category_col:
                from src.charts import create_category_chart
                with chart_cols[idx]:
                    st.caption("Distribución por categoría")
                    st.plotly_chart(create_category_chart(df, category_col, amount_col), width="stretch", key="exec_dashboard_category")

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
    if profile["columns"] > 40:
        st.warning("El archivo tiene muchas columnas. Revisa las columnas detectadas antes de ejecutar el análisis.")
    if profile["missing_percent"] >= 30:
        st.warning("Se detecta un porcentaje alto de datos faltantes.")

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
