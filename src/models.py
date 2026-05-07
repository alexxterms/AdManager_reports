from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class ParsedMetrics:
    report_date: date
    spend_cad: float
    impressions: int
    ctr_percent: float
    link_clicks: int
    leads: int
    cpc_cad: float
    cpm_cad: float
    cpl_cad: float


@dataclass(frozen=True)
class ConvertedMetrics:
    parsed: ParsedMetrics
    fx_rate_cad_to_usd: float
    converted_at_utc: datetime
    spend_usd: float
    cpc_usd: float
    cpm_usd: float
    cpl_usd: float
