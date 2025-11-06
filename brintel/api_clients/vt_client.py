"""VirusTotal client implementation."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List
import re

from ..models import Indicator, IndicatorSource
from ..utils.logging import get_logger
from .base import BaseApiClient

LOGGER = get_logger(__name__)


class VirusTotalClient(BaseApiClient):
    """Client for the public VirusTotal API v3."""

    source = IndicatorSource.VIRUSTOTAL
    base_url = "https://www.virustotal.com/api/v3"

    async def _collect_impl(self, since: datetime | None) -> List[Indicator]:
        """Collect recent file submissions from VirusTotal."""
        if not self.api_key:
            LOGGER.warning("VirusTotal API key not configured, skipping collection")
            return []

        try:
            indicators = []

            # VT API v3 doesn't have a direct "recent submissions" endpoint
            # We'll use the intelligence search with a time filter
            timestamp = since or (datetime.utcnow() - timedelta(hours=24))

            # Search for recently submitted files with high detection rates
            query = f"fs:{timestamp.strftime('%Y-%m-%d')}+ positives:10+"

            try:
                response = await self._request(
                    "GET",
                    "/intelligence/search",
                    params={"query": query, "limit": 40}
                )

                if "data" in response:
                    for item in response["data"]:
                        indicator = self._parse_file_report(item)
                        if indicator:
                            indicators.append(indicator)

            except Exception as e:
                LOGGER.warning(f"Intelligence search not available: {e}")
                # Fall back to empty results if intelligence API is not accessible

            LOGGER.info(
                f"Collected {len(indicators)} indicators from VirusTotal",
                extra={"source": "virustotal", "count": len(indicators)},
            )
            return indicators

        except Exception as e:
            LOGGER.error(f"Error collecting from VirusTotal: {e}", exc_info=True)
            return []

    async def _search_impl(self, query: str) -> List[Indicator]:
        """Search for an indicator in VirusTotal."""
        if not self.api_key:
            LOGGER.warning("VirusTotal API key not configured")
            return []

        try:
            # Determine the type of indicator
            indicator_type = self._determine_type(query)

            # Build the appropriate endpoint
            if indicator_type == "ip":
                endpoint = f"/ip_addresses/{query}"
            elif indicator_type == "domain":
                endpoint = f"/domains/{query}"
            elif indicator_type == "url":
                # URLs need to be base64 encoded
                import base64
                url_id = base64.urlsafe_b64encode(query.encode()).decode().rstrip("=")
                endpoint = f"/urls/{url_id}"
            elif indicator_type == "hash":
                endpoint = f"/files/{query}"
            else:
                LOGGER.warning(f"Unsupported indicator type: {indicator_type}")
                return []

            # Make the API request
            response = await self._request("GET", endpoint)

            if "data" in response:
                indicator = self._parse_indicator_response(
                    response["data"], query, indicator_type
                )
                if indicator:
                    return [indicator]

            return []

        except Exception as e:
            LOGGER.error(f"Error searching VirusTotal for {query}: {e}", exc_info=True)
            return []

    def _parse_indicator_response(
        self, data: Dict, query: str, indicator_type: str
    ) -> Indicator | None:
        """Parse a VirusTotal API response into an Indicator."""
        try:
            attributes = data.get("attributes", {})

            # Get analysis stats
            last_analysis_stats = attributes.get("last_analysis_stats", {})
            malicious = last_analysis_stats.get("malicious", 0)
            suspicious = last_analysis_stats.get("suspicious", 0)
            harmless = last_analysis_stats.get("harmless", 0)
            undetected = last_analysis_stats.get("undetected", 0)
            total = malicious + suspicious + harmless + undetected

            # Calculate confidence based on detection ratio
            confidence = self._calculate_confidence(malicious, suspicious, total)

            # Get timestamps
            last_analysis_date = attributes.get("last_analysis_date")
            first_submission_date = attributes.get("first_submission_date")

            # Build tags from categories and popular votes
            tags = []
            if "categories" in attributes:
                tags.extend(attributes["categories"].values())

            reputation = attributes.get("reputation", 0)
            if reputation < 0:
                tags.append("malicious")
            elif reputation > 0:
                tags.append("trusted")

            indicator = Indicator.from_raw(
                {
                    "value": query,
                    "malicious": malicious,
                    "suspicious": suspicious,
                    "harmless": harmless,
                    "total_detections": total,
                    "reputation": reputation,
                    "last_analysis_date": last_analysis_date,
                    "first_submission_date": first_submission_date,
                    **attributes,
                },
                source=self.source,
                value_key="value",
                type_value=indicator_type,
                confidence=confidence,
                first_seen_key="first_submission_date",
                last_seen_key="last_analysis_date",
            )

            return indicator

        except Exception as e:
            LOGGER.warning(f"Error parsing VT response: {e}")
            return None

    def _parse_file_report(self, data: Dict) -> Indicator | None:
        """Parse a file report from VT intelligence search."""
        try:
            attributes = data.get("attributes", {})
            sha256 = attributes.get("sha256", "")

            if not sha256:
                return None

            last_analysis_stats = attributes.get("last_analysis_stats", {})
            malicious = last_analysis_stats.get("malicious", 0)
            total = sum(last_analysis_stats.values())

            confidence = self._calculate_confidence(
                malicious, last_analysis_stats.get("suspicious", 0), total
            )

            indicator = Indicator.from_raw(
                {
                    "value": sha256,
                    "md5": attributes.get("md5"),
                    "sha1": attributes.get("sha1"),
                    "sha256": sha256,
                    "size": attributes.get("size"),
                    "type_description": attributes.get("type_description"),
                    "malicious": malicious,
                    "total_detections": total,
                    "last_analysis_date": attributes.get("last_analysis_date"),
                },
                source=self.source,
                value_key="value",
                type_value="hash",
                confidence=confidence,
                last_seen_key="last_analysis_date",
            )

            return indicator

        except Exception as e:
            LOGGER.warning(f"Error parsing VT file report: {e}")
            return None

    def _determine_type(self, query: str) -> str:
        """Determine the indicator type based on the query."""
        # IP address
        if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", query):
            return "ip"

        # Domain
        if re.match(r"^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$", query):
            return "domain"

        # Hash patterns
        if re.match(r"^[a-fA-F0-9]{32}$", query):  # MD5
            return "hash"
        if re.match(r"^[a-fA-F0-9]{40}$", query):  # SHA1
            return "hash"
        if re.match(r"^[a-fA-F0-9]{64}$", query):  # SHA256
            return "hash"

        # URL
        if query.startswith("http://") or query.startswith("https://"):
            return "url"

        return "domain"

    def _calculate_confidence(
        self, malicious: int, suspicious: int, total: int
    ) -> int:
        """Calculate confidence score based on VT detection stats."""
        if total == 0:
            return 0

        detection_rate = (malicious + suspicious) / total

        if detection_rate >= 0.3:  # 30% or more engines detected it
            base_confidence = 85
        elif detection_rate >= 0.1:  # 10-30% detection
            base_confidence = 70
        elif detection_rate > 0:  # Some detection
            base_confidence = 55
        else:
            base_confidence = 30  # No detections

        # Boost confidence if many engines agree
        if malicious >= 10:
            base_confidence = min(base_confidence + 10, 95)

        return base_confidence

    def _auth_headers(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        return {"x-apikey": self.api_key}
