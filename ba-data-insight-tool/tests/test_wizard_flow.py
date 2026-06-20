"""Integration tests for the 8-step wizard UI flow in app.py.

Uses Streamlit's AppTest to simulate real user interaction (button
clicks) rather than injecting session_state directly, so these tests
catch the same class of bug as the "columnas stays locked after
upload" and "upload controls render in sidebar instead of main area"
regressions found during manual testing.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).parent.parent / "app.py"


@pytest.fixture
def at():
    test = AppTest.from_file(str(APP_PATH), default_timeout=60)
    test.run()
    return test


def _click(at, key, where=None):
    buttons = where if where is not None else at.button
    btn = next(b for b in buttons if b.key == key)
    btn.click().run()
    return at


class TestInicioStep:
    def test_loads_without_exceptions(self, at):
        assert len(at.exception) == 0

    def test_shows_onboarding_ctas(self, at):
        keys = [b.key for b in at.button]
        assert "btn_cta_cargar" in keys
        assert "btn_cta_demo" in keys

    def test_wizard_step_defaults_to_inicio(self, at):
        inicio_btn = next(b for b in at.sidebar.button if b.key == "wizard_btn_inicio")
        columnas_btn = next(b for b in at.sidebar.button if b.key == "wizard_btn_columnas")
        assert inicio_btn.disabled is False
        assert columnas_btn.disabled is True


class TestCargarStep:
    def test_cta_cargar_navigates_to_cargar_step(self, at):
        _click(at, "btn_cta_cargar")
        assert len(at.exception) == 0
        assert at.session_state["wizard_step"] == "cargar"

    def test_source_controls_render_in_main_area_not_sidebar(self, at):
        _click(at, "btn_cta_cargar")
        main_buttons = {b.key for b in at.button}
        sidebar_buttons = {b.key for b in at.sidebar.button}
        assert "source_btn_Subir archivo" in main_buttons
        assert "source_btn_Subir archivo" not in sidebar_buttons

        main_uploaders = {u.key for u in at.get("file_uploader")}
        sidebar_uploaders = {u.key for u in at.sidebar.get("file_uploader")}
        assert "uploaded_data_file" in main_uploaders
        assert "uploaded_data_file" not in sidebar_uploaders

    def test_columnas_locked_before_any_data(self, at):
        _click(at, "btn_cta_cargar")
        col_btn = next(b for b in at.sidebar.button if b.key == "wizard_btn_columnas")
        assert col_btn.disabled is True


class TestDemoDataFlow:
    """Covers the regression where 'columnas' stayed locked the same
    render a file/demo data became available."""

    def test_demo_button_loads_data_without_exceptions(self, at):
        _click(at, "btn_cta_demo")
        assert len(at.exception) == 0
        assert at.session_state["demo_df"] is not None

    def test_columnas_unlocks_immediately_after_demo_load(self, at):
        _click(at, "btn_cta_demo")
        col_btn = next(b for b in at.sidebar.button if b.key == "wizard_btn_columnas")
        assert col_btn.disabled is False

    def test_demo_load_auto_advances_to_columnas(self, at):
        _click(at, "btn_cta_demo")
        assert at.session_state["wizard_step"] == "columnas"
        assert len(at.exception) == 0

    def test_columnas_step_shows_detection_cards_and_controls(self, at):
        _click(at, "btn_cta_demo")
        assert len(at.exception) == 0

        selectbox_keys = {s.key for s in at.selectbox}
        assert {"date_column", "amount_column", "category_column", "status_column"} <= selectbox_keys

        sidebar_selectbox_keys = {s.key for s in at.sidebar.selectbox}
        assert sidebar_selectbox_keys == set()

        main_button_keys = {b.key for b in at.button}
        assert "run_analysis_button" in main_button_keys


class TestFullWizardFlow:
    """Walks Inicio -> demo data -> columnas -> run analysis -> every
    remaining step, asserting no step raises an exception."""

    @pytest.fixture
    def analyzed(self, at):
        _click(at, "btn_cta_demo")
        assert at.session_state["wizard_step"] == "columnas"
        _click(at, "run_analysis_button")
        return at

    def test_run_analysis_sets_flag(self, analyzed):
        assert analyzed.session_state["analysis_has_run"] is True
        assert len(analyzed.exception) == 0

    @pytest.mark.parametrize(
        "step_key",
        ["resumen", "calidad", "analisis", "insights", "exportar"],
    )
    def test_step_renders_without_exceptions(self, analyzed, step_key):
        _click(analyzed, f"wizard_btn_{step_key}", where=analyzed.sidebar.button)
        assert len(analyzed.exception) == 0

    def test_context_card_shows_in_sidebar_for_result_steps(self, analyzed):
        _click(analyzed, "wizard_btn_resumen", where=analyzed.sidebar.button)
        sidebar_text = " ".join(m.value for m in analyzed.sidebar.markdown)
        assert "Archivo actual" in sidebar_text
