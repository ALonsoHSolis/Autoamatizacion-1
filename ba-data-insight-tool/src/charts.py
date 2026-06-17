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
