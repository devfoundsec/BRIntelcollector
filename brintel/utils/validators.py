"""Validators for indicators of compromise."""

from __future__ import annotations

import ipaddress
import re
from typing import Optional, Tuple
from urllib.parse import urlparse


class IndicatorValidator:
    """Validates and normalizes indicators of compromise."""

    # Regex patterns
    DOMAIN_PATTERN = re.compile(
        r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    )
    EMAIL_PATTERN = re.compile(
        r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    )
    MD5_PATTERN = re.compile(r"^[a-fA-F0-9]{32}$")
    SHA1_PATTERN = re.compile(r"^[a-fA-F0-9]{40}$")
    SHA256_PATTERN = re.compile(r"^[a-fA-F0-9]{64}$")
    CVE_PATTERN = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)

    @classmethod
    def validate_and_identify(cls, value: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate an indicator and identify its type.

        Args:
            value: The indicator value to validate.

        Returns:
            Tuple of (is_valid, indicator_type, error_message)
        """
        value = value.strip()

        if not value:
            return False, None, "Empty value"

        # Try IPv4
        if cls.is_ipv4(value):
            return True, "ip", None

        # Try IPv6
        if cls.is_ipv6(value):
            return True, "ip", None

        # Try domain
        if cls.is_domain(value):
            return True, "domain", None

        # Try URL
        if cls.is_url(value):
            return True, "url", None

        # Try email
        if cls.is_email(value):
            return True, "email", None

        # Try hashes
        if cls.is_md5(value):
            return True, "hash", None
        if cls.is_sha1(value):
            return True, "hash", None
        if cls.is_sha256(value):
            return True, "hash", None

        # Try CVE
        if cls.is_cve(value):
            return True, "cve", None

        return False, None, "Unknown indicator type"

    @staticmethod
    def is_ipv4(value: str) -> bool:
        """Check if value is a valid IPv4 address."""
        try:
            ipaddress.IPv4Address(value)
            return True
        except (ipaddress.AddressValueError, ValueError):
            return False

    @staticmethod
    def is_ipv6(value: str) -> bool:
        """Check if value is a valid IPv6 address."""
        try:
            ipaddress.IPv6Address(value)
            return True
        except (ipaddress.AddressValueError, ValueError):
            return False

    @classmethod
    def is_domain(cls, value: str) -> bool:
        """Check if value is a valid domain name."""
        if len(value) > 253:
            return False
        return bool(cls.DOMAIN_PATTERN.match(value))

    @staticmethod
    def is_url(value: str) -> bool:
        """Check if value is a valid URL."""
        try:
            result = urlparse(value)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @classmethod
    def is_email(cls, value: str) -> bool:
        """Check if value is a valid email address."""
        return bool(cls.EMAIL_PATTERN.match(value))

    @classmethod
    def is_md5(cls, value: str) -> bool:
        """Check if value is a valid MD5 hash."""
        return bool(cls.MD5_PATTERN.match(value))

    @classmethod
    def is_sha1(cls, value: str) -> bool:
        """Check if value is a valid SHA1 hash."""
        return bool(cls.SHA1_PATTERN.match(value))

    @classmethod
    def is_sha256(cls, value: str) -> bool:
        """Check if value is a valid SHA256 hash."""
        return bool(cls.SHA256_PATTERN.match(value))

    @classmethod
    def is_cve(cls, value: str) -> bool:
        """Check if value is a valid CVE identifier."""
        return bool(cls.CVE_PATTERN.match(value))

    @staticmethod
    def normalize_domain(domain: str) -> str:
        """Normalize a domain name.

        Args:
            domain: Domain to normalize.

        Returns:
            Normalized domain (lowercase, no trailing dot).
        """
        domain = domain.lower().strip()
        if domain.endswith("."):
            domain = domain[:-1]
        return domain

    @staticmethod
    def normalize_ip(ip: str) -> str:
        """Normalize an IP address.

        Args:
            ip: IP address to normalize.

        Returns:
            Normalized IP address.
        """
        try:
            # This handles both IPv4 and IPv6
            return str(ipaddress.ip_address(ip))
        except ValueError:
            return ip.strip()

    @staticmethod
    def normalize_hash(hash_value: str) -> str:
        """Normalize a hash value.

        Args:
            hash_value: Hash to normalize.

        Returns:
            Normalized hash (lowercase).
        """
        return hash_value.lower().strip()

    @staticmethod
    def normalize_url(url: str) -> str:
        """Normalize a URL.

        Args:
            url: URL to normalize.

        Returns:
            Normalized URL.
        """
        url = url.strip()

        # Remove trailing slashes from path
        parsed = urlparse(url)
        if parsed.path.endswith("/") and len(parsed.path) > 1:
            path = parsed.path.rstrip("/")
            url = f"{parsed.scheme}://{parsed.netloc}{path}"
            if parsed.query:
                url += f"?{parsed.query}"
            if parsed.fragment:
                url += f"#{parsed.fragment}"

        return url

    @classmethod
    def defang(cls, value: str, indicator_type: str) -> str:
        """Defang an indicator for safe display.

        Args:
            value: Indicator value.
            indicator_type: Type of indicator.

        Returns:
            Defanged indicator.
        """
        if indicator_type == "url":
            value = value.replace("http://", "hxxp://")
            value = value.replace("https://", "hxxps://")
            value = value.replace(".", "[.]")
        elif indicator_type in ("domain", "email"):
            value = value.replace(".", "[.]")
        elif indicator_type == "ip":
            value = value.replace(".", "[.]")

        return value

    @classmethod
    def refang(cls, value: str) -> str:
        """Refang a defanged indicator.

        Args:
            value: Defanged indicator.

        Returns:
            Original indicator.
        """
        value = value.replace("hxxp://", "http://")
        value = value.replace("hxxps://", "https://")
        value = value.replace("[.]", ".")
        value = value.replace("[:]", ":")

        return value

    @staticmethod
    def extract_domain_from_url(url: str) -> Optional[str]:
        """Extract domain from a URL.

        Args:
            url: URL to extract domain from.

        Returns:
            Extracted domain or None.
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc if parsed.netloc else None
        except Exception:
            return None

    @staticmethod
    def is_private_ip(ip: str) -> bool:
        """Check if IP address is private/internal.

        Args:
            ip: IP address to check.

        Returns:
            True if IP is private.
        """
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private
        except ValueError:
            return False

    @staticmethod
    def get_ip_version(ip: str) -> Optional[int]:
        """Get IP version (4 or 6).

        Args:
            ip: IP address.

        Returns:
            4, 6, or None if invalid.
        """
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.version
        except ValueError:
            return None


class EnrichmentScorer:
    """Calculate enrichment scores for indicators."""

    @staticmethod
    def calculate_confidence_score(
        *,
        detections: int = 0,
        total_engines: int = 1,
        age_days: Optional[int] = None,
        source_reputation: int = 50,
        cross_references: int = 0,
    ) -> int:
        """Calculate a comprehensive confidence score.

        Args:
            detections: Number of positive detections.
            total_engines: Total number of engines that scanned.
            age_days: Age of the indicator in days.
            source_reputation: Reputation of the reporting source (0-100).
            cross_references: Number of cross-references from other sources.

        Returns:
            Confidence score (0-100).
        """
        # Base score from detection rate
        if total_engines > 0:
            detection_rate = detections / total_engines
            base_score = int(detection_rate * 100)
        else:
            base_score = 50

        # Adjust for age (fresher = higher confidence)
        age_adjustment = 0
        if age_days is not None:
            if age_days <= 7:
                age_adjustment = 10
            elif age_days <= 30:
                age_adjustment = 5
            elif age_days >= 365:
                age_adjustment = -10

        # Adjust for source reputation
        reputation_adjustment = int((source_reputation - 50) / 10)

        # Adjust for cross-references
        cross_ref_adjustment = min(cross_references * 5, 20)

        # Calculate final score
        final_score = base_score + age_adjustment + reputation_adjustment + cross_ref_adjustment

        return max(0, min(final_score, 100))

    @staticmethod
    def calculate_threat_level(
        confidence: int,
        indicator_type: str,
        tags: list[str],
    ) -> str:
        """Calculate threat level based on indicator properties.

        Args:
            confidence: Confidence score.
            indicator_type: Type of indicator.
            tags: Associated tags.

        Returns:
            Threat level: 'critical', 'high', 'medium', 'low', or 'info'.
        """
        # Base level from confidence
        if confidence >= 90:
            level = "critical"
        elif confidence >= 75:
            level = "high"
        elif confidence >= 50:
            level = "medium"
        elif confidence >= 25:
            level = "low"
        else:
            level = "info"

        # Escalate based on tags
        critical_tags = {"ransomware", "apt", "c2", "command_and_control", "exfiltration"}
        high_tags = {"malware", "trojan", "exploit", "phishing", "botnet"}

        tag_set = {tag.lower() for tag in tags}

        if tag_set & critical_tags:
            if level in ("high", "medium", "low", "info"):
                level = "critical"
        elif tag_set & high_tags:
            if level in ("medium", "low", "info"):
                level = "high"

        return level
