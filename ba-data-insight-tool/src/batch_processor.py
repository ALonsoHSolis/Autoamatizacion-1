"""Batch processing: consolidate multiple uploaded files into one."""
from __future__ import annotations

import pandas as pd
from typing import Any


def validate_compatible_schemas(
    dfs: list[pd.DataFrame],
    filenames: list[str],
) -> dict[str, Any]:
    """Check whether multiple DataFrames share a compatible schema.

    Returns:
        common_columns:   columns present in ALL files
        all_columns:      union of all columns across files
        per_file_missing: {filename: [columns missing in that file]}
        is_compatible:    True if common columns cover >= 50% of
                          all columns across files
    """
    if not dfs:
        return {"common_columns": [], "all_columns": [],
                "per_file_missing": {}, "is_compatible": False}

    column_sets = [set(df.columns) for df in dfs]
    common = set.intersection(*column_sets)
    all_cols = set.union(*column_sets)

    per_file_missing: dict[str, list[str]] = {}
    for fname, cols in zip(filenames, column_sets):
        missing = sorted(all_cols - cols)
        if missing:
            per_file_missing[fname] = missing

    is_compatible = (
        len(all_cols) > 0 and len(common) / len(all_cols) >= 0.5
    )

    return {
        "common_columns": sorted(common),
        "all_columns": sorted(all_cols),
        "per_file_missing": per_file_missing,
        "is_compatible": is_compatible,
    }


def consolidate_files(
    dfs: list[pd.DataFrame],
    filenames: list[str],
    add_source_column: bool = True,
) -> pd.DataFrame:
    """Concatenate multiple DataFrames aligning by column name.

    Columns missing in a given file become NaN for those rows.
    Adds an "_archivo_origen" column tracking the source file.
    """
    pieces = []
    for df, fname in zip(dfs, filenames):
        piece = df.copy()
        if add_source_column:
            piece["_archivo_origen"] = fname
        pieces.append(piece)
    return pd.concat(pieces, ignore_index=True, sort=False)


def batch_summary(
    dfs: list[pd.DataFrame],
    filenames: list[str],
) -> pd.DataFrame:
    """Per-file row/column count summary."""
    rows = [
        {"archivo": fname, "filas": len(df), "columnas": len(df.columns)}
        for df, fname in zip(dfs, filenames)
    ]
    return pd.DataFrame(rows)
