"""Step content rendering for BA Data Insight Tool's 8-step wizard.

Each render_step_*() function receives the current context dict
(ctx) built in app.py's main() and renders the matching step's
content. Logic, session_state keys, and widget keys are unchanged
from the original flat-tab implementation — only the navigation
shell changed.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from src.charts import (
    create_amount_distribution,
    create_boxplot,
    create_budget_chart,
    create_category_chart,
    create_cluster_profiles_chart,
    create_cluster_scatter,
    create_correlation_heatmap,
    create_elbow_chart,
    create_forecast_chart,
    create_fuzzy_groups_chart,
    create_null_heatmap,
    create_pareto_chart,
    create_rfm_scatter,
    create_rfm_segment_chart,
    create_status_chart,
    create_temporal_chart,
    create_treemap,
    create_waterfall,
)
from src.clustering import auto_cluster
from src.data_loader import load_data
from src.fuzzy_match import apply_consolidation, build_mapping_from_groups, find_similar_categories
from src.kpi_engine import (
    category_ranking,
    compare_vs_budget,
    forecast_kpis,
    forecast_trend,
    pareto_analysis,
    period_comparison,
    status_summary,
    temporal_trend,
)
from src.rfm import calculate_rfm, rfm_summary
from src.export_utils import export_excel, export_pdf, export_pptx

from src.ui.dashboard import (
    build_default_recommendations,
    render_business_kpis,
    render_executive_dashboard,
    render_insights,
    render_preview,
    render_quality_overview,
    render_recommendations,
    render_summary_metrics,
)


def render_step_resumen(ctx: dict) -> None:
    analysis_ready = ctx["analysis_ready"]
    if analysis_ready:
        render_executive_dashboard(ctx["quality_score"], ctx["warnings"])

    st.subheader("Resumen del dataset")
    st.caption("Vista general para confirmar que el archivo se cargó como esperabas.")
    render_summary_metrics(ctx["profile"], ctx["warnings_df"])
    st.divider()
    render_preview(ctx["source_filename"], ctx["df"], ctx["profile"])


def render_step_calidad(ctx: dict) -> None:
    quality_score = ctx["quality_score"]
    df = ctx["df"]
    st.subheader("Revisión de calidad")
    st.caption("Antes de tomar decisiones, revisa nulos, duplicados, formatos inválidos y valores sospechosos.")
    st.metric(
        label="Calidad del dataset",
        value=f"{quality_score['score']}/100",
        delta=quality_score['label'],
        delta_color=quality_score['color'],
    )
    render_quality_overview(ctx["warnings_df"])
    with st.expander("Mapa simple de datos faltantes", expanded=False):
        st.plotly_chart(create_null_heatmap(df), width="stretch", key="null_heatmap_chart")


def _render_sub_numerico(ctx: dict) -> None:
    df = ctx["df"]
    date_col = ctx["date_col"]
    amount_col = ctx["amount_col"]
    anomalies = ctx["anomalies"]

    st.subheader("KPIs y análisis numérico")
    render_business_kpis(ctx["kpis_df"])
    st.divider()
    if date_col:
        st.subheader("Tendencia temporal")
        st.plotly_chart(create_temporal_chart(df, date_col, amount_col), width="stretch", key="temporal_chart")
        st.dataframe(temporal_trend(df, date_col, amount_col), width="stretch", hide_index=True)
    else:
        st.info("Selecciona una columna de fecha para ver tendencia temporal.")

    st.subheader("Distribución y anomalías")
    if amount_col:
        left, right = st.columns(2)
        left.plotly_chart(create_amount_distribution(df, amount_col), width="stretch", key="amount_distribution_chart")
        right.plotly_chart(create_boxplot(df, amount_col), width="stretch", key="amount_boxplot_chart")
    if anomalies.empty:
        st.success("No se detectaron anomalías con el umbral seleccionado.")
    else:
        st.warning(f"Se detectaron {len(anomalies)} registros sospechosos.")
        st.dataframe(anomalies, width="stretch")


def _render_sub_categorias_pareto(ctx: dict) -> None:
    df = ctx["df"]
    category_col = ctx["category_col"]
    amount_col = ctx["amount_col"]
    status_col = ctx["status_col"]

    st.subheader("Análisis por categorías y estados")
    if category_col:
        st.subheader("Ranking por categoría")
        st.plotly_chart(create_category_chart(df, category_col, amount_col), width="stretch", key="category_chart")
        st.dataframe(category_ranking(df, category_col, amount_col), width="stretch", hide_index=True)
    else:
        st.info("Selecciona una columna de categoría para ver ranking.")

    if status_col:
        st.subheader("Distribución por estado")
        st.plotly_chart(create_status_chart(df, status_col, amount_col), width="stretch", key="status_chart")
        st.dataframe(status_summary(df, status_col, amount_col), width="stretch", hide_index=True)
    else:
        st.info("Selecciona una columna de estado para ver distribución.")

    st.divider()
    st.subheader("Análisis de Pareto / ABC")
    st.caption(
        "Identifica automáticamente qué categorías concentran el 80 % (segmento A), "
        "el 15 % (B) y el 5 % (C) del valor. Útil para priorizar revisión y recursos."
    )
    if not category_col:
        st.info("Selecciona una columna de categoría para ver el análisis de Pareto.")
    else:
        st.plotly_chart(
            create_pareto_chart(df, category_col, amount_col),
            width="stretch",
            key="pareto_chart",
        )
        pareto_df = pareto_analysis(df, category_col, amount_col)
        if not pareto_df.empty:
            seg_a = pareto_df[pareto_df["segmento"] == "A"]
            seg_b = pareto_df[pareto_df["segmento"] == "B"]
            seg_c = pareto_df[pareto_df["segmento"] == "C"]
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Segmento A - vital", len(seg_a), help="Concentran el 80 % del valor")
            col_b.metric("Segmento B - importante", len(seg_b), help="Llevan el acumulado al 95 %")
            col_c.metric("Segmento C - trivial", len(seg_c), help="El restante 5 %")
            with st.expander("Ver tabla Pareto completa", expanded=False):
                st.dataframe(pareto_df, width="stretch", hide_index=True)


def _render_sub_pivot(ctx: dict) -> None:
    df = ctx["df"]
    st.subheader("Tabla pivot dinámica")
    st.caption(
        "Cruza dos dimensiones y agrega un valor numérico. "
        "Ideal para comparar categorías por período o estado."
    )
    cat_cols = [c for c in df.columns if df[c].dtype == "object"]
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if len(cat_cols) < 2 or len(num_cols) < 1:
        st.info("Se necesitan al menos 2 columnas categóricas y 1 numérica para la tabla pivot.")
    else:
        pc1, pc2, pc3 = st.columns(3)
        pivot_row = pc1.selectbox("Filas", cat_cols, key="pivot_row")
        pivot_col = pc2.selectbox("Columnas", [c for c in cat_cols if c != pivot_row], key="pivot_col")
        pivot_val = pc3.selectbox("Valor", num_cols, key="pivot_val")
        agg = st.radio("Agregación", ["sum", "mean", "count"], horizontal=True, key="pivot_agg")
        try:
            pivot_df = pd.pivot_table(
                df,
                values=pivot_val,
                index=pivot_row,
                columns=pivot_col,
                aggfunc=agg,
                fill_value=0,
            ).round(2)
            st.dataframe(pivot_df, width="stretch", key="pivot_table")
            buf = pivot_df.to_csv().encode("utf-8")
            st.download_button(
                "Descargar pivot CSV",
                buf,
                file_name="pivot.csv",
                mime="text/csv",
                key="pivot_download",
            )
        except Exception as e:
            st.warning(f"No se pudo generar el pivot: {e}")


def _render_sub_segmentacion(ctx: dict) -> None:
    df = ctx["df"]
    date_col = ctx["date_col"]
    amount_col = ctx["amount_col"]

    st.subheader("Clustering automático de segmentos")
    st.caption(
        "Agrupa automáticamente los registros en segmentos "
        "similares usando K-means. No requiere columna de "
        "categoría — detecta patrones ocultos en los datos."
    )
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if len(num_cols) < 2:
        st.warning("Se necesitan al menos 2 columnas numéricas para clustering.")
    else:
        c1, c2 = st.columns(2)
        k_mode = c1.radio(
            "Número de clusters",
            ["Automático (método del codo)", "Manual"],
            key="k_mode", horizontal=True)
        k_manual = c2.slider(
            "K manual", 2, 8, 3,
            key="k_manual",
            disabled=(k_mode == "Automático (método del codo)"))

        selected_cols = st.multiselect(
            "Columnas para clustering",
            num_cols, default=num_cols[:min(4, len(num_cols))],
            key="cluster_cols")

        if st.button("Ejecutar clustering", key="btn_cluster"):
            with st.spinner("Calculando segmentos..."):
                n = ("auto" if "Automático" in k_mode else k_manual)
                result = auto_cluster(df, n_clusters=n, cols=selected_cols or None)

            if "error" in result:
                st.error(result["error"])
            else:
                st.session_state["cluster_result"] = result

        result = st.session_state.get("cluster_result")
        if result and "error" not in result:
            m1, m2, m3 = st.columns(3)
            m1.metric("Segmentos detectados", result["n_clusters"])
            m2.metric("Silhouette score",
                      result["silhouette"] or "N/A",
                      help="Cercano a 1 = clusters bien separados")
            m3.metric("Registros analizados", len(result["labels"]))

            st.plotly_chart(
                create_elbow_chart(result["k_range"], result["inertias"]),
                width="stretch", key="elbow_chart")

            num_cols_result = result["numeric_cols"]
            if len(num_cols_result) >= 2:
                st.subheader("Dispersión por segmento")
                ea, eb = st.columns(2)
                ax = ea.selectbox("Eje X", num_cols_result, key="cl_x")
                ay = eb.selectbox(
                    "Eje Y", num_cols_result,
                    index=min(1, len(num_cols_result) - 1),
                    key="cl_y")
                df_labeled = result["df_with_labels"]
                st.plotly_chart(
                    create_cluster_scatter(df_labeled, ax, ay),
                    width="stretch", key="cluster_scatter")

            st.subheader("Perfil de cada segmento")
            st.plotly_chart(
                create_cluster_profiles_chart(result["profiles"]),
                width="stretch", key="cluster_profiles")

            with st.expander("Ver tabla de perfiles", expanded=False):
                st.dataframe(result["profiles"], width="stretch", hide_index=True)

    st.divider()
    st.subheader("Segmentación RFM")
    st.caption(
        "Clasifica clientes según Recencia, Frecuencia y Monto. "
        "Requiere un archivo con una fila por transacción y una "
        "columna que identifique al cliente."
    )
    date_cols_all = [c for c in df.columns]

    rc1, rc2, rc3 = st.columns(3)
    rfm_id_col = rc1.selectbox("Columna de cliente", df.columns.tolist(), key="rfm_id")
    rfm_date_col = rc2.selectbox(
        "Columna de fecha", date_cols_all,
        index=date_cols_all.index(date_col) if date_col in date_cols_all else 0,
        key="rfm_date")
    rfm_amount_col = rc3.selectbox(
        "Columna de monto", date_cols_all,
        index=date_cols_all.index(amount_col) if amount_col in date_cols_all else 0,
        key="rfm_amount")

    if st.button("Calcular RFM", key="btn_rfm"):
        rfm_df = calculate_rfm(df, rfm_id_col, rfm_date_col, rfm_amount_col)
        if rfm_df.empty:
            st.warning("No se pudo calcular RFM. Verifica que "
                      "el archivo tenga múltiples transacciones "
                      "por cliente.")
        else:
            st.session_state["rfm_result"] = rfm_df

    rfm_result = st.session_state.get("rfm_result")
    if rfm_result is not None and not rfm_result.empty:
        summary = rfm_summary(rfm_result)
        m1, m2, m3 = st.columns(3)
        m1.metric("Clientes analizados", len(rfm_result))
        m2.metric("Segmentos detectados", rfm_result["segmento"].nunique())
        top_seg = summary.iloc[0]["segmento"] if not summary.empty else "—"
        m3.metric("Segmento de mayor valor", top_seg)

        st.plotly_chart(create_rfm_segment_chart(summary), width="stretch", key="rfm_segment_chart")
        st.plotly_chart(create_rfm_scatter(rfm_result), width="stretch", key="rfm_scatter")

        with st.expander("Ver tabla completa de clientes", expanded=False):
            st.dataframe(rfm_result, width="stretch", hide_index=True)
        with st.expander("Ver resumen por segmento", expanded=False):
            st.dataframe(summary, width="stretch", hide_index=True)
        with st.expander("Ver criterios de clasificación", expanded=False):
            st.markdown("""
**Cada cliente recibe 3 puntajes del 1 al 5** (por quintiles,
comparado contra el resto de los clientes):

| Puntaje | Qué mide |
|---|---|
| **R — Recencia** | Qué tan reciente fue su última compra. 5 = compró hace poco, 1 = hace mucho tiempo |
| **F — Frecuencia** | Cuántas veces compró en total. 5 = compra muy seguido, 1 = casi nunca |
| **M — Monto** | Cuánto ha gastado en total. 5 = alto gasto, 1 = bajo gasto |

**La combinación de los 3 puntajes define el segmento:**

| Segmento | Condición | Significado |
|---|---|---|
| 🏆 Champions | R≥4, F≥4, M≥4 | Compran seguido, recientemente y gastan mucho |
| 💚 Clientes leales | R≥3, F≥3, M≥3 | Buen comportamiento general |
| ⚠️ En riesgo | R≤2, F≥3, M≥3 | Antes compraban bien, hace tiempo no vuelven |
| 🆕 Nuevos | R≥4, F≤2 | Compraron hace poco, pocas veces |
| 💤 Perdidos | R≤2, F≤2, M≤2 | Hace mucho que no compran, bajo gasto |
| 🔹 Regulares | Otra combinación | No encaja claramente en las anteriores |
    """)


def _render_sub_categorias_limpieza(ctx: dict) -> None:
    df = ctx["df"]
    category_col = ctx["category_col"]

    st.subheader("Limpieza de categorías duplicadas")
    st.caption(
        "Detecta variantes de texto que probablemente representan "
        "la misma categoría — mayúsculas, espacios extra, acentos "
        "faltantes o errores de tipeo — y sugiere unificarlas."
    )
    text_cols = [
        c for c in df.columns
        if not pd.api.types.is_numeric_dtype(df[c])
        and not pd.api.types.is_datetime64_any_dtype(df[c])
    ]
    if not text_cols:
        text_cols = df.columns.tolist()
    if not text_cols:
        st.info("No se encontraron columnas de texto para analizar.")
        return

    cc1, cc2 = st.columns(2)
    cleanup_col = cc1.selectbox(
        "Columna a revisar", text_cols,
        index=text_cols.index(category_col) if category_col in text_cols else 0,
        key="cleanup_col")
    threshold = cc2.slider(
        "Sensibilidad de similitud", 0.70, 1.00, 0.85,
        step=0.01, key="cleanup_threshold",
        help="Más alto = más estricto, solo detecta "
             "variantes muy parecidas entre sí")

    if st.button("Detectar duplicados", key="btn_detect_fuzzy"):
        groups = find_similar_categories(df[cleanup_col], threshold=threshold)
        st.session_state["fuzzy_groups"] = groups
        st.session_state["fuzzy_col"] = cleanup_col

    groups = st.session_state.get("fuzzy_groups")
    stored_col = st.session_state.get("fuzzy_col")

    if groups is not None and stored_col == cleanup_col:
        if groups.empty:
            st.success("No se detectaron categorías duplicadas con este nivel de sensibilidad.")
        else:
            n_groups = groups["grupo"].nunique()
            n_variants = len(groups)
            before_unique = df[cleanup_col].nunique()
            st.warning(
                f"Se detectaron **{n_groups} grupos** de "
                f"categorías similares ({n_variants} "
                f"variantes de {before_unique} valores "
                "únicos totales).")

            st.plotly_chart(create_fuzzy_groups_chart(groups), width="stretch", key="fuzzy_chart")

            with st.expander("Ver tabla de grupos detectados", expanded=True):
                display_df = groups.copy()
                display_df["es_canonico"] = display_df["es_canonico"].map({
                    True: "✅ Sugerido como canónico",
                    False: "🔁 Variante a reemplazar",
                })
                st.dataframe(display_df, width="stretch", hide_index=True)

            if st.button("Aplicar consolidación", key="btn_apply_fuzzy"):
                mapping = build_mapping_from_groups(groups)
                cleaned_df = apply_consolidation(df, cleanup_col, mapping)
                after_unique = cleaned_df[cleanup_col].nunique()
                st.session_state["cleaned_df"] = cleaned_df
                st.success(
                    f"Consolidación aplicada: de "
                    f"**{before_unique}** a **{after_unique}** "
                    "valores únicos.")

            cleaned_df = st.session_state.get("cleaned_df")
            if cleaned_df is not None:
                st.divider()
                st.subheader("Comparación antes vs después")
                comp_a, comp_b = st.columns(2)
                with comp_a:
                    st.caption("Antes (top 10)")
                    st.dataframe(
                        df[cleanup_col].value_counts().head(10).rename("frecuencia"),
                        width="stretch")
                with comp_b:
                    st.caption("Después (top 10)")
                    st.dataframe(
                        cleaned_df[cleanup_col].value_counts().head(10).rename("frecuencia"),
                        width="stretch")

                csv_bytes = cleaned_df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    "Descargar dataset con categorías unificadas",
                    csv_bytes,
                    file_name="dataset_categorias_limpias.csv",
                    mime="text/csv",
                    key="download_cleaned")


def _render_sub_avanzado(ctx: dict) -> None:
    df = ctx["df"]
    date_col = ctx["date_col"]
    amount_col = ctx["amount_col"]
    category_col = ctx["category_col"]

    st.subheader("Análisis avanzado")
    if date_col:
        st.subheader("Comparación de períodos")
        comp_col1, comp_col2 = st.columns(2)

        with comp_col1:
            mom = period_comparison(df, date_col, amount_col, periods=1)
            if mom:
                delta_str = f"{mom['percent_change']:+.1f} %" if mom["percent_change"] is not None else "N/A"
                st.metric(
                    label=f"Último período ({mom['current_period']})",
                    value=f"${mom['current_value']:,.0f}",
                    delta=delta_str,
                    help=f"vs período anterior {mom['previous_period']}: ${mom['previous_value']:,.0f}",
                )

        with comp_col2:
            yoy = period_comparison(df, date_col, amount_col, periods=12)
            if yoy:
                delta_str = f"{yoy['percent_change']:+.1f} %" if yoy["percent_change"] is not None else "N/A"
                st.metric(
                    label=f"Variación anual ({yoy['current_period']} vs {yoy['previous_period']})",
                    value=f"${yoy['current_value']:,.0f}",
                    delta=delta_str,
                )
        st.divider()

    if date_col:
        st.subheader("Proyección de tendencia")
        st.caption(
            "Regresión lineal sobre los períodos históricos. "
            "La banda sombreada representa el intervalo de confianza del 95%."
        )
        periods_ahead = st.slider(
            "Períodos a proyectar",
            min_value=1, max_value=12, value=3,
            key="forecast_periods",
        )
        forecast = forecast_trend(df, date_col, amount_col, periods_ahead=periods_ahead)
        if forecast:
            st.session_state["forecast"] = forecast
            f_kpis = forecast_kpis(forecast)
            if f_kpis:
                k_cols = st.columns(min(len(f_kpis), 3))
                for i, kpi in enumerate(f_kpis[:3]):
                    k_cols[i].metric(
                        label=kpi["kpi"],
                        value=kpi["valor"],
                        help=kpi["interpretacion"],
                    )
            st.plotly_chart(
                create_forecast_chart(forecast),
                width="stretch",
                key="forecast_chart",
            )
            if len(f_kpis) > 3:
                with st.expander("Ver todas las proyecciones", expanded=False):
                    proj_df = pd.DataFrame(forecast["projected"])
                    proj_df.columns = ["Período", "Valor proyectado", "Límite inferior", "Límite superior"]
                    st.dataframe(proj_df, width="stretch", hide_index=True)
        else:
            st.info("Se necesitan al menos 3 períodos históricos para proyectar.")
        st.divider()

    st.subheader("Matriz de correlación")
    st.caption(
        "Detecta relaciones lineales entre columnas numéricas. "
        "Valores cercanos a 1 o -1 indican correlación fuerte."
    )
    st.plotly_chart(
        create_correlation_heatmap(df),
        width="stretch",
        key="correlation_heatmap",
    )
    st.divider()

    if category_col and amount_col:
        st.subheader("Waterfall por categoría")
        st.caption(
            "Visualiza cómo cada categoría contribuye al total. "
            "Ideal para análisis financiero y de ventas."
        )
        st.plotly_chart(
            create_waterfall(df, category_col, amount_col),
            width="stretch",
            key="waterfall_chart",
        )
        st.divider()

    if category_col:
        st.subheader("Treemap de distribución")
        object_cols = [c for c in df.columns if c != category_col and df[c].dtype == "object"]
        sub_cat_choice = st.selectbox(
            "Segunda dimensión (opcional)",
            ["Ninguna"] + object_cols,
            key="treemap_subcat",
        )
        sub_cat_col = None if sub_cat_choice == "Ninguna" else sub_cat_choice
        st.plotly_chart(
            create_treemap(df, category_col, amount_col, sub_cat_col),
            width="stretch",
            key="treemap_chart",
        )

    st.divider()
    st.subheader("Comparación Real vs Presupuesto")
    st.caption(
        "Sube un archivo de presupuesto con las mismas categorías "
        "que el dataset principal. La app compara montos reales vs esperados."
    )
    budget_file = st.file_uploader(
        "Archivo de presupuesto (CSV o Excel)",
        type=["csv", "xlsx", "xls"],
        key="budget_uploader",
    )
    if budget_file:
        try:
            df_budget = load_data(budget_file, budget_file.name)
            st.success(f"Presupuesto cargado: {len(df_budget)} filas · "
                       f"{len(df_budget.columns)} columnas")

            b1, b2, b3 = st.columns(3)
            budget_group = b1.selectbox(
                "Columna de agrupación (presupuesto)",
                df_budget.columns.tolist(), key="bg_group")
            budget_amount = b2.selectbox(
                "Columna de monto (presupuesto)",
                df_budget.columns.tolist(), key="bg_amount")
            actual_group = b3.selectbox(
                "Columna de agrupación (real)",
                df.columns.tolist(),
                index=df.columns.tolist().index(category_col) if category_col in df.columns else 0,
                key="bg_actual_group")

            if st.button("Comparar", key="btn_compare"):
                comparison = compare_vs_budget(
                    df, df_budget,
                    group_col=actual_group,
                    actual_amount_col=amount_col or df.select_dtypes(include="number").columns[0],
                    budget_amount_col=budget_amount,
                )
                if not comparison.empty:
                    total_real = comparison["real"].sum()
                    total_ppto = comparison["presupuesto"].sum()
                    varianza = total_real - total_ppto
                    cumplimiento = total_real / total_ppto * 100 if total_ppto else 0

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Total real", f"${total_real:,.0f}")
                    m2.metric("Total presupuesto", f"${total_ppto:,.0f}")
                    m3.metric("Varianza",
                              f"${varianza:,.0f}",
                              delta=f"{varianza/total_ppto*100:+.1f}%" if total_ppto else None)
                    m4.metric("Cumplimiento", f"{cumplimiento:.1f}%")

                    st.plotly_chart(create_budget_chart(comparison), width="stretch", key="budget_chart")
                    st.dataframe(comparison, width="stretch", hide_index=True)
                else:
                    st.warning("No se encontraron categorías comunes entre los dos archivos.")
        except Exception as e:
            st.error(f"Error al cargar el presupuesto: {e}")
    else:
        st.info("Sube el archivo de presupuesto para comenzar.")


def render_step_analisis(ctx: dict) -> None:
    analysis_ready = ctx["analysis_ready"]
    if not analysis_ready:
        st.info("Ejecuta el análisis para desbloquear tendencias, categorías, segmentación y más.")
        return

    sub_tabs = st.tabs([
        "Tendencias y números",
        "Categorías y Pareto",
        "Tabla pivot",
        "Segmentación",
        "Calidad de categorías",
        "Avanzado",
    ])
    with sub_tabs[0]:
        _render_sub_numerico(ctx)
    with sub_tabs[1]:
        _render_sub_categorias_pareto(ctx)
    with sub_tabs[2]:
        _render_sub_pivot(ctx)
    with sub_tabs[3]:
        _render_sub_segmentacion(ctx)
    with sub_tabs[4]:
        _render_sub_categorias_limpieza(ctx)
    with sub_tabs[5]:
        _render_sub_avanzado(ctx)


def render_step_insights(ctx: dict) -> None:
    insights = ctx["insights"]
    kpis_df = ctx["kpis_df"]
    profile = ctx["profile"]
    anomalies = ctx["anomalies"]

    st.subheader("Insights automáticos")
    render_insights(insights, kpis_df, profile, anomalies)
    with st.expander("Ver texto completo de insights", expanded=False):
        st.text_area("Resumen generado", ctx["insights_text"], height=360, key="executive_insights_text")

    st.divider()
    default_recommendations = build_default_recommendations(
        profile, ctx["warnings_df"], anomalies, ctx["amount_col"], ctx["category_col"], ctx["date_col"])
    render_recommendations(insights, default_recommendations)


def render_step_exportar(ctx: dict) -> None:
    df = ctx["df"]
    profile = ctx["profile"]
    kpis_df = ctx["kpis_df"]
    warnings_df = ctx["warnings_df"]
    anomalies = ctx["anomalies"]
    category_col = ctx["category_col"]
    amount_col = ctx["amount_col"]
    status_col = ctx["status_col"]
    date_col = ctx["date_col"]
    insights = ctx["insights"]
    insights_text = ctx["insights_text"]
    APP_TITLE = ctx["app_title"]

    st.subheader("Descargar resultados")
    export_sheets = {
        "Resumen": pd.DataFrame(
            [
                {
                    "archivo": ctx["source_filename"],
                    "tipo_analisis": ctx["analysis_type"],
                    "filas": profile["rows"],
                    "columnas": profile["columns"],
                    "faltantes_pct": profile["missing_percent"],
                    "duplicados": profile["duplicates"],
                }
            ]
        ),
        "KPIs": kpis_df,
        "Calidad de datos": warnings_df,
        "Anomalías": anomalies,
        "Ranking categoría": category_ranking(df, category_col, amount_col) if category_col else pd.DataFrame(),
        "Estados": status_summary(df, status_col, amount_col) if status_col else pd.DataFrame(),
        "Tendencia temporal": temporal_trend(df, date_col, amount_col) if date_col else pd.DataFrame(),
    }
    excel_bytes = export_excel(export_sheets, insights_text)
    pdf_figures = st.session_state.get("figures_for_pdf", {}).copy()
    saved_forecast = st.session_state.get("forecast")
    if saved_forecast:
        pdf_figures["Tendencia temporal"] = create_forecast_chart(saved_forecast)
    pdf_bytes = export_pdf(APP_TITLE, profile, kpis_df, insights, figures=pdf_figures)
    col_a, col_b = st.columns(2)
    col_a.download_button(
        "Descargar Excel",
        excel_bytes,
        file_name="ba_data_insight_resultados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
        key="download_excel",
    )
    col_b.download_button(
        "Descargar PDF ejecutivo",
        pdf_bytes,
        file_name="ba_data_insight_resumen.pdf",
        mime="application/pdf",
        width="stretch",
        key="download_pdf",
    )

    st.divider()
    st.subheader("PowerPoint ejecutivo")
    st.caption("Presentación lista para compartir con stakeholders. "
               "Incluye portada, KPIs, gráficos y insights.")
    if st.button("Generar PowerPoint", key="btn_pptx"):
        with st.spinner("Generando presentación..."):
            try:
                pptx_bytes = export_pptx(
                    title=APP_TITLE,
                    profile=profile,
                    kpis=kpis_df,
                    insights=insights,
                    figures=pdf_figures,
                    quality_score=st.session_state.get("quality_score"),
                )
                st.download_button(
                    label="Descargar .pptx",
                    data=pptx_bytes,
                    file_name="reporte_ba_insight.pptx",
                    mime="application/vnd.openxmlformats-officedocument"
                         ".presentationml.presentation",
                    key="download_pptx",
                )
                st.success("Presentación lista. Haz clic en Descargar .pptx")
            except Exception as e:
                st.error(f"Error al generar PowerPoint: {e}")
