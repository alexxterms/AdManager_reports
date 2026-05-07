from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from src.config import Point
from src.models import ConvertedMetrics


def _draw_text(c: canvas.Canvas, point: Point, text: str) -> None:
    c.drawString(point.x, point.y, text)


def build_report_pdf(
    template_path: Path,
    output_path: Path,
    field_coords: dict[str, Point],
    converted: ConvertedMetrics,
) -> Path:
    overlay_path = output_path.with_suffix(".overlay.pdf")

    c = canvas.Canvas(str(overlay_path), pagesize=letter)
    c.setFont("Helvetica", 10)

    _draw_text(c, field_coords["date"], converted.parsed.report_date.strftime("%d/%m/%Y"))
    _draw_text(c, field_coords["spend_usd"], f"${converted.spend_usd:,.2f}")
    _draw_text(c, field_coords["impressions"], f"{converted.parsed.impressions:,}")
    _draw_text(c, field_coords["ctr"], f"{converted.parsed.ctr_percent:.2f}%")
    _draw_text(c, field_coords["link_clicks"], str(converted.parsed.link_clicks))
    _draw_text(c, field_coords["leads"], str(converted.parsed.leads))
    _draw_text(c, field_coords["cpc_usd"], f"${converted.cpc_usd:,.2f}")
    _draw_text(c, field_coords["cpm_usd"], f"${converted.cpm_usd:,.2f}")
    _draw_text(c, field_coords["cpl_usd"], f"${converted.cpl_usd:,.2f}")
    _draw_text(c, field_coords["fx_note"], f"FX CAD->USD: {converted.fx_rate_cad_to_usd:.6f}")

    c.save()

    template_pdf = PdfReader(str(template_path))
    overlay_pdf = PdfReader(str(overlay_path))

    writer = PdfWriter()
    first_page = template_pdf.pages[0]
    first_page.merge_page(overlay_pdf.pages[0])
    writer.add_page(first_page)

    for page in template_pdf.pages[1:]:
        writer.add_page(page)

    with output_path.open("wb") as output_file:
        writer.write(output_file)

    if overlay_path.exists():
        overlay_path.unlink()

    return output_path
