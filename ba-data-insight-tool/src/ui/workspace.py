"""Workspace entrypoint and switcher for APP BA."""
from __future__ import annotations

from html import escape

import streamlit as st

WORKSPACE_BA = "ba_data"
WORKSPACE_TREASURY = "treasury_tower"
WORKSPACE_RECONCILIATION = "reconciliation_e2e"
WORKSPACE_COST_JC = "cost_jc"

WORKSPACE_LABELS = {
    WORKSPACE_BA: "BA Insight",
    WORKSPACE_TREASURY: "Treasury Tower",
    WORKSPACE_RECONCILIATION: "ReconciliationE2E",
    WORKSPACE_COST_JC: "Model of Costs",
}

WORKSPACE_OPTIONS = [WORKSPACE_BA, WORKSPACE_TREASURY, WORKSPACE_RECONCILIATION, WORKSPACE_COST_JC]


def set_active_workspace(workspace: str) -> None:
    if workspace in WORKSPACE_OPTIONS:
        st.session_state["active_workspace"] = workspace


def render_workspace_landing() -> None:
    """First view: choose which workspace to enter."""
    st.markdown(
        '<div class="workspace-landing">'
        '<div class="workspace-kicker">Bienvenido</div>'
        '<h1>Selecciona tu espacio de trabajo</h1>'
        '<p>Elige el modulo que quieres abrir. '
        '<span translate="no" class="notranslate">BA Insight</span> esta activo; '
        '<span translate="no" class="notranslate">Treasury Tower</span>, '
        '<span translate="no" class="notranslate">ReconciliationE2E</span> y '
        '<span translate="no" class="notranslate">Model of Costs</span> estan disponibles como MVP en desarrollo.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    row_one = st.columns(2, gap="large")
    _render_workspace_card(
        row_one[0],
        workspace=WORKSPACE_BA,
        icon="BA",
        title="BA Insight",
        description="Analiza archivos, confirma columnas, revisa KPIs, calidad de datos, insights y exporta informes.",
        badge="Activo",
        icon_class="blue",
        is_active=True,
        button_key="workspace_enter_ba",
        primary=True,
    )
    _render_workspace_card(
        row_one[1],
        workspace=WORKSPACE_TREASURY,
        icon="TT",
        title="Treasury Tower",
        description="MVP para tesoreria, liquidez, posicion de caja, informes y control financiero.",
        badge="MVP en desarrollo",
        icon_class="amber",
        button_key="workspace_enter_treasury",
    )

    row_two = st.columns(2, gap="large")
    _render_workspace_card(
        row_two[0],
        workspace=WORKSPACE_RECONCILIATION,
        icon="R2",
        title="ReconciliationE2E",
        description="MVP para conciliacion end-to-end, seguimiento de diferencias, evidencias y cierre operativo.",
        badge="MVP en desarrollo",
        icon_class="violet",
        button_key="workspace_enter_reconciliation",
    )
    _render_workspace_card(
        row_two[1],
        workspace=WORKSPACE_COST_JC,
        icon="MC",
        title="Model of Costs",
        description="MVP para modelado de costos, pricing, rutas, trazabilidad y desviaciones presupuestarias.",
        badge="MVP en desarrollo",
        icon_class="green",
        button_key="workspace_enter_cost_jc",
    )


def _render_workspace_card(
    target,
    *,
    workspace: str,
    icon: str,
    title: str,
    description: str,
    badge: str,
    icon_class: str,
    button_key: str,
    is_active: bool = False,
    primary: bool = False,
) -> None:
    active_class = " workspace-card-active" if is_active else ""
    badge_class = "active" if is_active else "pending"
    with target:
        st.markdown(
            f'<div class="workspace-card{active_class}">'
            '<div class="workspace-card-top">'
            f'<div class="workspace-icon {icon_class} notranslate" translate="no">{escape(icon)}</div>'
            f'<span class="workspace-badge {badge_class}">{escape(badge)}</span>'
            '</div>'
            f'<h2 class="notranslate" translate="no">{escape(title)}</h2>'
            f'<p>{escape(description)}</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        button_kwargs = {"key": button_key, "width": "stretch"}
        if primary:
            button_kwargs["type"] = "primary"
        if st.button("Entrar", **button_kwargs):
            set_active_workspace(workspace)
            st.rerun()


def render_workspace_switcher() -> str:
    """Persistent top selector once a workspace is active."""
    current = st.session_state.get("active_workspace", WORKSPACE_BA)
    if current not in WORKSPACE_OPTIONS:
        current = WORKSPACE_BA
        st.session_state["active_workspace"] = current

    label_by_value = WORKSPACE_LABELS
    current_index = WORKSPACE_OPTIONS.index(current)

    left, right = st.columns([0.74, 0.26], vertical_alignment="center")
    with left:
        st.markdown(
            '<div class="workspace-topbar-title">'
            '<span>Espacio de trabajo</span>'
            f'<strong class="notranslate" translate="no">{escape(label_by_value[current])}</strong>'
            '</div>',
            unsafe_allow_html=True,
        )
    with right:
        selected = st.selectbox(
            "Cambiar espacio",
            WORKSPACE_OPTIONS,
            index=current_index,
            format_func=lambda value: label_by_value[value],
            key=f"workspace_switcher_{current}",
            label_visibility="collapsed",
        )

    if selected != current:
        set_active_workspace(selected)
        st.rerun()

    return current


def render_treasury_workspace() -> None:
    from src.ui.treasury import render_treasury_app

    render_treasury_app()


def render_workspace_mvp_placeholder(workspace: str) -> None:
    title = WORKSPACE_LABELS.get(workspace, "Modulo")
    descriptions = {
        WORKSPACE_RECONCILIATION: (
            "Este MVP queda preparado para flujos de conciliacion end-to-end, "
            "gestion de diferencias y seguimiento de cierres."
        ),
        WORKSPACE_COST_JC: (
            "Este MVP queda preparado para modelado de costos, pricing, "
            "trazabilidad y alertas de desviacion."
        ),
    }
    st.markdown(
        '<div class="treasury-placeholder workspace-mvp-placeholder">'
        f'<div class="workspace-kicker notranslate" translate="no">{escape(title)}</div>'
        '<h1>MVP en desarrollo</h1>'
        f'<p>{escape(descriptions.get(workspace, "Este espacio esta reservado para una proxima etapa."))}</p>'
        '<div class="treasury-placeholder-grid">'
        '<div><span>01</span><strong>Entrada lista</strong><p>El modulo ya esta visible en la pagina principal.</p></div>'
        '<div><span>02</span><strong>Navegacion conectada</strong><p>Puedes volver o cambiar de espacio desde el selector superior.</p></div>'
        '<div><span>03</span><strong>Proxima etapa</strong><p>La logica funcional se implementara cuando se defina el alcance operativo.</p></div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_treasury_coming_soon() -> None:
    st.markdown(
        '<div class="treasury-placeholder">'
        '<div class="workspace-kicker notranslate" translate="no">TREASURY TOWER</div>'
        '<h1>Proximamente</h1>'
        '<p>Este espacio esta reservado para <span translate="no" class="notranslate">Treasury Tower</span>. '
        'La entrada ya esta conectada, pero la logica funcional se implementara en una siguiente etapa.</p>'
        '<div class="treasury-placeholder-grid">'
        '<div><span>01</span><strong>Liquidez</strong><p>Vista futura de caja, bancos y saldos operativos.</p></div>'
        '<div><span>02</span><strong>Pagos</strong><p>Control de compromisos, vencimientos y prioridades.</p></div>'
        '<div><span>03</span><strong>Riesgo</strong><p>Alertas de tension de caja y cobertura.</p></div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )
