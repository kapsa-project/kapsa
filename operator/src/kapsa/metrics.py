"""Prometheus metrics for Kapsa operator."""

from prometheus_client import Counter, Gauge, Histogram, start_http_server

from kapsa.config import get_settings
from kapsa.logging import get_logger

logger = get_logger(__name__)

# Project metrics
project_total = Counter(
    "kapsa_projects_total",
    "Total number of Projects",
    ["namespace"],
)

project_reconcile_total = Counter(
    "kapsa_project_reconcile_total",
    "Total number of Project reconciliations",
    ["namespace", "project", "status"],
)

project_reconcile_duration = Histogram(
    "kapsa_project_reconcile_duration_seconds",
    "Duration of Project reconciliations",
    ["namespace", "project"],
)

# Environment metrics
environment_total = Gauge(
    "kapsa_environments_total",
    "Total number of Environments",
    ["namespace", "project", "type"],
)

environment_reconcile_total = Counter(
    "kapsa_environment_reconcile_total",
    "Total number of Environment reconciliations",
    ["namespace", "environment", "status"],
)

# Build metrics
build_total = Counter(
    "kapsa_builds_total",
    "Total number of builds triggered",
    ["namespace", "project", "status"],
)

build_duration = Histogram(
    "kapsa_build_duration_seconds",
    "Duration of builds",
    ["namespace", "project"],
)

# Git polling metrics
git_poll_total = Counter(
    "kapsa_git_poll_total",
    "Total number of git polls",
    ["namespace", "project", "status"],
)

git_poll_duration = Histogram(
    "kapsa_git_poll_duration_seconds",
    "Duration of git polls",
    ["namespace", "project"],
)


def start_metrics_server() -> None:
    """Start the Prometheus metrics HTTP server."""
    settings = get_settings()

    if not settings.metrics_enabled:
        logger.info("metrics_disabled")
        return

    try:
        start_http_server(settings.metrics_port)
        logger.info("metrics_server_started", port=settings.metrics_port)
    except Exception as e:
        logger.error("metrics_server_failed", error=str(e))
        raise
