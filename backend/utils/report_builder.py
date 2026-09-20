"""
Shared report-rendering helpers. Every report in Module 8 has the same
shape — a title, a date range, a table of rows, an optional summary line —
so this builds that once instead of five bespoke layouts.
"""
import csv
import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_csv(headers: list[str], rows: list[list[str]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(headers)
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def build_pdf(
    title: str,
    headers: list[str],
    rows: list[list[str]],
    date_from: date | None = None,
    date_to: date | None = None,
    summary_line: str | None = None,
) -> bytes:
    buffer = io.BytesIO()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"], fontSize=18, textColor=colors.HexColor("#34432F")
    )
    label_style = ParagraphStyle("Label", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#77816F"))

    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        leftMargin=16 * mm,
        rightMargin=16 * mm,
    )
    story = [Paragraph("RK Residency Hub", title_style), Paragraph(title, label_style)]

    if date_from and date_to:
        story.append(Paragraph(f"{date_from.strftime('%d %b %Y')} — {date_to.strftime('%d %b %Y')}", label_style))
    story.append(Spacer(1, 14))

    table_data = [headers] + rows
    if not rows:
        table_data.append(["No data for this period."] + [""] * (len(headers) - 1))

    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1ECE1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#CFC6B4")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAF7F1")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)

    if summary_line:
        story.append(Spacer(1, 14))
        story.append(Paragraph(summary_line, ParagraphStyle("Summary", parent=styles["Normal"], fontSize=10.5, fontName="Helvetica-Bold")))

    doc.build(story)
    return buffer.getvalue()
