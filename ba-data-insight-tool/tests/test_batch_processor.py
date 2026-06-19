"""Tests for batch file processing."""
from __future__ import annotations
import pandas as pd
import pytest


@pytest.fixture
def compatible_dfs():
    df1 = pd.DataFrame({"categoria": ["A","B"], "monto": [100,200]})
    df2 = pd.DataFrame({"categoria": ["C","D"], "monto": [300,400]})
    return [df1, df2], ["enero.csv","febrero.csv"]


@pytest.fixture
def incompatible_dfs():
    df1 = pd.DataFrame({"categoria": ["A"], "monto": [100]})
    df2 = pd.DataFrame({"nombre": ["X"], "edad": [30]})
    return [df1, df2], ["ventas.csv","personas.csv"]


class TestValidateCompatibleSchemas:
    def test_compatible_files_detected(self, compatible_dfs):
        from src.batch_processor import validate_compatible_schemas
        dfs, names = compatible_dfs
        result = validate_compatible_schemas(dfs, names)
        assert result["is_compatible"] is True
        assert set(result["common_columns"]) == {"categoria","monto"}

    def test_incompatible_files_detected(self, incompatible_dfs):
        from src.batch_processor import validate_compatible_schemas
        dfs, names = incompatible_dfs
        result = validate_compatible_schemas(dfs, names)
        assert result["is_compatible"] is False

    def test_empty_list_returns_safe_defaults(self):
        from src.batch_processor import validate_compatible_schemas
        result = validate_compatible_schemas([], [])
        assert result["is_compatible"] is False
        assert result["common_columns"] == []


class TestConsolidateFiles:
    def test_concatenates_all_rows(self, compatible_dfs):
        from src.batch_processor import consolidate_files
        dfs, names = compatible_dfs
        result = consolidate_files(dfs, names)
        assert len(result) == sum(len(d) for d in dfs)

    def test_adds_source_column(self, compatible_dfs):
        from src.batch_processor import consolidate_files
        dfs, names = compatible_dfs
        result = consolidate_files(dfs, names, add_source_column=True)
        assert "_archivo_origen" in result.columns
        assert set(result["_archivo_origen"].unique()) == set(names)

    def test_no_source_column_when_disabled(self, compatible_dfs):
        from src.batch_processor import consolidate_files
        dfs, names = compatible_dfs
        result = consolidate_files(dfs, names, add_source_column=False)
        assert "_archivo_origen" not in result.columns


class TestBatchSummary:
    def test_returns_row_per_file(self, compatible_dfs):
        from src.batch_processor import batch_summary
        dfs, names = compatible_dfs
        result = batch_summary(dfs, names)
        assert len(result) == len(dfs)
        assert list(result["archivo"]) == names
