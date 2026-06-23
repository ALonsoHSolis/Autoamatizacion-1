"""Integration tests for the 4-step wizard UI flow in app.py.

Uses Streamlit's AppTest to simulate real user interaction (button
clicks) rather than injecting session_state directly, so these tests
catch the same class of bug as the "columnas stays locked after
upload" and "upload controls render in sidebar instead of main area"
regressions found during manual testing.

Calidad/Análisis/Insights/Exportar are NOT separate wizard steps —
they live as subtabs inside the "Resumen ejecutivo" step's content
(see src/ui/tabs.py::render_step_resumen).
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


def _seed_loaded_step(step: str, analysis_has_run: bool = True):
    from src.data_loader import load_data

    test = AppTest.from_file(str(APP_PATH), default_timeout=60)
    demo = load_data("sample_data/ventas_mensuales.csv", "ventas_mensuales.csv")
    test.session_state["demo_df"] = demo
    test.session_state["df"] = demo
    test.session_state["df_loaded"] = True
    test.session_state["source_filename"] = "ventas_mensuales.csv (ejemplo)"
    test.session_state["active_file_signature"] = "demo:ventas_mensuales"
    test.session_state["analysis_has_run"] = analysis_has_run
    test.session_state["active_subtab"] = "Insights"
    test.session_state["wizard_step"] = step
    test.run()
    return test


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

    def test_wizard_has_only_four_steps(self, at):
        keys = {b.key for b in at.sidebar.button if b.key.startswith("wizard_btn_")}
        assert keys == {
            "wizard_btn_inicio",
            "wizard_btn_cargar",
            "wizard_btn_columnas",
            "wizard_btn_resumen",
        }

    def test_no_result_subtabs_on_inicio_even_after_analysis(self):
        test = _seed_loaded_step("inicio", analysis_has_run=True)
        assert "active_subtab" not in {r.key for r in test.radio}
        assert len(test.exception) == 0


class TestCargarStep:
    def test_cta_cargar_navigates_to_cargar_step(self, at):
        _click(at, "btn_cta_cargar")
        assert len(at.exception) == 0
        assert at.session_state["wizard_step"] == "cargar"

    def test_source_controls_render_in_main_area_not_sidebar(self, at):
        _click(at, "btn_cta_cargar")
        main_radios = {r.key for r in at.radio}
        sidebar_radios = {r.key for r in at.sidebar.radio}
        assert "data_source" in main_radios
        assert "data_source" not in sidebar_radios

        main_uploaders = {u.key for u in at.get("file_uploader")}
        sidebar_uploaders = {u.key for u in at.sidebar.get("file_uploader")}
        assert "uploaded_data_file" in main_uploaders
        assert "uploaded_data_file" not in sidebar_uploaders

    def test_columnas_locked_before_any_data(self, at):
        _click(at, "btn_cta_cargar")
        col_btn = next(b for b in at.sidebar.button if b.key == "wizard_btn_columnas")
        assert col_btn.disabled is True

    def test_no_result_subtabs_on_cargar_even_after_analysis(self):
        test = _seed_loaded_step("cargar", analysis_has_run=True)
        assert "active_subtab" not in {r.key for r in test.radio}
        assert len(test.exception) == 0


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

    def test_no_result_subtabs_on_columnas_even_after_analysis(self):
        test = _seed_loaded_step("columnas", analysis_has_run=True)
        assert "active_subtab" not in {r.key for r in test.radio}
        assert len(test.exception) == 0


class TestRunAnalysisAutoAdvance:
    """Covers clicking 'Ejecutar análisis' on the columnas step: it should
    set analysis_has_run and jump straight to 'resumen' in one click,
    without the user needing to click the wizard nav manually."""

    def test_run_analysis_sets_flag_and_advances(self, at):
        _click(at, "btn_cta_demo")
        assert at.session_state["wizard_step"] == "columnas"
        _click(at, "run_analysis_button")
        assert at.session_state["analysis_has_run"] is True
        assert at.session_state["wizard_step"] == "resumen"
        assert len(at.exception) == 0


class TestResumenSubtabs:
    """Calidad/Análisis/Insights/Exportar are subtabs inside the
    'Resumen ejecutivo' wizard step, not separate wizard steps.

    Each test seeds session_state directly with an already-analyzed demo
    dataset and lands on "resumen" in a single AppTest.run() call. This
    avoids routing through the "columnas" step's widgets (date_column,
    etc.), which Streamlit's AppTest keeps stale references to once they
    stop being rendered — a later .run() call on the same tree would raise
    a spurious KeyError trying to resolve them.
    """

    def _seed_resumen(self):
        return _seed_loaded_step("resumen", analysis_has_run=True)

    def test_renders_without_exceptions(self):
        test = self._seed_resumen()
        assert len(test.exception) == 0
        assert test.session_state["wizard_step"] == "resumen"

    def test_main_subtabs_present(self):
        test = self._seed_resumen()
        from src.ui.header import SUBTAB_OPTIONS

        labels = set(next(r for r in test.radio if r.key == "active_subtab").options)
        assert labels == set(SUBTAB_OPTIONS)
        assert {
            "Resumen",
            "Calidad de datos",
            "Insights",
            "Exportar",
        } <= labels

    def test_analisis_subtab_nested_sub_subtabs_present(self):
        """Verifies the Análisis section still declares its 6 sub-sections.

        The top-level resumen navigation is a radio styled as underline tabs,
        so AppTest should not assert those labels through test.tabs anymore.
        """
        test = self._seed_resumen()
        from src.ui.tabs import ANALYSIS_SUBTAB_OPTIONS

        assert set(ANALYSIS_SUBTAB_OPTIONS) == {
            "Básico",
            "Categorías y Pareto",
            "Tabla pivot",
            "Segmentación",
            "Limpieza",
            "Avanzado",
        }
        assert len(test.exception) == 0

    def test_context_card_shows_in_sidebar(self):
        test = self._seed_resumen()
        sidebar_text = " ".join(m.value for m in test.sidebar.markdown)
        assert "Archivo actual" in sidebar_text

    def test_no_separate_wizard_steps_for_calidad_analisis_insights_exportar(self):
        test = self._seed_resumen()
        sidebar_keys = {b.key for b in test.sidebar.button}
        assert "wizard_btn_calidad" not in sidebar_keys
        assert "wizard_btn_analisis" not in sidebar_keys
        assert "wizard_btn_insights" not in sidebar_keys
        assert "wizard_btn_exportar" not in sidebar_keys
