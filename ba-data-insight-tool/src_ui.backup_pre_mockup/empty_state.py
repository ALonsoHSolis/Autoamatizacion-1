"""Welcome / empty-state rendering for BA Data Insight Tool.

Shown before the user has uploaded any file (step 1 - Inicio).
"""
from __future__ import annotations

import streamlit as st


def render_empty_state() -> None:
    st.info("👋 Bienvenido. Carga un archivo Excel o CSV desde el panel lateral para comenzar.")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Formatos soportados")
        st.write("Puedes subir archivos `.csv`, `.xlsx` o `.xls` con encabezados en la primera fila.")
    with col_b:
        st.subheader("Datos de ejemplo")
        st.write("Si quieres probar la herramienta, usa los archivos disponibles en la carpeta `sample_data/`.")
    st.divider()
    st.subheader("Qué obtendrás")
    st.write("- Un resumen ejecutivo claro de tu archivo, sin necesidad de fórmulas.")
    st.write("- Una revisión automática de calidad: nulos, duplicados y registros sospechosos.")
    st.write("- KPIs, gráficos, insights y reportes listos para compartir con tu equipo.")
