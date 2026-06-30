from __future__ import annotations

from datetime import date

import pandas as pd

from src.treasury_repository import MemoryTreasuryRepository, parse_treasury_balances


def test_parse_treasury_balances_normalizes_required_columns():
    raw = pd.DataFrame(
        {
            "Cuenta": ["Operativa"],
            "Fecha": ["23-06-2026"],
            "Saldo": ["$1.250.000"],
            "Saldo Extracto": ["$1.240.000"],
            "Reserva Minima": ["500000"],
        }
    )

    parsed = parse_treasury_balances(raw, source="archivo")

    assert parsed.loc[0, "cuenta"] == "Operativa"
    assert parsed.loc[0, "fecha"] == date(2026, 6, 23)
    assert parsed.loc[0, "saldo_interno"] == 1_250_000
    assert parsed.loc[0, "saldo_extracto"] == 1_240_000
    assert parsed.loc[0, "reserva_minima"] == 500_000
    assert parsed.loc[0, "fuente"] == "archivo"


def test_memory_treasury_repository_covers_core_workflow():
    repo = MemoryTreasuryRepository({})
    repo.initialize_schema()
    target_date = date(2026, 1, 5)
    upload = pd.DataFrame(
        {
            "cuenta": ["Cuenta Test"],
            "fecha": [target_date],
            "saldo_interno": [1000],
            "saldo_extracto": [900],
            "reserva_minima": [800],
        }
    )

    loaded = repo.upsert_balances(upload, fuente="archivo", cargado_por="pytest")
    latest = repo.latest_balances()
    created = repo.detect_discrepancies(target_date)
    open_items = repo.open_discrepancies(target_date)

    assert loaded == 1
    assert "Cuenta Test" in set(latest["cuenta"])
    assert created == 1
    assert len(open_items) == 1

    repo.register_action(int(open_items.iloc[0]["id"]), "Ajuste validado", registrado_por="pytest")
    actions = repo.actions_for_date(target_date)

    assert repo.open_discrepancies(target_date).empty
    assert actions.iloc[0]["descripcion"] == "Ajuste validado"

    report_id = repo.save_report(
        target_date,
        target_date,
        ["Liquidez"],
        "PDF",
        generado_por="pytest",
        filename="test.pdf",
        content=b"demo",
    )
    repo.add_note("pytest", "Finanzas", "Nota de coordinacion")

    assert report_id == 1
    assert repo.recent_reports().iloc[0]["nombre_archivo"] == "test.pdf"
    assert repo.notes().iloc[0]["mensaje"] == "Nota de coordinacion"
