from __future__ import annotations

from io import BytesIO

import pandas as pd
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


def export_pdf(title: str, profile: dict, kpis: pd.DataFrame, insights: dict) -> bytes:
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
    story.append(Paragraph("Resumen del dataset", styles["Heading2"]))
    story.append(Paragraph(f"Filas: {profile['rows']} | Columnas: {profile['columns']} | Faltantes: {profile['missing_percent']}%", styles["BodyText"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph("KPIs principales", styles["Heading2"]))
    data = [["KPI", "Valor"]] + kpis[["kpi", "valor"]].head(8).astype(str).values.tolist()
    table = Table(data, hAlign="LEFT")
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#243447")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("GRID", (0, 0), (-1, -1), 0.25, colors.grey)]))
    story.extend([table, Spacer(1, 12), Paragraph("Insights ejecutivos", styles["Heading2"])])
    for line in insights_to_text(insights).splitlines():
        if line.strip():
            story.append(Paragraph(line, styles["BodyText"]))
    doc.build(story)
    return output.getvalue()
