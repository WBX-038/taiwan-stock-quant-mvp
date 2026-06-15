import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SQLiteCache:
    def __init__(self, db_path: str) -> None:
        self.db_path = Path(db_path)
        self._init()

    def _init(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def get(self, key: str) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT value FROM cache WHERE key = ?", (key,)).fetchone()
        if not row:
            return None
        return json.loads(row[0])

    def set(self, key: str, value: dict[str, Any]) -> None:
        payload = json.dumps(value, ensure_ascii=False, default=str)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, updated_at) VALUES (?, ?, ?)",
                (key, payload, datetime.now(timezone.utc).isoformat()),
            )
