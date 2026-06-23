"""Welcome / onboarding rendering for BA Data Insight Tool.

Shown before the user has uploaded any file (step 1 - Inicio).
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

SAMPLE_FILE = Path(__file__).resolve().parent.parent.parent / "sample_data" / "ventas_mensuales.csv"

HOW_IT_WORKS = [
    ("1", "Carga tus datos", "Sube tu archivo o conecta una fuente de datos."),
    ("2", "Confirma columnas", "Revisa y ajusta las columnas clave del análisis."),
    ("3", "Revisa insights", "Explora el resumen ejecutivo, calidad y análisis detallado."),
    ("4", "Exporta informe", "Descarga tu informe en Excel, PDF o PowerPoint."),
]

WHAT_YOU_GET = [
    ("📊", "Resumen ejecutivo", "KPIs y métricas clave"),
    ("🛡️", "Calidad de datos", "Score y detección de problemas"),
    ("🔔", "Alertas y anomalías", "Detección automática"),
    ("💡", "Insights accionables", "Recomendaciones inteligentes"),
    ("📄", "Exportación", "Excel, PDF y PPTX"),
]


def render_empty_state(load_data=None) -> None:
    st.markdown(
        '<div class="card hero-card">'
        '<div class="eyebrow">DE PLANILLA A DECISIÓN</div>'
        '<h2>Convierte tus datos en <span class="accent">insights</span> de negocio en minutos</h2>'
        '<p class="hero-subtitle">Carga un Excel, CSV o Google Sheet y obtén KPIs, calidad de datos, '
        'alertas, tendencias y recomendaciones accionables.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📂 Cargar archivo", type="primary", width="stretch", key="btn_cta_cargar"):
            st.session_state["wizard_step"] = "cargar"
            st.rerun()
        st.caption("Sube tu archivo Excel o CSV para comenzar el análisis.")
    with col_b:
        if st.button("▶️ Probar con datos de ejemplo", width="stretch", key="btn_cta_demo"):
            if load_data is not None and SAMPLE_FILE.exists():
                st.session_state["demo_df"] = load_data(str(SAMPLE_FILE), SAMPLE_FILE.name)
                st.session_state["wizard_step"] = "columnas"
                st.rerun()
            else:
                st.error("No se encontró el archivo de ejemplo.")
        st.caption("Explora la herramienta con datos de muestra.")

    st.divider()
    st.subheader("Cómo funciona")
    cols = st.columns(4)
    for col, (num, title, desc) in zip(cols, HOW_IT_WORKS):
        with col:
            st.markdown(
                f'<div class="card step-card">'
                f'<div class="step-num">{num}</div>'
                f'<div class="step-title">{title}</div>'
                f'<div class="step-desc">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.divider()
    st.subheader("Qué obtendrás")
    cols = st.columns(5)
    for col, (icon, title, desc) in zip(cols, WHAT_YOU_GET):
        with col:
            st.markdown(
                f'<div class="card feature-card">'
                f'<div class="icon-badge">{icon}</div>'
                f'<div class="feature-title">{title}</div>'
                f'<div class="feature-desc">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
