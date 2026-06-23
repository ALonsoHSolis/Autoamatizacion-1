"""Header rendering for BA Data Insight Tool."""
from __future__ import annotations

from html import escape

import streamlit as st

STEP_TITLES = {
    "inicio": ("Bienvenido", "Convierte tus datos en decisiones de negocio"),
    "cargar": ("Cargar datos", "Sube un archivo o conecta una fuente para empezar"),
    "columnas": ("Confirmar columnas", "Revisa la detección automática antes de analizar"),
    "resumen": ("Resumen ejecutivo", "KPIs, calidad de datos, análisis e insights de tu archivo."),
}

STEPS_WITHOUT_BANNER = set()

SUBTAB_OPTIONS = ["Resumen", "Calidad de datos", "Insights", "Exportar"]

SECTION_TITLES = {
    "Resumen": ("Resumen ejecutivo", "{source} · análisis de {analysis_type}"),
    "Calidad de datos": ("Calidad de datos", "Validaciones automáticas y score de confianza"),
    "Insights": ("Insights y recomendaciones", "Qué pasa, dónde impacta y qué hacer"),
    "Exportar": ("Exportar informe", "Descarga el análisis en el formato que necesites"),
}


def _go_to_resumen_subtab() -> None:
    st.session_state["wizard_step"] = "resumen"


def render_header(app_title: str, app_subtitle: str, step: str | None = None) -> None:
    """Render the page banner.

    When `step` is given, shows a title/subtitle relevant to the current
    wizard step instead of the generic app name on every screen. Falls
    back to (app_title, app_subtitle) for unknown steps. Steps in
    STEPS_WITHOUT_BANNER render nothing (their content has its own heading).
    """
    if step in STEPS_WITHOUT_BANNER:
        return

    source_filename = st.session_state.get("source_filename")
    analysis_type = st.session_state.get("analysis_type", "General")
    analysis_ready = st.session_state.get("analysis_has_run", False)
    show_file_badge = bool(source_filename) and step in ("columnas", "resumen")
    if step == "resumen" and analysis_ready:
        active_subtab = st.session_state.get("active_subtab", "Resumen")
        if active_subtab not in SUBTAB_OPTIONS:
            active_subtab = "Resumen"
        title, subtitle_template = SECTION_TITLES.get(active_subtab, SECTION_TITLES["Resumen"])
        subtitle = subtitle_template.format(source=source_filename or "archivo", analysis_type=analysis_type)
    else:
        title, subtitle = STEP_TITLES.get(step, (app_title, app_subtitle))

    if show_file_badge and analysis_ready:
        title_col, badge_col, action_col = st.columns([4.4, 0.9, 0.55], vertical_alignment="top")
        with title_col:
            st.markdown(
                '<div class="app-page-header">'
                '<div class="app-header-kicker">BA DATA INSIGHT TOOL</div>'
                f'<h1 class="app-header-title">{escape(title)}</h1>'
                f'<div class="app-header-subtitle">{escape(subtitle)}</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        with badge_col:
            st.markdown(
                f'<div style="text-align:right"><div class="file-badge" title="{escape(source_filename)}">'
                f'<span class="dot"></span>{escape(source_filename)}</div></div>',
                unsafe_allow_html=True,
            )
        with action_col:
            if st.button(
                "Exportar",
                key="btn_header_exportar",
                width="stretch",
                type="primary",
                icon=":material/upload:",
            ):
                st.session_state["active_subtab"] = "Exportar"
                st.session_state["wizard_step"] = "resumen"
                st.rerun()
    elif show_file_badge:
        title_col, badge_col, action_col = st.columns([4.4, 0.9, 0.55], vertical_alignment="top")
        with title_col:
            st.markdown(
                '<div class="app-page-header">'
                '<div class="app-header-kicker">BA DATA INSIGHT TOOL</div>'
                f'<h1 class="app-header-title">{escape(title)}</h1>'
                f'<div class="app-header-subtitle">{escape(subtitle)}</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        with badge_col:
            st.markdown(
                f'<div style="text-align:right"><div class="file-badge" title="{escape(source_filename)}">'
                f'<span class="dot"></span>{escape(source_filename)}</div></div>',
                unsafe_allow_html=True,
            )
        with action_col:
            st.button(
                "Exportar",
                key="btn_header_exportar_disabled",
                width="stretch",
                type="primary",
                icon=":material/upload:",
                disabled=True,
            )
    else:
        st.markdown(
            '<div class="app-page-header">'
            '<div class="app-header-kicker">BA DATA INSIGHT TOOL</div>'
            f'<h1 class="app-header-title">{escape(title)}</h1>'
            f'<div class="app-header-subtitle">{escape(subtitle)}</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    if step == "resumen" and analysis_ready:
        if st.session_state.get("active_subtab") not in SUBTAB_OPTIONS:
            st.session_state["active_subtab"] = "Resumen"
        st.radio(
            "Secciones",
            SUBTAB_OPTIONS,
            key="active_subtab",
            horizontal=True,
            label_visibility="collapsed",
            on_change=_go_to_resumen_subtab,
        )

    st.divider()
