"""Shodan client implementation."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from ..models import Indicator, IndicatorSource
from .base import BaseApiClient


class ShodanClient(BaseApiClient):
    """Client for Shodan API."""

    source = IndicatorSource.SHODAN
    base_url = "https://api.shodan.io"

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
            confidence=65,
        )
        return [indicator]

    def _auth_headers(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        return {"Authorization": f"Token {self.api_key}"}
