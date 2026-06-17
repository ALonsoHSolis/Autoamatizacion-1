import pandas as pd

from src.business_insights import build_insight_context, enrich_context_for_app, generate_insights, insights_to_text


def test_business_insights_public_api_simple_signatures():
    df = pd.DataFrame(
        {
            "monto": [100, 200, None],
            "categoria": ["A", "B", "A"],
            "estado": ["Pagado", "Pendiente", "Pagado"],
        }
    )
    context = build_insight_context(df)
    insights = generate_insights(df, context=context)
    text = insights_to_text(insights)

    assert context["dataset"]["rows"] == 3
    assert "monto" in context["columns"]["numeric"]
    assert "categoria" in context["columns"]["categorical"]
    assert "resumen_ejecutivo" in insights
    assert "Resumen ejecutivo:" in text


def test_business_insights_imports_match_app_usage():
    df = pd.DataFrame(
        {
            "fecha": ["2026-01-01", "2026-02-01"],
            "monto": [1000, 1200],
            "categoria": ["A", "B"],
            "estado": ["Pagado", "Pendiente"],
        }
    )
    context = build_insight_context(df)
    context = enrich_context_for_app(
        context=context,
        df=df,
        analysis_type="Análisis general",
        kpis=[],
        warnings_df=pd.DataFrame(columns=["severity", "column", "issue", "detail"]),
        anomalies=pd.DataFrame(),
        amount_col="monto",
        date_col="fecha",
        category_col="categoria",
        status_col="estado",
    )
    insights = generate_insights(df, context=context)

    assert context["selected_columns"]["amount"] == "monto"
    assert context["top_category"]["categoria"] in {"A", "B"}
    assert "resumen_ejecutivo" in insights


def test_insights_to_text_accepts_legacy_preguntas_key():
    text = insights_to_text(
        {
            "resumen_ejecutivo": "Resumen de prueba",
            "hallazgos": ["Hallazgo"],
            "preguntas": ["Pregunta heredada"],
        }
    )

    assert "Resumen de prueba" in text
    assert "Pregunta heredada" in text
