"""Configuration utilities for the BRIntelcollector package."""

from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    api_timeout: float = Field(10.0, description="Default timeout for API calls")
    cache_path: Path = Field(Path("data/cache.sqlite"), description="SQLite cache path")
    cache_ttl_seconds: int = Field(300, description="TTL for cached API responses")
    rate_dynamic: bool = Field(False, description="Enable dynamic rate limiting")
    proxy_enabled: bool = Field(False, description="Enable proxy usage")
    proxy_list: Path | None = Field(None, description="Path to proxy list file")
    proxy_rotate: bool = Field(True, description="Enable proxy rotation")
    sqlite_db_path: Path = Field(Path("data/brintel.db"), description="Primary SQLite database")
    allowed_hosts: List[str] = Field(default_factory=lambda: ["*"], description="Allowed CORS hosts")

    class Config:
        env_file = ".env"
        env_prefix = "BRINTEL_"

    @validator("cache_path", "sqlite_db_path", pre=True)
    def _expand_path(cls, value: Path | str) -> Path:  # noqa: N805
        path = Path(value).expanduser()
        if not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
