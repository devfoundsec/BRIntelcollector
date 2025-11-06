"""FastAPI application exposing collection capabilities."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from ..core import CollectorOrchestrator
from ..data.stats import StatsCollector
from ..models import Indicator, IndicatorSource
from ..utils.config import settings
from ..utils.logging import get_logger
from ..utils.metrics import GLOBAL_METRICS, Timer, track_api_call

LOGGER = get_logger(__name__)


def create_app() -> FastAPI:
    """Return a configured FastAPI instance."""

    app = FastAPI(
        title="BRIntelcollector",
        version="2.0.0",
        description="Advanced Threat Intelligence Collection and Analysis Platform",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_hosts,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    orchestrator = CollectorOrchestrator()
    stats_collector = StatsCollector(settings.SQLITE_DB_PATH)

    async def get_orchestrator() -> CollectorOrchestrator:
        return orchestrator

    async def get_stats_collector() -> StatsCollector:
        return stats_collector

    # ========== Health & Status ==========

    @app.get("/v1/health", tags=["health"])
    async def health() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok", "version": "2.0.0"}

    @app.get("/v1/status", tags=["health"])
    async def status(
        orchestrator: CollectorOrchestrator = Depends(get_orchestrator)
    ) -> dict:
        """Get detailed system status."""
        repo_stats = orchestrator.repository.get_stats_by_source()

        return {
            "status": "operational",
            "sources": {
                "total": len(orchestrator.clients),
                "active": len([c for c in orchestrator.clients if c.api_key]),
            },
            "indicators": repo_stats,
            "uptime": "N/A",  # Would need startup time tracking
        }

    # ========== Search & Query ==========

    @app.get("/v1/search", response_model=List[dict], tags=["indicators"])
    async def search(
        source: str,
        q: str,
        orchestrator: CollectorOrchestrator = Depends(get_orchestrator),
    ) -> List[dict]:
        """Search for indicators in a specific source.

        Args:
            source: Source to search (otx, virustotal, etc.)
            q: Query string (IP, domain, hash, etc.)
        """
        with Timer(f"api_search_{source}"):
            try:
                indicators = await orchestrator.search(source, q)
                track_api_call(source, success=True)
                return [indicator.as_dict() for indicator in indicators]
            except ValueError as exc:
                track_api_call(source, success=False)
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            except Exception as exc:
                track_api_call(source, success=False)
                LOGGER.error(f"Error searching {source}: {exc}", exc_info=True)
                raise HTTPException(status_code=500, detail="Internal server error") from exc

    @app.get("/v1/indicators", response_model=List[dict], tags=["indicators"])
    async def get_indicators(
        type: Optional[str] = None,
        source: Optional[str] = None,
        min_confidence: Optional[int] = Query(None, ge=0, le=100),
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        orchestrator: CollectorOrchestrator = Depends(get_orchestrator),
    ) -> List[dict]:
        """Query indicators with filters.

        Args:
            type: Filter by indicator type
            source: Filter by source
            min_confidence: Minimum confidence score
            limit: Maximum results to return
            offset: Pagination offset
        """
        source_enum = IndicatorSource(source) if source else None

        indicators = orchestrator.repository.search(
            type=type,
            source=source_enum,
            min_confidence=min_confidence,
            limit=limit,
            offset=offset,
        )

        return [ind.as_dict() for ind in indicators]

    @app.get("/v1/indicators/recent", response_model=List[dict], tags=["indicators"])
    async def get_recent_indicators(
        hours: int = Query(24, ge=1, le=168),
        limit: int = Query(100, ge=1, le=1000),
        orchestrator: CollectorOrchestrator = Depends(get_orchestrator),
    ) -> List[dict]:
        """Get recently seen indicators.

        Args:
            hours: Number of hours to look back
            limit: Maximum results to return
        """
        indicators = orchestrator.repository.get_recent(hours=hours, limit=limit)
        return [ind.as_dict() for ind in indicators]

    @app.get("/v1/indicators/high-confidence", response_model=List[dict], tags=["indicators"])
    async def get_high_confidence_indicators(
        min_confidence: int = Query(80, ge=0, le=100),
        limit: int = Query(100, ge=1, le=1000),
        orchestrator: CollectorOrchestrator = Depends(get_orchestrator),
    ) -> List[dict]:
        """Get high-confidence indicators.

        Args:
            min_confidence: Minimum confidence threshold
            limit: Maximum results to return
        """
        indicators = orchestrator.repository.get_high_confidence(
            min_confidence=min_confidence, limit=limit
        )
        return [ind.as_dict() for ind in indicators]

    # ========== Collection ==========

    @app.post("/v1/collect", tags=["collection"])
    async def trigger_collection(
        since: Optional[str] = None,
        orchestrator: CollectorOrchestrator = Depends(get_orchestrator),
    ) -> dict:
        """Trigger a collection from all sources.

        Args:
            since: ISO format timestamp to collect since
        """
        timestamp: Optional[datetime] = None
        if since:
            try:
                timestamp = datetime.fromisoformat(since)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid timestamp format")

        with Timer("api_collection"):
            try:
                count = await orchestrator.collect_since(timestamp)
                return {
                    "status": "success",
                    "indicators_collected": count,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            except Exception as exc:
                LOGGER.error(f"Collection error: {exc}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(exc)) from exc

    # ========== Statistics ==========

    @app.get("/v1/stats", tags=["statistics"])
    async def get_statistics(
        stats: StatsCollector = Depends(get_stats_collector)
    ) -> dict:
        """Get comprehensive statistics."""
        all_stats = stats.collect_all_stats()

        return {
            "total_indicators": all_stats.total_count,
            "unique_types": all_stats.unique_types,
            "unique_sources": all_stats.unique_sources,
            "avg_confidence": all_stats.avg_confidence,
            "high_confidence_count": all_stats.high_confidence_count,
            "recent_24h_count": all_stats.recent_24h_count,
            "by_source": all_stats.by_source,
            "by_type": all_stats.by_type,
            "top_tags": all_stats.top_tags,
            "oldest_indicator": all_stats.oldest_indicator.isoformat()
            if all_stats.oldest_indicator
            else None,
            "newest_indicator": all_stats.newest_indicator.isoformat()
            if all_stats.newest_indicator
            else None,
        }

    @app.get("/v1/stats/sources", tags=["statistics"])
    async def get_source_stats(
        orchestrator: CollectorOrchestrator = Depends(get_orchestrator)
    ) -> dict:
        """Get statistics grouped by source."""
        return orchestrator.repository.get_stats_by_source()

    @app.get("/v1/stats/types", tags=["statistics"])
    async def get_type_stats(
        orchestrator: CollectorOrchestrator = Depends(get_orchestrator)
    ) -> dict:
        """Get statistics grouped by indicator type."""
        return orchestrator.repository.get_stats_by_type()

    @app.get("/v1/stats/trends", tags=["statistics"])
    async def get_trends(
        days: int = Query(7, ge=1, le=30),
        stats: StatsCollector = Depends(get_stats_collector),
    ) -> dict:
        """Get trend analysis over time.

        Args:
            days: Number of days to analyze
        """
        return stats.get_trend_analysis(days=days)

    # ========== Metrics & Monitoring ==========

    @app.get("/metrics", tags=["observability"])
    async def metrics_json() -> dict:
        """Get metrics in JSON format."""
        return GLOBAL_METRICS.get_all_metrics()

    @app.get("/metrics/prometheus", tags=["observability"], response_class=PlainTextResponse)
    async def metrics_prometheus() -> str:
        """Get metrics in Prometheus exposition format."""
        return GLOBAL_METRICS.export_prometheus()

    # ========== Export ==========

    @app.get("/v1/export", tags=["export"])
    async def export_indicators(
        format: str = Query("json", regex="^(json|csv)$"),
        type: Optional[str] = None,
        source: Optional[str] = None,
        min_confidence: Optional[int] = None,
        limit: int = Query(1000, ge=1, le=10000),
        orchestrator: CollectorOrchestrator = Depends(get_orchestrator),
    ) -> Response:
        """Export indicators in various formats.

        Args:
            format: Export format (json or csv)
            type: Filter by indicator type
            source: Filter by source
            min_confidence: Minimum confidence score
            limit: Maximum indicators to export
        """
        source_enum = IndicatorSource(source) if source else None

        indicators = orchestrator.repository.search(
            type=type,
            source=source_enum,
            min_confidence=min_confidence,
            limit=limit,
        )

        if format == "json":
            import json

            data = [ind.as_dict() for ind in indicators]
            content = json.dumps(data, indent=2, default=str)
            return Response(
                content=content,
                media_type="application/json",
                headers={"Content-Disposition": "attachment; filename=indicators.json"},
            )
        elif format == "csv":
            import csv
            import io

            output = io.StringIO()
            if indicators:
                fieldnames = ["type", "value", "source", "confidence", "first_seen", "last_seen", "tags"]
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()

                for ind in indicators:
                    writer.writerow(
                        {
                            "type": ind.type,
                            "value": ind.value,
                            "source": ind.source.value,
                            "confidence": ind.confidence,
                            "first_seen": ind.first_seen.isoformat() if ind.first_seen else "",
                            "last_seen": ind.last_seen.isoformat() if ind.last_seen else "",
                            "tags": ",".join(ind.tags),
                        }
                    )

            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=indicators.csv"},
            )

    return app


__all__ = ["create_app"]
