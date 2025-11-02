"""SQLite backed cache implementation."""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Optional

from .config import settings
from .logging import get_logger

LOGGER = get_logger(__name__)


class SQLiteCache:
    """A lightweight TTL cache backed by SQLite."""

    def __init__(self, path: Path | None = None, ttl_seconds: int | None = None) -> None:
        self.path = path or settings.cache_path
        self.ttl_seconds = ttl_seconds or settings.cache_ttl_seconds
        self._initialize()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a cached value if it has not expired."""

        with self._connection() as conn:
            cursor = conn.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            value, expires_at = row
            if expires_at and expires_at < time.time():
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                return None
            return json.loads(value)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Store a value in the cache with an optional TTL."""

        expires_at = int(time.time()) + int(ttl or self.ttl_seconds)
        payload = json.dumps(value)
        with self._connection() as conn:
            conn.execute(
                "REPLACE INTO cache(key, value, expires_at) VALUES (?, ?, ?)",
                (key, payload, expires_at),
            )

    def clear(self) -> None:
        """Remove all entries from the cache."""

        with self._connection() as conn:
            conn.execute("DELETE FROM cache")

    def _initialize(self) -> None:
        with self._connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS cache ("
                "key TEXT PRIMARY KEY, "
                "value TEXT NOT NULL, "
                "expires_at INTEGER" ")"
            )

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        try:
            yield conn
        finally:
            conn.commit()
            conn.close()


cache = SQLiteCache()
