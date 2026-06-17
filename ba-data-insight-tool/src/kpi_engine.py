from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .utils import format_currency, format_number, format_percent, parse_date_series, parse_numeric_series, strip_accents, validate_chilean_rut


def _kpi(name: str, value: Any, interpretation: str, raw_value: Any | None = None) -> dict[str, Any]:
    return {"kpi": name, "valor": value, "interpretacion": interpretation, "raw_value": raw_value if raw_value is not None else value}


def _analysis_key(analysis_type: str) -> str:
    return strip_accents(analysis_type.lower())


def _find_column(df: pd.DataFrame, keywords: list[str], exclude: list[str] | None = None) -> str | None:
    excluded = {strip_accents(item.lower()) for item in (exclude or [])}
    for col in df.columns:
        normalized = strip_accents(col.lower())
        if normalized in excluded:
            continue
        if any(strip_accents(word.lower()) in normalized for word in keywords):
            return col
    return None


def calculate_kpis(
    df: pd.DataFrame,
    analysis_type: str,
    amount_col: str | None = None,
    date_col: str | None = None,
    category_col: str | None = None,
    status_col: str | None = None,
) -> list[dict[str, Any]]:
    kpis = _general_kpis(df)
    amount = parse_numeric_series(df[amount_col]) if amount_col and amount_col in df else None
    if amount is not None:
        kpis.extend(_amount_kpis(amount))

    if status_col and status_col in df:
        kpis.extend(_status_kpis(df, status_col, amount_col))
    if category_col and category_col in df:
        kpis.extend(_category_kpis(df, category_col, amount_col))
    if date_col and date_col in df:
        kpis.extend(_trend_kpis(df, date_col, amount_col))

    key = _analysis_key(analysis_type)
    if "venta" in key:
        kpis.extend(_sales_kpis(df, amount_col, date_col, category_col))
    elif "pago" in key:
        kpis.extend(_payment_kpis(df, amount_col, status_col, category_col))
    elif "conciliacion" in key:
        kpis.extend(_reconciliation_kpis(df, amount_col, status_col))
    elif "registro" in key or "persona" in key:
        kpis.extend(_people_kpis(df, category_col, status_col))
    elif "financiero" in key:
        kpis.extend(_financial_kpis(df, amount_col, category_col, date_col))
    return _deduplicate_kpis(kpis)


def _general_kpis(df: pd.DataFrame) -> list[dict[str, Any]]:
    missing_pct = df.isna().sum().sum() / max(df.shape[0] * df.shape[1], 1) * 100
    return [
        _kpi("Cantidad de registros", len(df), "Volumen total de registros analizados.", len(df)),
        _kpi("Columnas disponibles", len(df.columns), "Campos disponibles para segmentar y revisar la base.", len(df.columns)),
        _kpi("Duplicados", int(df.duplicated().sum()), "Filas repetidas que podrían distorsionar los indicadores.", int(df.duplicated().sum())),
        _kpi("Datos faltantes", format_percent(missing_pct), "Porcentaje global de celdas vacías en el dataset.", missing_pct),
        _kpi("Registros únicos", int(len(df.drop_duplicates())), "Filas distintas después de remover duplicados exactos.", int(len(df.drop_duplicates()))),
    ]


def _amount_kpis(amount: pd.Series) -> list[dict[str, Any]]:
    valid = amount.dropna()
    if valid.empty:
        return []
    total = float(valid.sum())
    return [
        _kpi("Monto total", format_currency(total), f"El monto acumulado es {format_currency(total)}.", total),
        _kpi("Monto promedio", format_currency(valid.mean()), "Promedio por registro con monto válido.", float(valid.mean())),
        _kpi("Mediana de monto", format_currency(valid.median()), "Valor central útil cuando existen extremos.", float(valid.median())),
        _kpi("Monto mínimo", format_currency(valid.min()), "Menor monto observado.", float(valid.min())),
        _kpi("Monto máximo", format_currency(valid.max()), "Mayor monto observado.", float(valid.max())),
    ]


def _status_kpis(df: pd.DataFrame, status_col: str, amount_col: str | None) -> list[dict[str, Any]]:
    summary = status_summary(df, status_col, amount_col)
    if summary.empty:
        return []
    first = summary.iloc[0]
    return [
        _kpi("Estado principal", first["estado"], f"Representa {format_percent(first['porcentaje'])} de los registros.", first["estado"]),
        _kpi("Estados distintos", int(summary["estado"].nunique()), "Cantidad de estados detectados en la base.", int(summary["estado"].nunique())),
    ]


def _category_kpis(df: pd.DataFrame, category_col: str, amount_col: str | None) -> list[dict[str, Any]]:
    ranking = category_ranking(df, category_col, amount_col)
    if ranking.empty:
        return []
    first = ranking.iloc[0]
    return [
        _kpi("Categoría líder", first["categoria"], f"Concentra {format_percent(first['participacion_pct'])} del valor analizado.", first["categoria"]),
        _kpi("Categorías distintas", int(df[category_col].nunique(dropna=True)), "Número de segmentos disponibles para comparación.", int(df[category_col].nunique(dropna=True))),
    ]


def _trend_kpis(df: pd.DataFrame, date_col: str, amount_col: str | None) -> list[dict[str, Any]]:
    trend = temporal_trend(df, date_col, amount_col)
    if trend.empty:
        return []
    kpis: list[dict[str, Any]] = []
    if len(trend) >= 2:
        last = trend.iloc[-1]
        growth = last["variacion_pct"]
        label = "crece" if pd.notna(growth) and growth > 0 else "cae" if pd.notna(growth) and growth < 0 else "se mantiene"
        kpis.append(_kpi("Variación último periodo", format_percent(growth) if pd.notna(growth) else "N/A", f"El último periodo {label} frente al periodo anterior.", growth))
    max_period = trend.loc[trend["valor"].idxmax()]
    min_period = trend.loc[trend["valor"].idxmin()]
    kpis.extend(
        [
            _kpi("Periodo de mayor valor", max_period["periodo"].strftime("%Y-%m"), f"Valor observado: {format_currency(max_period['valor'])}.", float(max_period["valor"])),
            _kpi("Periodo de menor valor", min_period["periodo"].strftime("%Y-%m"), f"Valor observado: {format_currency(min_period['valor'])}.", float(min_period["valor"])),
        ]
    )
    return kpis


def _sales_kpis(df: pd.DataFrame, amount_col: str | None, date_col: str | None, category_col: str | None) -> list[dict[str, Any]]:
    kpis: list[dict[str, Any]] = []
    quantity_col = _find_column(df, ["cantidad", "clientes", "unidades", "tickets"])
    ticket_col = _find_column(df, ["ticket_promedio", "ticket"])
    if amount_col and quantity_col and amount_col in df and quantity_col in df:
        total_amount = parse_numeric_series(df[amount_col]).sum()
        total_quantity = parse_numeric_series(df[quantity_col]).sum()
        if total_quantity:
            kpis.append(_kpi("Ticket promedio calculado", format_currency(total_amount / total_quantity), f"Monto promedio por unidad/cliente usando {quantity_col}.", float(total_amount / total_quantity)))
    if ticket_col:
        ticket = parse_numeric_series(df[ticket_col]).dropna()
        if not ticket.empty:
            kpis.append(_kpi("Ticket promedio informado", format_currency(ticket.mean()), f"Promedio detectado desde la columna {ticket_col}.", float(ticket.mean())))
    if date_col and amount_col:
        trend = temporal_trend(df, date_col, amount_col)
        if len(trend) >= 3:
            last_three = trend.tail(3)["valor"]
            direction = "creciente" if last_three.is_monotonic_increasing else "decreciente" if last_three.is_monotonic_decreasing else "mixta"
            kpis.append(_kpi("Tendencia últimos 3 periodos", direction, "Lectura simple de los últimos tres periodos disponibles.", direction))
    return kpis


def _payment_kpis(df: pd.DataFrame, amount_col: str | None, status_col: str | None, category_col: str | None) -> list[dict[str, Any]]:
    expected_col = _find_column(df, ["esperado", "monto_total", "total_a_pagar"])
    paid_col = _find_column(df, ["pagado", "monto_pagado", "pago_real", "abonado"], exclude=[expected_col] if expected_col else None)
    if not paid_col and amount_col:
        paid_col = amount_col
    if not expected_col or not paid_col:
        return []

    expected = parse_numeric_series(df[expected_col])
    paid = parse_numeric_series(df[paid_col])
    pending = expected - paid
    total_expected = float(expected.sum())
    total_paid = float(paid.sum())
    total_pending = float(pending.sum())
    progress = total_paid / total_expected * 100 if total_expected else 0
    incomplete = int((paid < expected).sum())
    overpaid = int((paid > expected).sum())
    kpis = [
        _kpi("Total esperado", format_currency(total_expected), "Monto que debería haberse recibido.", total_expected),
        _kpi("Total pagado", format_currency(total_paid), "Monto efectivamente registrado como pagado.", total_paid),
        _kpi("Diferencia pendiente", format_currency(total_pending), "Brecha entre lo esperado y lo pagado.", total_pending),
        _kpi("Avance de pago", format_percent(progress), "Porcentaje de avance respecto al total esperado.", progress),
        _kpi("Pagos incompletos", incomplete, "Registros donde el monto pagado es menor al esperado.", incomplete),
        _kpi("Pagos sobre esperado", overpaid, "Registros donde el pago supera el monto esperado.", overpaid),
    ]
    if category_col:
        by_category = pd.DataFrame({"categoria": df[category_col].fillna("Sin categoría"), "pendiente": pending}).groupby("categoria", as_index=False)["pendiente"].sum()
        if not by_category.empty:
            top = by_category.sort_values("pendiente", ascending=False).iloc[0]
            kpis.append(_kpi("Mayor brecha por categoría", top["categoria"], f"Pendiente estimado: {format_currency(top['pendiente'])}.", float(top["pendiente"])))
    if status_col:
        pending_status = df[status_col].fillna("").astype(str).str.contains("pend|deud|incom", case=False, regex=True)
        kpis.append(_kpi("Registros con estado pendiente", int(pending_status.sum()), "Casos marcados como pendientes, deuda o incompletos.", int(pending_status.sum())))
    return kpis


def _reconciliation_kpis(df: pd.DataFrame, amount_col: str | None, status_col: str | None) -> list[dict[str, Any]]:
    debit_col = _find_column(df, ["debito", "débito", "cargo", "egreso"])
    credit_col = _find_column(df, ["credito", "crédito", "abono", "ingreso"])
    reference_col = _find_column(df, ["referencia", "comprobante", "transaction", "transaccion", "id"])
    kpis = [_kpi("Total de movimientos", len(df), "Cantidad de movimientos revisados para conciliación.", len(df))]
    if debit_col:
        total_debit = parse_numeric_series(df[debit_col]).sum()
        kpis.append(_kpi("Total débitos", format_currency(total_debit), f"Suma detectada desde {debit_col}.", float(total_debit)))
    if credit_col:
        total_credit = parse_numeric_series(df[credit_col]).sum()
        kpis.append(_kpi("Total créditos", format_currency(total_credit), f"Suma detectada desde {credit_col}.", float(total_credit)))
    if amount_col and amount_col in df:
        kpis.append(_kpi("Movimientos duplicados", int(df.duplicated(subset=[amount_col]).sum()), "Duplicados aproximados por monto seleccionado.", int(df.duplicated(subset=[amount_col]).sum())))
    if reference_col:
        missing_reference = int(df[reference_col].isna().sum() + (df[reference_col].astype(str).str.strip() == "").sum())
        kpis.append(_kpi("Movimientos sin referencia", missing_reference, f"Registros sin dato usable en {reference_col}.", missing_reference))
    if status_col:
        reconciled = df[status_col].fillna("").astype(str).str.contains("concili|match|ok", case=False, regex=True)
        kpis.append(_kpi("Registros conciliados", int(reconciled.sum()), "Casos cuyo estado sugiere conciliación exitosa.", int(reconciled.sum())))
        kpis.append(_kpi("Registros no conciliados", int((~reconciled).sum()), "Casos restantes que pueden requerir revisión.", int((~reconciled).sum())))
    return kpis


def _people_kpis(df: pd.DataFrame, category_col: str | None, status_col: str | None) -> list[dict[str, Any]]:
    name_col = _find_column(df, ["nombre", "persona", "cliente", "beneficiario"])
    email_col = _find_column(df, ["email", "correo", "mail"])
    rut_col = _find_column(df, ["rut"])
    phone_col = _find_column(df, ["telefono", "teléfono", "celular", "phone"])
    birth_col = _find_column(df, ["nacimiento", "fecha_nacimiento"])
    kpis = [_kpi("Total de personas/registros", len(df), "Tamaño de la base de personas o usuarios.", len(df))]
    if name_col:
        kpis.append(_kpi("Duplicados por nombre", int(df.duplicated(subset=[name_col]).sum()), f"Registros repetidos usando {name_col}.", int(df.duplicated(subset=[name_col]).sum())))
    if email_col:
        emails = df[email_col].dropna().astype(str)
        invalid = ~emails.str.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        kpis.append(_kpi("Emails inválidos", int(invalid.sum()), "Correos con formato no válido.", int(invalid.sum())))
    if rut_col:
        invalid_rut = int(df[rut_col].dropna().apply(lambda x: not validate_chilean_rut(x)).sum())
        kpis.append(_kpi("RUT inválidos", invalid_rut, "RUT que no pasan validación de dígito verificador.", invalid_rut))
    if phone_col:
        digits = df[phone_col].dropna().astype(str).str.replace(r"\D", "", regex=True)
        suspicious = digits.apply(lambda x: len(x) < 8 or len(x) > 12)
        kpis.append(_kpi("Teléfonos sospechosos", int(suspicious.sum()), "Teléfonos con largo inusual.", int(suspicious.sum())))
    if birth_col:
        dates = parse_date_series(df[birth_col])
        ages = (pd.Timestamp.today() - dates).dt.days / 365.25
        valid_ages = ages[(ages >= 0) & (ages <= 120)].dropna()
        if not valid_ages.empty:
            kpis.append(_kpi("Edad promedio", f"{valid_ages.mean():.1f}", "Edad promedio estimada desde fecha de nacimiento.", float(valid_ages.mean())))
    if category_col:
        kpis.append(_category_kpis(df, category_col, None)[0])
    if status_col:
        kpis.append(_status_kpis(df, status_col, None)[0])
    incomplete_rows = int(df.isna().any(axis=1).sum())
    kpis.append(_kpi("Registros incompletos", incomplete_rows, "Filas con al menos un campo vacío.", incomplete_rows))
    return kpis


def _financial_kpis(df: pd.DataFrame, amount_col: str | None, category_col: str | None, date_col: str | None) -> list[dict[str, Any]]:
    income_col = _find_column(df, ["ingreso", "credito", "crédito", "abono"])
    expense_col = _find_column(df, ["egreso", "gasto", "debito", "débito", "cargo"])
    kpis: list[dict[str, Any]] = []
    income = parse_numeric_series(df[income_col]).sum() if income_col else 0
    expense = parse_numeric_series(df[expense_col]).sum() if expense_col else 0
    if income_col or expense_col:
        net = float(income - expense)
        margin = net / income * 100 if income else np.nan
        kpis.extend(
            [
                _kpi("Total ingresos", format_currency(income), "Suma de columnas asociadas a ingresos.", float(income)),
                _kpi("Total egresos", format_currency(expense), "Suma de columnas asociadas a egresos/gastos.", float(expense)),
                _kpi("Resultado neto", format_currency(net), "Diferencia entre ingresos y egresos detectados.", net),
                _kpi("Margen simple", format_percent(margin) if pd.notna(margin) else "N/A", "Resultado neto dividido por ingresos.", margin),
            ]
        )
    elif amount_col:
        values = parse_numeric_series(df[amount_col])
        income = values[values > 0].sum()
        expense = abs(values[values < 0].sum())
        net = income - expense
        kpis.extend(
            [
                _kpi("Ingresos estimados", format_currency(income), "Suma de montos positivos.", float(income)),
                _kpi("Egresos estimados", format_currency(expense), "Suma absoluta de montos negativos.", float(expense)),
                _kpi("Resultado neto estimado", format_currency(net), "Ingresos positivos menos egresos negativos.", float(net)),
            ]
        )
    if category_col and amount_col:
        ranking = category_ranking(df, category_col, amount_col)
        if not ranking.empty:
            top = ranking.iloc[0]
            kpis.append(_kpi("Categoría de mayor impacto", top["categoria"], f"Representa {format_percent(top['participacion_pct'])} del monto seleccionado.", top["categoria"]))
    return kpis


def _deduplicate_kpis(kpis: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for item in kpis:
        if item["kpi"] in seen:
            continue
        seen.add(item["kpi"])
        output.append(item)
    return output


def temporal_trend(df: pd.DataFrame, date_col: str, amount_col: str | None = None) -> pd.DataFrame:
    dates = parse_date_series(df[date_col])
    value = parse_numeric_series(df[amount_col]) if amount_col and amount_col in df else pd.Series(1, index=df.index, dtype="float64")
    trend = pd.DataFrame({"periodo": dates.dt.to_period("M").dt.to_timestamp(), "valor": value})
    trend = trend.dropna(subset=["periodo"]).groupby("periodo", as_index=False)["valor"].sum()
    trend["variacion_abs"] = trend["valor"].diff()
    trend["variacion_pct"] = trend["valor"].pct_change() * 100
    return trend


def category_ranking(df: pd.DataFrame, category_col: str, amount_col: str | None = None, top_n: int = 10) -> pd.DataFrame:
    if not category_col or category_col not in df:
        return pd.DataFrame(columns=["categoria", "valor", "participacion_pct"])
    if amount_col and amount_col in df:
        values = parse_numeric_series(df[amount_col])
        ranking = pd.DataFrame({"categoria": df[category_col].fillna("Sin categoría"), "valor": values})
        ranking = ranking.groupby("categoria", as_index=False)["valor"].sum()
    else:
        ranking = df[category_col].fillna("Sin categoría").value_counts().rename_axis("categoria").reset_index(name="valor")
    total = ranking["valor"].sum()
    ranking["participacion_pct"] = np.where(total != 0, ranking["valor"] / total * 100, 0)
    return ranking.sort_values("valor", ascending=False).head(top_n)


def status_summary(df: pd.DataFrame, status_col: str, amount_col: str | None = None) -> pd.DataFrame:
    if not status_col or status_col not in df:
        return pd.DataFrame(columns=["estado", "registros", "monto", "porcentaje"])
    base = pd.DataFrame({"estado": df[status_col].fillna("Sin estado").astype(str)})
    base["monto"] = parse_numeric_series(df[amount_col]) if amount_col and amount_col in df else 0
    summary = base.groupby("estado", as_index=False).agg(registros=("estado", "size"), monto=("monto", "sum"))
    summary["porcentaje"] = summary["registros"] / max(summary["registros"].sum(), 1) * 100
    return summary.sort_values("registros", ascending=False)


def kpis_to_frame(kpis: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(kpis, columns=["kpi", "valor", "interpretacion", "raw_value"])


def pareto_analysis(df: pd.DataFrame, category_col: str, amount_col: str | None = None) -> pd.DataFrame:
    """Pareto/ABC analysis: classify categories into A (top 80 %), B (80-95 %), C (95-100 %).

    Returns a DataFrame with columns:
      categoria, valor, participacion_pct, acumulado_pct, segmento

    Useful for identifying which categories drive the bulk of value or volume.
    """
    columns = ["categoria", "valor", "participacion_pct", "acumulado_pct", "segmento"]
    if not category_col or category_col not in df:
        return pd.DataFrame(columns=columns)

    all_cats = category_ranking(df, category_col, amount_col, top_n=len(df))
    if all_cats.empty:
        return pd.DataFrame(columns=columns)

    result = all_cats.sort_values("valor", ascending=False).copy().reset_index(drop=True)
    result["acumulado_pct"] = result["participacion_pct"].cumsum().round(2)

    def _segment(cumulative: float) -> str:
        if cumulative <= 80:
            return "A"
        if cumulative <= 95:
            return "B"
        return "C"

    result["segmento"] = result["acumulado_pct"].apply(_segment)
    return result[columns]


def period_comparison(
    df: pd.DataFrame,
    date_col: str,
    amount_col: str | None = None,
    periods: int = 1,
) -> dict[str, Any]:
    """Compare the last available period against *periods* steps back.

    Args:
        df: Source DataFrame.
        date_col: Column with date/datetime values.
        amount_col: Numeric column to aggregate. Counts rows if None.
        periods: How many periods to look back (1 = MoM, 12 = YoY).

    Returns:
        Dict with keys: current_period, previous_period, current_value,
        previous_value, absolute_change, percent_change, direction,
        periods_back. Returns empty dict when there is insufficient data.
    """
    if not date_col or date_col not in df or periods < 1:
        return {}

    trend = temporal_trend(df, date_col, amount_col)
    if len(trend) < periods + 1:
        return {}

    last = trend.iloc[-1]
    previous = trend.iloc[-(periods + 1)]

    current_value = float(last["valor"])
    previous_value = float(previous["valor"])
    absolute_change = current_value - previous_value
    percent_change: float | None = absolute_change / previous_value * 100 if previous_value != 0 else None

    if absolute_change > 0:
        direction = "up"
    elif absolute_change < 0:
        direction = "down"
    else:
        direction = "stable"

    return {
        "current_period": last["periodo"].strftime("%Y-%m"),
        "current_value": current_value,
        "previous_period": previous["periodo"].strftime("%Y-%m"),
        "previous_value": previous_value,
        "absolute_change": absolute_change,
        "percent_change": percent_change,
        "direction": direction,
        "periods_back": periods,
    }


def forecast_trend(
    df: pd.DataFrame,
    date_col: str,
    amount_col: str | None = None,
    periods_ahead: int = 3,
) -> dict[str, Any]:
    """Fit a linear trend to the temporal series and project N periods ahead.

    Returns a dict with:
      - historical: list of {periodo, valor} dicts (existing data)
      - projected:  list of {periodo, valor, lower, upper} dicts
      - slope:      change per period
      - r_squared:  goodness of fit (0-1)
      - direction:  'creciente' | 'decreciente' | 'estable'
      - next_value: projected value for next period
      - trend_pct:  slope as % of mean value
    """
    trend = temporal_trend(df, date_col, amount_col)
    if len(trend) < 3:
        return {}

    x = np.arange(len(trend), dtype=float)
    y = trend["valor"].astype(float).values

    # Linear fit
    coeffs = np.polyfit(x, y, 1)
    slope, intercept = coeffs
    y_fit = np.polyval(coeffs, x)

    # R²
    ss_res = np.sum((y - y_fit) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = float(1 - ss_res / ss_tot) if ss_tot != 0 else 0.0

    # Residual std for confidence band
    residuals = y - y_fit
    std_err = float(np.std(residuals))

    # Historical points
    historical = [
        {"periodo": row["periodo"], "valor": float(row["valor"])}
        for _, row in trend.iterrows()
    ]

    # Projected periods
    last_date = trend["periodo"].iloc[-1]
    projected = []
    for i in range(1, periods_ahead + 1):
        xi = len(trend) - 1 + i
        proj_val = float(np.polyval(coeffs, xi))
        try:
            next_date = last_date + pd.DateOffset(months=i)
        except Exception:
            next_date = last_date
        projected.append({
            "periodo": next_date,
            "valor":   round(proj_val, 2),
            "lower":   round(proj_val - 1.96 * std_err, 2),
            "upper":   round(proj_val + 1.96 * std_err, 2),
        })

    mean_val = float(y.mean()) if y.mean() != 0 else 1
    trend_pct = float(slope / abs(mean_val) * 100)

    if abs(trend_pct) < 1:
        direction = "estable"
    elif slope > 0:
        direction = "creciente"
    else:
        direction = "decreciente"

    return {
        "historical":  historical,
        "projected":   projected,
        "slope":       round(float(slope), 4),
        "r_squared":   round(r2, 4),
        "direction":   direction,
        "next_value":  projected[0]["valor"] if projected else None,
        "trend_pct":   round(trend_pct, 2),
        "periods_ahead": periods_ahead,
    }


def forecast_kpis(forecast: dict) -> list[dict[str, Any]]:
    """Build KPI rows from a forecast result dict."""
    if not forecast:
        return []
    direction_label = {
        "creciente":  "📈 Tendencia creciente",
        "decreciente":"📉 Tendencia decreciente",
        "estable":    "➡️ Tendencia estable",
    }.get(forecast.get("direction",""), "—")

    kpis = [
        {"kpi": "Dirección de tendencia",
         "valor": direction_label,
         "interpretacion": f"{abs(forecast.get('trend_pct',0)):.1f}% por período"},
        {"kpi": "R² del modelo",
         "valor": f"{forecast.get('r_squared',0):.2f}",
         "interpretacion": "1.0 = ajuste perfecto · <0.5 = alta variabilidad"},
        {"kpi": "Proyección próximo período",
         "valor": f"{forecast.get('next_value',0):,.0f}",
         "interpretacion": "Valor estimado según tendencia lineal"},
    ]
    for i, p in enumerate(forecast.get("projected", []), 1):
        kpis.append({
            "kpi": f"Proyección +{i} período{'s' if i>1 else ''}",
            "valor": f"{p['valor']:,.0f}",
            "interpretacion": f"Rango: {p['lower']:,.0f} — {p['upper']:,.0f}",
        })
    return kpis
