"""IBM X-Force Exchange client."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from ..models import Indicator, IndicatorSource
from .base import BaseApiClient


class XForceExchangeClient(BaseApiClient):
    """Client for IBM X-Force Exchange API."""

    source = IndicatorSource.XFE
    base_url = "https://api.xforce.ibmcloud.com"

    async def _collect_impl(self, since: datetime | None) -> List[Indicator]:
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
            confidence=60,
        )
        return [indicator]

    def _auth_headers(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        return {"Authorization": f"Basic {self.api_key}"}
