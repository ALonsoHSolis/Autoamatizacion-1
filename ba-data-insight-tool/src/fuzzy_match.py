"""Fuzzy matching for detecting near-duplicate category text.

Uses only Python's built-in difflib — no new dependencies.
"""
from __future__ import annotations

import difflib
import pandas as pd

from .utils import normalize_name


def _similarity(a: str, b: str) -> float:
    """Similarity ratio 0-1 between two normalized strings."""
    return difflib.SequenceMatcher(
        None, normalize_name(a), normalize_name(b)
    ).ratio()


def find_similar_categories(
    series: pd.Series,
    threshold: float = 0.85,
) -> pd.DataFrame:
    """Detect near-duplicate category values.

    Groups values whose normalized similarity is >= threshold.
    Exact matches after normalization (case, accents, spacing)
    are always grouped regardless of threshold.

    Args:
        series:    Column to analyze.
        threshold: Minimum similarity ratio (0.70-1.00) to group
                   two different-looking values together.

    Returns:
        DataFrame with: grupo, valor, frecuencia, es_canonico,
        sugerencia_canonica, similitud.
        Groups with only 1 unique value are excluded.
    """
    counts = series.dropna().astype(str).str.strip().value_counts()
    values = counts.index.tolist()

    parent = {v: v for v in values}

    def find(v: str) -> str:
        while parent[v] != v:
            v = parent[v]
        return v

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    normalized = {v: normalize_name(v) for v in values}

    for i, v1 in enumerate(values):
        for v2 in values[i + 1:]:
            if normalized[v1] == normalized[v2]:
                union(v1, v2)
            elif _similarity(v1, v2) >= threshold:
                union(v1, v2)

    groups: dict[str, list[str]] = {}
    for v in values:
        root = find(v)
        groups.setdefault(root, []).append(v)

    rows = []
    group_id = 0
    for root, members in groups.items():
        if len(members) < 2:
            continue
        group_id += 1
        canonical = max(members, key=lambda m: counts[m])
        for m in members:
            sim = 1.0 if m == canonical else round(
                _similarity(m, canonical), 3)
            rows.append({
                "grupo": group_id,
                "valor": m,
                "frecuencia": int(counts[m]),
                "es_canonico": m == canonical,
                "sugerencia_canonica": canonical,
                "similitud": sim,
            })

    cols = ["grupo","valor","frecuencia","es_canonico",
            "sugerencia_canonica","similitud"]
    if not rows:
        return pd.DataFrame(columns=cols)

    result = pd.DataFrame(rows)
    return result.sort_values(
        ["grupo","frecuencia"], ascending=[True, False]
    ).reset_index(drop=True)


def apply_consolidation(
    df: pd.DataFrame,
    col: str,
    mapping: dict[str, str],
) -> pd.DataFrame:
    """Replace values in col using mapping. Returns a NEW DataFrame."""
    result = df.copy()
    result[col] = result[col].astype(str).str.strip().replace(mapping)
    return result


def build_mapping_from_groups(groups_df: pd.DataFrame) -> dict[str, str]:
    """Build {original_value: canonical_value} from groups output."""
    if groups_df.empty:
        return {}
    return dict(zip(groups_df["valor"], groups_df["sugerencia_canonica"]))
