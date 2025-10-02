"""Configuration for Kapsa operator."""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Operator configuration settings."""

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"  # json or console

    # Reconciliation
    default_poll_interval: int = 300  # seconds
    reconciliation_timeout: int = 600  # seconds

    # Metrics
    metrics_port: int = 8080
    metrics_enabled: bool = True

    # Kubernetes
    namespace: str = "kapsa-system"

    # kpack integration
    kpack_builder_image: str = "paketobuildpacks/builder:base"
    kpack_service_account: str = "kapsa-build"

    class Config:
        """Pydantic config."""

        env_prefix = "KAPSA_"
        case_sensitive = False


def get_settings() -> Settings:
    """Get operator settings."""
    return Settings()
