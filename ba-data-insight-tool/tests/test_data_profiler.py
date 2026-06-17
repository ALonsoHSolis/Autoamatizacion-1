import pandas as pd

from src.data_profiler import detect_columns, profile_dataset, quality_warnings
from src.utils import parse_date_series, validate_chilean_rut


def test_detect_columns_by_name_and_content():
    df = pd.DataFrame(
        {
            "fecha_pago": ["2025-01-01", "2025-02-01"],
            "monto_pagado": ["1.000", "2.000"],
            "estado": ["Pagado", "Pendiente"],
            "rut": ["12.345.678-5", "11111111-1"],
        }
    )
    detected = detect_columns(df)
    assert "fecha_pago" in detected["date"]
    assert "monto_pagado" in detected["amount"]
    assert "estado" in detected["status"]
    assert "rut" in detected["rut"]


def test_validate_chilean_rut_accepts_common_formats():
    assert validate_chilean_rut("12.345.678-5")
    assert validate_chilean_rut("123456785")
    assert not validate_chilean_rut("12.345.678-9")


def test_profile_and_quality_warnings():
    df = pd.DataFrame({"monto": [100, 0, -50], "email": ["ok@test.com", "malo", None]})
    profile = profile_dataset(df)
    warnings = quality_warnings(df, profile["detected"])
    assert profile["rows"] == 3
    assert any(w.issue == "Montos negativos" for w in warnings)
    assert any(w.issue == "Emails inválidos" for w in warnings)


def test_parse_date_series_handles_iso_and_local_dates():
    parsed = parse_date_series(pd.Series(["2025-01-15", "15/02/2025", "fecha mala"]))
    assert parsed.iloc[0].month == 1
    assert parsed.iloc[1].month == 2
    assert pd.isna(parsed.iloc[2])
