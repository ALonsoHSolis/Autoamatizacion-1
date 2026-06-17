from __future__ import annotations

import re
import unicodedata
from typing import Any

import pandas as pd


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value))
    return "".join(char for char in normalized if not unicodedata.combining(char))


def normalize_name(value: str) -> str:
    text = strip_accents(str(value).strip().lower())
    text = re.sub(r"[^a-z0-9_]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    names: list[str] = []
    seen: dict[str, int] = {}
    for idx, col in enumerate(cleaned.columns):
        name = normalize_name(col) if str(col).strip() else f"columna_{idx + 1}"
        seen[name] = seen.get(name, 0) + 1
        names.append(name if seen[name] == 1 else f"{name}_{seen[name]}")
    cleaned.columns = names
    return cleaned


def parse_numeric_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    def parse_value(value: Any) -> float | None:
        if pd.isna(value):
            return None
        text = str(value).strip()
        if not text or text.lower() in {"nan", "none", "null"}:
            return None
        negative = text.startswith("(") and text.endswith(")")
        text = re.sub(r"(?i)\b(clp|usd|eur|cop|ars|mxn)\b", "", text)
        if re.search(r"[A-Za-z]", text):
            return None
        text = re.sub(r"[^\d,.\-]", "", text)
        if negative:
            text = f"-{text.strip('()')}"
        if not text or text in {"-", ".", ","}:
            return None

        last_dot = text.rfind(".")
        last_comma = text.rfind(",")
        if last_dot >= 0 and last_comma >= 0:
            decimal_sep = "." if last_dot > last_comma else ","
            thousands_sep = "," if decimal_sep == "." else "."
            text = text.replace(thousands_sep, "").replace(decimal_sep, ".")
        elif last_comma >= 0:
            decimals = len(text) - last_comma - 1
            text = text.replace(",", ".") if decimals in {1, 2} else text.replace(",", "")
        elif last_dot >= 0:
            decimals = len(text) - last_dot - 1
            if decimals == 3 and text.count(".") == 1:
                text = text.replace(".", "")
            elif text.count(".") > 1:
                text = text.replace(".", "")
        try:
            return float(text)
        except ValueError:
            return None

    return series.apply(parse_value).astype("float64")


def parse_date_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")

    raw = series.copy()
    cleaned = raw.astype("string").str.strip()
    cleaned = cleaned.mask(cleaned.str.lower().isin(["", "nan", "none", "null"]))

    iso_like = cleaned.str.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}", na=False)
    parsed_iso = pd.to_datetime(cleaned.where(iso_like), errors="coerce", yearfirst=True)
    parsed_local = pd.to_datetime(cleaned.where(~iso_like), errors="coerce", dayfirst=True, format="mixed")
    parsed = parsed_iso.combine_first(parsed_local)

    numeric = pd.to_numeric(cleaned, errors="coerce")
    excel_like = numeric.between(20_000, 80_000)
    if excel_like.any():
        excel_dates = pd.to_datetime(numeric.where(excel_like), unit="D", origin="1899-12-30", errors="coerce")
        parsed = parsed.combine_first(excel_dates)
    return parsed


def format_number(value: Any) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(number) >= 1000:
        return f"{number:,.0f}".replace(",", ".")
    return f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_currency(value: Any, symbol: str = "$") -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)
    sign = "-" if number < 0 else ""
    return f"{sign}{symbol}{format_number(abs(number))}"


def format_percent(value: Any) -> str:
    try:
        return f"{float(value):.1f}%".replace(".", ",")
    except (TypeError, ValueError):
        return "N/A"


def validate_chilean_rut(rut: Any) -> bool:
    raw = re.sub(r"[^0-9kK]", "", str(rut or ""))
    if len(raw) < 2:
        return False
    body, check_digit = raw[:-1], raw[-1].upper()
    if not body.isdigit():
        return False
    factors = [2, 3, 4, 5, 6, 7]
    total = 0
    for i, digit in enumerate(reversed(body)):
        total += int(digit) * factors[i % len(factors)]
    expected = 11 - (total % 11)
    expected_digit = "0" if expected == 11 else "K" if expected == 10 else str(expected)
    return check_digit == expected_digit


def dataframe_to_records(df: pd.DataFrame, max_rows: int = 500) -> list[dict[str, Any]]:
    safe = df.head(max_rows).copy()
    for col in safe.columns:
        if pd.api.types.is_datetime64_any_dtype(safe[col]):
            safe[col] = safe[col].dt.strftime("%Y-%m-%d")
    return safe.where(pd.notnull(safe), None).to_dict("records")
