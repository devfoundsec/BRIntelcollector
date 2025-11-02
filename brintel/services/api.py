"""FastAPI application exposing collection capabilities."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ..core import CollectorOrchestrator
from ..models import Indicator
from ..utils.config import settings


def create_app() -> FastAPI:
    """Return a configured FastAPI instance."""

    app = FastAPI(title="BRIntelcollector", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_hosts,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    orchestrator = CollectorOrchestrator()

    async def get_orchestrator() -> CollectorOrchestrator:
        return orchestrator

    @app.get("/v1/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/search", response_model=List[dict])
    async def search(source: str, q: str, orchestrator: CollectorOrchestrator = Depends(get_orchestrator)) -> List[dict]:
        try:
            indicators = await orchestrator.search(source, q)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return [indicator.as_dict() for indicator in indicators]

    @app.get("/v1/iocs", response_model=List[dict])
    async def iocs(
        since: Optional[str] = None, orchestrator: CollectorOrchestrator = Depends(get_orchestrator)
    ) -> List[dict]:
        timestamp: Optional[datetime] = None
        if since:
            timestamp = datetime.fromisoformat(since)
        count = await orchestrator.collect_since(timestamp)
        return [indicator.as_dict() for indicator in orchestrator.repository.fetch_all(limit=count or 100)]

    @app.get("/metrics", tags=["observability"])
    async def metrics() -> dict[str, float]:
        return {
            "requests_per_minute": 0.0,
            "average_latency": 0.0,
        }

    return app


__all__ = ["create_app"]
