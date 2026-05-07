from __future__ import annotations

import sqlite3
from pathlib import Path


class IdempotencyStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._initialize()

    def _initialize(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_events (
                    event_id TEXT PRIMARY KEY,
                    processed_at_utc TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def is_processed(self, event_id: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT event_id FROM processed_events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
        return row is not None

    def mark_processed(self, event_id: str, processed_at_utc_iso: str) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO processed_events (event_id, processed_at_utc) VALUES (?, ?)",
                (event_id, processed_at_utc_iso),
            )
            conn.commit()
