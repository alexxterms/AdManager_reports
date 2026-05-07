import sys
import os
from pathlib import Path
sys.path.insert(0, '.')

from src.html_renderer import render_report_html

def main():
    # usage: python test_pdf_offset.py <metrics_offset_mm> [<problems_offset_mm> <opportunities_offset_mm>]
    metrics_offset = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    problems_offset = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    opportunities_offset = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    current_metrics = {
        "ad_spend": 141.52,
        "ctr": 1.03,
        "cpc": 7.16,
        "cpm": 73.37,
        "form_fills": 0,
        "cost_per_form_fill": 72.41,
        "sales": 0,
        "cost_per_sale": 0,
        "revenue": 0,
        "roas": 0,
    }
    previous_metrics = {
        "ad_spend": 143.99,
        "ctr": 0.98,
        "cpc": 7.98,
        "cpm": 78.22,
        "form_fills": 1,
        "cost_per_form_fill": 72.00,
        "sales": 0,
        "cost_per_sale": 0,
        "revenue": 0,
        "roas": 0,
    }
    problems = [
        "Ad spend decreased week-over-week, limiting reach.",
        "CPC and CPM increased, reducing cost efficiency.",
        "Cost per form fill rose slightly.",
    ]
    solutions = [
        "Increase ad spend to improve data volume.",
        "Test new creatives to improve CTR.",
        "Optimize targeting to reduce costs.",
    ]

    out = Path('output') / f'test_report_offsets_{int(metrics_offset)}-{int(problems_offset)}-{int(opportunities_offset)}mm.pdf'
    render_report_html(
        current_metrics=current_metrics,
        previous_metrics=previous_metrics,
        problems=problems,
        solutions=solutions,
        output_path=out,
        report_date='May 7, 2026',
        content_offset_mm=0.0,
        metrics_offset_mm=metrics_offset,
        problems_offset_mm=problems_offset,
        opportunities_offset_mm=opportunities_offset,
        template_dir='.'
    )
    print(f'Generated: {out}')
    try:
        os.startfile(str(out))
    except Exception:
        print('Open the PDF manually at', out)

if __name__ == '__main__':
    main()
