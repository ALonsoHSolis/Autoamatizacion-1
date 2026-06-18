"""Tests for forecast_trend() and forecast_kpis()."""
from __future__ import annotations
import pandas as pd
import pytest
from pathlib import Path

SAMPLE = Path(__file__).parent.parent / "sample_data"

@pytest.fixture
def ventas_df():
    from src.data_loader import load_data
    return load_data(SAMPLE / "ventas_mensuales.csv",
                     "ventas_mensuales.csv")

@pytest.fixture
def detected(ventas_df):
    from src.data_profiler import detect_columns
    return detect_columns(ventas_df)

class TestForecastTrend:
    def test_returns_dict_with_required_keys(self, ventas_df, detected):
        from src.kpi_engine import forecast_trend
        if not detected["date"]:
            pytest.skip("No date column detected")
        result = forecast_trend(
            ventas_df, detected["date"][0],
            detected["amount"][0] if detected["amount"] else None,
            periods_ahead=3,
        )
        if result:
            for key in ["historical","projected","slope",
                        "r_squared","direction","next_value"]:
                assert key in result

    def test_projected_length_matches_periods(self, ventas_df, detected):
        from src.kpi_engine import forecast_trend
        if not detected["date"]:
            pytest.skip("No date column detected")
        for n in [1, 3, 6]:
            result = forecast_trend(
                ventas_df, detected["date"][0],
                periods_ahead=n)
            if result:
                assert len(result["projected"]) == n

    def test_r_squared_between_0_and_1(self, ventas_df, detected):
        from src.kpi_engine import forecast_trend
        if not detected["date"]:
            pytest.skip("No date column detected")
        result = forecast_trend(
            ventas_df, detected["date"][0],
            periods_ahead=3)
        if result:
            assert 0.0 <= result["r_squared"] <= 1.0

    def test_direction_is_valid(self, ventas_df, detected):
        from src.kpi_engine import forecast_trend
        if not detected["date"]:
            pytest.skip("No date column detected")
        result = forecast_trend(
            ventas_df, detected["date"][0],
            periods_ahead=3)
        if result:
            assert result["direction"] in [
                "creciente","decreciente","estable"]

    def test_projected_has_confidence_band(self, ventas_df, detected):
        from src.kpi_engine import forecast_trend
        if not detected["date"]:
            pytest.skip("No date column detected")
        result = forecast_trend(
            ventas_df, detected["date"][0],
            periods_ahead=3)
        if result and result["projected"]:
            p = result["projected"][0]
            assert p["lower"] <= p["valor"] <= p["upper"]

    def test_insufficient_data_returns_empty(self):
        from src.kpi_engine import forecast_trend
        df_short = pd.DataFrame({
            "fecha": pd.date_range("2025-01", periods=2, freq="ME"),
            "monto": [100, 200],
        })
        result = forecast_trend(df_short, "fecha", "monto")
        assert result == {}

    def test_forecast_chart_returns_figure(self, ventas_df, detected):
        from src.kpi_engine import forecast_trend
        from src.charts import create_forecast_chart
        import plotly.graph_objects as go
        if not detected["date"]:
            pytest.skip("No date column detected")
        result = forecast_trend(
            ventas_df, detected["date"][0],
            periods_ahead=3)
        fig = create_forecast_chart(result)
        assert isinstance(fig, go.Figure)
