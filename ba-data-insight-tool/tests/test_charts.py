"""Tests for src/charts.py — all functions must return go.Figure."""
from __future__ import annotations
import pandas as pd
import pytest
import plotly.graph_objects as go
from pathlib import Path

SAMPLE = Path(__file__).parent.parent / "sample_data"

@pytest.fixture
def df():
    from src.data_loader import load_data
    return load_data(SAMPLE / "ventas_mensuales.csv",
                     "ventas_mensuales.csv")

@pytest.fixture
def detected(df):
    from src.data_profiler import detect_columns
    return detect_columns(df)

def is_figure(obj):
    return isinstance(obj, go.Figure)

class TestChartsReturnFigure:
    def test_temporal_chart(self, df, detected):
        from src.charts import create_temporal_chart
        if detected["date"] and detected["amount"]:
            fig = create_temporal_chart(
                df, detected["date"][0], detected["amount"][0])
            assert is_figure(fig)

    def test_category_chart(self, df, detected):
        from src.charts import create_category_chart
        if detected["category"] and detected["amount"]:
            fig = create_category_chart(
                df, detected["category"][0], detected["amount"][0])
            assert is_figure(fig)

    def test_status_chart(self, df, detected):
        from src.charts import create_status_chart
        if detected["status"]:
            fig = create_status_chart(df, detected["status"][0])
            assert is_figure(fig)

    def test_amount_distribution(self, df, detected):
        from src.charts import create_amount_distribution
        if detected["amount"]:
            fig = create_amount_distribution(
                df, detected["amount"][0])
            assert is_figure(fig)

    def test_boxplot(self, df, detected):
        from src.charts import create_boxplot
        if detected["amount"]:
            fig = create_boxplot(df, detected["amount"][0])
            assert is_figure(fig)

    def test_null_heatmap(self, df):
        from src.charts import create_null_heatmap
        fig = create_null_heatmap(df)
        assert is_figure(fig)

    def test_correlation_heatmap(self, df):
        from src.charts import create_correlation_heatmap
        fig = create_correlation_heatmap(df)
        assert is_figure(fig)

    def test_correlation_heatmap_single_column(self):
        from src.charts import create_correlation_heatmap
        df_single = pd.DataFrame({"a": [1, 2, 3]})
        fig = create_correlation_heatmap(df_single)
        assert is_figure(fig)

    def test_waterfall(self, df, detected):
        from src.charts import create_waterfall
        if detected["category"] and detected["amount"]:
            fig = create_waterfall(
                df, detected["category"][0], detected["amount"][0])
            assert is_figure(fig)

    def test_pareto_chart(self, df, detected):
        from src.charts import create_pareto_chart
        if detected["category"]:
            fig = create_pareto_chart(
                df, detected["category"][0])
            assert is_figure(fig)

    def test_treemap(self, df, detected):
        from src.charts import create_treemap
        if detected["category"]:
            fig = create_treemap(df, detected["category"][0])
            assert is_figure(fig)
