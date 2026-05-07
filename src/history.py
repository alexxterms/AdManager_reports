from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.models import ParsedMetrics


class MetricsHistoryStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._initialize()

    def _initialize(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metrics_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_id TEXT NOT NULL,
                    report_date TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    stored_at_utc TEXT NOT NULL,
                    UNIQUE(channel_id, report_date)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_channel_date ON metrics_history(channel_id, report_date DESC)"
            )
            conn.commit()

    def get_previous(self, channel_id: str) -> ParsedMetrics | None:
        """Get the most recent metrics record for a channel (typically the previous week)."""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                """
                SELECT payload_json FROM metrics_history 
                WHERE channel_id = ? 
                ORDER BY report_date DESC 
                LIMIT 1
                """,
                (channel_id,),
            ).fetchone()
        if row is None:
            return None

        payload = json.loads(row[0])
        return ParsedMetrics(
            report_date=datetime.strptime(payload["report_date"], "%Y-%m-%d").date(),
            spend_cad=float(payload["spend_cad"]),
            impressions=int(payload["impressions"]),
            ctr_percent=float(payload["ctr_percent"]),
            link_clicks=int(payload["link_clicks"]),
            leads=int(payload["leads"]),
            cpc_cad=float(payload["cpc_cad"]),
            cpm_cad=float(payload["cpm_cad"]),
            cpl_cad=float(payload["cpl_cad"]),
        )

    def get_history(self, channel_id: str, days: int | None = None) -> list[ParsedMetrics]:
        """
        Get historical metrics for a channel.
        
        Args:
            channel_id: The Slack channel ID
            days: Optional; if set, return records from the last N days. If None, return all records.
        
        Returns:
            List of ParsedMetrics ordered by most recent first
        """
        with sqlite3.connect(self.db_path) as conn:
            if days is not None:
                cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
                rows = conn.execute(
                    """
                    SELECT payload_json FROM metrics_history 
                    WHERE channel_id = ? AND stored_at_utc >= ? 
                    ORDER BY report_date DESC
                    """,
                    (channel_id, cutoff_date),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT payload_json FROM metrics_history 
                    WHERE channel_id = ? 
                    ORDER BY report_date DESC
                    """,
                    (channel_id,),
                ).fetchall()

        history = []
        for row in rows:
            payload = json.loads(row[0])
            history.append(
                ParsedMetrics(
                    report_date=datetime.strptime(payload["report_date"], "%Y-%m-%d").date(),
                    spend_cad=float(payload["spend_cad"]),
                    impressions=int(payload["impressions"]),
                    ctr_percent=float(payload["ctr_percent"]),
                    link_clicks=int(payload["link_clicks"]),
                    leads=int(payload["leads"]),
                    cpc_cad=float(payload["cpc_cad"]),
                    cpm_cad=float(payload["cpm_cad"]),
                    cpl_cad=float(payload["cpl_cad"]),
                )
            )
        return history

    def store(self, channel_id: str, parsed: ParsedMetrics) -> None:
        """Store a new metrics record. Duplicate (channel_id, report_date) pairs are ignored."""
        payload = asdict(parsed)
        payload["report_date"] = parsed.report_date.isoformat()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO metrics_history (channel_id, report_date, payload_json, stored_at_utc)
                VALUES (?, ?, ?, ?)
                """,
                (
                    channel_id,
                    parsed.report_date.isoformat(),
                    json.dumps(payload),
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
