"""Dynamic rate limiting utilities."""

from __future__ import annotations

import asyncio
import math
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Deque, Dict, Optional

from ..utils.config import settings
from ..utils.logging import get_logger

LOGGER = get_logger(__name__)


@dataclass
class RateLimit:
    """Stores configuration for a single API rate limit."""

    max_per_minute: int
    max_per_day: Optional[int] = None
    remaining: Optional[int] = None
    reset_at: Optional[float] = None
    history: Deque[float] = field(default_factory=deque)

    def allowance(self) -> float:
        """Return the minimum interval between requests in seconds."""

        if self.max_per_minute <= 0:
            return 0.0
        return 60.0 / self.max_per_minute


class RateManager:
    """Coordinates rate limiting and backoff strategies for API clients."""

    def __init__(self, *, mode: str = "auto") -> None:
        self.mode = mode
        self._limits: Dict[str, RateLimit] = {}
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    def register(
        self,
        source: str,
        *,
        max_per_minute: int,
        max_per_day: Optional[int] = None,
    ) -> None:
        """Register static limits for a source."""

        self._limits[source] = RateLimit(max_per_minute=max_per_minute, max_per_day=max_per_day)
        LOGGER.debug("Registered rate limit", extra={"source": source, "per_minute": max_per_minute})

    def update_from_headers(self, source: str, headers: Dict[str, str]) -> None:
        """Update limits from HTTP response headers."""

        limit = self._limits.get(source)
        if not limit:
            return
        if "X-RateLimit-Limit" in headers:
            try:
                limit.max_per_minute = int(headers["X-RateLimit-Limit"])
            except ValueError:
                LOGGER.debug("Failed to parse X-RateLimit-Limit", extra={"source": source})
        if "X-RateLimit-Remaining" in headers:
            try:
                limit.remaining = int(headers["X-RateLimit-Remaining"])
            except ValueError:
                limit.remaining = None
        if "Retry-After" in headers:
            try:
                delay = float(headers["Retry-After"])
                limit.reset_at = time.monotonic() + delay
            except ValueError:
                limit.reset_at = None

    async def wait_for_slot(self, source: str) -> None:
        """Wait until a request slot becomes available."""

        limit = self._limits.setdefault(source, RateLimit(max_per_minute=60))
        lock = self._locks[source]
        async with lock:
            await self._apply_backoff(limit)
            now = time.monotonic()
            allowance = limit.allowance()
            while limit.history and now - limit.history[0] > 60:
                limit.history.popleft()
            if limit.history and allowance > 0:
                elapsed = now - limit.history[-1]
                wait = allowance - elapsed
                if wait > 0:
                    LOGGER.debug(
                        "Waiting for rate limit slot",
                        extra={"source": source, "wait": wait},
                    )
                    await asyncio.sleep(wait)
            limit.history.append(time.monotonic())

    async def _apply_backoff(self, limit: RateLimit) -> None:
        if limit.reset_at and limit.reset_at > time.monotonic():
            delay = limit.reset_at - time.monotonic()
            LOGGER.debug("Respecting Retry-After", extra={"delay": delay})
            await asyncio.sleep(delay)
            limit.reset_at = None
            return
        if limit.remaining is not None and limit.remaining <= 0:
            delay = allowance = limit.allowance()
            if allowance > 0:
                delay = allowance
            LOGGER.debug("Remaining quota exhausted", extra={"delay": delay})
            await asyncio.sleep(delay)
            limit.remaining = None

    def record_failure(self, source: str, attempt: int) -> float:
        """Return backoff delay for a failed request."""

        base = 1.0
        delay = base * math.pow(2, attempt)
        if settings.rate_dynamic:
            delay *= 1.5
        LOGGER.debug(
            "Calculated backoff",
            extra={"source": source, "attempt": attempt, "delay": delay},
        )
        return delay


GLOBAL_RATE_MANAGER = RateManager(mode="auto")
