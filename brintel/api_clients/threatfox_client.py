"""ThreatFox client implementation."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from ..models import Indicator, IndicatorSource
from .base import BaseApiClient


class ThreatFoxClient(BaseApiClient):
    """Client for ThreatFox API."""

    source = IndicatorSource.THREATFOX
    base_url = "https://threatfox-api.abuse.ch/api/v1"

    async def _collect_impl(self, since: datetime | None) -> List[Indicator]:
        return []

    async def _search_impl(self, query: str) -> List[Indicator]:
        payload = {
            "type": "url",
            "indicator": query,
            "source": self.source.value,
        }
        indicator = Indicator.from_raw(
            payload,
            source=self.source,
            value_key="indicator",
            type_value="url",
            confidence=65,
        )
        return [indicator]

    def _auth_headers(self) -> Dict[str, str]:
        return {}
