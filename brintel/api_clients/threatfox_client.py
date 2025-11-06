"""ThreatFox client implementation."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List
import httpx

from ..models import Indicator, IndicatorSource
from ..utils.logging import get_logger
from .base import BaseApiClient

LOGGER = get_logger(__name__)


class ThreatFoxClient(BaseApiClient):
    """Client for ThreatFox API (abuse.ch).

    ThreatFox is a free platform sharing IOCs associated with malware.
    API documentation: https://threatfox.abuse.ch/api/
    """

    source = IndicatorSource.THREATFOX
    base_url = "https://threatfox-api.abuse.ch/api/v1"

    async def _collect_impl(self, since: datetime | None) -> List[Indicator]:
        """Collect recent IOCs from ThreatFox."""
        try:
            indicators = []

            # Calculate days parameter
            if since:
                days_ago = (datetime.utcnow() - since).days
                days_ago = max(1, min(days_ago, 7))  # ThreatFox allows 1-7 days
            else:
                days_ago = 1  # Default to last 24 hours

            # Build request payload for ThreatFox API
            payload = {"query": "get_iocs", "days": days_ago}

            # ThreatFox uses POST requests with JSON body
            await self.rate_manager.wait_for_slot(self.source.value)

            response = await self.proxy_manager.request(
                "POST",
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
                source=self.source.value,
            )

            data = response.json()

            if data.get("query_status") == "ok" and "data" in data:
                for ioc_data in data["data"]:
                    indicator = self._parse_ioc(ioc_data)
                    if indicator:
                        indicators.append(indicator)

            LOGGER.info(
                f"Collected {len(indicators)} indicators from ThreatFox",
                extra={"source": "threatfox", "count": len(indicators), "days": days_ago},
            )
            return indicators

        except Exception as e:
            LOGGER.error(f"Error collecting from ThreatFox: {e}", exc_info=True)
            return []

    async def _search_impl(self, query: str) -> List[Indicator]:
        """Search for a specific IOC in ThreatFox."""
        try:
            # Build search payload
            payload = {"query": "search_ioc", "search_term": query}

            await self.rate_manager.wait_for_slot(self.source.value)

            response = await self.proxy_manager.request(
                "POST",
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
                source=self.source.value,
            )

            data = response.json()

            if data.get("query_status") == "ok" and "data" in data:
                indicators = []
                for ioc_data in data["data"]:
                    indicator = self._parse_ioc(ioc_data)
                    if indicator:
                        indicators.append(indicator)
                return indicators

            return []

        except Exception as e:
            LOGGER.error(f"Error searching ThreatFox for {query}: {e}", exc_info=True)
            return []

    def _parse_ioc(self, ioc_data: Dict) -> Indicator | None:
        """Parse a ThreatFox IOC into an Indicator."""
        try:
            ioc_value = ioc_data.get("ioc", "")
            ioc_type = ioc_data.get("ioc_type", "")

            if not ioc_value:
                return None

            # Normalize IOC type
            normalized_type = self._normalize_type(ioc_type)

            # Calculate confidence based on ThreatFox data
            confidence = self._calculate_confidence(ioc_data)

            # Build tags
            tags = []
            if malware_family := ioc_data.get("malware"):
                tags.append(malware_family)

            if threat_type := ioc_data.get("threat_type"):
                tags.append(threat_type)

            if malware_alias := ioc_data.get("malware_alias"):
                tags.append(malware_alias)

            indicator = Indicator.from_raw(
                {
                    "ioc": ioc_value,
                    "malware": ioc_data.get("malware"),
                    "malware_printable": ioc_data.get("malware_printable"),
                    "malware_alias": ioc_data.get("malware_alias"),
                    "threat_type": ioc_data.get("threat_type"),
                    "confidence_level": ioc_data.get("confidence_level"),
                    "first_seen": ioc_data.get("first_seen"),
                    "last_seen": ioc_data.get("last_seen"),
                    "reference": ioc_data.get("reference"),
                    "reporter": ioc_data.get("reporter"),
                },
                source=self.source,
                value_key="ioc",
                type_value=normalized_type,
                confidence=confidence,
                first_seen_key="first_seen",
                last_seen_key="last_seen",
            )

            return indicator

        except Exception as e:
            LOGGER.warning(f"Error parsing ThreatFox IOC: {e}")
            return None

    def _normalize_type(self, threatfox_type: str) -> str:
        """Normalize ThreatFox IOC types to our standard types."""
        type_mapping = {
            "ip:port": "ip",
            "domain": "domain",
            "url": "url",
            "md5_hash": "hash",
            "sha256_hash": "hash",
            "sha1_hash": "hash",
        }
        return type_mapping.get(threatfox_type, threatfox_type)

    def _calculate_confidence(self, ioc_data: Dict) -> int:
        """Calculate confidence score based on ThreatFox data."""
        base_confidence = 65

        # ThreatFox provides confidence_level (0-100)
        if confidence_level := ioc_data.get("confidence_level"):
            base_confidence = confidence_level

        # Boost confidence for verified reporters
        reporter = ioc_data.get("reporter", "")
        if "abuse_ch" in reporter.lower():
            base_confidence = min(base_confidence + 10, 95)

        return base_confidence

    def _auth_headers(self) -> Dict[str, str]:
        # ThreatFox API is free and doesn't require authentication
        return {}
