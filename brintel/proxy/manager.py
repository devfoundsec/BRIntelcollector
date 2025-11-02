"""Proxy manager coordinating outbound requests."""

from __future__ import annotations

import asyncio
import random
from pathlib import Path
from typing import Dict, Iterable, Optional

import httpx

from ..core.rate_manager import RateManager
from ..utils.cache import cache
from ..utils.config import settings
from ..utils.logging import get_logger

LOGGER = get_logger(__name__)


class ProxyManager:
    """Handles proxy rotation, retries and caching."""

    def __init__(self, *, rate_manager: RateManager | None = None) -> None:
        self.rate_manager = rate_manager
        self._proxies = self._load_proxies(settings.proxy_list) if settings.proxy_enabled else []
        self._lock = asyncio.Lock()

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, str]] = None,
        timeout: float = 10.0,
        source: str,
    ) -> httpx.Response:
        """Perform an HTTP request with retry and proxy rotation."""

        cache_key = f"response:{source}:{url}:{params}"
        if response_data := cache.get(cache_key):
            LOGGER.debug("Proxy cache hit", extra={"cache_key": cache_key})
            return httpx.Response(status_code=200, json=response_data)  # type: ignore[arg-type]

        attempt = 0
        delay = 0.0
        while True:
            proxy = await self._choose_proxy()
            try:
                async with httpx.AsyncClient(proxies=proxy, timeout=timeout) as client:
                    response = await client.request(method, url, headers=headers, params=params)
                if response.status_code == 429 and self.rate_manager:
                    attempt += 1
                    delay = self.rate_manager.record_failure(source, attempt)
                    LOGGER.warning(
                        "Received 429 response", extra={"source": source, "attempt": attempt}
                    )
                    await asyncio.sleep(delay)
                    continue
                response.raise_for_status()
                cache.set(cache_key, response.json())
                return response
            except httpx.HTTPError as exc:  # pragma: no cover - network dependent
                attempt += 1
                delay = min(60.0, 2 ** attempt)
                LOGGER.error(
                    "Proxy request failed",
                    extra={"url": url, "proxy": proxy, "error": str(exc), "attempt": attempt},
                )
                await asyncio.sleep(delay)

    async def _choose_proxy(self) -> Optional[str]:
        if not self._proxies:
            return None
        async with self._lock:
            if settings.proxy_rotate:
                random.shuffle(self._proxies)
            return self._proxies[0]

    def _load_proxies(self, path: Optional[Path]) -> list[str]:
        if not path or not Path(path).exists():
            return []
        with Path(path).open() as handle:
            return [line.strip() for line in handle if line.strip()]
