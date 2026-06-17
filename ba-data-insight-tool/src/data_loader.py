from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import pandas as pd

from .utils import clean_column_names


def load_google_sheet(url: str) -> pd.DataFrame:
    """Load a public Google Sheet from its URL as a DataFrame.

    Accepts both /edit and /pub URLs. Converts to CSV export URL
    automatically and reads with pandas.
    """
    import re
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise ValueError(
            "URL de Google Sheets no válida. "
            "Asegúrate de que sea un enlace público con /d/ID/."
        )
    sheet_id = match.group(1)
    gid = "0"
    gid_match = re.search(r"gid=(\d+)", url)
    if gid_match:
        gid = gid_match.group(1)
    csv_url = (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        f"/export?format=csv&gid={gid}"
    )
    try:
        df = pd.read_csv(csv_url)
    except Exception as exc:
        raise ValueError(
            "No se pudo cargar el Google Sheet. "
            "Verifica que el archivo es público (Cualquiera con el enlace)."
        ) from exc
    if df.empty:
        raise ValueError("El Google Sheet está vacío.")
    return clean_column_names(df)


def get_excel_sheets(file: BinaryIO | BytesIO | str | Path) -> list[str]:
    try:
        return pd.ExcelFile(file).sheet_names
    except Exception as exc:
        raise ValueError("No se pudieron leer las hojas del archivo Excel.") from exc


def load_data(file: BinaryIO | BytesIO | str | Path, filename: str | None = None, sheet_name: str | None = None) -> pd.DataFrame:
    name = (filename or str(file)).lower()
    try:
        if name.endswith(".csv"):
            df = _read_csv(file)
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file, sheet_name=sheet_name or 0)
        else:
            raise ValueError("Formato no soportado. Sube un archivo CSV, XLSX o XLS.")
    except pd.errors.EmptyDataError as exc:
        raise ValueError("El archivo está vacío o no contiene datos tabulares.") from exc
    except Exception as exc:
        raise ValueError(f"No se pudo cargar el archivo: {exc}") from exc

    if df.empty:
        raise ValueError("El archivo no contiene filas para analizar.")
    if len(df.columns) == 0:
        raise ValueError("El archivo no contiene columnas válidas.")
    return clean_column_names(df)


def _read_csv(file: BinaryIO | BytesIO | str | Path) -> pd.DataFrame:
    attempts = [
        {"encoding": "utf-8-sig", "sep": None, "engine": "python"},
        {"encoding": "latin-1", "sep": None, "engine": "python"},
        {"encoding": "utf-8-sig"},
    ]
    last_error: Exception | None = None
    for kwargs in attempts:
        try:
            if hasattr(file, "seek"):
                file.seek(0)
            return pd.read_csv(file, **kwargs)
        except UnicodeDecodeError as exc:
            last_error = exc
        except pd.errors.ParserError as exc:
            last_error = exc
    raise ValueError(f"No se pudo interpretar el CSV. Revisa separador, encoding o estructura. Detalle: {last_error}")
