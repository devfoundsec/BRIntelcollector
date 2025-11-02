from __future__ import annotations

import asyncio

import pytest

typer = pytest.importorskip("typer")

from typer.testing import CliRunner

pytest.importorskip("brintel")

from brintel import CollectorOrchestrator
from brintel.cli import app
from brintel.models import Indicator, IndicatorSource


runner = CliRunner()


class DummyClient:
    source = "otx"

    async def search(self, term: str):
        return [
            Indicator(
                type="domain",
                value=term,
                source=IndicatorSource.OTX,
                confidence=80,
            )
        ]


def test_cli_search(monkeypatch):
    orchestrator = CollectorOrchestrator(clients=[])
    orchestrator.clients.append(DummyClient())  # type: ignore[arg-type]

    async def fake_search(self, source: str, term: str):
        return await orchestrator.clients[0].search(term)

    monkeypatch.setattr(CollectorOrchestrator, "search", fake_search)

    result = runner.invoke(app, ["search", "otx", "example.com"])
    assert result.exit_code == 0
    assert "example.com" in result.stdout
