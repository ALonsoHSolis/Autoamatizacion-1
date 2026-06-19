"""Tests for RFM segmentation."""
from __future__ import annotations
import pandas as pd
import pytest
from datetime import datetime, timedelta


@pytest.fixture
def transactions_df():
    base = datetime(2026, 1, 15)
    rows = []
    # Customer A: frequent, recent, high value -> Champion
    for i in range(8):
        rows.append({"cliente_id": "A", "fecha": base - timedelta(days=i*3),
                     "monto": 100000})
    # Customer B: infrequent, old, low value -> Lost
    rows.append({"cliente_id": "B", "fecha": base - timedelta(days=150),
                 "monto": 20000})
    rows.append({"cliente_id": "B", "fecha": base - timedelta(days=160),
                 "monto": 15000})
    return pd.DataFrame(rows)


class TestCalculateRFM:
    def test_returns_one_row_per_customer(self, transactions_df):
        from src.rfm import calculate_rfm
        result = calculate_rfm(
            transactions_df, "cliente_id", "fecha", "monto")
        assert len(result) == transactions_df["cliente_id"].nunique()

    def test_required_columns_present(self, transactions_df):
        from src.rfm import calculate_rfm
        result = calculate_rfm(
            transactions_df, "cliente_id", "fecha", "monto")
        for col in ["cliente","recency_days","frequency",
                    "monetary","r_score","f_score","m_score",
                    "segmento"]:
            assert col in result.columns

    def test_frequency_matches_transaction_count(self, transactions_df):
        from src.rfm import calculate_rfm
        result = calculate_rfm(
            transactions_df, "cliente_id", "fecha", "monto")
        row_a = result[result["cliente"] == "A"].iloc[0]
        assert row_a["frequency"] == 8

    def test_scores_between_1_and_5(self, transactions_df):
        from src.rfm import calculate_rfm
        result = calculate_rfm(
            transactions_df, "cliente_id", "fecha", "monto")
        for col in ["r_score","f_score","m_score"]:
            assert result[col].between(1,5).all()

    def test_empty_dataframe_returns_empty(self):
        from src.rfm import calculate_rfm
        df_empty = pd.DataFrame(
            {"cliente_id": [], "fecha": [], "monto": []})
        result = calculate_rfm(df_empty, "cliente_id", "fecha", "monto")
        assert result.empty


class TestRFMSummary:
    def test_returns_dataframe(self, transactions_df):
        from src.rfm import calculate_rfm, rfm_summary
        rfm_df = calculate_rfm(
            transactions_df, "cliente_id", "fecha", "monto")
        summary = rfm_summary(rfm_df)
        assert isinstance(summary, pd.DataFrame)
        assert not summary.empty

    def test_pct_clientes_sums_to_100(self, transactions_df):
        from src.rfm import calculate_rfm, rfm_summary
        rfm_df = calculate_rfm(
            transactions_df, "cliente_id", "fecha", "monto")
        summary = rfm_summary(rfm_df)
        assert abs(summary["pct_clientes"].sum() - 100) < 1
