from src.parser import parse_metrics_message


def test_parse_metrics_message_valid_payload() -> None:
    text = (
        "Date:24/4/2026 Spend: $4217.59 Impressions: 38,657 CTR: 0.98% "
        "Link Clicks: 379 Leads: 42 CPC: $11.13 CPM: $109.10 CPL: $100.42"
    )
    parsed = parse_metrics_message(text)

    assert parsed.report_date.day == 24
    assert parsed.report_date.month == 4
    assert parsed.report_date.year == 2026
    assert parsed.spend_cad == 4217.59
    assert parsed.impressions == 38657
    assert parsed.ctr_percent == 0.98
    assert parsed.link_clicks == 379
    assert parsed.leads == 42
    assert parsed.cpc_cad == 11.13
    assert parsed.cpm_cad == 109.10
    assert parsed.cpl_cad == 100.42


def test_parse_metrics_message_invalid_payload() -> None:
    text = "Date:24/4/2026 Spend: $4217.59 Incomplete"
    try:
        parse_metrics_message(text)
    except ValueError as exc:
        assert "invalid" in str(exc).lower()
    else:
        raise AssertionError("Expected ValueError for malformed payload")
