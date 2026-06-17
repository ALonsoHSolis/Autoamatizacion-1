from __future__ import annotations

import pandas as pd

from .utils import parse_numeric_series


def detect_anomalies(df: pd.DataFrame, amount_col: str | None, threshold: float = 2.0) -> pd.DataFrame:
    if not amount_col or amount_col not in df:
        return pd.DataFrame()
    values = parse_numeric_series(df[amount_col])
    std = values.std()
    mean = values.mean()
    if pd.isna(std) or std == 0:
        return pd.DataFrame()
    z_score = (values - mean).abs() / std
    anomalies = df.loc[z_score > threshold].copy()
    if anomalies.empty:
        return anomalies
    anomalies["valor_analizado"] = values.loc[anomalies.index]
    anomalies["z_score"] = z_score.loc[anomalies.index].round(2)
    anomalies["promedio_referencia"] = round(float(mean), 2)
    anomalies["limite_inferior"] = round(float(mean - threshold * std), 2)
    anomalies["limite_superior"] = round(float(mean + threshold * std), 2)
    anomalies["tipo_desvio"] = anomalies["valor_analizado"].apply(lambda value: "Sobre el rango esperado" if value > mean else "Bajo el rango esperado")
    anomalies["motivo"] = anomalies["z_score"].apply(lambda z: f"Valor a más de {z:.2f} desviaciones estándar del promedio.")
    return anomalies.sort_values("z_score", ascending=False)
