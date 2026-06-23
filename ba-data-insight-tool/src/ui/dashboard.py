"""Dashboard rendering helpers for BA Data Insight Tool.

Reusable blocks (KPI cards, quality overview, dataset preview,
executive dashboard, insights, recommendations) composed together
by src/ui/tabs.py.
"""
from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from src.utils import format_currency, format_number, parse_date_series, parse_numeric_series
from src.kpi_engine import category_ranking

PREVIEW_ROWS = 20


def _html(value) -> str:
    return escape(str(value), quote=True)


def _first_detected(detected: dict, key: str, exclude: set[str] | None = None) -> str | None:
    excluded = exclude or set()
    for value in detected.get(key, []):
        if value not in excluded:
            return value
    return None


def _find_channel_column(df: pd.DataFrame | None, detected: dict) -> str | None:
    if df is None:
        return None
    candidates = list(detected.get("category", [])) + list(df.columns)
    for col in candidates:
        normalized = str(col).lower()
        if "canal" in normalized or "channel" in normalized:
            return col
    return None


def _column_meta(df: pd.DataFrame | None, col: str | None, kind: str) -> str:
    if not col or df is None or col not in df:
        return "No detectada"
    series = df[col]
    if kind == "date":
        parsed = parse_date_series(series).dropna()
        if parsed.empty:
            return "Formato fecha"
        months = parsed.dt.to_period("M").nunique()
        return f"Formato ISO · {months} meses"
    if kind == "amount":
        numeric = parse_numeric_series(series)
        valid_pct = numeric.notna().mean() * 100
        return f"Numérico · {valid_pct:.0f}% válido"
    unique = series.nunique(dropna=True)
    return f"{unique} valores únicos"


def render_column_detection_cards(detected: dict, df: pd.DataFrame | None = None) -> None:
    """Show detected date/amount/category/status columns as cards."""
    channel_col = _find_channel_column(df, detected)
    category_col = _first_detected(detected, "category", exclude={channel_col} if channel_col else set())
    labels = [
        ("date", "Fecha", _first_detected(detected, "date"), "blue"),
        ("amount", "Monto", _first_detected(detected, "amount"), "green"),
        ("category", "Categoría", category_col, "purple"),
        ("channel", "Canal", channel_col, "amber"),
    ]
    cols = st.columns(4)
    for col, (key, title, value, color) in zip(cols, labels):
        value_text = value if value else "No detectada"
        meta = _column_meta(df, value, key)
        with col:
            st.markdown(
                f'<div class="card detect-card detect-card-premium">'
                f'<div class="detect-title"><span class="detect-dot {color}"></span>{_html(title)}</div>'
                f'<div class="detect-value">{_html(value_text)}</div>'
                f'<div class="detect-meta">{_html(meta)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


def _format_preview_cell(value) -> str:
    if pd.isna(value):
        return "—"
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%Y-%m-%d")
        except Exception:
            pass
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return format_number(value)
    return str(value)


def render_dark_preview_table(df: pd.DataFrame, max_rows: int = 6, max_cols: int = 8) -> None:
    """Render a compact HTML preview table styled like the reference."""
    visible = df.head(max_rows).iloc[:, :max_cols].copy()
    header = "".join(f"<th>{_html(col).upper()}</th>" for col in visible.columns)
    rows = []
    for _, row in visible.iterrows():
        cells = "".join(f"<td>{_html(_format_preview_cell(row[col]))}</td>" for col in visible.columns)
        rows.append(f"<tr>{cells}</tr>")
    st.markdown(
        '<div class="preview-head">'
        f'<span>Vista previa · primeras {min(max_rows, len(df))} filas</span>'
        f'<span>{len(df):,} filas · {len(df.columns)} columnas</span>'
        '</div>'
        '<div class="dark-table-wrap">'
        '<table class="dark-preview-table">'
        f'<thead><tr>{header}</tr></thead>'
        f'<tbody>{"".join(rows)}</tbody>'
        '</table>'
        '</div>',
        unsafe_allow_html=True,
    )


def _compact_currency(value: float | int | None) -> str:
    if value is None:
        return "N/A"
    number = float(value)
    sign = "-" if number < 0 else ""
    number = abs(number)
    if number >= 1_000_000:
        return f"{sign}${number / 1_000_000:.1f}M".replace(".", ",")
    if number >= 1_000:
        return f"{sign}${number / 1_000:.1f}K".replace(".", ",")
    return format_currency(number)


def _find_text_column(df: pd.DataFrame, keywords: tuple[str, ...]) -> str | None:
    for col in df.columns:
        normalized = str(col).lower()
        if any(word in normalized for word in keywords):
            return col
    return None


def _render_kpi_cards(cards: list[tuple[str, str, str, str]]) -> None:
    cols = st.columns(len(cards))
    for col, (title, value, delta, tone) in zip(cols, cards):
        with col:
            st.markdown(
                '<div class="dashboard-kpi-card">'
                f'<div class="dashboard-kpi-title">{_html(title)}</div>'
                f'<div class="dashboard-kpi-value">{_html(value)}</div>'
                f'<div class="dashboard-kpi-delta {tone}">{_html(delta)}</div>'
                '</div>',
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
    st.markdown('<div class="section-kicker">KPIs principales</div>', unsafe_allow_html=True)
    total_amount = None
    ticket_avg = None
    if df is not None and amount_col and amount_col in df:
        amounts = parse_numeric_series(df[amount_col])
        valid_amounts = amounts.dropna()
        if not valid_amounts.empty:
            total_amount = float(valid_amounts.sum())
            ticket_avg = float(valid_amounts.mean())
    ticket_col = _find_text_column(df, ("ticket",)) if df is not None else None
    if df is not None and ticket_col:
        ticket_values = parse_numeric_series(df[ticket_col]).dropna()
        if not ticket_values.empty:
            ticket_avg = float(ticket_values.mean())
    client_col = _find_text_column(df, ("cliente", "customer", "rut", "email", "id")) if df is not None else None
    client_value = "N/A"
    if df is not None and client_col:
        if pd.api.types.is_numeric_dtype(df[client_col]):
            client_value = f"{int(parse_numeric_series(df[client_col]).sum()):,}".replace(",", ".")
        else:
            client_value = f"{df[client_col].nunique():,}".replace(",", ".")
    channel_col = _find_channel_column(df, {"category": [category_col] if category_col else []}) if df is not None else None
    channel_label = "N/A"
    channel_meta = "Sin canal detectado"
    if df is not None:
        lead_col = channel_col or category_col
        if lead_col and lead_col in df:
            ranking = category_ranking(df, lead_col, amount_col)
            if not ranking.empty:
                channel_label = str(ranking.iloc[0]["categoria"])
                channel_meta = f"{ranking.iloc[0]['participacion_pct']:.0f}% del total"
    cards = [
        ("Ventas totales", _compact_currency(total_amount), "^ listo para analizar", "positive"),
        ("Ticket promedio", _compact_currency(ticket_avg), "^ promedio calculado", "positive"),
        ("Transacciones", f"{len(df):,}".replace(",", ".") if df is not None else "0", "^ volumen total", "positive"),
        ("Clientes únicos", client_value, "— estable", "muted"),
        ("Canal líder", channel_label, channel_meta, "muted"),
    ]
    _render_kpi_cards(cards)

    st.markdown('<div class="section-kicker">Alertas y prioridades</div>', unsafe_allow_html=True)
    alert_col, priority_col = st.columns(2)
    with alert_col:
        if warnings:
            high_warnings = [w for w in warnings if w.severity == "Alta"]
            top_warning = (high_warnings[0] if high_warnings else warnings[0])
            badge_class, badge_icon = {
                "Alta": ("badge-high", "🔴"),
                "Media": ("badge-medium", "🟡"),
            }.get(top_warning.severity, ("badge-low", "🟢"))
            severity_class = badge_class.replace("badge-", "alert-")
            st.markdown(
                f'<div class="card alert-card {severity_class}">'
                f'<div class="card-header"><span class="badge {badge_class}">{_html(top_warning.severity)} prioridad</span></div>'
                f'<div class="card-title">{_html(top_warning.issue)}</div>'
                f'<div class="card-desc">{_html(top_warning.detail)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="card alert-card alert-low"><div class="card-title">Sin alertas</div>'
                '<div class="card-desc">No se detectaron advertencias relevantes.</div></div>',
                unsafe_allow_html=True,
            )

    with priority_col:
        if quality_score and quality_score.get("score", 100) < 70:
            action = "Revisar y corregir datos antes de presentar resultados a stakeholders."
            badge_class = "badge-high"
        elif warnings and any(w.severity == "Alta" for w in warnings):
            action = "Resolver advertencias de severidad alta primero."
            badge_class = "badge-high"
        else:
            action = "Datos listos para análisis y presentación."
            badge_class = "badge-low"
        score = quality_score.get("score", 0) if quality_score else 0
        severity_class = badge_class.replace("badge-", "alert-")
        st.markdown(
            f'<div class="card alert-card {severity_class}">'
            f'<div class="card-header"><span class="badge {badge_class}">Qué revisar primero</span></div>'
            f'<div class="card-title">Calidad de datos: {score}/100</div>'
            f'<div class="card-desc">{_html(action)}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if df is not None and (date_col or category_col):
        st.markdown('<div class="section-kicker">Tendencias</div>', unsafe_allow_html=True)
        chart_cols = st.columns(2) if (date_col and category_col) else st.columns(1)
        idx = 0
        if date_col:
            from src.charts import create_temporal_chart
            with chart_cols[idx]:
                st.markdown('<div class="chart-panel-title">Ventas por mes</div>', unsafe_allow_html=True)
                fig = create_temporal_chart(df, date_col, amount_col)
                fig.update_layout(title_text="", height=310, margin={"l": 42, "r": 22, "t": 18, "b": 36})
                st.plotly_chart(fig, width="stretch", key="exec_dashboard_temporal")
            idx += 1
        if category_col:
            from src.charts import create_category_chart
            with chart_cols[idx]:
                st.markdown('<div class="chart-panel-title">Ventas por categoría</div>', unsafe_allow_html=True)
                fig = create_category_chart(df, category_col, amount_col)
                fig.update_layout(title_text="", height=310, margin={"l": 96, "r": 24, "t": 18, "b": 36})
                st.plotly_chart(fig, width="stretch", key="exec_dashboard_category")


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

    st.markdown('<div class="section-kicker">Validaciones detectadas</div>', unsafe_allow_html=True)
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
    summary = str(insights.get("resumen_ejecutivo", "No hay resumen disponible."))
    st.markdown(
        '<div class="insight-summary-card">'
        '<div class="section-kicker" style="margin:0 0 9px 0">Resumen ejecutivo</div>'
        f'<div class="summary-text">{_html(summary)}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

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

    st.markdown('<div class="section-kicker">Hallazgos principales</div>', unsafe_allow_html=True)
    for idx, finding in enumerate(findings[:3], start=1):
        if actions:
            action = actions[min(idx - 1, len(actions) - 1)]
        elif risks:
            action = risks[min(idx - 1, len(risks) - 1)]
        else:
            action = "Validar el hallazgo con el equipo dueño del proceso."
        st.markdown(
            '<div class="insight-card">'
            '<div class="insight-card-head">'
            f'<div class="insight-number">{idx:02d}</div>'
            f'<div class="insight-title">{_html(finding)}</div>'
            '</div>'
            '<div class="insight-grid">'
            '<div>'
            '<div class="insight-label">Evidencia</div>'
            f'<div class="insight-copy">{_html(evidence)}</div>'
            '</div>'
            '<div>'
            '<div class="insight-label">Acción recomendada</div>'
            f'<div class="insight-copy">{_html(action)}</div>'
            '</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )


def render_recommendations(insights: dict, default_recommendations: list[str]) -> None:
    st.markdown('<div class="section-kicker">Recomendaciones iniciales</div>', unsafe_allow_html=True)
    actions = insights.get("acciones_recomendadas", [])
    risks = insights.get("riesgos", [])
    questions = insights.get("preguntas_negocio", [])

    if isinstance(actions, str):
        actions = [actions]
    if isinstance(risks, str):
        risks = [risks]
    if isinstance(questions, str):
        questions = [questions]

    items = list(dict.fromkeys(list(actions) + default_recommendations))
    html_items = "".join(
        '<div class="recommendation-item">'
        '<span class="recommendation-check">✓</span>'
        f'<span>{_html(recommendation)}</span>'
        '</div>'
        for recommendation in items[:8]
    )
    st.markdown(f'<div class="recommendation-list">{html_items}</div>', unsafe_allow_html=True)

    with st.expander("Riesgos y preguntas para profundizar", expanded=False):
        if risks:
            st.write("**Riesgos detectados**")
            for risk in risks:
                st.write(f"- {risk}")
        if questions:
            st.write("**Preguntas sugeridas**")
            for question in questions:
                st.write(f"- {question}")
