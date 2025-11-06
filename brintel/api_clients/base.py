"""Base classes and registry for API clients."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import ClassVar, Dict, Iterable, List, Optional, Type

import httpx

from ..core.rate_manager import GLOBAL_RATE_MANAGER, RateManager
from ..models import Indicator, IndicatorSource
from ..proxy.manager import ProxyManager
from ..utils.cache import cache
from ..utils.config import settings
from ..utils.logging import get_logger

LOGGER = get_logger(__name__)


class BaseApiClient(ABC):
    """Abstract base class encapsulating shared behaviour."""

    source: ClassVar[IndicatorSource]
    base_url: ClassVar[str]

    def __init__(
        self,
        *,
        api_key: str | None = None,
        rate_manager: RateManager | None = None,
        proxy_manager: ProxyManager | None = None,
        timeout: float | None = None,
    ) -> None:
        self.api_key = api_key
        self.rate_manager = rate_manager or GLOBAL_RATE_MANAGER
        self.proxy_manager = proxy_manager or ProxyManager(rate_manager=self.rate_manager)
        self.timeout = timeout or settings.api_timeout
        ApiClientRegistry.register(self)

    @property
    def headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "User-Agent": "BRIntelcollector/0.1",
        }
        if self.api_key:
            headers.update(self._auth_headers())
        return headers

    async def collect_since(self, since: datetime | None = None) -> List[Indicator]:
        """Collect indicators since the provided datetime."""

        return await self._collect_impl(since)

    async def search(self, query: str) -> List[Indicator]:
        """Perform a search against the upstream API."""

        cache_key = f"search:{self.source.value}:{query}"
        if data := cache.get(cache_key):
            LOGGER.debug("Cache hit", extra={"cache_key": cache_key})
            return [Indicator(**item) for item in data]
        results = await self._search_impl(query)
        cache.set(cache_key, [indicator.as_dict() for indicator in results])
        return results

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, any]:
        """Send an HTTP request respecting proxy and rate limits."""

        await self.rate_manager.wait_for_slot(self.source.value)
        response = await self.proxy_manager.request(
            method,
            f"{self.base_url}{path}",
            headers=self.headers,
            params=params,
            timeout=self.timeout,
            source=self.source.value,
        )
        self.rate_manager.update_from_headers(self.source.value, dict(response.headers))
        return response.json()

    @abstractmethod
    async def _collect_impl(self, since: datetime | None) -> List[Indicator]:
        """Provider specific collection implementation."""

    @abstractmethod
    async def _search_impl(self, query: str) -> List[Indicator]:
        """Provider specific search implementation."""

    def _auth_headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}


class ApiClientRegistry:
    """Registry keeping track of instantiated clients."""

    _clients: ClassVar[List[BaseApiClient]] = []

    @classmethod
    def register(cls, client: BaseApiClient) -> None:
        if client not in cls._clients:
            cls._clients.append(client)

    @classmethod
    def clients(cls) -> Iterable[BaseApiClient]:
        return list(cls._clients)

    @classmethod
    def load_registered_clients(cls) -> List[BaseApiClient]:
        if cls._clients:
            return list(cls._clients)
        # Instantiate default clients with environment configuration.
        OTXClient(api_key="", rate_manager=GLOBAL_RATE_MANAGER)
        XForceExchangeClient(api_key="", rate_manager=GLOBAL_RATE_MANAGER)
        VirusTotalClient(api_key="", rate_manager=GLOBAL_RATE_MANAGER)
        MispClient(api_key="", rate_manager=GLOBAL_RATE_MANAGER)
        ThreatFoxClient(api_key="", rate_manager=GLOBAL_RATE_MANAGER)
        AbuseIPDBClient(api_key="", rate_manager=GLOBAL_RATE_MANAGER)
        ShodanClient(api_key="", rate_manager=GLOBAL_RATE_MANAGER)
        return list(cls._clients)


# Avoid circular imports
from .otx_client import OTXClient
from .xfe_client import XForceExchangeClient
from .vt_client import VirusTotalClient
from .misp_client import MispClient
from .threatfox_client import ThreatFoxClient
from .abuseipdb_client import AbuseIPDBClient
from .shodan_client import ShodanClient
