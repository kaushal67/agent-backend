"""Centralized logging setup for the application."""

from __future__ import annotations

import logging


def configure_logging(level: str) -> None:
    """Configure root logger once with production-friendly format."""
    if getattr(configure_logging, "_configured", False):
        return

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    configure_logging._configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger instance."""
    return logging.getLogger(name)
