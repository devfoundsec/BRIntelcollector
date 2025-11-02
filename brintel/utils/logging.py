"""Logging configuration for the project."""

from __future__ import annotations

import logging
from logging.config import dictConfig
from typing import Any, Dict


def configure_logging(level: int | str = "INFO") -> None:
    """Configure structured logging for the application."""

    dict_config = _build_logging_config(level)
    dictConfig(dict_config)


def _build_logging_config(level: int | str) -> Dict[str, Any]:
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
                "level": level,
            }
        },
        "root": {"handlers": ["console"], "level": level},
    }


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger instance."""

    return logging.getLogger(name)
