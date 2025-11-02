"""MISP client implementation."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from ..models import Indicator, IndicatorSource
from .base import BaseApiClient


class MispClient(BaseApiClient):
    """Client for MISP compatible APIs."""

    source = IndicatorSource.MISP
    base_url = "https://misp.example.com/api"

    async def _collect_impl(self, since: datetime | None) -> List[Indicator]:
        return []

    async def _search_impl(self, query: str) -> List[Indicator]:
        payload = {
            "type": "hash",
            "indicator": query,
            "source": self.source.value,
        }
        indicator = Indicator.from_raw(
            payload,
            source=self.source,
            value_key="indicator",
            type_value="hash",
            confidence=70,
        )
        return [indicator]

    def _auth_headers(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        return {"Authorization": self.api_key, "Accept": "application/json"}
