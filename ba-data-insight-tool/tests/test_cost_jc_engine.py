from __future__ import annotations

from src.cost_jc.domain import SimulationInput
from src.cost_jc.engine import CostJCEngine
from src.cost_jc.repository import MemoryCostJCRepository


def test_cost_jc_engine_calculates_financial_outputs():
    engine = CostJCEngine()
    result = engine.calculate(
        SimulationInput(
            route_id="route_test",
            provider_id="provider_test",
            amount=100,
            volume=100,
            fx_rate=1,
            provider_fixed_fee=1,
            provider_variable_bps=50,
            method_cost_bps=25,
            revenue_bps=150,
            spread_bps=20,
            tax_rate=10,
            extra_cost=10,
        )
    )

    assert result.gross_volume == 10_000
    assert result.cost_in == 150
    assert result.cost_out == 35
    assert result.taxes == 18.5
    assert result.total_cost == 203.5
    assert result.revenue == 170
    assert round(result.profit, 2) == -33.5
    assert "Profit negativo" in " ".join(result.validations)


def test_cost_jc_engine_validates_invalid_payload():
    engine = CostJCEngine()
    result = engine.calculate(
        SimulationInput(
            route_id="route_test",
            provider_id="provider_test",
            amount=0,
            volume=0,
            fx_rate=0,
            provider_fixed_fee=-1,
            provider_variable_bps=-2,
            method_cost_bps=0,
            revenue_bps=0,
            spread_bps=0,
            tax_rate=-1,
        )
    )

    joined = " ".join(result.validations)
    assert "monto debe ser mayor a cero" in joined
    assert "volumen debe ser mayor a cero" in joined
    assert "tipo de cambio debe ser mayor a cero" in joined
    assert "provider_variable_bps no puede ser negativo" in joined


def test_cost_jc_repository_saves_simulation_and_audit():
    repo = MemoryCostJCRepository({})
    route = repo.routes()[0]
    provider = repo.find_provider(route.provider_id)
    rule = repo.rule_for_route(route.id)
    result = CostJCEngine().calculate(
        SimulationInput(
            route_id=route.id,
            provider_id=provider.id,
            amount=25_000,
            volume=1_000,
            fx_rate=1,
            provider_fixed_fee=provider.fixed_fee,
            provider_variable_bps=provider.variable_bps,
            method_cost_bps=30,
            revenue_bps=rule.revenue_bps,
            spread_bps=rule.spread_bps,
            tax_rate=rule.tax_rate,
        )
    )

    simulation_id = repo.save_simulation(result, actor="pytest")

    assert simulation_id == 1
    assert len(repo.simulations()) == 1
    assert repo.audit_logs()[0].action == "simulate"
    assert not repo.quality_issues().empty

