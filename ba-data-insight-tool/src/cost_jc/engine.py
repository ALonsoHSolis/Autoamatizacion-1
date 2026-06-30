from __future__ import annotations

from datetime import datetime

from src.cost_jc.domain import SimulationInput, SimulationResult


def bps_to_rate(value: float) -> float:
    return value / 10_000


class CostJCEngine:
    """Central financial engine for Model of Costs pricing and route simulations."""

    def calculate(self, payload: SimulationInput) -> SimulationResult:
        validations = self.validate(payload)
        gross_volume = payload.amount * payload.volume
        cost_in = (payload.provider_fixed_fee * payload.volume) + (
            gross_volume * bps_to_rate(payload.provider_variable_bps)
        )
        cost_out = gross_volume * bps_to_rate(payload.method_cost_bps) + payload.extra_cost
        fx_spread_revenue = gross_volume * bps_to_rate(payload.spread_bps)
        taxable_base = max(cost_in + cost_out, 0)
        taxes = taxable_base * (payload.tax_rate / 100)
        total_cost = cost_in + cost_out + taxes
        revenue = gross_volume * bps_to_rate(payload.revenue_bps) + fx_spread_revenue
        profit = revenue - total_cost
        margin_pct = (profit / revenue * 100) if revenue else 0
        roi_pct = (profit / total_cost * 100) if total_cost else 0
        break_even_bps = (total_cost / gross_volume * 10_000) if gross_volume else 0

        if profit < 0:
            validations.append("Profit negativo: revisar fees, spread o costo proveedor.")
        if revenue and margin_pct < 10:
            validations.append("Margen bajo el umbral enterprise sugerido de 10%.")
        if payload.spread_bps > 0 and payload.fx_rate <= 0:
            validations.append("FX rate invalido para una ruta con spread.")

        return SimulationResult(
            route_id=payload.route_id,
            provider_id=payload.provider_id,
            amount=payload.amount,
            volume=payload.volume,
            gross_volume=gross_volume,
            cost_in=cost_in,
            cost_out=cost_out,
            fx_spread_revenue=fx_spread_revenue,
            taxes=taxes,
            total_cost=total_cost,
            revenue=revenue,
            profit=profit,
            margin_pct=margin_pct,
            roi_pct=roi_pct,
            break_even_bps=break_even_bps,
            validations=validations,
            created_at=datetime.now(),
        )

    def validate(self, payload: SimulationInput) -> list[str]:
        issues: list[str] = []
        if payload.amount <= 0:
            issues.append("El monto debe ser mayor a cero.")
        if payload.volume <= 0:
            issues.append("El volumen debe ser mayor a cero.")
        if payload.fx_rate <= 0:
            issues.append("El tipo de cambio debe ser mayor a cero.")
        rate_fields = {
            "provider_variable_bps": payload.provider_variable_bps,
            "method_cost_bps": payload.method_cost_bps,
            "revenue_bps": payload.revenue_bps,
            "spread_bps": payload.spread_bps,
        }
        for name, value in rate_fields.items():
            if value < 0:
                issues.append(f"{name} no puede ser negativo.")
        if payload.tax_rate < 0:
            issues.append("La tasa de impuesto no puede ser negativa.")
        if payload.provider_fixed_fee < 0 or payload.extra_cost < 0:
            issues.append("Los costos fijos no pueden ser negativos.")
        return issues
