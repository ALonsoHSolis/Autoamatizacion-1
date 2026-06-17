from __future__ import annotations

from io import BytesIO

import pandas as pd
from plotly import graph_objects as go
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .business_insights import insights_to_text


def export_excel(sheets: dict[str, pd.DataFrame], insights_text: str) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        for name, df in sheets.items():
            safe_name = name[:31]
            if df is None or df.empty:
                pd.DataFrame({"mensaje": ["Sin datos disponibles"]}).to_excel(writer, sheet_name=safe_name, index=False)
            else:
                df.to_excel(writer, sheet_name=safe_name, index=False)
        pd.DataFrame({"insights": insights_text.splitlines()}).to_excel(writer, sheet_name="Insights ejecutivos", index=False)
        for sheet in writer.sheets.values():
            sheet.set_column(0, 20, 24)
    return output.getvalue()


def _fig_to_image(fig, width=640, height=320):
    """Convert a Plotly figure to PNG bytes via kaleido."""
    try:
        import plotly.io as pio
        return pio.to_image(fig, format="png", width=width, height=height, scale=1.5)
    except Exception:
        return None


def export_pdf(
    title: str,
    profile: dict,
    kpis: pd.DataFrame,
    insights: dict,
    figures: dict[str, go.Figure] | None = None,
) -> bytes:
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import HRFlowable, Image, PageBreak

    output = BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    NAVY = colors.HexColor("#1E3A5F")
    BLUE = colors.HexColor("#2E6DA4")
    LGRAY = colors.HexColor("#F2F5F8")

    title_style = ParagraphStyle("title_s", parent=styles["Title"], textColor=NAVY, fontSize=22, spaceAfter=6)
    h2_style = ParagraphStyle("h2_s", parent=styles["Heading2"], textColor=BLUE, fontSize=14, spaceBefore=14)
    body_style = ParagraphStyle("body_s", parent=styles["BodyText"], fontSize=10, leading=14)
    caption_style = ParagraphStyle("cap_s", parent=styles["BodyText"], fontSize=9, textColor=colors.grey, alignment=TA_CENTER)

    story = []

    # ── Portada ──────────────────────────────────────────────
    story.append(Spacer(1, 1 * inch))
    story.append(Paragraph(title, title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=12))
    story.append(Paragraph("Reporte ejecutivo de análisis de datos", body_style))
    meta_data = [
        ["Registros analizados", str(profile.get("rows", "—"))],
        ["Columnas", str(profile.get("columns", "—"))],
        ["Datos faltantes", f"{profile.get('missing_percent', 0):.1f}%"],
        ["Duplicados", str(profile.get("duplicates", 0))],
    ]
    meta_table = Table(meta_data, colWidths=[2.5 * inch, 2.5 * inch])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LGRAY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, LGRAY]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([Spacer(1, 0.3 * inch), meta_table, PageBreak()])

    # ── KPIs ─────────────────────────────────────────────────
    story.append(Paragraph("KPIs principales", h2_style))
    story.append(HRFlowable(width="100%", thickness=1, color=LGRAY, spaceAfter=8))
    kpi_rows = [["KPI", "Valor", "Interpretación"]]
    for _, row in kpis.head(10).iterrows():
        kpi_rows.append([str(row.get("kpi", "—")), str(row.get("valor", "—")), str(row.get("interpretacion", "—"))])
    kpi_table = Table(kpi_rows, colWidths=[2.2 * inch, 1.4 * inch, 3.4 * inch])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LGRAY]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.extend([kpi_table, PageBreak()])

    # ── Gráficos ─────────────────────────────────────────────
    if figures:
        story.append(Paragraph("Visualizaciones", h2_style))
        story.append(HRFlowable(width="100%", thickness=1, color=LGRAY, spaceAfter=8))
        for fig_name, fig in figures.items():
            img_bytes = _fig_to_image(fig)
            if img_bytes:
                img_io = BytesIO(img_bytes)
                img = Image(img_io, width=6.5 * inch, height=3.2 * inch)
                story.append(img)
                story.append(Paragraph(fig_name, caption_style))
                story.append(Spacer(1, 0.2 * inch))
        story.append(PageBreak())

    # ── Insights ─────────────────────────────────────────────
    story.append(Paragraph("Insights ejecutivos", h2_style))
    story.append(HRFlowable(width="100%", thickness=1, color=LGRAY, spaceAfter=8))
    for line in insights_to_text(insights).splitlines():
        if line.strip():
            style = h2_style if line.startswith("##") else body_style
            story.append(Paragraph(line.replace("##", "").strip(), style))
            story.append(Spacer(1, 4))

    doc.build(story)
    return output.getvalue()
