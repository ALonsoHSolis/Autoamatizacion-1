from __future__ import annotations

from typing import Any

import pandas as pd

from .kpi_engine import category_ranking, status_summary, temporal_trend
from .utils import format_currency, format_number, format_percent, parse_numeric_series, strip_accents


InsightDict = dict[str, list[str] | str]

INSIGHT_LIST_KEYS = (
    "hallazgos",
    "riesgos",
    "hipotesis",
    "preguntas_negocio",
    "preguntas",
    "acciones_recomendadas",
    "proximos_pasos",
)

__all__ = [
    "build_insight_context",
    "enrich_context_for_app",
    "generate_insights",
    "insights_to_text",
]


def build_insight_context(df: pd.DataFrame) -> dict[str, Any]:
    """Build a robust, generic business context from any pandas DataFrame.

    This is the public function imported by app.py. Keep the signature simple:
    build_insight_context(df).
    """
    if df is None or df.empty:
        return {
            "dataset": {"rows": 0, "columns": 0, "missing_percent": 0.0, "duplicates": 0},
            "columns": {"numeric": [], "categorical": [], "date_like": [], "numeric_like": []},
            "missing": {"total_cells": 0, "total_missing": 0, "percent": 0.0, "by_column": []},
            "statistics": {},
            "categorical_summary": {},
            "auto_findings": ["No hay datos suficientes para generar insights."],
        }

    numeric_columns = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
    numeric_like_columns = [
        col for col in df.columns if col not in numeric_columns and parse_numeric_series(df[col]).notna().mean() >= 0.75
    ]
    date_like_columns = [
        col
        for col in df.columns
        if col not in numeric_columns
        and col not in numeric_like_columns
        and pd.to_datetime(df[col], errors="coerce", format="mixed").notna().mean() >= 0.65
    ]
    categorical_columns = [
        col
        for col in df.columns
        if col not in numeric_columns and col not in numeric_like_columns and col not in date_like_columns
    ]

    total_cells = max(int(df.shape[0] * df.shape[1]), 1)
    missing_by_column = (
        df.isna()
        .mean()
        .mul(100)
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"index": "columna", 0: "faltantes_pct"})
    )
    missing_records = [
        {"columna": row["columna"], "faltantes_pct": round(float(row["faltantes_pct"]), 2)}
        for _, row in missing_by_column.head(10).iterrows()
        if row["faltantes_pct"] > 0
    ]

    numeric_for_stats = pd.DataFrame(index=df.index)
    for col in numeric_columns + numeric_like_columns:
        numeric_for_stats[col] = parse_numeric_series(df[col])
    statistics = (
        numeric_for_stats.describe().round(2).where(pd.notna(numeric_for_stats.describe()), None).to_dict()
        if not numeric_for_stats.empty
        else {}
    )

    categorical_summary: dict[str, list[dict[str, Any]]] = {}
    for col in categorical_columns[:8]:
        counts = df[col].fillna("Sin dato").astype(str).value_counts(dropna=False).head(5)
        total = max(int(counts.sum()), 1)
        categorical_summary[col] = [
            {"valor": idx, "registros": int(value), "participacion_pct": round(float(value / total * 100), 2)}
            for idx, value in counts.items()
        ]

    missing_percent = round(float(df.isna().sum().sum() / total_cells * 100), 2)
    duplicates = int(df.duplicated().sum())
    auto_findings = [
        f"El dataset contiene {len(df)} registros y {len(df.columns)} columnas.",
        f"Se detectaron {len(numeric_columns) + len(numeric_like_columns)} columnas numéricas o convertibles a número.",
        f"El porcentaje global de datos faltantes es {missing_percent}%.",
    ]
    if duplicates:
        auto_findings.append(f"Hay {duplicates} registros duplicados que podrían afectar conteos y montos.")
    if missing_records:
        top_missing = missing_records[0]
        auto_findings.append(f"La columna con más faltantes es {top_missing['columna']} con {top_missing['faltantes_pct']}%.")
    if statistics:
        first_numeric = next(iter(statistics))
        auto_findings.append(f"La columna numérica {first_numeric} tiene promedio {format_number(statistics[first_numeric].get('mean', 0))}.")

    return {
        "dataset": {
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "missing_percent": missing_percent,
            "duplicates": duplicates,
        },
        "columns": {
            "numeric": numeric_columns,
            "numeric_like": numeric_like_columns,
            "categorical": categorical_columns,
            "date_like": date_like_columns,
        },
        "missing": {
            "total_cells": total_cells,
            "total_missing": int(df.isna().sum().sum()),
            "percent": missing_percent,
            "by_column": missing_records,
        },
        "statistics": statistics,
        "categorical_summary": categorical_summary,
        "auto_findings": auto_findings,
    }


def generate_insights(df: pd.DataFrame, context: dict[str, Any] | None = None) -> InsightDict:
    """Generate executive insights in Spanish from a DataFrame and optional context.

    Public signature expected by app.py and tests: generate_insights(df, context=None).
    The optional context can include app-level enrichments such as selected columns,
    KPIs, anomalies, quality warnings, trend, category ranking, and payment summary.
    """
    context = context or build_insight_context(df)
    dataset = context.get("dataset", {})
    selected = context.get("selected_columns", {})
    amount_col = selected.get("amount")
    analysis_type = context.get("analysis_type", "Análisis general")

    findings = list(context.get("auto_findings", []))
    risks: list[str] = []
    hypotheses: list[str] = []
    questions: list[str] = []
    actions: list[str] = []

    amount = context.get("amount")
    payment = context.get("payment")
    top_category = context.get("top_category")
    top_status = context.get("top_status")
    biggest_variation = context.get("biggest_variation")
    quality = context.get("quality", {})
    anomalies = context.get("anomalies", {})

    if payment:
        summary = (
            f"El monto pagado alcanza {format_currency(payment['total_paid'])} frente a un esperado de "
            f"{format_currency(payment['total_expected'])}, con avance de {format_percent(payment['progress'])} "
            f"y brecha pendiente de {format_currency(payment['pending'])}."
        )
        top_pending = payment.get("top_pending_category")
        if top_pending:
            summary += f" La mayor brecha se concentra en {top_pending['categoria']} con {format_currency(top_pending['pendiente'])}."
            findings.append(f"{top_pending['categoria']} explica la mayor brecha pendiente.")
            actions.append(f"Priorizar seguimiento de {top_pending['categoria']} antes de revisar casos individuales.")
        findings.append(f"Hay {payment.get('incomplete_count', 0)} pagos incompletos y {payment.get('overpaid_count', 0)} sobrepagos.")
    elif amount:
        summary = (
            f"El dataset contiene {dataset.get('rows', len(df))} registros y el monto total analizado es "
            f"{format_currency(amount['total'])} en la columna {amount.get('column', amount_col)}."
        )
    else:
        summary = (
            f"El dataset contiene {dataset.get('rows', len(df))} registros y {dataset.get('columns', len(df.columns))} columnas. "
            "No se seleccionó una columna principal de monto, por lo que el foco está en estructura, calidad y distribución."
        )

    summary += (
        f" La calidad muestra {dataset.get('missing_percent', context.get('missing', {}).get('percent', 0))}% de datos faltantes "
        f"y {dataset.get('duplicates', 0)} duplicados."
    )

    if biggest_variation:
        direction = "aumento" if biggest_variation["absolute"] > 0 else "caída"
        findings.append(
            f"La mayor variación temporal ocurre en {biggest_variation['period']}: {direction} de "
            f"{format_currency(abs(biggest_variation['absolute']))}"
            + (f" ({format_percent(biggest_variation['percent'])})." if biggest_variation.get("percent") is not None else ".")
        )
        hypotheses.append("La variación puede explicarse por estacionalidad, cambios de proceso, eventos comerciales o carga tardía de datos.")
        questions.append(f"¿Qué ocurrió en {biggest_variation['period']} que explique la variación observada?")

    if top_category:
        findings.append(
            f"La categoría {top_category['categoria']} concentra {format_percent(top_category['participacion_pct'])} "
            f"del valor o volumen analizado, con {format_number(top_category['valor'])}."
        )
        questions.append(f"¿La concentración en {top_category['categoria']} es esperada o representa dependencia operativa?")
        actions.append(f"Profundizar el análisis de {top_category['categoria']} y compararlo contra el resto de categorías.")

    if top_status:
        findings.append(
            f"El estado dominante es {top_status['estado']}, con {format_percent(top_status['porcentaje'])} "
            f"de los registros y monto asociado de {format_currency(top_status['monto'])}."
        )
        if "pend" in strip_accents(str(top_status["estado"]).lower()):
            risks.append("El estado pendiente lidera la distribución y puede indicar atrasos o falta de actualización operacional.")

    anomaly_count = int(anomalies.get("count", 0) or 0)
    if anomaly_count:
        risks.append(f"Se detectaron {anomaly_count} registros anómalos que deben validarse antes de tomar decisiones.")
        actions.append("Revisar anomalías contra documentos fuente, reglas del proceso o responsables operativos.")

    if quality.get("high"):
        risks.append(f"Existen {quality['high']} advertencias de calidad con severidad alta.")
        actions.append("Resolver primero columnas vacías, campos clave incompletos o errores estructurales.")
    if quality.get("medium"):
        risks.append(f"Hay {quality['medium']} advertencias medias que pueden afectar segmentaciones o conciliaciones.")

    missing = context.get("missing", {})
    if missing.get("by_column") and not quality:
        first_missing = missing["by_column"][0]
        risks.append(f"La columna {first_missing['columna']} tiene {first_missing['faltantes_pct']}% de valores faltantes.")
        actions.append("Validar campos con mayor cantidad de faltantes antes de usar el dataset como fuente oficial.")

    if dataset.get("duplicates", 0):
        risks.append(f"Los {dataset['duplicates']} duplicados pueden inflar KPIs, rankings o conteos.")
        actions.append("Eliminar, justificar o marcar duplicados antes de presentar cifras finales.")

    analysis_key = strip_accents(str(analysis_type).lower())
    if "venta" in analysis_key:
        questions.extend(["¿El cambio se explica por volumen, ticket promedio o mezcla de canales?", "¿Qué categoría explica la mayor variación?"])
        actions.append("Separar efecto volumen y efecto ticket para explicar ventas con mayor precisión.")
    elif "pago" in analysis_key:
        questions.extend(["¿Qué unidad concentra la mayor deuda?", "¿Los pendientes son atrasos reales o problemas de actualización?"])
    elif "conciliacion" in analysis_key:
        questions.extend(["¿Qué movimientos no tienen referencia?", "¿Los descuadres se concentran por banco, partner o estado?"])
        actions.append("Priorizar partidas sin referencia y estados no conciliados.")
    elif "registro" in analysis_key or "persona" in analysis_key:
        questions.extend(["¿Qué campos son obligatorios para operar sin reprocesos?", "¿Los duplicados corresponden a personas repetidas u homónimos?"])
    elif "financiero" in analysis_key:
        questions.extend(["¿Qué categoría explica el mayor gasto?", "¿La variación es puntual o recurrente?"])

    if not findings:
        findings.append("La base es analizable y permite una primera lectura de estructura, calidad y distribución.")
    if not risks:
        risks.append("No se observan riesgos críticos con las reglas automáticas aplicadas; se recomienda validar supuestos con el dueño del dato.")
    if not hypotheses:
        hypotheses.append("Los patrones detectados podrían estar asociados a estacionalidad, cambios operativos, concentración por segmento o calidad de carga.")
    if not questions:
        questions.append("¿Qué segmento, periodo o estado requiere revisión prioritaria por impacto de negocio?")
    if not actions:
        actions.append("Documentar supuestos, validar datos críticos y repetir el análisis con una fuente oficial de comparación.")

    return _normalize_insights({
        "resumen_ejecutivo": summary,
        "hallazgos": findings,
        "riesgos": risks,
        "hipotesis": hypotheses,
        "preguntas_negocio": questions,
        "preguntas": questions,
        "acciones_recomendadas": actions,
        "proximos_pasos": [
            "Validar los hallazgos con el equipo dueño del proceso.",
            "Corregir datos críticos y volver a ejecutar el análisis.",
            "Convertir los KPIs más útiles en un control recurrente.",
        ],
    })


def insights_to_text(insights: InsightDict) -> str:
    insights = _normalize_insights(insights)
    lines = ["Resumen ejecutivo:", str(insights.get("resumen_ejecutivo", "")), ""]
    labels = [
        ("Hallazgos principales", "hallazgos"),
        ("Riesgos", "riesgos"),
        ("Hipótesis", "hipotesis"),
        ("Preguntas de negocio", "preguntas_negocio"),
        ("Acciones recomendadas", "acciones_recomendadas"),
        ("Próximos pasos", "proximos_pasos"),
    ]
    for title, key in labels:
        values = insights.get(key, [])
        if isinstance(values, str):
            values = [values]
        lines.append(f"{title}:")
        lines.extend([f"- {item}" for item in values])
        lines.append("")
    return "\n".join(lines).strip()


def _normalize_insights(insights: dict[str, Any] | None) -> InsightDict:
    """Return a complete insights dict and accept legacy key names."""
    source = insights or {}
    normalized: InsightDict = {
        "resumen_ejecutivo": str(source.get("resumen_ejecutivo") or source.get("resumen") or ""),
    }

    for key in INSIGHT_LIST_KEYS:
        normalized[key] = _as_text_items(source.get(key))

    if not normalized["preguntas_negocio"]:
        normalized["preguntas_negocio"] = _as_text_items(source.get("preguntas"))
    if not normalized["preguntas"]:
        normalized["preguntas"] = _as_text_items(normalized.get("preguntas_negocio"))

    return normalized


def _as_text_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def enrich_context_for_app(
    context: dict[str, Any],
    df: pd.DataFrame,
    analysis_type: str,
    kpis: list[dict[str, Any]],
    warnings_df: pd.DataFrame,
    anomalies: pd.DataFrame,
    amount_col: str | None,
    date_col: str | None,
    category_col: str | None,
    status_col: str | None,
) -> dict[str, Any]:
    """Internal compatibility helper for the Streamlit app.

    The public API stays as requested, while app.py can enrich the generic
    context with selected columns and precomputed analysis outputs.
    """
    context = dict(context)
    context.update(
        {
            "analysis_type": analysis_type,
            "selected_columns": {"amount": amount_col, "date": date_col, "category": category_col, "status": status_col},
            "kpis": kpis,
            "quality": {
                "warnings_count": 0 if warnings_df.empty else len(warnings_df),
                "high": 0 if warnings_df.empty else int((warnings_df["severity"] == "Alta").sum()),
                "medium": 0 if warnings_df.empty else int((warnings_df["severity"] == "Media").sum()),
                "low": 0 if warnings_df.empty else int((warnings_df["severity"] == "Baja").sum()),
                "top_warnings": [] if warnings_df.empty else warnings_df.head(6).to_dict("records"),
            },
            "anomalies": {"count": len(anomalies), "top": [] if anomalies.empty else anomalies.head(5).to_dict("records")},
        }
    )

    if amount_col and amount_col in df:
        values = parse_numeric_series(df[amount_col])
        context["amount"] = {
            "column": amount_col,
            "total": float(values.sum()),
            "average": float(values.mean()) if values.notna().any() else None,
            "min": float(values.min()) if values.notna().any() else None,
            "max": float(values.max()) if values.notna().any() else None,
        }

    if date_col and date_col in df:
        trend = temporal_trend(df, date_col, amount_col)
        context["trend"] = trend.tail(12).to_dict("records")
        variation = trend.dropna(subset=["variacion_abs"]) if not trend.empty else pd.DataFrame()
        if not variation.empty:
            biggest = variation.loc[variation["variacion_abs"].abs().idxmax()]
            context["biggest_variation"] = {
                "period": biggest["periodo"].strftime("%Y-%m"),
                "absolute": float(biggest["variacion_abs"]),
                "percent": float(biggest["variacion_pct"]) if pd.notna(biggest["variacion_pct"]) else None,
            }

    if category_col and category_col in df:
        ranking = category_ranking(df, category_col, amount_col)
        context["category_ranking"] = ranking.to_dict("records")
        if not ranking.empty:
            context["top_category"] = ranking.iloc[0].to_dict()

    if status_col and status_col in df:
        statuses = status_summary(df, status_col, amount_col)
        context["status_summary"] = statuses.to_dict("records")
        if not statuses.empty:
            context["top_status"] = statuses.iloc[0].to_dict()

    expected_col = _find_column(df, ["esperado", "monto_total", "total_a_pagar"])
    paid_col = _find_column(df, ["pagado", "monto_pagado", "abonado"], exclude=[expected_col] if expected_col else None)
    if expected_col and paid_col:
        expected = parse_numeric_series(df[expected_col])
        paid = parse_numeric_series(df[paid_col])
        pending = expected - paid
        total_expected = float(expected.sum())
        total_paid = float(paid.sum())
        context["payment"] = {
            "expected_col": expected_col,
            "paid_col": paid_col,
            "total_expected": total_expected,
            "total_paid": total_paid,
            "pending": float(pending.sum()),
            "progress": total_paid / total_expected * 100 if total_expected else 0,
            "incomplete_count": int((paid < expected).sum()),
            "overpaid_count": int((paid > expected).sum()),
        }
        if category_col and category_col in df:
            by_category = pd.DataFrame({"categoria": df[category_col].fillna("Sin categoría"), "pendiente": pending})
            by_category = by_category.groupby("categoria", as_index=False)["pendiente"].sum().sort_values("pendiente", ascending=False)
            if not by_category.empty:
                context["payment"]["top_pending_category"] = by_category.iloc[0].to_dict()
    return context


def _find_column(df: pd.DataFrame, keywords: list[str], exclude: list[str] | None = None) -> str | None:
    excluded = {strip_accents(item.lower()) for item in (exclude or [])}
    for col in df.columns:
        normalized = strip_accents(col.lower())
        if normalized in excluded:
            continue
        if any(strip_accents(word.lower()) in normalized for word in keywords):
            return col
    return None
