from __future__ import annotations

import asyncio

import pytest

pytest.importorskip("brintel")

from brintel.core.rate_manager import RateManager


@pytest.mark.asyncio
async def test_rate_manager_waits_between_calls(monkeypatch):
    rate_manager = RateManager()
    rate_manager.register("otx", max_per_minute=60)

    timestamps: list[float] = []

    async def fake_sleep(duration: float) -> None:
        timestamps.append(duration)

    monkeypatch.setattr(asyncio, "sleep", fake_sleep)
    await rate_manager.wait_for_slot("otx")
    await rate_manager.wait_for_slot("otx")

    assert timestamps and timestamps[-1] >= 0


def test_rate_manager_backoff_dynamic(monkeypatch):
    monkeypatch.setattr("brintel.utils.config.settings.rate_dynamic", True, raising=False)
    rate_manager = RateManager()
    delay = rate_manager.record_failure("otx", attempt=2)
    assert delay > 0
