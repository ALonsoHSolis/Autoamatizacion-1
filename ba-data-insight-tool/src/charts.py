from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from .kpi_engine import category_ranking, pareto_analysis, status_summary, temporal_trend
from .utils import parse_numeric_series


PALETTE = [
    "#3B8BD4",  # blue
    "#1D9E75",  # teal
    "#EF9F27",  # amber
    "#D85A30",  # coral
    "#7F77DD",  # purple
    "#D4537E",  # pink
    "#639922",  # green
    "#888780",  # gray
]


def create_temporal_chart(df: pd.DataFrame, date_col: str, amount_col: str | None = None) -> go.Figure:
    trend = temporal_trend(df, date_col, amount_col)
    fig = px.line(trend, x="periodo", y="valor", markers=True, title="Tendencia temporal", color_discrete_sequence=[PALETTE[0]])
    fig.update_layout(xaxis_title="Periodo", yaxis_title="Valor", hovermode="x unified")
    return fig


def create_category_chart(df: pd.DataFrame, category_col: str, amount_col: str | None = None) -> go.Figure:
    ranking = category_ranking(df, category_col, amount_col)
    fig = px.bar(ranking, x="valor", y="categoria", orientation="h", title="Top categorías", color_discrete_sequence=[PALETTE[0]])
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="Valor", yaxis_title="")
    return fig


def create_status_chart(df: pd.DataFrame, status_col: str, amount_col: str | None = None) -> go.Figure:
    summary = status_summary(df, status_col, amount_col)
    fig = px.pie(summary, values="registros", names="estado", hole=0.45, title="Distribución por estado", color_discrete_sequence=PALETTE)
    return fig


def create_amount_distribution(df: pd.DataFrame, amount_col: str) -> go.Figure:
    values = parse_numeric_series(df[amount_col])
    fig = px.histogram(values.dropna(), nbins=25, title="Distribución de montos", color_discrete_sequence=[PALETTE[0]])
    fig.update_layout(showlegend=False, xaxis_title=amount_col, yaxis_title="Frecuencia")
    return fig


def create_boxplot(df: pd.DataFrame, amount_col: str) -> go.Figure:
    values = parse_numeric_series(df[amount_col])
    fig = px.box(values.dropna(), points="outliers", title="Valores extremos", color_discrete_sequence=[PALETTE[0]])
    fig.update_layout(showlegend=False, yaxis_title=amount_col)
    return fig


def create_null_heatmap(df: pd.DataFrame) -> go.Figure:
    matrix = df.isna().astype(int)
    fig = px.imshow(matrix, aspect="auto", title="Mapa de datos faltantes", color_continuous_scale=["#f4f7fb", "#cc2f4a"])
    fig.update_layout(xaxis_title="Columnas", yaxis_title="Filas")
    return fig


def create_correlation_heatmap(df: pd.DataFrame) -> go.Figure:
    """Pearson correlation matrix for all numeric columns.

    Returns an informative empty figure when fewer than 2 numeric columns
    are available so callers do not need to guard against errors.
    """
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.shape[1] < 2:
        fig = go.Figure()
        fig.update_layout(title="Se necesitan al menos 2 columnas numéricas para la matriz de correlación.")
        return fig

    corr = numeric_df.corr().round(2)
    fig = px.imshow(
        corr,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Matriz de correlación (Pearson)",
    )
    fig.update_layout(
        xaxis_title="",
        yaxis_title="",
        coloraxis_colorbar=dict(title="r", tickformat=".1f"),
    )
    return fig


def create_waterfall(
    df: pd.DataFrame,
    category_col: str,
    amount_col: str,
    top_n: int = 12,
) -> go.Figure:
    """Waterfall chart showing the contribution of each category to the total.

    Categories with positive net values are shown in teal; negative in coral.
    A final "Total" bar summarises the sum.
    """
    if not category_col or not amount_col or category_col not in df or amount_col not in df:
        fig = go.Figure()
        fig.update_layout(title="Selecciona columnas de categoría y monto para el waterfall.")
        return fig

    values = parse_numeric_series(df[amount_col])
    summary = (
        pd.DataFrame({"categoria": df[category_col].fillna("Sin categoría"), "valor": values})
        .groupby("categoria", as_index=False)["valor"]
        .sum()
        .sort_values("valor", ascending=False)
        .head(top_n)
    )

    categories = summary["categoria"].tolist()
    amounts = summary["valor"].tolist()
    measure = ["relative"] * len(categories) + ["total"]
    x_labels = categories + ["Total"]
    y_values = amounts + [sum(amounts)]

    fig = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=measure,
            x=x_labels,
            y=y_values,
            connector={"line": {"color": "#B4B2A9", "width": 1}},
            increasing={"marker": {"color": PALETTE[1]}},
            decreasing={"marker": {"color": PALETTE[3]}},
            totals={"marker": {"color": PALETTE[0]}},
            text=[f"{v:,.0f}" for v in y_values],
            textposition="outside",
        )
    )
    fig.update_layout(
        title=f"Waterfall: distribución por {category_col} (top {top_n})",
        showlegend=False,
        yaxis_title="Valor",
        xaxis_title="",
    )
    return fig


def create_pareto_chart(
    df: pd.DataFrame,
    category_col: str,
    amount_col: str | None = None,
    top_n: int = 15,
) -> go.Figure:
    """Combined bar + cumulative line Pareto chart with ABC segmentation.

    The 80 % and 95 % thresholds are marked with dashed horizontal reference
    lines so the A/B/C cut-off is immediately visible to the user.
    """
    if not category_col or category_col not in df:
        fig = go.Figure()
        fig.update_layout(title="Selecciona una columna de categoría para el análisis de Pareto.")
        return fig

    pareto = pareto_analysis(df, category_col, amount_col).head(top_n)
    if pareto.empty:
        fig = go.Figure()
        fig.update_layout(title="Sin datos para el análisis de Pareto.")
        return fig

    segment_colors = {"A": PALETTE[1], "B": PALETTE[2], "C": PALETTE[3]}
    bar_colors = [segment_colors[s] for s in pareto["segmento"]]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            name="Valor",
            x=pareto["categoria"],
            y=pareto["valor"],
            marker_color=bar_colors,
            yaxis="y",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="% Acumulado",
            x=pareto["categoria"],
            y=pareto["acumulado_pct"],
            mode="lines+markers",
            line={"color": PALETTE[6], "width": 2},
            marker={"size": 6},
            yaxis="y2",
        )
    )

    for threshold, label in [(80, "Límite A (80%)"), (95, "Límite B (95%)")]:
        fig.add_hline(
            y=threshold,
            yref="y2",
            line_dash="dash",
            line_color="#888780",
            annotation_text=label,
            annotation_position="top right",
        )

    fig.update_layout(
        title=f"Análisis de Pareto / ABC - {category_col}",
        yaxis=dict(title="Valor"),
        yaxis2=dict(
            title="% Acumulado",
            overlaying="y",
            side="right",
            range=[0, 105],
            ticksuffix="%",
        ),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def create_treemap(
    df: pd.DataFrame,
    category_col: str,
    amount_col: str | None = None,
    sub_category_col: str | None = None,
) -> go.Figure:
    """Treemap showing relative weight of each category and optional subcategory.

    If sub_category_col is provided the treemap shows two levels of hierarchy.
    Absolute values are used so that negative amounts do not break the chart.
    """
    if not category_col or category_col not in df:
        fig = go.Figure()
        fig.update_layout(title="Selecciona una columna de categoría para el treemap.")
        return fig

    path_cols = [category_col]
    if sub_category_col and sub_category_col in df and sub_category_col != category_col:
        path_cols.append(sub_category_col)

    plot_df = df[path_cols].copy()
    plot_df["valor"] = (
        parse_numeric_series(df[amount_col]).abs()
        if amount_col and amount_col in df
        else pd.Series(1, index=df.index, dtype="float64")
    )
    plot_df = plot_df.dropna(subset=["valor"])
    for col in path_cols:
        plot_df[col] = plot_df[col].fillna("Sin dato").astype(str)

    fig = px.treemap(
        plot_df,
        path=path_cols,
        values="valor",
        title=f"Treemap: distribución por {' > '.join(path_cols)}",
        color_discrete_sequence=PALETTE,
    )
    fig.update_traces(textinfo="label+percent parent")
    return fig


def create_forecast_chart(forecast: dict) -> "go.Figure":
    """Render historical trend + linear projection with confidence band.

    Args:
        forecast: result dict from kpi_engine.forecast_trend()

    Returns:
        Plotly Figure with 4 traces:
          1. Historical values (solid blue line)
          2. Confidence band fill (light amber area)
          3. Projected values (dashed amber line)
          4. Vertical divider annotation
    """
    if not forecast or not forecast.get("historical"):
        fig = go.Figure()
        fig.update_layout(title="Sin datos suficientes para proyección.")
        return fig

    hist = forecast["historical"]
    proj = forecast["projected"]

    def _to_pydatetime(value):
        return value.to_pydatetime() if hasattr(value, "to_pydatetime") else value

    hist_x = [_to_pydatetime(h["periodo"]) for h in hist]
    hist_y = [h["valor"]   for h in hist]
    proj_x = [_to_pydatetime(p["periodo"]) for p in proj]
    proj_y = [p["valor"]   for p in proj]
    lower  = [p["lower"]   for p in proj]
    upper  = [p["upper"]   for p in proj]

    fig = go.Figure()

    # Confidence band
    fig.add_trace(go.Scatter(
        x=proj_x + proj_x[::-1],
        y=upper + lower[::-1],
        fill="toself",
        fillcolor="rgba(239,159,39,0.15)",
        line=dict(color="rgba(0,0,0,0)"),
        hoverinfo="skip",
        showlegend=True,
        name="Banda de confianza 95%",
    ))

    # Historical line
    fig.add_trace(go.Scatter(
        x=hist_x, y=hist_y,
        mode="lines+markers",
        name="Histórico",
        line=dict(color=PALETTE[0], width=2.5),
        marker=dict(size=5),
    ))

    # Projected line
    # Connect last historical point to first projected
    conn_x = [hist_x[-1]] + proj_x
    conn_y = [hist_y[-1]] + proj_y
    fig.add_trace(go.Scatter(
        x=conn_x, y=conn_y,
        mode="lines+markers",
        name="Proyección",
        line=dict(color=PALETTE[2], width=2.5, dash="dot"),
        marker=dict(size=6, symbol="diamond"),
    ))

    # Vertical divider at last historical point
    fig.add_vline(
        x=hist_x[-1],
        line_dash="dash",
        line_color=PALETTE[7],
        annotation_text="Hoy",
        annotation_position="top right",
    )

    direction = forecast.get("direction", "")
    r2 = forecast.get("r_squared", 0)
    pct = abs(forecast.get("trend_pct", 0))
    title = (f"Tendencia {'📈' if direction=='creciente' else '📉' if direction=='decreciente' else '➡️'} "
             f"{direction} · {pct:.1f}% por período · R²={r2:.2f}")

    fig.update_layout(
        title=title,
        xaxis_title="Período",
        yaxis_title="Valor",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom",
                    y=1.02, xanchor="right", x=1),
    )
    return fig


def create_budget_chart(comparison_df: "pd.DataFrame") -> "go.Figure":
    """Grouped bar chart: Real vs Presupuesto by group."""
    import plotly.graph_objects as go
    if comparison_df.empty:
        fig = go.Figure()
        fig.update_layout(title="Sin datos para comparar.")
        return fig

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Real",
        x=comparison_df["grupo"],
        y=comparison_df["real"],
        marker_color=PALETTE[0],
        text=comparison_df["cumplimiento_pct"].apply(
            lambda v: f"{v:.0f}%" if v is not None else ""),
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="Presupuesto",
        x=comparison_df["grupo"],
        y=comparison_df["presupuesto"],
        marker_color=PALETTE[2],
        opacity=0.7,
    ))
    fig.update_layout(
        title="Real vs Presupuesto por categoría",
        barmode="group",
        xaxis_title="",
        yaxis_title="Valor",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom",
                    y=1.02, xanchor="right", x=1),
    )
    return fig


def create_elbow_chart(k_range: list, inertias: list) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(k_range), y=inertias,
        mode="lines+markers",
        line=dict(color=PALETTE[0], width=2),
        marker=dict(size=8),
        name="Inercia",
    ))
    fig.update_layout(
        title="Método del codo — número óptimo de clusters",
        xaxis_title="Número de clusters (K)",
        yaxis_title="Inercia",
        hovermode="x unified",
    )
    return fig


def create_cluster_scatter(
    df_labeled: pd.DataFrame,
    col_x: str,
    col_y: str,
) -> go.Figure:
    fig = px.scatter(
        df_labeled, x=col_x, y=col_y,
        color="cluster",
        color_discrete_sequence=PALETTE,
        title=f"Clusters: {col_x} vs {col_y}",
        hover_data=df_labeled.columns.tolist(),
    )
    fig.update_traces(marker=dict(size=8, opacity=0.8))
    fig.update_layout(legend_title="Segmento")
    return fig


def create_cluster_profiles_chart(profiles: pd.DataFrame) -> go.Figure:
    numeric_cols = [c for c in profiles.columns
                    if c not in ["segmento", "registros", "pct"]]
    fig = go.Figure()
    for i, col in enumerate(numeric_cols):
        fig.add_trace(go.Bar(
            name=col,
            x=profiles["segmento"],
            y=profiles[col],
            marker_color=PALETTE[i % len(PALETTE)],
        ))
    fig.update_layout(
        title="Perfil promedio por segmento",
        barmode="group",
        xaxis_title="",
        yaxis_title="Valor promedio",
        legend_title="Variable",
    )
    return fig


def create_rfm_scatter(rfm_df: pd.DataFrame) -> go.Figure:
    """Scatter: Recency vs Frequency, sized by Monetary, colored by segment."""
    fig = px.scatter(
        rfm_df, x="recency_days", y="frequency",
        size="monetary", color="segmento",
        color_discrete_sequence=PALETTE,
        hover_data=["cliente", "monetary"],
        title="Mapa de clientes: Recencia vs Frecuencia",
        labels={
            "recency_days": "Días desde última compra",
            "frequency": "Cantidad de compras",
        },
    )
    fig.update_layout(legend_title="Segmento")
    return fig


def create_rfm_segment_chart(summary_df: pd.DataFrame) -> go.Figure:
    """Bar chart: number of clients and monetary value per segment."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Clientes",
        x=summary_df["segmento"],
        y=summary_df["clientes"],
        marker_color=PALETTE[0],
        yaxis="y",
    ))
    fig.add_trace(go.Scatter(
        name="Monto total",
        x=summary_df["segmento"],
        y=summary_df["monetary_total"],
        mode="lines+markers",
        line=dict(color=PALETTE[3], width=2),
        marker=dict(size=8),
        yaxis="y2",
    ))
    fig.update_layout(
        title="Clientes y valor por segmento",
        yaxis=dict(title="Cantidad de clientes"),
        yaxis2=dict(title="Monto total", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom",
                    y=1.02, xanchor="right", x=1),
    )
    return fig


def create_fuzzy_groups_chart(groups_df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of variants within each duplicate group.

    Bars colored teal mark the suggested canonical value;
    coral marks the variants to be replaced.
    """
    if groups_df.empty:
        fig = go.Figure()
        fig.update_layout(title="No se detectaron categorías duplicadas.")
        return fig

    plot_df = groups_df.copy()
    plot_df["label"] = (
        "Grupo " + plot_df["grupo"].astype(str) + ": " + plot_df["valor"]
    )
    colors = [
        PALETTE[1] if canon else PALETTE[3]
        for canon in plot_df["es_canonico"]
    ]

    fig = go.Figure(go.Bar(
        x=plot_df["frecuencia"],
        y=plot_df["label"],
        orientation="h",
        marker_color=colors,
        text=plot_df["frecuencia"],
        textposition="outside",
    ))
    fig.update_layout(
        title="Variantes detectadas (verde = sugerido como canónico)",
        xaxis_title="Frecuencia",
        yaxis_title="",
        yaxis={"categoryorder": "total ascending"},
        showlegend=False,
    )
    return fig


def create_batch_summary_chart(summary_df: pd.DataFrame) -> go.Figure:
    """Bar chart showing rows contributed by each file in a batch upload."""
    if summary_df.empty:
        fig = go.Figure()
        fig.update_layout(title="Sin archivos para mostrar.")
        return fig

    fig = go.Figure(go.Bar(
        x=summary_df["archivo"],
        y=summary_df["filas"],
        marker_color=PALETTE[0],
        text=summary_df["filas"],
        textposition="outside",
    ))
    fig.update_layout(
        title="Filas aportadas por cada archivo",
        xaxis_title="",
        yaxis_title="Cantidad de filas",
        showlegend=False,
    )
    return fig
