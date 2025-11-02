"""AlienVault OTX API client implementation."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from ..models import Indicator, IndicatorSource
from .base import BaseApiClient


class OTXClient(BaseApiClient):
    """Client for interacting with AlienVault OTX."""

    source = IndicatorSource.OTX
    base_url = "https://otx.alienvault.com/api/v1"

    async def _collect_impl(self, since: datetime | None) -> List[Indicator]:
        # Placeholder implementation using mock data due to offline environment.
        return []

    async def _search_impl(self, query: str) -> List[Indicator]:
        payload = {
            "type": "domain",
            "indicator": query,
            "source": self.source.value,
        }
        indicator = Indicator.from_raw(
            payload,
            source=self.source,
            value_key="indicator",
            type_value="domain",
            confidence=75,
        )
        return [indicator]

    def _auth_headers(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        return {"X-OTX-API-KEY": self.api_key}
