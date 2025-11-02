from __future__ import annotations

import pytest

fastapi = pytest.importorskip("fastapi")

from fastapi.testclient import TestClient

pytest.importorskip("brintel")

from brintel.services import create_app


def test_health_endpoint():
    client = TestClient(create_app())
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_search_endpoint(monkeypatch):
    app = create_app()
    client = TestClient(app)

    async def fake_search(self, source: str, query: str):
        from brintel.models import Indicator, IndicatorSource

        return [
            Indicator(
                type="domain",
                value=query,
                source=IndicatorSource.OTX,
                confidence=80,
            )
        ]

    from brintel.core.orchestrator import CollectorOrchestrator

    monkeypatch.setattr(CollectorOrchestrator, "search", fake_search)

    response = client.get("/v1/search", params={"source": "otx", "q": "example.com"})
    assert response.status_code == 200
    assert response.json()[0]["value"] == "example.com"
