"""Structured logging configuration for Kapsa operator."""

import logging
import sys
from typing import Any

import structlog

from kapsa.config import get_settings


def configure_logging() -> None:
    """Configure structured logging for the operator."""
    settings = get_settings()

    # Convert log level string to numeric level
    log_level_str = settings.log_level.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Determine processors based on log format
    if settings.log_format == "json":
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )


def get_logger(name: str) -> Any:
    """Get a logger instance."""
    return structlog.get_logger(name)
