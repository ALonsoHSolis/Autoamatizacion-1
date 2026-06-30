"""Model of Costs enterprise MVP UI."""
from __future__ import annotations

from datetime import datetime
from html import escape

import pandas as pd
import plotly.express as px
import streamlit as st

from src.cost_jc.domain import Route, SimulationInput
from src.cost_jc.engine import CostJCEngine
from src.cost_jc.repository import create_cost_jc_repository
from src.utils import format_currency, format_number


COST_JC_SECTIONS = [
    "Inicio ejecutivo",
    "Proveedores",
    "Rutas wizard",
    "Motor de costeo",
    "Simulador",
    "Dashboard",
    "Calidad",
    "Auditoria",
    "Versionado",
    "Configuracion",
    "Integraciones",
]


def render_cost_jc_app() -> None:
    store = st.session_state.setdefault("_cost_jc_store", {})
    repo = create_cost_jc_repository(store)

    st.markdown(
        '<div class="cost-jc-header">'
        '<div class="workspace-kicker notranslate" translate="no">MODEL OF COSTS</div>'
        '<h1>Plataforma enterprise de costeo y pricing</h1>'
        '<p>Motor financiero, rutas, proveedores, simulaciones, calidad, auditoria e integraciones preparadas para evolucionar a SaaS.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="treasury-status-card warn">'
        '<strong>MVP en desarrollo</strong>'
        '<span>Implementacion incremental sobre Streamlit con dominio y servicios separados. API REST y RBAC quedan preparados para fases futuras.</span>'
        '</div>',
        unsafe_allow_html=True,
    )

    if st.session_state.get("cost_jc_section") not in COST_JC_SECTIONS:
        st.session_state["cost_jc_section"] = COST_JC_SECTIONS[0]
    st.radio(
        "Secciones Model of Costs",
        COST_JC_SECTIONS,
        key="cost_jc_section",
        horizontal=True,
        label_visibility="collapsed",
    )

    section = st.session_state["cost_jc_section"]
    if section == "Inicio ejecutivo":
        _render_executive_home(repo)
    elif section == "Proveedores":
        _render_providers(repo)
    elif section == "Rutas wizard":
        _render_route_wizard(repo)
    elif section == "Motor de costeo":
        _render_cost_engine(repo)
    elif section == "Simulador":
        _render_simulator(repo)
    elif section == "Dashboard":
        _render_dashboard(repo)
    elif section == "Calidad":
        _render_quality(repo)
    elif section == "Auditoria":
        _render_audit(repo)
    elif section == "Versionado":
        _render_versions(repo)
    elif section == "Configuracion":
        _render_configuration(repo)
    else:
        _render_integrations()


def _render_executive_home(repo) -> None:
    routes = repo.routes()
    providers = repo.providers()
    simulations = repo.simulations()
    issues = repo.quality_issues()
    avg_margin = _average_margin(simulations)

    st.markdown('<div class="section-kicker">Inicio ejecutivo</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    metrics = [
        ("Rutas activas", format_number(len(routes)), "Rutas configuradas"),
        ("Proveedores", format_number(len(providers)), "Entidades disponibles"),
        ("Margen promedio", f"{avg_margin:.1f}%", "Segun simulaciones"),
        ("Issues calidad", format_number(len(issues)), "Validaciones automaticas"),
    ]
    for col, (label, value, detail) in zip(cols, metrics):
        with col:
            _metric_card(label, value, detail)

    st.markdown('<div class="section-kicker">Mapa enterprise</div>', unsafe_allow_html=True)
    grid = st.columns(3)
    cards = [
        ("Dominio", "Providers, Routes, PricingRules, Simulations, AuditLogs, Versions."),
        ("Motor financiero", "Costos IN/OUT, FX, impuestos, revenue, margen, profit, spread y ROI."),
        ("Roadmap", "API REST, RBAC, cache, paginacion servidor, integraciones y E2E."),
    ]
    for col, (title, copy) in zip(grid, cards):
        with col:
            _feature_card(title, copy)


def _render_providers(repo) -> None:
    st.markdown('<div class="section-kicker">Gestion de proveedores</div>', unsafe_allow_html=True)
    df = repo.provider_frame().rename(
        columns={
            "name": "proveedor",
            "country": "pais",
            "method": "metodo",
            "currency": "moneda",
            "status": "estado",
            "fixed_fee": "fee fijo",
            "variable_bps": "variable bps",
            "sla_hours": "sla horas",
        }
    )
    st.dataframe(df, width="stretch", hide_index=True)
    st.caption("Vista MVP: alta/edicion y permisos por proveedor quedan en backlog RBAC.")


def _render_route_wizard(repo) -> None:
    st.markdown('<div class="section-kicker">Constructor wizard de rutas</div>', unsafe_allow_html=True)
    providers = repo.providers()
    provider_options = {f"{provider.name} · {provider.method} · {provider.country}": provider for provider in providers}

    with st.form("cost_jc_route_form", clear_on_submit=True):
        col_a, col_b, col_c = st.columns(3)
        origin = col_a.text_input("Pais origen", value="CL")
        destination = col_b.text_input("Pais destino", value="CO")
        method = col_c.selectbox("Metodo", ["Transfer", "ACH", "Cashout", "Card", "Wallet"])
        provider_label = st.selectbox("Proveedor", list(provider_options.keys()))
        route_name = st.text_input("Nombre de ruta", value=f"{origin} -> {destination} {method}")
        submitted = st.form_submit_button("Crear ruta draft", type="primary")

    if submitted:
        provider = provider_options[provider_label]
        route_id = f"route_{len(repo.routes()) + 1:03d}"
        route = Route(
            id=route_id,
            name=route_name.strip() or f"{origin} -> {destination} {method}",
            origin_country=origin.strip().upper(),
            destination_country=destination.strip().upper(),
            method=method,
            provider_id=provider.id,
            currency=provider.currency,
            status="Draft",
            approval_version="v0.1",
        )
        repo.add_route(route, actor=_current_user())
        st.success(f"Ruta draft creada: {route.name}")
        st.rerun()

    st.markdown('<div class="section-kicker">Rutas existentes</div>', unsafe_allow_html=True)
    st.dataframe(repo.route_frame(), width="stretch", hide_index=True)


def _render_cost_engine(repo) -> None:
    st.markdown('<div class="section-kicker">Motor de costeo</div>', unsafe_allow_html=True)
    result = _simulation_form(repo, form_key="cost_jc_engine_form", button_label="Calcular y guardar simulacion")
    if result is not None:
        repo.save_simulation(result, actor=_current_user())
        _render_simulation_result(result)


def _render_simulator(repo) -> None:
    st.markdown('<div class="section-kicker">Simulador de escenarios</div>', unsafe_allow_html=True)
    route = repo.routes()[0]
    provider = repo.find_provider(route.provider_id)
    rule = repo.rule_for_route(route.id)
    engine = CostJCEngine()
    volumes = [500, 1_000, 2_500, 5_000]
    rows = []
    for volume in volumes:
        result = engine.calculate(
            SimulationInput(
                route_id=route.id,
                provider_id=provider.id,
                amount=25_000,
                volume=volume,
                fx_rate=1,
                provider_fixed_fee=provider.fixed_fee,
                provider_variable_bps=provider.variable_bps,
                method_cost_bps=30,
                revenue_bps=rule.revenue_bps,
                spread_bps=rule.spread_bps,
                tax_rate=rule.tax_rate,
            )
        )
        rows.append(
            {
                "volumen": volume,
                "revenue": result.revenue,
                "costo total": result.total_cost,
                "profit": result.profit,
                "margen %": result.margin_pct,
                "break-even bps": result.break_even_bps,
            }
        )
    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)
    fig = px.line(df, x="volumen", y=["revenue", "costo total", "profit"], markers=True)
    _style_plotly(fig)
    st.plotly_chart(fig, width="stretch")


def _render_dashboard(repo) -> None:
    st.markdown('<div class="section-kicker">Dashboard</div>', unsafe_allow_html=True)
    simulations = repo.simulation_frame()
    if simulations.empty:
        st.info("Aun no hay simulaciones guardadas. Usa el Motor de costeo para alimentar el dashboard.")
        return
    cols = st.columns(3)
    with cols[0]:
        _metric_card("Profit acumulado", format_currency(simulations["profit"].sum()), "Simulaciones guardadas")
    with cols[1]:
        _metric_card("Margen promedio", f"{simulations['margin_pct'].mean():.1f}%", "Promedio simple")
    with cols[2]:
        _metric_card("Break-even", f"{simulations['break_even_bps'].mean():.1f} bps", "Promedio rutas")

    fig = px.bar(simulations, x="route_id", y="profit", color="provider_id")
    _style_plotly(fig)
    st.plotly_chart(fig, width="stretch")


def _render_quality(repo) -> None:
    st.markdown('<div class="section-kicker">Calidad de datos</div>', unsafe_allow_html=True)
    issues = repo.quality_issues()
    if issues.empty:
        st.success("No hay validaciones pendientes.")
        return
    issues["badge"] = issues["severidad"].apply(_severity_badge)
    st.markdown(
        issues[["validacion", "detalle", "badge"]]
        .rename(columns={"badge": "severidad"})
        .to_html(index=False, escape=False, classes="dark-preview-table treasury-html-table"),
        unsafe_allow_html=True,
    )


def _render_audit(repo) -> None:
    st.markdown('<div class="section-kicker">Auditoria</div>', unsafe_allow_html=True)
    st.dataframe(repo.audit_frame(), width="stretch", hide_index=True)


def _render_versions(repo) -> None:
    st.markdown('<div class="section-kicker">Versionado</div>', unsafe_allow_html=True)
    st.dataframe(repo.version_frame(), width="stretch", hide_index=True)


def _render_configuration(repo) -> None:
    st.markdown('<div class="section-kicker">Configuracion</div>', unsafe_allow_html=True)
    st.dataframe(repo.pricing_frame(), width="stretch", hide_index=True)
    st.caption("Las reglas se mantienen versionadas en memoria para el MVP. En fase backend se moveran a persistencia transaccional.")


def _render_integrations() -> None:
    st.markdown('<div class="section-kicker">Integraciones</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    integrations = [
        ("Salesforce", "DTO de oportunidad y pricing request."),
        ("SAP", "Interfaz para costos, centros y aprobaciones."),
        ("Oracle", "Conector planificado para financial master data."),
        ("Webhooks / REST", "Contratos preparados, implementacion futura."),
    ]
    for col, (title, detail) in zip(cols, integrations):
        with col:
            _feature_card(title, detail)


def _simulation_form(repo, *, form_key: str, button_label: str):
    route_options = {route.name: route for route in repo.routes()}
    with st.form(form_key):
        route = route_options[st.selectbox("Ruta", list(route_options.keys()))]
        provider = repo.find_provider(route.provider_id)
        rule = repo.rule_for_route(route.id)
        col_a, col_b, col_c = st.columns(3)
        amount = col_a.number_input("Monto promedio", min_value=1.0, value=25_000.0, step=1_000.0)
        volume = col_b.number_input("Volumen mensual", min_value=1, value=1_000, step=100)
        fx_rate = col_c.number_input("FX rate", min_value=0.0001, value=1.0, step=0.01)

        col_d, col_e, col_f = st.columns(3)
        method_cost_bps = col_d.number_input("Costo metodo bps", min_value=0.0, value=30.0, step=1.0)
        revenue_bps = col_e.number_input("Revenue bps", min_value=0.0, value=float(rule.revenue_bps), step=1.0)
        spread_bps = col_f.number_input("Spread bps", min_value=0.0, value=float(rule.spread_bps), step=1.0)

        col_g, col_h, col_i = st.columns(3)
        tax_rate = col_g.number_input("Impuesto %", min_value=0.0, value=float(rule.tax_rate), step=0.5)
        fixed_fee = col_h.number_input("Fee fijo proveedor", min_value=0.0, value=float(provider.fixed_fee), step=1.0)
        variable_bps = col_i.number_input("Variable proveedor bps", min_value=0.0, value=float(provider.variable_bps), step=1.0)
        extra_cost = st.number_input("Costo extra mensual", min_value=0.0, value=0.0, step=100.0)
        submitted = st.form_submit_button(button_label, type="primary")

    if not submitted:
        return None

    engine = CostJCEngine()
    return engine.calculate(
        SimulationInput(
            route_id=route.id,
            provider_id=provider.id,
            amount=float(amount),
            volume=int(volume),
            fx_rate=float(fx_rate),
            provider_fixed_fee=float(fixed_fee),
            provider_variable_bps=float(variable_bps),
            method_cost_bps=float(method_cost_bps),
            revenue_bps=float(revenue_bps),
            spread_bps=float(spread_bps),
            tax_rate=float(tax_rate),
            extra_cost=float(extra_cost),
        )
    )


def _render_simulation_result(result) -> None:
    st.markdown('<div class="section-kicker">Resultado</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    values = [
        ("Revenue", format_currency(result.revenue), "Ingresos estimados"),
        ("Costo total", format_currency(result.total_cost), "IN + OUT + impuestos"),
        ("Profit", format_currency(result.profit), "Resultado operativo"),
        ("Margen", f"{result.margin_pct:.1f}%", f"ROI {result.roi_pct:.1f}%"),
    ]
    for col, (label, value, detail) in zip(cols, values):
        with col:
            _metric_card(label, value, detail)
    if result.validations:
        for issue in result.validations:
            st.warning(issue)
    else:
        st.success("Simulacion sin alertas de validacion.")


def _average_margin(simulations: list) -> float:
    if not simulations:
        return 0
    return sum(item.margin_pct for item in simulations) / len(simulations)


def _metric_card(label: str, value: str, detail: str) -> None:
    st.markdown(
        '<div class="dashboard-kpi-card cost-jc-kpi">'
        f'<div class="dashboard-kpi-title">{escape(label)}</div>'
        f'<div class="dashboard-kpi-value">{escape(value)}</div>'
        f'<div class="dashboard-kpi-delta muted">{escape(detail)}</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def _feature_card(title: str, copy: str) -> None:
    st.markdown(
        '<div class="feature-card cost-jc-feature">'
        f'<h3>{escape(title)}</h3>'
        f'<p>{escape(copy)}</p>'
        '</div>',
        unsafe_allow_html=True,
    )


def _severity_badge(value: str) -> str:
    classes = {"Alta": "high", "Media": "medium", "Baja": "low"}
    cls = classes.get(value, "medium")
    return f'<span class="severity-badge {cls}">{escape(value)}</span>'


def _style_plotly(fig) -> None:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#CBD5E1",
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor="rgba(148, 163, 184, 0.10)", zerolinecolor="rgba(148, 163, 184, 0.14)")
    fig.update_yaxes(gridcolor="rgba(148, 163, 184, 0.10)", zerolinecolor="rgba(148, 163, 184, 0.14)")


def _current_user() -> str:
    return str(st.session_state.get("current_user") or "usuario")
