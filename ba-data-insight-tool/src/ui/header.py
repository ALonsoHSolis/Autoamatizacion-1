"""Header rendering for BA Data Insight Tool."""
from __future__ import annotations

import streamlit as st

STEP_TITLES = {
    "inicio": ("Bienvenido a tu panel de análisis", "Sigue los pasos para transformar tus datos en decisiones inteligentes."),
    "cargar": ("Cargar datos", "Sube tu archivo o conecta una fuente de datos para comenzar."),
    "columnas": ("Confirmar columnas", "Revisa y ajusta las columnas clave detectadas en tu archivo."),
    "resumen": ("Resumen ejecutivo", "KPIs, calidad de datos, análisis e insights de tu archivo."),
}


def render_header(app_title: str, app_subtitle: str, step: str | None = None) -> None:
    """Render the page banner.

    When `step` is given, shows a title/subtitle relevant to the current
    wizard step instead of the generic app name on every screen. Falls
    back to (app_title, app_subtitle) for unknown steps.
    """
    title, subtitle = STEP_TITLES.get(step, (app_title, app_subtitle))
    st.title(title)
    st.caption(subtitle)
    st.divider()
