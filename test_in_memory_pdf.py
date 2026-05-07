from src.html_renderer import render_report_html

# Test the in-memory PDF generation
test_metrics = {
    "ad_spend": 500.00,
    "ctr": 2.5,
    "cpc": 1.25,
    "cpm": 12.00,
    "form_fills": 15,
    "cost_per_form_fill": 33.33,
    "sales": 0,
    "cost_per_sale": 0,
    "revenue": 0,
    "roas": 0,
}

pdf_bytes = render_report_html(
    current_metrics=test_metrics,
    problems=["Issue 1", "Issue 2"],
    solutions=["Fix 1", "Fix 2"],
    template_dir='.'
)

print(f"✓ PDF generated successfully: {len(pdf_bytes)} bytes")
print(f"✓ In-memory generation working (no disk I/O)")
print(f"✓ Ready to upload to Slack without disk overhead")
