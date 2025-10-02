"""Main entry point for Kapsa operator."""

import asyncio

import kopf

from kapsa.config import get_settings
from kapsa.logging import configure_logging, get_logger
from kapsa.metrics import start_metrics_server

# Import controllers (registers handlers)
from kapsa.controllers import project  # noqa: F401

logger = get_logger(__name__)


@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_: object) -> None:
    """Configure operator on startup."""
    config = get_settings()

    # Configure logging
    configure_logging()
    logger.info("operator_starting", version="0.1.0")

    # Configure kopf settings
    settings.posting.enabled = True
    settings.watching.server_timeout = 600
    settings.persistence.finalizer = "kapsa.io/finalizer"

    # Start metrics server
    try:
        start_metrics_server()
    except Exception as e:
        logger.error("metrics_server_start_failed", error=str(e))


@kopf.on.cleanup()
async def cleanup(**_: object) -> None:
    """Cleanup on operator shutdown."""
    logger.info("operator_shutting_down")


def main() -> None:
    """Run the operator."""
    # Run kopf
    kopf.run(
        clusterwide=True,
        liveness_endpoint="http://0.0.0.0:8080/healthz",
    )


if __name__ == "__main__":
    main()
