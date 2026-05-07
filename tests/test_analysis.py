from datetime import date

from src.analysis import analyze_metrics
from src.models import ParsedMetrics


def test_analyze_metrics_week_over_week_trends() -> None:
    previous = ParsedMetrics(
        report_date=date(2026, 4, 17),
        spend_cad=5000.00,
        impressions=42000,
        ctr_percent=0.90,
        link_clicks=400,
        leads=45,
        cpc_cad=10.00,
        cpm_cad=90.00,
        cpl_cad=95.00,
    )
    current = ParsedMetrics(
        report_date=date(2026, 4, 24),
        spend_cad=4217.59,
        impressions=38657,
        ctr_percent=0.98,
        link_clicks=379,
        leads=42,
        cpc_cad=11.13,
        cpm_cad=109.10,
        cpl_cad=100.42,
    )

    analysis = analyze_metrics(current, previous)

    assert any("Ad spend decreased week-over-week" in item for item in analysis.problems)
    assert any("CPC increased" in item for item in analysis.problems)
    assert any("CPM increased" in item for item in analysis.problems)
    assert any("Cost per form fill rose" in item for item in analysis.problems)
    assert any("CTR improved slightly" in item for item in analysis.problems)
    assert any("Lead volume remained flat" in item for item in analysis.problems)
    assert any("Stabilize and gradually increase ad spend" in item for item in analysis.solutions)
