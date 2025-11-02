"""VirusTotal client implementation."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from ..models import Indicator, IndicatorSource
from .base import BaseApiClient


class VirusTotalClient(BaseApiClient):
    """Client for the public VirusTotal API."""

    source = IndicatorSource.VIRUSTOTAL
    base_url = "https://www.virustotal.com/api/v3"

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
            confidence=80,
        )
        return [indicator]

    def _auth_headers(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        return {"x-apikey": self.api_key}
