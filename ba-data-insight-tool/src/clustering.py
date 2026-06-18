"""Automatic K-means clustering for BA Data Insight Tool."""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Any


def _select_numeric_cols(df: pd.DataFrame) -> list[str]:
    cols = []
    for col in df.select_dtypes(include="number").columns:
        series = df[col].dropna()
        if series.nunique() >= 3 and not set(series.unique()).issubset({0, 1}):
            cols.append(col)
    return cols


def find_optimal_k(data: np.ndarray, max_k: int = 8) -> tuple[int, list[float]]:
    from sklearn.cluster import KMeans
    k_range = range(2, min(max_k + 1, len(data)))
    inertias: list[float] = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(data)
        inertias.append(float(km.inertia_))
    if len(inertias) < 2:
        return 2, inertias
    drops = [inertias[i] - inertias[i + 1] for i in range(len(inertias) - 1)]
    elbow_idx = int(np.argmax(drops))
    optimal_k = list(k_range)[elbow_idx]
    return optimal_k, inertias


def auto_cluster(
    df: pd.DataFrame,
    n_clusters: int | str = "auto",
    max_k: int = 8,
    cols: list[str] | None = None,
) -> dict[str, Any]:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score

    numeric_cols = cols or _select_numeric_cols(df)
    if len(numeric_cols) < 2:
        return {"error": "Se necesitan al menos 2 columnas numéricas para clustering."}

    subset = df[numeric_cols].dropna()
    if len(subset) < 4:
        return {"error": "Se necesitan al menos 4 registros sin valores nulos."}

    scaler = StandardScaler()
    scaled = scaler.fit_transform(subset)

    if n_clusters == "auto":
        optimal_k, inertias = find_optimal_k(scaled, max_k)
    else:
        optimal_k = int(n_clusters)
        k_range = range(2, min(max_k + 1, len(subset)))
        from sklearn.cluster import KMeans as _KM
        inertias = [
            float(_KM(n_clusters=k, random_state=42, n_init=10).fit(scaled).inertia_)
            for k in k_range
        ]

    km = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
    labels = km.fit_predict(scaled)

    try:
        sil = float(silhouette_score(scaled, labels))
    except Exception:
        sil = None

    df_result = subset.copy()
    df_result["cluster"] = [f"Segmento {i + 1}" for i in labels]
    profiles = cluster_profiles(df_result, numeric_cols)

    return {
        "labels":         df_result["cluster"].tolist(),
        "n_clusters":     optimal_k,
        "inertias":       inertias,
        "k_range":        list(range(2, min(max_k + 1, len(subset)))),
        "numeric_cols":   numeric_cols,
        "silhouette":     round(sil, 3) if sil is not None else None,
        "profiles":       profiles,
        "df_with_labels": df_result,
        "index":          subset.index.tolist(),
    }


def cluster_profiles(
    df_labeled: pd.DataFrame,
    numeric_cols: list[str],
) -> pd.DataFrame:
    grp = df_labeled.groupby("cluster")[numeric_cols].mean().round(2)
    counts = df_labeled["cluster"].value_counts().rename("registros")
    grp["registros"] = counts
    total = grp["registros"].sum()
    grp["pct"] = (grp["registros"] / total * 100).round(1).astype(str) + "%"
    return grp.reset_index().rename(columns={"cluster": "segmento"})
