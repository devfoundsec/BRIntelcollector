"""Collector orchestrator coordinating API clients and storage."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Dict, Iterable, List, Optional

from ..api_clients.base import ApiClientRegistry, BaseApiClient
from ..data import IndicatorRepository
from ..models import Indicator
from ..utils.logging import get_logger

LOGGER = get_logger(__name__)


class CollectorOrchestrator:
    """Coordinates collection flows across API clients."""

    def __init__(
        self,
        *,
        repository: IndicatorRepository | None = None,
        clients: Optional[Iterable[BaseApiClient]] = None,
    ) -> None:
        self.repository = repository or IndicatorRepository()
        if clients is None:
            clients = ApiClientRegistry.load_registered_clients()
        self.clients = list(clients)

    async def collect_since(self, since: datetime | None = None) -> int:
        """Collect indicators from all registered clients."""

        tasks = [client.collect_since(since) for client in self.clients]
        results = await asyncio.gather(*tasks)
        indicators: List[Indicator] = [indicator for batch in results for indicator in batch]
        if not indicators:
            return 0
        inserted = self.repository.upsert_many(indicators)
        LOGGER.info("Stored indicators", extra={"count": inserted})
        return inserted

    async def search(self, source: str, query: str) -> List[Indicator]:
        """Search indicators for a specific source."""

        client = self._find_client(source)
        results = await client.search(query)
        if results:
            self.repository.upsert_many(results)
        return results

    def _find_client(self, source: str) -> BaseApiClient:
        for client in self.clients:
            if client.source == source:
                return client
        raise ValueError(f"Client not registered: {source}")
