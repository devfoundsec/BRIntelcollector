"""AbuseIPDB client implementation."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from ..models import Indicator, IndicatorSource
from .base import BaseApiClient


class AbuseIPDBClient(BaseApiClient):
    """Client for AbuseIPDB API."""

    source = IndicatorSource.ABUSEIPDB
    base_url = "https://api.abuseipdb.com/api/v2"

    async def _collect_impl(self, since: datetime | None) -> List[Indicator]:
        return []

    async def _search_impl(self, query: str) -> List[Indicator]:
        payload = {
            "type": "ip",
            "indicator": query,
            "source": self.source.value,
        }
        indicator = Indicator.from_raw(
            payload,
            source=self.source,
            value_key="indicator",
            type_value="ip",
            confidence=55,
        )
        return [indicator]

    def _auth_headers(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        return {"Key": self.api_key}
