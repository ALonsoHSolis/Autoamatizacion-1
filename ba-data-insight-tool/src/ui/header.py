"""Header rendering for BA Data Insight Tool."""
from __future__ import annotations

import streamlit as st

STEP_TITLES = {
    "inicio": ("Bienvenido a tu panel de análisis", "Sigue los pasos para transformar tus datos en decisiones inteligentes."),
    "columnas": ("Confirmar columnas", "Revisa y ajusta las columnas clave detectadas en tu archivo."),
    "resumen": ("Resumen ejecutivo", "KPIs, calidad de datos, análisis e insights de tu archivo."),
}

# "cargar" has no banner: its own "Cargar archivo" subheader already
# introduces the step, so the big gradient title would be redundant.
STEPS_WITHOUT_BANNER = {"cargar"}


def render_header(app_title: str, app_subtitle: str, step: str | None = None) -> None:
    """Render the page banner.

    When `step` is given, shows a title/subtitle relevant to the current
    wizard step instead of the generic app name on every screen. Falls
    back to (app_title, app_subtitle) for unknown steps. Steps in
    STEPS_WITHOUT_BANNER render nothing (their content has its own heading).
    """
    if step in STEPS_WITHOUT_BANNER:
        return
    title, subtitle = STEP_TITLES.get(step, (app_title, app_subtitle))

    source_filename = st.session_state.get("source_filename")
    show_file_badge = step in ("columnas", "resumen") and source_filename

    if show_file_badge:
        title_col, badge_col = st.columns([3, 1])
        with badge_col:
            st.markdown(
                f'<div style="text-align:right"><div class="file-badge">'
                f'<span class="dot"></span>{source_filename}</div></div>',
                unsafe_allow_html=True,
            )
        with title_col:
            st.title(title)
            st.caption(subtitle)
    else:
        st.title(title)
        st.caption(subtitle)
    st.divider()
