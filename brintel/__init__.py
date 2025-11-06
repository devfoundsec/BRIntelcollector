"""Top-level package for the BRIntelcollector project."""

from __future__ import annotations

from importlib import metadata

from .core.orchestrator import CollectorOrchestrator
from .models.ioc import Indicator
from .services.api import create_app

__all__ = ["CollectorOrchestrator", "Indicator", "create_app", "__version__"]

try:
    __version__ = metadata.version("brintelcollector")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "0.1.0"
