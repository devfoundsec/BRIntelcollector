"""Command line interface for BRIntelcollector."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Optional

import typer

from .core import CollectorOrchestrator
from .models import Indicator
from .services.api import create_app
from .utils.logging import configure_logging

app = typer.Typer(help="BRIntelcollector threat intelligence toolkit")


@app.callback()
def main(ctx: typer.Context, verbose: bool = typer.Option(False, "--verbose", "-v")) -> None:
    """Configure logging verbosity."""

    configure_logging("DEBUG" if verbose else "INFO")


@app.command()
def search(source: str, term: str) -> None:
    """Search for indicators from a specific source."""

    orchestrator = CollectorOrchestrator()

    async def _run() -> None:
        indicators = await orchestrator.search(source, term)
        _render_indicators(indicators)

    asyncio.run(_run())


@app.command()
def collect(all: bool = typer.Option(False, "--all"), since: Optional[str] = typer.Option(None, "--since")) -> None:  # noqa: A002
    """Collect indicators from all sources."""

    orchestrator = CollectorOrchestrator()

    async def _run() -> None:
        timestamp: Optional[datetime] = None
        if all:
            timestamp = None
        elif since:
            if since.endswith("h"):
                hours = int(since[:-1])
                timestamp = datetime.utcnow() - timedelta(hours=hours)
            else:
                timestamp = datetime.fromisoformat(since)
        inserted = await orchestrator.collect_since(timestamp)
        typer.echo(f"Inserted {inserted} indicators")

    asyncio.run(_run())


@app.command()
def serve(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start the FastAPI service."""

    from uvicorn import run

    api = create_app()
    run(api, host=host, port=port)


def _render_indicators(indicators: list[Indicator]) -> None:
    if not indicators:
        typer.echo("No indicators found")
        return
    for indicator in indicators:
        typer.echo(indicator.as_dict())


if __name__ == "__main__":  # pragma: no cover
    app()
