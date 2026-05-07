from __future__ import annotations

import re
from datetime import datetime

from src.models import ParsedMetrics

PAYLOAD_REGEX = re.compile(
    r"Date:(?P<date>\d{1,2}/\d{1,2}/\d{4})\s+"
    r"Spend:\s*\$(?P<spend>[\d,.]+)\s+"
    r"Impressions:\s*(?P<impressions>[\d,.]+)\s+"
    r"CTR:\s*(?P<ctr>[\d,.]+)%\s+"
    r"Link Clicks:\s*(?P<link_clicks>[\d,.]+)\s+"
    r"Leads:\s*(?P<leads>[\d,.]+)\s+"
    r"CPC:\s*\$(?P<cpc>[\d,.]+)\s+"
    r"CPM:\s*\$(?P<cpm>[\d,.]+)\s+"
    r"CPL:\s*\$(?P<cpl>[\d,.]+)",
    re.IGNORECASE,
)


def _number(text: str) -> float:
    return float(text.replace(",", ""))


def _integer(text: str) -> int:
    return int(round(_number(text)))


def parse_metrics_message(message_text: str) -> ParsedMetrics:
    match = PAYLOAD_REGEX.search(message_text.strip())
    if not match:
        raise ValueError("Message format is invalid")

    report_date = datetime.strptime(match.group("date"), "%d/%m/%Y").date()

    return ParsedMetrics(
        report_date=report_date,
        spend_cad=_number(match.group("spend")),
        impressions=_integer(match.group("impressions")),
        ctr_percent=_number(match.group("ctr")),
        link_clicks=_integer(match.group("link_clicks")),
        leads=_integer(match.group("leads")),
        cpc_cad=_number(match.group("cpc")),
        cpm_cad=_number(match.group("cpm")),
        cpl_cad=_number(match.group("cpl")),
    )
