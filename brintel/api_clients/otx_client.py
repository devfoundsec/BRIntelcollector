"""AlienVault OTX API client implementation."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List

from ..models import Indicator, IndicatorSource
from ..utils.logging import get_logger
from .base import BaseApiClient

LOGGER = get_logger(__name__)


class OTXClient(BaseApiClient):
    """Client for interacting with AlienVault OTX."""

    source = IndicatorSource.OTX
    base_url = "https://otx.alienvault.com/api/v1"

    async def _collect_impl(self, since: datetime | None) -> List[Indicator]:
        """Collect pulses and extract indicators from OTX."""
        if not self.api_key:
            LOGGER.warning("OTX API key not configured, skipping collection")
            return []

        try:
            # Calculate timestamp for modified_since parameter
            modified_since = None
            if since:
                modified_since = since.isoformat()
            else:
                # Default to last 24 hours
                modified_since = (datetime.utcnow() - timedelta(hours=24)).isoformat()

            # Get subscribed pulses
            params = {"modified_since": modified_since, "limit": 50}
            response = await self._request("GET", "/pulses/subscribed", params=params)

            indicators = []
            if "results" in response:
                for pulse in response["results"]:
                    indicators.extend(self._extract_indicators_from_pulse(pulse))

            LOGGER.info(
                f"Collected {len(indicators)} indicators from OTX",
                extra={"source": "otx", "count": len(indicators)},
            )
            return indicators

        except Exception as e:
            LOGGER.error(f"Error collecting from OTX: {e}", exc_info=True)
            return []

    async def _search_impl(self, query: str) -> List[Indicator]:
        """Search for indicators in OTX."""
        if not self.api_key:
            LOGGER.warning("OTX API key not configured")
            return []

        try:
            indicators = []

            # Determine indicator type
            indicator_type = self._determine_type(query)

            # Search for the indicator
            response = await self._request(
                "GET", f"/indicators/{indicator_type}/{query}/general"
            )

            if response:
                # Extract basic indicator info
                indicator = Indicator.from_raw(
                    {
                        "indicator": query,
                        "type_title": response.get("type_title", indicator_type),
                        "pulse_info": response.get("pulse_info", {}),
                        "reputation": response.get("reputation", 0),
                    },
                    source=self.source,
                    value_key="indicator",
                    type_value=indicator_type,
                    confidence=self._calculate_confidence(response),
                )
                indicators.append(indicator)

            return indicators

        except Exception as e:
            LOGGER.error(f"Error searching OTX for {query}: {e}", exc_info=True)
            return []

    def _extract_indicators_from_pulse(self, pulse: Dict) -> List[Indicator]:
        """Extract indicators from an OTX pulse."""
        indicators = []

        for ioc_data in pulse.get("indicators", []):
            try:
                indicator_type = ioc_data.get("type", "unknown")
                indicator_value = ioc_data.get("indicator", "")

                if not indicator_value:
                    continue

                # Map OTX types to our normalized types
                normalized_type = self._normalize_type(indicator_type)

                indicator = Indicator.from_raw(
                    {
                        **ioc_data,
                        "pulse_name": pulse.get("name"),
                        "pulse_id": pulse.get("id"),
                        "created": ioc_data.get("created"),
                    },
                    source=self.source,
                    value_key="indicator",
                    type_value=normalized_type,
                    confidence=self._calculate_ioc_confidence(ioc_data, pulse),
                    first_seen_key="created",
                )

                indicators.append(indicator)

            except Exception as e:
                LOGGER.warning(f"Error parsing OTX indicator: {e}")
                continue

        return indicators

    def _determine_type(self, query: str) -> str:
        """Determine the indicator type based on the query."""
        import re

        # IP address pattern
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", query):
            return "IPv4"

        # Domain pattern
        if re.match(r"^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$", query):
            return "domain"

        # Hash patterns
        if re.match(r"^[a-fA-F0-9]{32}$", query):
            return "file"  # MD5

        if re.match(r"^[a-fA-F0-9]{40}$", query):
            return "file"  # SHA1

        if re.match(r"^[a-fA-F0-9]{64}$", query):
            return "file"  # SHA256

        # URL
        if query.startswith("http://") or query.startswith("https://"):
            return "url"

        return "hostname"

    def _normalize_type(self, otx_type: str) -> str:
        """Normalize OTX indicator types to our standard types."""
        type_mapping = {
            "IPv4": "ip",
            "IPv6": "ip",
            "domain": "domain",
            "hostname": "domain",
            "URL": "url",
            "FileHash-MD5": "hash",
            "FileHash-SHA1": "hash",
            "FileHash-SHA256": "hash",
            "email": "email",
            "CVE": "cve",
        }
        return type_mapping.get(otx_type, otx_type.lower())

    def _calculate_confidence(self, response: Dict) -> int:
        """Calculate confidence score based on OTX response."""
        base_confidence = 50

        # Increase confidence if referenced in multiple pulses
        pulse_count = len(response.get("pulse_info", {}).get("pulses", []))
        base_confidence += min(pulse_count * 5, 30)

        # Adjust based on reputation
        reputation = response.get("reputation", 0)
        if reputation < 0:
            base_confidence += 20

        return min(base_confidence, 100)

    def _calculate_ioc_confidence(self, ioc_data: Dict, pulse: Dict) -> int:
        """Calculate confidence for an individual IOC."""
        base_confidence = 60

        # Increase confidence for trusted authors
        if pulse.get("author_name") in ["AlienVault", "Recorded Future"]:
            base_confidence += 20

        # Increase confidence if IOC has been validated
        if ioc_data.get("is_active", True):
            base_confidence += 10

        return min(base_confidence, 100)

    def _auth_headers(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        return {"X-OTX-API-KEY": self.api_key}
