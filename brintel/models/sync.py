"""Synchronization state models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class SyncState:
    """Represents the synchronization state for a provider."""

    source: str
    last_synced_at: Optional[datetime] = None

    def bump(self, new_timestamp: datetime) -> None:
        """Update the last synchronization timestamp."""

        if self.last_synced_at is None or new_timestamp > self.last_synced_at:
            self.last_synced_at = new_timestamp
