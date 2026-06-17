from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import pandas as pd

from .utils import normalize_name, parse_date_series, parse_numeric_series, strip_accents, validate_chilean_rut


KEYWORDS = {
    "date": ["fecha", "date", "created_at", "paid_at", "transferido", "nacimiento"],
    "amount": ["monto", "total", "valor", "pago", "pagado", "ingreso", "egreso", "venta", "amount", "price", "ventas"],
    "status": ["estado", "status", "situacion", "situación"],
    "category": ["unidad", "categoria", "categoría", "tipo", "segmento", "banco", "partner", "canal"],
    "id": ["id", "identificador", "transaccion", "transacción", "transaction_id", "rut", "email", "comprobante"],
    "name": ["nombre", "cliente", "beneficiario", "persona", "apoderado"],
    "phone": ["telefono", "teléfono", "phone", "celular"],
    "email": ["email", "correo", "mail"],
    "rut": ["rut"],
}


@dataclass
class QualityWarning:
    severity: str
    column: str
    issue: str
    detail: str


def _contains_keyword(column: str, key: str) -> bool:
    normalized = normalize_name(column)
    tokens = set(normalized.split("_"))
    for word in KEYWORDS[key]:
        keyword = normalize_name(word)
        if len(keyword) <= 2:
            if keyword in tokens:
                return True
            continue
        if keyword in normalized:
            return True
    return False


def detect_columns(df: pd.DataFrame) -> dict[str, list[str]]:
    detected: dict[str, list[str]] = {
        "numeric": [],
        "categorical": [],
        "date": [],
        "amount": [],
        "status": [],
        "category": [],
        "id": [],
        "name": [],
        "email": [],
        "rut": [],
        "phone": [],
    }
    row_count = max(len(df), 1)
    for col in df.columns:
        series = df[col]
        numeric_ratio = parse_numeric_series(series).notna().mean()
        date_ratio = parse_date_series(series).notna().mean() if not pd.api.types.is_numeric_dtype(series) else 0
        unique_ratio = series.nunique(dropna=True) / row_count
        lower_col = strip_accents(col.lower())
        is_numeric = pd.api.types.is_numeric_dtype(series) or numeric_ratio >= 0.75
        is_date_candidate = date_ratio >= 0.65 or _contains_keyword(col, "date")

        if is_numeric:
            detected["numeric"].append(col)
        if is_date_candidate:
            detected["date"].append(col)
        if not is_date_candidate and (_contains_keyword(col, "amount") or (numeric_ratio >= 0.75 and any(x in lower_col for x in ["total", "valor", "monto"]))):
            detected["amount"].append(col)
        if _contains_keyword(col, "status") or (series.dtype == "object" and 1 < series.nunique(dropna=True) <= 12):
            detected["status"].append(col)
        if _contains_keyword(col, "category") or (series.dtype == "object" and 2 <= series.nunique(dropna=True) <= 30):
            detected["category"].append(col)
            detected["categorical"].append(col)
        elif series.dtype == "object":
            detected["categorical"].append(col)
        if _contains_keyword(col, "id") or (series.dtype == "object" and unique_ratio > 0.9 and row_count >= 10):
            detected["id"].append(col)
        for key in ("name", "email", "rut", "phone"):
            if _contains_keyword(col, key) and (key != "name" or not is_numeric):
                detected[key].append(col)
    return {key: list(dict.fromkeys(value)) for key, value in detected.items()}


def profile_dataset(df: pd.DataFrame) -> dict[str, Any]:
    detected = detect_columns(df)
    total_cells = max(df.shape[0] * df.shape[1], 1)
    return {
        "rows": len(df),
        "columns": len(df.columns),
        "numeric_columns": detected["numeric"],
        "categorical_columns": detected["categorical"],
        "date_columns": detected["date"],
        "missing_percent": round(float(df.isna().sum().sum() / total_cells * 100), 2),
        "duplicates": int(df.duplicated().sum()),
        "detected": detected,
        "dtypes": pd.DataFrame({"columna": df.columns, "tipo": [str(df[c].dtype) for c in df.columns]}),
    }


def quality_warnings(df: pd.DataFrame, detected: dict[str, list[str]]) -> list[QualityWarning]:
    warnings: list[QualityWarning] = []
    rows = max(len(df), 1)
    duplicate_count = int(df.duplicated().sum())
    if duplicate_count:
        warnings.append(QualityWarning("Media", "dataset", "Registros duplicados", f"{duplicate_count} filas duplicadas detectadas."))

    for col in df.columns:
        series = df[col]
        null_pct = series.isna().mean() * 100
        is_key_column = col in detected.get("id", []) + detected.get("amount", []) + detected.get("date", []) + detected.get("status", [])
        if null_pct == 100:
            warnings.append(QualityWarning("Alta", col, "Columna vacía", "La columna está completamente vacía."))
        elif null_pct >= 30:
            warnings.append(QualityWarning("Alta", col, "Muchos valores nulos", f"{null_pct:.1f}% de valores faltantes."))
        elif is_key_column and null_pct >= 10:
            warnings.append(QualityWarning("Media", col, "Valores nulos en columna clave", f"{null_pct:.1f}% de valores faltantes en una columna relevante."))
        elif null_pct > 0:
            warnings.append(QualityWarning("Baja", col, "Valores nulos", f"{null_pct:.1f}% de valores faltantes."))

        unique = series.nunique(dropna=True)
        if unique == 1 and rows > 1:
            warnings.append(QualityWarning("Baja", col, "Un solo valor", "No aporta segmentación para el análisis."))
        if series.dtype == "object" and unique / rows > 0.85 and col not in detected.get("id", []):
            warnings.append(QualityWarning("Baja", col, "Alta cardinalidad", "Tiene muchos valores únicos."))
        if series.dtype == "object" and series.dropna().astype(str).str.contains(r"^\s+|\s+$", regex=True).any():
            warnings.append(QualityWarning("Baja", col, "Espacios extra", "Hay textos con espacios al inicio o final."))

    for col in detected.get("date", []):
        invalid = parse_date_series(df[col]).isna() & df[col].notna()
        if invalid.any():
            warnings.append(QualityWarning("Media", col, "Fechas inválidas", f"{int(invalid.sum())} valores no se pudieron interpretar como fecha."))

    for col in detected.get("amount", []):
        values = parse_numeric_series(df[col])
        if (values < 0).any():
            warnings.append(QualityWarning("Media", col, "Montos negativos", f"{int((values < 0).sum())} registros con monto negativo."))
        if (values == 0).any():
            warnings.append(QualityWarning("Baja", col, "Montos en cero", f"{int((values == 0).sum())} registros con monto cero."))

    for col in detected.get("email", []):
        invalid = ~df[col].dropna().astype(str).str.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        if invalid.any():
            warnings.append(QualityWarning("Media", col, "Emails inválidos", f"{int(invalid.sum())} correos con formato sospechoso."))

    for col in detected.get("rut", []):
        invalid_count = int(df[col].dropna().apply(lambda x: not validate_chilean_rut(x)).sum())
        if invalid_count:
            warnings.append(QualityWarning("Media", col, "RUT inválido", f"{invalid_count} RUT no pasan validación de dígito verificador."))

    for col in detected.get("phone", []):
        digits = df[col].dropna().astype(str).str.replace(r"\D", "", regex=True)
        suspicious = digits.apply(lambda x: len(x) < 8 or len(x) > 12)
        if suspicious.any():
            warnings.append(QualityWarning("Baja", col, "Teléfono sospechoso", f"{int(suspicious.sum())} teléfonos tienen largo inusual."))
    return warnings


def warnings_to_frame(warnings: list[QualityWarning]) -> pd.DataFrame:
    return pd.DataFrame([w.__dict__ for w in warnings], columns=["severity", "column", "issue", "detail"])


def calculate_quality_score(profile: dict, warnings: list) -> dict:
    """Return a quality score from 0 to 100 with label and color.

    Penalties:
    - missing_percent:    up to -30 pts  (linear: 0%=0, 30%+=30)
    - duplicates ratio:   up to -20 pts  (linear: 0%=0, 20%+=20)
    - high warnings:      -10 pts each   (max -30, includes empty columns)
    - medium warnings:    -4 pts each    (max -20)
    - single-value cols:  -3 pts each    (max -15)
    """
    score = 100
    score -= min(profile.get("missing_percent", 0), 30)
    rows = max(profile.get("rows", 1), 1)
    dup_ratio = profile.get("duplicates", 0) / rows * 100
    score -= min(dup_ratio, 20)
    high = sum(1 for w in warnings if w.severity == "Alta")
    med = sum(1 for w in warnings if w.severity == "Media")
    single_value = sum(1 for w in warnings if w.issue == "Un solo valor")
    score -= min(high * 10, 30)
    score -= min(med * 4, 20)
    score -= min(single_value * 3, 15)
    score = max(int(score), 0)
    if score >= 80:
        label, color = "Buena", "normal"
    elif score >= 55:
        label, color = "Regular", "inverse"
    else:
        label, color = "Crítica", "off"
    return {"score": score, "label": label, "color": color} 