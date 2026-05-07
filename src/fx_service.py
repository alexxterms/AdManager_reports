from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import requests

from src.models import ConvertedMetrics, ParsedMetrics


@dataclass
class FxCache:
    rate: float | None = None
    fetched_at: datetime | None = None


class FxService:
    def __init__(self, api_url: str, api_key: str | None, timeout_seconds: int, ttl_seconds: int) -> None:
        self.api_url = api_url
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.ttl = timedelta(seconds=ttl_seconds)
        self.cache = FxCache()

    def get_cad_to_usd_rate(self) -> float:
        now = datetime.now(timezone.utc)
        if self.cache.rate is not None and self.cache.fetched_at is not None:
            if now - self.cache.fetched_at <= self.ttl:
                return self.cache.rate

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = requests.get(self.api_url, timeout=self.timeout_seconds, headers=headers)
        response.raise_for_status()
        payload = response.json()

        rates = payload.get("rates", {})
        usd_rate = rates.get("USD")
        if usd_rate is None:
            raise ValueError("FX API response does not include USD rate")

        self.cache = FxCache(rate=float(usd_rate), fetched_at=now)
        return float(usd_rate)

    def convert(self, parsed: ParsedMetrics) -> ConvertedMetrics:
        rate = self.get_cad_to_usd_rate()
        converted_at = datetime.now(timezone.utc)
        return ConvertedMetrics(
            parsed=parsed,
            fx_rate_cad_to_usd=rate,
            converted_at_utc=converted_at,
            spend_usd=round(parsed.spend_cad * rate, 2),
            cpc_usd=round(parsed.cpc_cad * rate, 2),
            cpm_usd=round(parsed.cpm_cad * rate, 2),
            cpl_usd=round(parsed.cpl_cad * rate, 2),
        )
