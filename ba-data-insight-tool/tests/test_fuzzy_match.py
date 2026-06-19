"""Tests for fuzzy category matching."""
from __future__ import annotations
import pandas as pd
import pytest


class TestFindSimilarCategories:
    def test_detects_case_and_space_variants(self):
        from src.fuzzy_match import find_similar_categories
        s = pd.Series(["Plan Pro","plan pro","PLAN PRO ",
                       "Plan Pro","Otro Plan"])
        result = find_similar_categories(s, threshold=0.85)
        assert not result.empty
        first_group = result["grupo"].iloc[0]
        members = result[result["grupo"] == first_group]
        assert len(members) >= 2

    def test_no_duplicates_returns_empty(self):
        from src.fuzzy_match import find_similar_categories
        s = pd.Series(["Ventas","Compras","Devoluciones"])
        result = find_similar_categories(s, threshold=0.85)
        assert result.empty

    def test_canonical_is_most_frequent(self):
        from src.fuzzy_match import find_similar_categories
        s = pd.Series(["Premium"]*5 + ["premium"]*2 + ["PREMIUM "]*1)
        result = find_similar_categories(s, threshold=0.85)
        canonical = result["sugerencia_canonica"].iloc[0]
        assert canonical == "Premium"

    def test_typo_detected_above_threshold(self):
        from src.fuzzy_match import find_similar_categories
        s = pd.Series(["Consultoria"]*3 + ["Consultoira"]*2)
        result = find_similar_categories(s, threshold=0.75)
        assert not result.empty


class TestApplyConsolidation:
    def test_replaces_values_correctly(self):
        from src.fuzzy_match import apply_consolidation
        df = pd.DataFrame({"cat": ["Plan Pro","plan pro","Otro"]})
        mapping = {"plan pro": "Plan Pro"}
        result = apply_consolidation(df, "cat", mapping)
        assert (result["cat"] == "Plan Pro").sum() == 2

    def test_does_not_mutate_original(self):
        from src.fuzzy_match import apply_consolidation
        df = pd.DataFrame({"cat": ["Plan Pro","plan pro"]})
        mapping = {"plan pro": "Plan Pro"}
        _ = apply_consolidation(df, "cat", mapping)
        assert df["cat"].tolist() == ["Plan Pro","plan pro"]


class TestBuildMapping:
    def test_builds_correct_mapping(self):
        from src.fuzzy_match import (find_similar_categories,
                                     build_mapping_from_groups)
        s = pd.Series(["Plan Pro"]*3 + ["plan pro"]*1)
        groups = find_similar_categories(s, threshold=0.85)
        mapping = build_mapping_from_groups(groups)
        assert mapping.get("plan pro") == "Plan Pro"
