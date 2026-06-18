"""Tests for compare_vs_budget()."""
from __future__ import annotations
import pandas as pd
import pytest

@pytest.fixture
def actual_df():
    return pd.DataFrame({
        "categoria": ["A","B","C","A","B"],
        "monto": [100, 200, 300, 50, 150],
    })

@pytest.fixture
def budget_df():
    return pd.DataFrame({
        "categoria": ["A","B","C"],
        "presupuesto": [120, 300, 250],
    })

class TestCompareVsBudget:
    def test_returns_dataframe(self, actual_df, budget_df):
        from src.kpi_engine import compare_vs_budget
        result = compare_vs_budget(
            actual_df, budget_df,
            group_col="categoria",
            actual_amount_col="monto",
            budget_amount_col="presupuesto",
        )
        assert isinstance(result, pd.DataFrame)
        assert not result.empty

    def test_required_columns_present(self, actual_df, budget_df):
        from src.kpi_engine import compare_vs_budget
        result = compare_vs_budget(
            actual_df, budget_df,
            group_col="categoria",
            actual_amount_col="monto",
            budget_amount_col="presupuesto",
        )
        for col in ["grupo","real","presupuesto",
                    "varianza","varianza_pct","cumplimiento_pct"]:
            assert col in result.columns

    def test_varianza_calculation(self, actual_df, budget_df):
        from src.kpi_engine import compare_vs_budget
        result = compare_vs_budget(
            actual_df, budget_df,
            group_col="categoria",
            actual_amount_col="monto",
            budget_amount_col="presupuesto",
        )
        for _, row in result.iterrows():
            assert abs(row["varianza"] -
                       (row["real"] - row["presupuesto"])) < 0.01

    def test_cumplimiento_pct(self, actual_df, budget_df):
        from src.kpi_engine import compare_vs_budget
        result = compare_vs_budget(
            actual_df, budget_df,
            group_col="categoria",
            actual_amount_col="monto",
            budget_amount_col="presupuesto",
        )
        for _, row in result.iterrows():
            if row["presupuesto"] != 0:
                expected = row["real"] / row["presupuesto"] * 100
                assert abs(row["cumplimiento_pct"] - expected) < 0.1

    def test_budget_chart_returns_figure(self, actual_df, budget_df):
        from src.kpi_engine import compare_vs_budget
        from src.charts import create_budget_chart
        import plotly.graph_objects as go
        result = compare_vs_budget(
            actual_df, budget_df,
            group_col="categoria",
            actual_amount_col="monto",
            budget_amount_col="presupuesto",
        )
        fig = create_budget_chart(result)
        assert isinstance(fig, go.Figure)
