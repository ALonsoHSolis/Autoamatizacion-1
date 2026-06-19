"""RFM segmentation: Recency, Frequency, Monetary analysis."""
from __future__ import annotations

import pandas as pd
from datetime import datetime
from typing import Any


def calculate_rfm(
    df: pd.DataFrame,
    id_col: str,
    date_col: str,
    amount_col: str,
    reference_date: "datetime | None" = None,
) -> pd.DataFrame:
    """Calculate RFM scores and segments per customer.

    Args:
        df:             Transaction-level DataFrame (one row per
                        transaction, not aggregated).
        id_col:         Column identifying the customer.
        date_col:       Transaction date column.
        amount_col:     Transaction amount column.
        reference_date: Date to calculate recency from.
                        Defaults to max date in data + 1 day.

    Returns:
        DataFrame with one row per customer:
          cliente, recency_days, frequency, monetary,
          r_score, f_score, m_score, rfm_score, segmento
    """
    from .utils import parse_numeric_series, parse_date_series

    work = df.copy()
    work["_date"] = parse_date_series(work[date_col])
    work["_amount"] = parse_numeric_series(work[amount_col])
    work = work.dropna(subset=["_date", "_amount", id_col])

    if work.empty:
        return pd.DataFrame()

    if reference_date is None:
        reference_date = work["_date"].max() + pd.Timedelta(days=1)

    grouped = work.groupby(id_col).agg(
        recency_days=("_date", lambda x: (reference_date - x.max()).days),
        frequency=("_date", "count"),
        monetary=("_amount", "sum"),
    ).reset_index()
    grouped = grouped.rename(columns={id_col: "cliente"})
    grouped["monetary"] = grouped["monetary"].round(2)

    # Score 1-5 by quintile. For recency, LOWER days = BETTER (score 5).
    grouped["r_score"] = pd.qcut(
        grouped["recency_days"], 5, labels=[5,4,3,2,1], duplicates="drop"
    ).astype(int)
    grouped["f_score"] = pd.qcut(
        grouped["frequency"].rank(method="first"), 5,
        labels=[1,2,3,4,5], duplicates="drop"
    ).astype(int)
    grouped["m_score"] = pd.qcut(
        grouped["monetary"].rank(method="first"), 5,
        labels=[1,2,3,4,5], duplicates="drop"
    ).astype(int)

    grouped["rfm_score"] = (
        grouped["r_score"].astype(str) +
        grouped["f_score"].astype(str) +
        grouped["m_score"].astype(str)
    )

    grouped["segmento"] = grouped.apply(_assign_segment, axis=1)
    return grouped.sort_values(
        ["m_score","f_score","r_score"], ascending=False
    ).reset_index(drop=True)


def _assign_segment(row) -> str:
    """Business-friendly segment label from R/F/M scores."""
    r, f, m = row["r_score"], row["f_score"], row["m_score"]

    if r >= 4 and f >= 4 and m >= 4:
        return "🏆 Champions"
    if r >= 3 and f >= 3 and m >= 3:
        return "💚 Clientes leales"
    if r <= 2 and f >= 3 and m >= 3:
        return "⚠️ En riesgo"
    if r >= 4 and f <= 2:
        return "🆕 Nuevos"
    if r <= 2 and f <= 2 and m <= 2:
        return "💤 Perdidos"
    return "🔹 Regulares"


def rfm_summary(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate RFM table into segment-level summary.

    Returns: segmento, clientes, pct_clientes, monetary_total,
             monetary_promedio, recency_promedio
    """
    if rfm_df.empty:
        return pd.DataFrame()

    total_clients = len(rfm_df)
    summary = rfm_df.groupby("segmento").agg(
        clientes=("cliente", "count"),
        monetary_total=("monetary", "sum"),
        monetary_promedio=("monetary", "mean"),
        recency_promedio=("recency_days", "mean"),
    ).reset_index()
    summary["pct_clientes"] = (
        summary["clientes"] / total_clients * 100
    ).round(1)
    summary["monetary_total"] = summary["monetary_total"].round(2)
    summary["monetary_promedio"] = summary["monetary_promedio"].round(2)
    summary["recency_promedio"] = summary["recency_promedio"].round(1)
    return summary.sort_values("monetary_total", ascending=False)
