from datetime import datetime, timezone

from src.fx_service import FxService
from src.models import ParsedMetrics


class StubFxService(FxService):
    def get_cad_to_usd_rate(self) -> float:
        return 0.73


def test_convert_rounded_values() -> None:
    service = StubFxService(
        api_url="https://example.com",
        api_key=None,
        timeout_seconds=5,
        ttl_seconds=1800,
    )
    parsed = ParsedMetrics(
        report_date=datetime(2026, 4, 24, tzinfo=timezone.utc).date(),
        spend_cad=4217.59,
        impressions=38657,
        ctr_percent=0.98,
        link_clicks=379,
        leads=42,
        cpc_cad=11.13,
        cpm_cad=109.10,
        cpl_cad=100.42,
    )

    converted = service.convert(parsed)

    assert converted.fx_rate_cad_to_usd == 0.73
    assert converted.spend_usd == round(4217.59 * 0.73, 2)
    assert converted.cpc_usd == round(11.13 * 0.73, 2)
    assert converted.cpm_usd == round(109.10 * 0.73, 2)
    assert converted.cpl_usd == round(100.42 * 0.73, 2)
