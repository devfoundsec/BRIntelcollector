"""Exporters for indicators in various formats."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from io import StringIO
from typing import Any, Dict, List
from uuid import uuid4

from ..models import Indicator


class BaseExporter:
    """Base class for exporters."""

    def export(self, indicators: List[Indicator]) -> str:
        """Export indicators to string format.

        Args:
            indicators: List of indicators to export.

        Returns:
            Exported data as string.
        """
        raise NotImplementedError


class JSONExporter(BaseExporter):
    """Export indicators to JSON format."""

    def export(self, indicators: List[Indicator], pretty: bool = True) -> str:
        """Export indicators to JSON.

        Args:
            indicators: List of indicators to export.
            pretty: Whether to pretty-print the JSON.

        Returns:
            JSON string.
        """
        data = [ind.as_dict() for ind in indicators]

        if pretty:
            return json.dumps(data, indent=2, default=str)
        else:
            return json.dumps(data, default=str)


class CSVExporter(BaseExporter):
    """Export indicators to CSV format."""

    DEFAULT_FIELDS = [
        "type",
        "value",
        "source",
        "confidence",
        "first_seen",
        "last_seen",
        "tags",
    ]

    def export(
        self, indicators: List[Indicator], fields: List[str] | None = None
    ) -> str:
        """Export indicators to CSV.

        Args:
            indicators: List of indicators to export.
            fields: Fields to include (defaults to DEFAULT_FIELDS).

        Returns:
            CSV string.
        """
        fields = fields or self.DEFAULT_FIELDS

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()

        for ind in indicators:
            row = {}
            for field in fields:
                if field == "source":
                    row[field] = ind.source.value
                elif field == "tags":
                    row[field] = ",".join(ind.tags)
                elif field in ("first_seen", "last_seen"):
                    value = getattr(ind, field)
                    row[field] = value.isoformat() if value else ""
                else:
                    row[field] = getattr(ind, field, "")

            writer.writerow(row)

        return output.getvalue()


class STIX2Exporter(BaseExporter):
    """Export indicators to STIX 2.1 format.

    STIX (Structured Threat Information Expression) is a standardized language
    for describing cyber threat information.
    """

    def export(self, indicators: List[Indicator]) -> str:
        """Export indicators to STIX 2.1 JSON.

        Args:
            indicators: List of indicators to export.

        Returns:
            STIX 2.1 JSON string.
        """
        bundle = self._create_bundle(indicators)
        return json.dumps(bundle, indent=2, default=str)

    def _create_bundle(self, indicators: List[Indicator]) -> Dict[str, Any]:
        """Create a STIX 2.1 bundle from indicators.

        Args:
            indicators: List of indicators.

        Returns:
            STIX bundle dictionary.
        """
        objects = []

        # Create identity object for BRIntelcollector
        identity = {
            "type": "identity",
            "spec_version": "2.1",
            "id": f"identity--{uuid4()}",
            "created": datetime.utcnow().isoformat() + "Z",
            "modified": datetime.utcnow().isoformat() + "Z",
            "name": "BRIntelcollector",
            "identity_class": "system",
        }
        objects.append(identity)

        # Convert each indicator
        for ind in indicators:
            stix_indicator = self._indicator_to_stix(ind, identity["id"])
            if stix_indicator:
                objects.append(stix_indicator)

        # Create bundle
        bundle = {
            "type": "bundle",
            "id": f"bundle--{uuid4()}",
            "spec_version": "2.1",
            "objects": objects,
        }

        return bundle

    def _indicator_to_stix(
        self, indicator: Indicator, created_by_ref: str
    ) -> Dict[str, Any] | None:
        """Convert an Indicator to STIX 2.1 format.

        Args:
            indicator: Indicator to convert.
            created_by_ref: Reference to the identity that created this.

        Returns:
            STIX indicator dictionary or None if conversion fails.
        """
        try:
            # Build pattern based on indicator type
            pattern = self._build_stix_pattern(indicator)

            if not pattern:
                return None

            # Map confidence score to STIX confidence
            confidence = self._map_confidence(indicator.confidence)

            stix_obj = {
                "type": "indicator",
                "spec_version": "2.1",
                "id": f"indicator--{uuid4()}",
                "created": indicator.first_seen.isoformat() + "Z"
                if indicator.first_seen
                else datetime.utcnow().isoformat() + "Z",
                "modified": indicator.last_seen.isoformat() + "Z"
                if indicator.last_seen
                else datetime.utcnow().isoformat() + "Z",
                "name": f"{indicator.type}: {indicator.value}",
                "pattern": pattern,
                "pattern_type": "stix",
                "valid_from": indicator.first_seen.isoformat() + "Z"
                if indicator.first_seen
                else datetime.utcnow().isoformat() + "Z",
                "confidence": confidence,
                "created_by_ref": created_by_ref,
                "labels": list(indicator.tags) if indicator.tags else [],
                "external_references": [
                    {
                        "source_name": indicator.source.value,
                        "description": f"Indicator from {indicator.source.value}",
                    }
                ],
            }

            return stix_obj

        except Exception as e:
            # Log error but don't fail entire export
            return None

    def _build_stix_pattern(self, indicator: Indicator) -> str | None:
        """Build a STIX pattern from an indicator.

        Args:
            indicator: Indicator to convert.

        Returns:
            STIX pattern string or None.
        """
        # Map our types to STIX cyber observable types
        if indicator.type == "ip":
            return f"[ipv4-addr:value = '{indicator.value}']"

        elif indicator.type == "domain":
            return f"[domain-name:value = '{indicator.value}']"

        elif indicator.type == "url":
            return f"[url:value = '{indicator.value}']"

        elif indicator.type == "email":
            return f"[email-addr:value = '{indicator.value}']"

        elif indicator.type == "hash":
            # Determine hash type based on length
            if len(indicator.value) == 32:
                return f"[file:hashes.MD5 = '{indicator.value}']"
            elif len(indicator.value) == 40:
                return f"[file:hashes.'SHA-1' = '{indicator.value}']"
            elif len(indicator.value) == 64:
                return f"[file:hashes.'SHA-256' = '{indicator.value}']"

        # Default fallback
        return None

    def _map_confidence(self, confidence: int) -> int:
        """Map our 0-100 confidence to STIX confidence (0-100).

        Args:
            confidence: Our confidence score.

        Returns:
            STIX confidence value.
        """
        # STIX uses 0-100 scale, so direct mapping works
        return confidence


class IOCTextExporter(BaseExporter):
    """Export indicators as plain text list (one per line)."""

    def export(self, indicators: List[Indicator], include_type: bool = False) -> str:
        """Export indicators to plain text.

        Args:
            indicators: List of indicators to export.
            include_type: Whether to include indicator type prefix.

        Returns:
            Plain text string with one indicator per line.
        """
        lines = []

        for ind in indicators:
            if include_type:
                lines.append(f"{ind.type}:{ind.value}")
            else:
                lines.append(ind.value)

        return "\n".join(lines)


class MISPExporter(BaseExporter):
    """Export indicators in MISP format."""

    def export(self, indicators: List[Indicator]) -> str:
        """Export indicators to MISP JSON format.

        Args:
            indicators: List of indicators to export.

        Returns:
            MISP JSON string.
        """
        misp_event = {
            "Event": {
                "uuid": str(uuid4()),
                "info": f"BRIntelcollector export - {datetime.utcnow().isoformat()}",
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "timestamp": int(datetime.utcnow().timestamp()),
                "published": False,
                "analysis": "2",  # Ongoing analysis
                "threat_level_id": "2",  # Medium
                "Attribute": [],
            }
        }

        for ind in indicators:
            attribute = self._indicator_to_misp_attribute(ind)
            if attribute:
                misp_event["Event"]["Attribute"].append(attribute)

        return json.dumps(misp_event, indent=2, default=str)

    def _indicator_to_misp_attribute(self, indicator: Indicator) -> Dict[str, Any] | None:
        """Convert an indicator to a MISP attribute.

        Args:
            indicator: Indicator to convert.

        Returns:
            MISP attribute dictionary or None.
        """
        # Map our types to MISP types
        type_mapping = {
            "ip": "ip-dst",
            "domain": "domain",
            "url": "url",
            "email": "email-dst",
            "hash": self._determine_hash_type(indicator.value),
        }

        misp_type = type_mapping.get(indicator.type)
        if not misp_type:
            return None

        attribute = {
            "uuid": str(uuid4()),
            "type": misp_type,
            "category": "Network activity",
            "value": indicator.value,
            "timestamp": int(indicator.last_seen.timestamp())
            if indicator.last_seen
            else int(datetime.utcnow().timestamp()),
            "comment": f"Source: {indicator.source.value}, Confidence: {indicator.confidence}",
            "to_ids": indicator.confidence >= 70,  # Enable IDS flag for high confidence
            "Tag": [{"name": tag} for tag in indicator.tags] if indicator.tags else [],
        }

        return attribute

    def _determine_hash_type(self, hash_value: str) -> str:
        """Determine MISP hash type based on length.

        Args:
            hash_value: Hash string.

        Returns:
            MISP hash type.
        """
        hash_len = len(hash_value)
        if hash_len == 32:
            return "md5"
        elif hash_len == 40:
            return "sha1"
        elif hash_len == 64:
            return "sha256"
        else:
            return "other"


# Export factory
def get_exporter(format_type: str) -> BaseExporter:
    """Get an exporter instance for the given format.

    Args:
        format_type: Format type (json, csv, stix, txt, misp).

    Returns:
        Exporter instance.

    Raises:
        ValueError: If format is not supported.
    """
    exporters = {
        "json": JSONExporter,
        "csv": CSVExporter,
        "stix": STIX2Exporter,
        "txt": IOCTextExporter,
        "misp": MISPExporter,
    }

    exporter_class = exporters.get(format_type.lower())
    if not exporter_class:
        raise ValueError(
            f"Unsupported export format: {format_type}. "
            f"Supported formats: {', '.join(exporters.keys())}"
        )

    return exporter_class()
