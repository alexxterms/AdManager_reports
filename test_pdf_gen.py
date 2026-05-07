import sys
sys.path.insert(0, '.')

from pathlib import Path
from src.html_renderer import render_report_html

# Sample metrics data
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

output_path = Path("output/test_report.pdf")
try:
    result = render_report_html(
        current_metrics=current_metrics,
        previous_metrics=previous_metrics,
        problems=problems,
        solutions=solutions,
        output_path=output_path,
        report_date="May 7, 2026"
    )
    print(f"✓ PDF generated successfully: {result}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
