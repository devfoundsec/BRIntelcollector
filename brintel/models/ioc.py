"""Indicator of Compromise (IoC) model definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Mapping, MutableMapping, Optional


class IndicatorSource(str, Enum):
    """Enumerates supported threat intelligence sources."""

    OTX = "otx"
    XFE = "xfe"
    VIRUSTOTAL = "virustotal"
    MISP = "misp"
    THREATFOX = "threatfox"
    ABUSEIPDB = "abuseipdb"
    SHODAN = "shodan"


@dataclass(slots=True)
class Indicator:
    """Represents a normalized indicator of compromise.

    Attributes:
        type: Normalized indicator type (e.g. ``domain`` or ``ip``).
        value: Value associated with the indicator.
        source: Source that produced the indicator.
        confidence: Confidence score between 0 and 100.
        first_seen: Timestamp of the earliest sighting.
        last_seen: Timestamp of the latest sighting.
        raw: Raw payload returned by the upstream provider.
        tags: Optional list of descriptive tags.
    """

    type: str
    value: str
    source: IndicatorSource
    confidence: int
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    raw: Mapping[str, Any] = field(default_factory=dict)
    tags: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> Dict[str, Any]:
        """Return the indicator as a serializable dictionary."""

        return {
            "type": self.type,
            "value": self.value,
            "source": self.source.value,
            "confidence": self.confidence,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "raw": dict(self.raw),
            "tags": list(self.tags),
        }

    def hash_key(self) -> str:
        """Return a deterministic hash key used for deduplication."""

        return f"{self.type}:{self.value}:{self.source.value}"

    @classmethod
    def from_raw(
        cls,
        data: Mapping[str, Any],
        *,
        source: IndicatorSource,
        value_key: str,
        type_value: str,
        confidence: int = 50,
        first_seen_key: str | None = None,
        last_seen_key: str | None = None,
    ) -> "Indicator":
        """Create an indicator from raw provider data.

        Parameters:
            data: Raw payload returned by the provider.
            source: Source enum describing the origin of the data.
            value_key: Key to extract the indicator value from ``data``.
            type_value: Normalized indicator type.
            confidence: Optional confidence score between 0 and 100.
            first_seen_key: Key to locate the first seen timestamp, if available.
            last_seen_key: Key to locate the last seen timestamp, if available.
        """

        first_seen: Optional[datetime] = None
        last_seen: Optional[datetime] = None
        if first_seen_key and (raw_first := data.get(first_seen_key)):
            first_seen = cls._parse_datetime(raw_first)
        if last_seen_key and (raw_last := data.get(last_seen_key)):
            last_seen = cls._parse_datetime(raw_last)

        value = str(data[value_key])
        return cls(
            type=type_value,
            value=value,
            source=source,
            confidence=confidence,
            first_seen=first_seen,
            last_seen=last_seen,
            raw=dict(data),
        )

    @staticmethod
    def _parse_datetime(value: Any) -> Optional[datetime]:
        """Parse an arbitrary datetime representation if possible."""

        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value)
        if isinstance(value, str):
            for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
        return None
