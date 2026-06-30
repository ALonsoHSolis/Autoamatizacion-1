"""Treasury Tower MVP UI."""
from __future__ import annotations

from datetime import date
from html import escape

import pandas as pd
import streamlit as st

from src.data_loader import load_data, load_google_sheet
from src.export_utils import export_excel, export_pdf, export_pptx
from src.treasury_repository import create_treasury_repository
from src.utils import format_currency, format_number


TREASURY_SECTIONS = [
    "Panel de liquidez",
    "Conciliación diaria",
    "Informes",
    "Comunicación",
]


def render_treasury_app() -> None:
    store = st.session_state.setdefault("_treasury_store", {})
    repo = create_treasury_repository(store)
    migration_ok = _initialize_treasury_schema(repo)

    st.markdown(
        '<div class="treasury-header">'
        '<div class="workspace-kicker notranslate" translate="no">TREASURY TOWER</div>'
        '<h1>Centro de tesorería</h1>'
        '<p>Liquidez, conciliación diaria, informes y coordinación operativa en un solo espacio.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    _render_treasury_status(repo, migration_ok)

    if st.session_state.get("treasury_section") not in TREASURY_SECTIONS:
        st.session_state["treasury_section"] = TREASURY_SECTIONS[0]
    st.radio(
        "Secciones Treasury",
        TREASURY_SECTIONS,
        key="treasury_section",
        horizontal=True,
        label_visibility="collapsed",
    )

    section = st.session_state["treasury_section"]
    if section == "Panel de liquidez":
        _render_liquidity_panel(repo)
    elif section == "Conciliación diaria":
        _render_reconciliation_console(repo)
    elif section == "Informes":
        _render_reports(repo)
    else:
        _render_communications(repo)


def _initialize_treasury_schema(repo) -> bool:
    try:
        repo.initialize_schema()
        return True
    except Exception as exc:
        st.error("No pudimos inicializar el esquema de Treasury Tower.")
        with st.expander("Ver detalle técnico"):
            st.code(str(exc))
        return False


def _render_treasury_status(repo, migration_ok: bool) -> None:
    if repo.is_mysql:
        badge = "MySQL conectado" if migration_ok else "MySQL con error"
        cls = "ok" if migration_ok else "alert"
        desc = "Las tablas Treasury se inicializan con la migración versionada." if migration_ok else "Revisa credenciales o permisos de la base."
    else:
        badge = "Demo en memoria"
        cls = "warn"
        desc = "Configura TREASURY_DATABASE_URL o DATABASE_URL con mysql+pymysql:// para persistir en MySQL."
    st.markdown(
        f'<div class="treasury-status-card {cls}">'
        f'<strong>{escape(badge)}</strong>'
        f'<span>{escape(desc)}</span>'
        '</div>',
        unsafe_allow_html=True,
    )


def _render_liquidity_panel(repo) -> None:
    st.markdown('<div class="section-kicker">Fuentes de saldos</div>', unsafe_allow_html=True)
    source_col, sheet_col = st.columns([1.1, 0.9], gap="large")

    with source_col:
        with st.container(border=False):
            st.markdown(
                '<div class="treasury-panel-card">'
                '<h3>Carga manual</h3>'
                '<p>Archivo CSV/XLSX con columnas mínimas: cuenta, fecha y saldo. Opcionales: saldo_extracto, banco, moneda, reserva_minima.</p>'
                '</div>',
                unsafe_allow_html=True,
            )
            uploaded = st.file_uploader(
                "Archivo de saldos",
                type=["csv", "xlsx", "xls"],
                key="treasury_balance_file",
            )
            if st.button("Cargar saldos", key="treasury_upload_balances", type="primary", disabled=uploaded is None):
                try:
                    df = load_data(uploaded, uploaded.name)
                    loaded = repo.upsert_balances(df, fuente="archivo", cargado_por=_current_user())
                    st.success(f"{loaded} saldo(s) cargado(s) desde archivo.")
                except Exception as exc:
                    st.error("No pudimos cargar el archivo de saldos.")
                    st.caption(str(exc))

    with sheet_col:
        st.markdown(
            '<div class="treasury-panel-card">'
            '<h3>Google Sheet compartido</h3>'
            '<p>Lee una URL pública bajo demanda. No se sincroniza automáticamente en cada refresh.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        sheet_url = st.text_input(
            "URL de Google Sheets",
            placeholder="https://docs.google.com/spreadsheets/d/...",
            key="treasury_sheet_url",
        )
        if st.button("Sincronizar ahora", key="treasury_sync_sheet", disabled=not sheet_url):
            try:
                df = load_google_sheet(sheet_url)
                loaded = repo.upsert_balances(df, fuente="google_sheet", cargado_por=_current_user())
                st.success(f"{loaded} saldo(s) sincronizado(s) desde Google Sheet.")
            except Exception as exc:
                st.error("No pudimos sincronizar el Google Sheet.")
                st.caption(str(exc))

    latest = repo.latest_balances()
    st.markdown('<div class="section-kicker">Panel de liquidez</div>', unsafe_allow_html=True)
    if latest.empty:
        st.info("Aún no hay saldos cargados.")
        return

    total = float(latest["saldo_interno"].fillna(0).sum())
    cols = st.columns(min(4, max(1, len(latest) + 1)))
    with cols[0]:
        _metric_card("Disponible consolidado", format_currency(total), "Último saldo interno por cuenta")
    for col, (_, row) in zip(cols[1:], latest.head(len(cols) - 1).iterrows()):
        with col:
            _metric_card(str(row["cuenta"]), format_currency(row["saldo_interno"]), str(row.get("moneda", "CLP")))

    table = latest.copy()
    table["saldo"] = table["saldo_interno"].apply(format_currency)
    table["reserva mínima"] = table["reserva_minima"].apply(format_currency)
    table["estado"] = table["estado"].apply(_status_badge)
    display = table[["cuenta", "moneda", "fecha", "saldo", "reserva mínima", "estado"]]
    st.markdown('<div class="section-kicker">Reservas mínimas</div>', unsafe_allow_html=True)
    st.markdown(display.to_html(index=False, escape=False, classes="dark-preview-table treasury-html-table"), unsafe_allow_html=True)


def _render_reconciliation_console(repo) -> None:
    selected_date = st.date_input("Fecha de conciliación", value=date.today(), key="treasury_reconciliation_date")
    balances = repo.balances_for_date(selected_date)

    st.markdown('<div class="section-kicker">Consola de conciliación diaria</div>', unsafe_allow_html=True)
    if balances.empty:
        st.info("No hay saldos para la fecha seleccionada.")
    else:
        display = balances.copy()
        for col in ["saldo_interno", "saldo_extracto", "diferencia"]:
            display[col] = display[col].apply(lambda value: "—" if pd.isna(value) else format_currency(value))
        st.dataframe(display[["cuenta", "saldo_interno", "saldo_extracto", "diferencia"]], width="stretch", hide_index=True)

    if st.button("Detectar discrepancias", key="treasury_detect_discrepancies", type="primary", disabled=balances.empty):
        created = repo.detect_discrepancies(selected_date)
        st.success(f"{created} discrepancia(s) abierta(s) detectada(s) o reutilizadas.")
        st.rerun()

    open_discrepancies = repo.open_discrepancies(selected_date)
    st.markdown('<div class="section-kicker">Acción correctiva</div>', unsafe_allow_html=True)
    if open_discrepancies.empty:
        st.caption("No hay discrepancias abiertas para esta fecha.")
    else:
        options = open_discrepancies["id"].tolist()
        labels = {
            row["id"]: f"{row['cuenta']} · {format_currency(row['diferencia'])}"
            for _, row in open_discrepancies.iterrows()
        }
        selected = st.selectbox(
            "Discrepancia abierta",
            options,
            format_func=lambda value: labels.get(value, str(value)),
            key="treasury_open_discrepancy",
        )
        action = st.text_area("Acción registrada", key="treasury_action_text", placeholder="Ej: Se valida cartola y se solicita ajuste contable.")
        if st.button("Registrar acción", key="treasury_register_action", disabled=not action.strip()):
            repo.register_action(int(selected), action.strip(), registrado_por=_current_user())
            st.success("Acción registrada y discrepancia cerrada.")
            st.rerun()

    actions = repo.actions_for_date(selected_date)
    st.markdown('<div class="section-kicker">Acciones registradas</div>', unsafe_allow_html=True)
    if actions.empty:
        st.caption("Sin acciones registradas para esta fecha.")
    else:
        st.dataframe(actions[["cuenta", "fecha", "diferencia", "descripcion", "registrado_por", "registrado_en"]], width="stretch", hide_index=True)


def _render_reports(repo) -> None:
    st.markdown('<div class="section-kicker">Generador de informes</div>', unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([0.22, 0.22, 0.56])
    with col_a:
        start_date = st.date_input("Desde", value=date.today(), key="treasury_report_start")
    with col_b:
        end_date = st.date_input("Hasta", value=date.today(), key="treasury_report_end")
    with col_c:
        fmt = st.selectbox("Formato", ["PDF", "PowerPoint", "Excel"], key="treasury_report_format")

    include_liquidity = st.checkbox("Liquidez", value=True, key="treasury_report_liquidity")
    st.checkbox("Conciliación avanzada (próximamente)", value=False, disabled=True)
    st.checkbox("Riesgo de caja (próximamente)", value=False, disabled=True)

    if st.button("Generar informe", key="treasury_generate_report", type="primary", disabled=not include_liquidity):
        try:
            content, filename = _build_report(repo, start_date, end_date, fmt)
            report_id = repo.save_report(
                start_date,
                end_date,
                ["Liquidez"],
                fmt,
                generado_por=_current_user(),
                filename=filename,
                content=content,
            )
            st.session_state[f"treasury_report_{report_id}"] = content
            st.success(f"Informe generado: {filename}")
        except Exception as exc:
            st.error("No pudimos generar el informe.")
            st.caption(str(exc))

    recent = repo.recent_reports()
    st.markdown('<div class="section-kicker">Informes recientes</div>', unsafe_allow_html=True)
    if recent.empty:
        st.caption("Aún no hay informes generados.")
        return
    for _, row in recent.head(8).iterrows():
        content = row.get("contenido")
        if isinstance(content, memoryview):
            content = content.tobytes()
        if not content:
            content = st.session_state.get(f"treasury_report_{row['id']}", b"")
        cols = st.columns([0.62, 0.18, 0.20], vertical_alignment="center")
        cols[0].markdown(f"**{row.get('nombre_archivo') or 'informe'}**  \n{row.get('periodo_desde')} → {row.get('periodo_hasta')}")
        cols[1].caption(str(row.get("formato", "")))
        cols[2].download_button(
            "Descargar",
            data=bytes(content or b""),
            file_name=row.get("nombre_archivo") or "treasury_report.bin",
            key=f"download_treasury_report_{row['id']}",
            disabled=not bool(content),
        )


def _render_communications(repo) -> None:
    st.markdown('<div class="section-kicker">Comunicación con proveedores y áreas</div>', unsafe_allow_html=True)
    with st.form("treasury_note_form", clear_on_submit=True):
        col_a, col_b = st.columns(2)
        author = col_a.text_input("Autor", value=_current_user())
        area = col_b.text_input("Área", placeholder="Ej: Finanzas, Operaciones, Proveedores")
        message = st.text_area("Mensaje", placeholder="Registra acuerdos, solicitudes o pendientes de coordinación.")
        submitted = st.form_submit_button("Agregar nota", type="primary")
    if submitted:
        if not author.strip() or not area.strip() or not message.strip():
            st.warning("Completa autor, área y mensaje.")
        else:
            repo.add_note(author.strip(), area.strip(), message.strip())
            st.success("Nota agregada.")
            st.rerun()

    notes = repo.notes()
    if notes.empty:
        st.caption("Sin notas registradas.")
        return
    for _, row in notes.iterrows():
        st.markdown(
            '<div class="treasury-note">'
            f'<div><strong>{escape(str(row.get("area", "")))}</strong>'
            f'<span>{escape(str(row.get("creado_en", "")))}</span></div>'
            f'<p>{escape(str(row.get("mensaje", "")))}</p>'
            f'<small>{escape(str(row.get("autor", "")))}</small>'
            '</div>',
            unsafe_allow_html=True,
        )


def _build_report(repo, start_date: date, end_date: date, fmt: str) -> tuple[bytes, str]:
    saldos, acciones = repo.period_data(start_date, end_date)
    latest = repo.latest_balances()
    total = float(latest["saldo_interno"].fillna(0).sum()) if not latest.empty else 0
    below = int((latest["estado"] == "Alerta").sum()) if not latest.empty and "estado" in latest else 0
    profile = {
        "rows": len(saldos),
        "columns": len(saldos.columns) if not saldos.empty else 0,
        "missing_percent": 0,
        "duplicates": 0,
    }
    kpis = pd.DataFrame([
        {"kpi": "Disponible consolidado", "valor": format_currency(total), "interpretacion": "Último saldo interno por cuenta activa."},
        {"kpi": "Cuentas bajo reserva", "valor": format_number(below), "interpretacion": "Cuentas con saldo menor a la reserva mínima."},
        {"kpi": "Acciones correctivas", "valor": format_number(len(acciones)), "interpretacion": "Acciones registradas en el período."},
    ])
    insights = {
        "resumen_ejecutivo": f"Reporte Treasury Tower del {start_date} al {end_date}. Disponible consolidado: {format_currency(total)}.",
        "hallazgos": ["Liquidez calculada con últimos saldos internos disponibles.", f"{below} cuenta(s) bajo reserva mínima."],
        "riesgos": ["Revisar cuentas bajo reserva y discrepancias abiertas antes de ejecutar pagos críticos."],
        "hipotesis": ["Las variaciones pueden responder a cargas manuales, timing bancario o registros pendientes."],
        "preguntas_negocio": ["¿Qué cuenta requiere fondeo o ajuste operativo hoy?"],
        "acciones_recomendadas": ["Cerrar discrepancias abiertas y documentar acuerdos con áreas responsables."],
        "proximos_pasos": ["Automatizar fuentes bancarias en una fase futura."],
    }

    suffix = fmt.lower().replace("powerpoint", "pptx")
    filename = f"treasury_tower_{start_date}_{end_date}.{suffix if suffix != 'pdf' else 'pdf'}"
    if fmt == "Excel":
        content = export_excel({"Liquidez": latest, "Saldos periodo": saldos, "Acciones": acciones}, insights["resumen_ejecutivo"])
        filename = filename.replace(".excel", ".xlsx")
    elif fmt == "PowerPoint":
        content = export_pptx("Treasury Tower", profile, kpis, insights, figures=None)
        filename = filename.replace(".pptx", ".pptx")
    else:
        content = export_pdf("Treasury Tower", profile, kpis, insights, figures=None)
    return content, filename


def _metric_card(label: str, value: str, detail: str) -> None:
    st.markdown(
        '<div class="dashboard-kpi-card">'
        f'<div class="dashboard-kpi-title">{escape(label)}</div>'
        f'<div class="dashboard-kpi-value">{escape(value)}</div>'
        f'<div class="dashboard-kpi-delta muted">{escape(detail)}</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def _status_badge(value: str) -> str:
    cls = "low" if value == "OK" else "high"
    return f'<span class="severity-badge {cls}">{escape(value)}</span>'


def _current_user() -> str:
    return str(st.session_state.get("current_user") or "usuario")
