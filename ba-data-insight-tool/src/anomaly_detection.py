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


def detect_anomalies_iforest(
    df: pd.DataFrame,
    cols: list[str] | None = None,
    contamination: float = 0.05,
    random_state: int = 42,
) -> pd.DataFrame:
    """Detect anomalies using Isolation Forest.

    Unlike Z-score, this method can use multiple numeric columns
    at once and doesn't assume a normal distribution. Good for
    detecting unusual *combinations* of values, not just extreme
    single values.

    Args:
        df:            Source DataFrame.
        cols:          Numeric columns to use. Auto-selects if None
                       (all numeric columns with 3+ unique values).
        contamination: Expected proportion of anomalies (0.01-0.5).
        random_state:  Seed for reproducibility.

    Returns:
        DataFrame with original rows flagged as anomalies, plus:
          anomaly_score: raw isolation score (lower = more anomalous)
          severity: "Alta" | "Media" based on score percentile
    """
    from sklearn.ensemble import IsolationForest
    from .utils import parse_numeric_series

    if cols is None:
        cols = []
        for col in df.select_dtypes(include="number").columns:
            if df[col].dropna().nunique() >= 3:
                cols.append(col)

    if len(cols) == 0:
        return pd.DataFrame()

    subset = pd.DataFrame({
        col: parse_numeric_series(df[col]) for col in cols
    })
    subset = subset.dropna()

    if len(subset) < 10:
        return pd.DataFrame()

    model = IsolationForest(
        contamination=contamination,
        random_state=random_state,
        n_estimators=100,
    )
    predictions = model.fit_predict(subset)
    scores = model.score_samples(subset)

    anomaly_mask = predictions == -1
    if not anomaly_mask.any():
        return pd.DataFrame()

    anomaly_indices = subset.index[anomaly_mask]
    result = df.loc[anomaly_indices].copy()
    result["anomaly_score"] = scores[anomaly_mask].round(4)

    # Lower score = more anomalous. Flag bottom 30% as "Alta"
    threshold = result["anomaly_score"].quantile(0.3)
    result["severity"] = result["anomaly_score"].apply(
        lambda s: "Alta" if s <= threshold else "Media"
    )
    result["motivo"] = (
        "Combinación atípica detectada en: " + ", ".join(cols)
    )

    return result.sort_values("anomaly_score")
