from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Provider:
    id: str
    name: str
    country: str
    method: str
    currency: str
    status: str
    fixed_fee: float
    variable_bps: float
    sla_hours: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Route:
    id: str
    name: str
    origin_country: str
    destination_country: str
    method: str
    provider_id: str
    currency: str
    status: str
    approval_version: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PricingRule:
    id: str
    name: str
    route_id: str
    revenue_bps: float
    spread_bps: float
    tax_rate: float
    min_margin_pct: float
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SimulationInput:
    route_id: str
    provider_id: str
    amount: float
    volume: int
    fx_rate: float
    provider_fixed_fee: float
    provider_variable_bps: float
    method_cost_bps: float
    revenue_bps: float
    spread_bps: float
    tax_rate: float
    extra_cost: float = 0


@dataclass(frozen=True)
class SimulationResult:
    route_id: str
    provider_id: str
    amount: float
    volume: int
    gross_volume: float
    cost_in: float
    cost_out: float
    fx_spread_revenue: float
    taxes: float
    total_cost: float
    revenue: float
    profit: float
    margin_pct: float
    roi_pct: float
    break_even_bps: float
    validations: list[str]
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat(timespec="seconds")
        return data


@dataclass(frozen=True)
class AuditLog:
    id: int
    actor: str
    action: str
    entity: str
    detail: str
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat(timespec="seconds")
        return data


@dataclass(frozen=True)
class VersionRecord:
    id: str
    entity: str
    label: str
    owner: str
    status: str
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat(timespec="seconds")
        return data

