"""AbuseIPDB client implementation."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List
import re

from ..models import Indicator, IndicatorSource
from ..utils.logging import get_logger
from .base import BaseApiClient

LOGGER = get_logger(__name__)


class AbuseIPDBClient(BaseApiClient):
    """Client for AbuseIPDB API.

    AbuseIPDB is a project helping combat the spread of hackers, spammers,
    and abusive activity on the internet.
    API documentation: https://docs.abuseipdb.com/
    """

    source = IndicatorSource.ABUSEIPDB
    base_url = "https://api.abuseipdb.com/api/v2"

    async def _collect_impl(self, since: datetime | None) -> List[Indicator]:
        """Collect recently reported IPs from AbuseIPDB."""
        if not self.api_key:
            LOGGER.warning("AbuseIPDB API key not configured, skipping collection")
            return []

        try:
            indicators = []

            # Get blacklist of most reported IPs
            # The blacklist endpoint returns IPs with confidence >= 100
            params = {
                "confidenceMinimum": "75",  # Only high confidence IPs
                "limit": "100",  # Max 10000 but we'll keep it reasonable
            }

            response = await self._request("GET", "/blacklist", params=params)

            if "data" in response:
                for ip_data in response["data"]:
                    indicator = self._parse_ip_data(ip_data)
                    if indicator:
                        indicators.append(indicator)

            LOGGER.info(
                f"Collected {len(indicators)} indicators from AbuseIPDB",
                extra={"source": "abuseipdb", "count": len(indicators)},
            )
            return indicators

        except Exception as e:
            LOGGER.error(f"Error collecting from AbuseIPDB: {e}", exc_info=True)
            return []

    async def _search_impl(self, query: str) -> List[Indicator]:
        """Check a specific IP address in AbuseIPDB."""
        if not self.api_key:
            LOGGER.warning("AbuseIPDB API key not configured")
            return []

        # Validate IP address
        if not self._is_valid_ip(query):
            LOGGER.warning(f"Invalid IP address: {query}")
            return []

        try:
            # Check IP with detailed report
            params = {
                "ipAddress": query,
                "maxAgeInDays": "90",  # Look back 90 days
                "verbose": "",  # Include detailed reports
            }

            response = await self._request("GET", "/check", params=params)

            if "data" in response:
                indicator = self._parse_ip_data(response["data"], detailed=True)
                if indicator:
                    return [indicator]

            return []

        except Exception as e:
            LOGGER.error(f"Error searching AbuseIPDB for {query}: {e}", exc_info=True)
            return []

    def _parse_ip_data(self, ip_data: Dict, detailed: bool = False) -> Indicator | None:
        """Parse AbuseIPDB IP data into an Indicator."""
        try:
            ip_address = ip_data.get("ipAddress", "")

            if not ip_address:
                return None

            # Calculate confidence based on abuse score
            abuse_confidence_score = ip_data.get("abuseConfidenceScore", 0)
            confidence = self._calculate_confidence(abuse_confidence_score, ip_data)

            # Build tags from categories
            tags = []
            if "usageType" in ip_data:
                tags.append(ip_data["usageType"])

            if ip_data.get("isWhitelisted"):
                tags.append("whitelisted")

            if ip_data.get("isTor"):
                tags.append("tor")

            # Get domain if available
            domain = ip_data.get("domain", "")
            if domain:
                tags.append(f"domain:{domain}")

            # Add country info
            if country_code := ip_data.get("countryCode"):
                tags.append(f"country:{country_code}")

            # Parse timestamps
            last_reported = ip_data.get("lastReportedAt")

            indicator = Indicator.from_raw(
                {
                    "ipAddress": ip_address,
                    "abuseConfidenceScore": abuse_confidence_score,
                    "totalReports": ip_data.get("totalReports", 0),
                    "numDistinctUsers": ip_data.get("numDistinctUsers", 0),
                    "countryCode": ip_data.get("countryCode"),
                    "domain": domain,
                    "hostnames": ip_data.get("hostnames", []),
                    "usageType": ip_data.get("usageType"),
                    "isp": ip_data.get("isp"),
                    "isTor": ip_data.get("isTor", False),
                    "isWhitelisted": ip_data.get("isWhitelisted", False),
                    "lastReportedAt": last_reported,
                },
                source=self.source,
                value_key="ipAddress",
                type_value="ip",
                confidence=confidence,
                last_seen_key="lastReportedAt",
            )

            return indicator

        except Exception as e:
            LOGGER.warning(f"Error parsing AbuseIPDB IP data: {e}")
            return None

    def _is_valid_ip(self, ip: str) -> bool:
        """Validate if the string is a valid IPv4 address."""
        pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
        if not re.match(pattern, ip):
            return False

        # Validate octets
        octets = ip.split(".")
        return all(0 <= int(octet) <= 255 for octet in octets)

    def _calculate_confidence(self, abuse_score: int, ip_data: Dict) -> int:
        """Calculate confidence score based on AbuseIPDB data."""
        # Start with abuse confidence score
        base_confidence = abuse_score

        # Increase confidence if reported by many users
        distinct_users = ip_data.get("numDistinctUsers", 0)
        if distinct_users >= 10:
            base_confidence = min(base_confidence + 10, 95)
        elif distinct_users >= 5:
            base_confidence = min(base_confidence + 5, 95)

        # Decrease confidence if whitelisted
        if ip_data.get("isWhitelisted"):
            base_confidence = max(base_confidence - 30, 10)

        return max(0, min(base_confidence, 100))

    def _auth_headers(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        return {"Key": self.api_key, "Accept": "application/json"}
