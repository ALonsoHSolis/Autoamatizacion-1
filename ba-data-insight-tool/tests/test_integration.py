"""Integration tests: full pipeline with sample_data files."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
import pytest

SAMPLE = Path(__file__).parent.parent / "sample_data"

# ── Fixtures ──────────────────────────────────────────────────
@pytest.fixture
def ventas_df():
    from src.data_loader import load_data
    return load_data(SAMPLE / "ventas_mensuales.csv",
                     "ventas_mensuales.csv")

@pytest.fixture
def pagos_df():
    from src.data_loader import load_data
    return load_data(SAMPLE / "pagos_demo.csv", "pagos_demo.csv")

@pytest.fixture
def registros_df():
    from src.data_loader import load_data
    return load_data(SAMPLE / "registros_demo.xlsx",
                     "registros_demo.xlsx")

# ── Data loader ───────────────────────────────────────────────
class TestDataLoader:
    def test_ventas_loads(self, ventas_df):
        assert not ventas_df.empty
        assert len(ventas_df) > 0
        assert len(ventas_df.columns) > 0

    def test_pagos_loads(self, pagos_df):
        assert not pagos_df.empty

    def test_registros_loads(self, registros_df):
        assert not registros_df.empty

    def test_columns_normalized(self, ventas_df):
        for col in ventas_df.columns:
            assert " " not in col
            assert col == col.lower()

# ── Profiler ──────────────────────────────────────────────────
class TestProfilerIntegration:
    def test_profile_returns_required_keys(self, ventas_df):
        from src.data_profiler import profile_dataset
        profile = profile_dataset(ventas_df)
        for key in ["rows","columns","missing_percent",
                    "duplicates","detected"]:
            assert key in profile

    def test_profile_rows_match(self, ventas_df):
        from src.data_profiler import profile_dataset
        profile = profile_dataset(ventas_df)
        assert profile["rows"] == len(ventas_df)

    def test_detect_columns_ventas(self, ventas_df):
        from src.data_profiler import detect_columns
        detected = detect_columns(ventas_df)
        assert len(detected["numeric"]) > 0

    def test_quality_warnings_returns_list(self, ventas_df):
        from src.data_profiler import (profile_dataset,
                                        quality_warnings)
        profile = profile_dataset(ventas_df)
        warnings = quality_warnings(ventas_df, profile["detected"])
        assert isinstance(warnings, list)

    def test_quality_score(self, ventas_df):
        from src.data_profiler import (profile_dataset,
                                        quality_warnings)
        from src.data_profiler import calculate_quality_score
        profile  = profile_dataset(ventas_df)
        warnings = quality_warnings(ventas_df, profile["detected"])
        score = calculate_quality_score(profile, warnings)
        assert 0 <= score["score"] <= 100
        assert score["label"] in ["Buena","Regular","Crítica"]

# ── KPI engine ────────────────────────────────────────────────
class TestKPIIntegration:
    def test_general_kpis_not_empty(self, ventas_df):
        from src.kpi_engine import calculate_kpis, kpis_to_frame
        from src.data_profiler import detect_columns
        detected = detect_columns(ventas_df)
        amount_col = detected["amount"][0] if detected["amount"] else None
        kpis = calculate_kpis(ventas_df, "general",
                              amount_col=amount_col)
        frame = kpis_to_frame(kpis)
        assert not frame.empty

    def test_category_ranking(self, ventas_df):
        from src.kpi_engine import category_ranking
        from src.data_profiler import detect_columns
        detected = detect_columns(ventas_df)
        if detected["category"]:
            ranking = category_ranking(
                ventas_df, detected["category"][0])
            assert not ranking.empty
            assert "categoria" in ranking.columns

    def test_temporal_trend(self, ventas_df):
        from src.kpi_engine import temporal_trend
        from src.data_profiler import detect_columns
        detected = detect_columns(ventas_df)
        if detected["date"]:
            trend = temporal_trend(
                ventas_df, detected["date"][0])
            assert not trend.empty
            assert "periodo" in trend.columns

# ── Anomaly detection ─────────────────────────────────────────
class TestAnomalyIntegration:
    def test_anomalies_returns_dataframe(self, ventas_df):
        from src.anomaly_detection import detect_anomalies
        from src.data_profiler import detect_columns
        detected = detect_columns(ventas_df)
        amount_col = detected["amount"][0] if detected["amount"] else None
        result = detect_anomalies(ventas_df, amount_col)
        assert isinstance(result, pd.DataFrame)

# ── Exports ───────────────────────────────────────────────────
class TestExportIntegration:
    def test_export_excel_returns_bytes(self, ventas_df):
        from src.export_utils import export_excel
        sheets = {"Datos": ventas_df}
        result = export_excel(sheets, "test insights")
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_export_pdf_returns_bytes(self, ventas_df):
        from src.export_utils import export_pdf
        from src.kpi_engine import calculate_kpis, kpis_to_frame
        from src.data_profiler import profile_dataset
        profile = profile_dataset(ventas_df)
        kpis_df = kpis_to_frame(
            calculate_kpis(ventas_df, "general"))
        insights = {"resumen_ejecutivo": "Test OK",
                    "hallazgos": [], "riesgos": [],
                    "hipotesis": [],
                    "preguntas_negocio": [],
                    "acciones_recomendadas": [],
                    "proximos_pasos": []}
        result = export_pdf("Test", profile, kpis_df, insights)
        assert isinstance(result, bytes)
        assert len(result) > 100
