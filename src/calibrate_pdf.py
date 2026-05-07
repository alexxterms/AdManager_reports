from __future__ import annotations

import json
import sys
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as pdf_canvas
from pypdf import PdfReader, PdfWriter


def calibrate_pdf(template_path: Path, output_path: Path) -> None:
    test_fields = {
        "date": (80, 725),
        "spend_usd": (80, 700),
        "impressions": (80, 675),
        "ctr": (80, 650),
        "link_clicks": (80, 625),
        "leads": (80, 600),
        "cpc_usd": (80, 575),
        "cpm_usd": (80, 550),
        "cpl_usd": (80, 525),
        "fx_note": (80, 500),
    }

    overlay_path = output_path.with_suffix(".overlay.pdf")

    c = pdf_canvas.Canvas(str(overlay_path), pagesize=letter)
    c.setFont("Helvetica", 10)

    text_samples = {
        "date": "24/04/2026",
        "spend_usd": "$3,078.84",
        "impressions": "38,657",
        "ctr": "0.98%",
        "link_clicks": "379",
        "leads": "42",
        "cpc_usd": "$8.13",
        "cpm_usd": "$79.64",
        "cpl_usd": "$73.30",
        "fx_note": "FX CAD->USD: 0.730000",
    }

    for field_name, (x, y) in test_fields.items():
        text = f"[{field_name}] {text_samples[field_name]}"
        c.drawString(x, y, text)

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

    print(f"✓ Calibration PDF created: {output_path}")
    print(f"✓ Check placement visually and adjust PDF_FIELD_COORDS_JSON as needed.")


if __name__ == "__main__":
    template_file = Path("(BIAB - Weekly) (5126) (2).pdf")
    if not template_file.exists():
        print(f"✗ Template PDF not found: {template_file}")
        sys.exit(1)

    output_file = Path("calibration_test.pdf")
    calibrate_pdf(template_file, output_file)
