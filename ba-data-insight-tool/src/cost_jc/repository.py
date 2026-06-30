from __future__ import annotations

from datetime import datetime
from typing import Any, MutableMapping

import pandas as pd

from src.cost_jc.domain import AuditLog, PricingRule, Provider, Route, SimulationResult, VersionRecord


class MemoryCostJCRepository:
    """Session-backed repository for the Model of Costs enterprise MVP."""

    def __init__(self, store: MutableMapping[str, Any] | None = None):
        self.store = store if store is not None else {}
        self._ensure_seed()

    def _ensure_seed(self) -> None:
        self.store.setdefault(
            "providers",
            [
                Provider("prov_001", "AndesPay", "CL", "Transfer", "CLP", "Activo", 120, 18, 4),
                Provider("prov_002", "Pacific Rails", "PE", "ACH", "USD", "Activo", 0.42, 32, 12),
                Provider("prov_003", "Norte Cash Network", "MX", "Cashout", "MXN", "Revision", 0.58, 45, 18),
            ],
        )
        self.store.setdefault(
            "routes",
            [
                Route("route_001", "CL -> CL Transfer", "CL", "CL", "Transfer", "prov_001", "CLP", "Aprobada", "v1.3"),
                Route("route_002", "CL -> PE ACH", "CL", "PE", "ACH", "prov_002", "USD", "Piloto", "v0.9"),
                Route("route_003", "US -> MX Cashout", "US", "MX", "Cashout", "prov_003", "MXN", "Revision", "v0.5"),
            ],
        )
        self.store.setdefault(
            "pricing_rules",
            [
                PricingRule("rule_001", "Standard Transfer CL", "route_001", 95, 25, 19, 18),
                PricingRule("rule_002", "Cross-border PE Pilot", "route_002", 145, 40, 8, 20),
                PricingRule("rule_003", "Cashout MX Controlled", "route_003", 180, 55, 16, 22),
            ],
        )
        self.store.setdefault("simulations", [])
        self.store.setdefault(
            "audit_logs",
            [
                AuditLog(1, "system", "seed", "route", "Rutas base cargadas para MVP Model of Costs.", datetime.now()),
                AuditLog(2, "pricing.ops", "review", "rule", "Reglas de margen minimo preparadas.", datetime.now()),
            ],
        )
        self.store.setdefault(
            "versions",
            [
                VersionRecord("v1.3", "route_001", "Ruta local CL aprobada", "pricing.ops", "Aprobada", datetime.now()),
                VersionRecord("v0.9", "route_002", "Piloto cross-border PE", "treasury.ops", "Piloto", datetime.now()),
                VersionRecord("v0.5", "route_003", "Cashout MX en revision", "risk.ops", "Revision", datetime.now()),
            ],
        )
        self.store.setdefault("next_audit_id", 3)

    def providers(self) -> list[Provider]:
        return list(self.store["providers"])

    def routes(self) -> list[Route]:
        return list(self.store["routes"])

    def pricing_rules(self) -> list[PricingRule]:
        return list(self.store["pricing_rules"])

    def find_provider(self, provider_id: str) -> Provider:
        return next(provider for provider in self.providers() if provider.id == provider_id)

    def find_route(self, route_id: str) -> Route:
        return next(route for route in self.routes() if route.id == route_id)

    def rule_for_route(self, route_id: str) -> PricingRule:
        return next(rule for rule in self.pricing_rules() if rule.route_id == route_id and rule.active)

    def save_simulation(self, result: SimulationResult, actor: str = "usuario") -> int:
        self.store["simulations"].append(result)
        self.add_audit(actor, "simulate", "simulation", f"Simulacion guardada para {result.route_id}.")
        return len(self.store["simulations"])

    def simulations(self) -> list[SimulationResult]:
        return list(reversed(self.store["simulations"]))

    def add_route(self, route: Route, actor: str = "usuario") -> None:
        self.store["routes"].append(route)
        self.add_audit(actor, "create", "route", f"Ruta creada: {route.name}.")

    def add_audit(self, actor: str, action: str, entity: str, detail: str) -> None:
        audit_id = int(self.store["next_audit_id"])
        self.store["next_audit_id"] = audit_id + 1
        self.store["audit_logs"].append(AuditLog(audit_id, actor, action, entity, detail, datetime.now()))

    def audit_logs(self) -> list[AuditLog]:
        return list(reversed(self.store["audit_logs"]))

    def versions(self) -> list[VersionRecord]:
        return list(reversed(self.store["versions"]))

    def provider_frame(self) -> pd.DataFrame:
        return pd.DataFrame([provider.to_dict() for provider in self.providers()])

    def route_frame(self) -> pd.DataFrame:
        return pd.DataFrame([route.to_dict() for route in self.routes()])

    def pricing_frame(self) -> pd.DataFrame:
        return pd.DataFrame([rule.to_dict() for rule in self.pricing_rules()])

    def simulation_frame(self) -> pd.DataFrame:
        return pd.DataFrame([simulation.to_dict() for simulation in self.simulations()])

    def audit_frame(self) -> pd.DataFrame:
        return pd.DataFrame([item.to_dict() for item in self.audit_logs()])

    def version_frame(self) -> pd.DataFrame:
        return pd.DataFrame([item.to_dict() for item in self.versions()])

    def quality_issues(self) -> pd.DataFrame:
        rows: list[dict[str, Any]] = []
        for route in self.routes():
            provider = self.find_provider(route.provider_id)
            rule = self.rule_for_route(route.id)
            if provider.status != "Activo":
                rows.append(
                    {
                        "validacion": "Proveedor no activo",
                        "detalle": f"{route.name} usa {provider.name} con estado {provider.status}.",
                        "severidad": "Media",
                    }
                )
            if rule.min_margin_pct < 15:
                rows.append(
                    {
                        "validacion": "Margen minimo bajo",
                        "detalle": f"{rule.name} exige solo {rule.min_margin_pct:.0f}% de margen minimo.",
                        "severidad": "Baja",
                    }
                )
            if route.status == "Revision":
                rows.append(
                    {
                        "validacion": "Ruta pendiente",
                        "detalle": f"{route.name} aun no esta aprobada.",
                        "severidad": "Alta",
                    }
                )
        return pd.DataFrame(rows)


def create_cost_jc_repository(store: MutableMapping[str, Any] | None = None) -> MemoryCostJCRepository:
    return MemoryCostJCRepository(store)
