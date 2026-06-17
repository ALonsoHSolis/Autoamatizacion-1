import pandas as pd

from src.kpi_engine import calculate_kpis, category_ranking, temporal_trend


def test_calculate_kpis_amounts():
    df = pd.DataFrame({"fecha": ["2025-01-01", "2025-02-01"], "ventas": [100, 150], "categoria": ["A", "B"]})
    kpis = calculate_kpis(df, "Análisis de ventas", "ventas", "fecha", "categoria", None)
    names = {item["kpi"] for item in kpis}
    assert "Monto total" in names
    assert "Variación último periodo" in names


def test_temporal_trend_and_ranking():
    df = pd.DataFrame({"fecha": ["2025-01-01", "2025-01-15", "2025-02-01"], "ventas": [100, 50, 200], "categoria": ["A", "A", "B"]})
    trend = temporal_trend(df, "fecha", "ventas")
    ranking = category_ranking(df, "categoria", "ventas")
    assert trend.loc[0, "valor"] == 150
    assert ranking.iloc[0]["categoria"] == "B"


def test_payment_kpis_include_progress_and_pending_gap():
    df = pd.DataFrame(
        {
            "monto_esperado": [100, 100, 100],
            "monto_pagado": [100, 50, 120],
            "estado": ["Pagado", "Pendiente", "Revisar"],
            "unidad": ["A", "B", "B"],
        }
    )
    kpis = calculate_kpis(df, "Análisis de pagos", "monto_pagado", None, "unidad", "estado")
    by_name = {item["kpi"]: item for item in kpis}
    assert by_name["Avance de pago"]["raw_value"] == 90
    assert by_name["Diferencia pendiente"]["raw_value"] == 30
    assert by_name["Pagos incompletos"]["raw_value"] == 1
    assert by_name["Pagos sobre esperado"]["raw_value"] == 1
