"""Registry CRD controller."""

from typing import Any, Dict

import kopf

from kapsa.logging import get_logger

logger = get_logger(__name__)


@kopf.on.create("kapsa-project.io", "v1alpha1", "registries")
async def registry_created(
    spec: Dict[str, Any],
    name: str,
    meta: kopf.Meta,
    **kwargs: object,
) -> Dict[str, Any]:
    """Handle Registry creation."""
    logger.info(
        "registry_created",
        registry=name,
        type=spec.get("type"),
        endpoint=spec.get("endpoint"),
    )

    # TODO: Validate registry credentials secret exists
    # TODO: Create image pull secret template if needed
    # TODO: Verify connection to the registry

    return {
        "conditions": [
            {
                "type": "Ready",
                "status": "True",
                "reason": "RegistryConfigured",
                "message": f"Registry {name} is configured and ready",
            }
        ],
    }


@kopf.on.update("kapsa-project.io", "v1alpha1", "registries")
async def registry_updated(
    spec: Dict[str, Any],
    name: str,
    old: Dict[str, Any],
    new: Dict[str, Any],
    **kwargs: object,
) -> Dict[str, Any]:
    """Handle Registry updates."""
    logger.info(
        "registry_updated",
        registry=name,
        type=spec.get("type"),
    )

    # TODO: Update image pull secrets in project namespaces if changed

    return {
        "conditions": [
            {
                "type": "Ready",
                "status": "True",
                "reason": "RegistryUpdated",
                "message": f"Registry {name} configuration updated",
            }
        ],
    }


@kopf.on.delete("kapsa-project.io", "v1alpha1", "registries")
async def registry_deleted(
    spec: Dict[str, Any],
    name: str,
    **kwargs: object,
) -> None:
    """Handle Registry deletion."""
    logger.info("registry_deleted", registry=name)

    # Note: We don't delete image pull secrets from project namespaces
    # as they might still be needed for existing deployments
