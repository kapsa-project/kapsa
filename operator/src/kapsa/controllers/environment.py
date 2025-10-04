"""Environment CRD controller."""

from typing import Any, Dict

import kopf

from kapsa.logging import get_logger

logger = get_logger(__name__)


@kopf.on.create("kapsa-project.io", "v1alpha1", "environments")
async def environment_created(
    spec: Dict[str, Any],
    name: str,
    namespace: str,
    meta: kopf.Meta,
    **kwargs: object,
) -> Dict[str, Any]:
    """Handle Environment creation."""
    project_ref = spec.get("projectRef", {})
    env_type = spec.get("type")
    branch = spec.get("branch")

    logger.info(
        "environment_created",
        environment=name,
        namespace=namespace,
        project=project_ref.get("name"),
        type=env_type,
        branch=branch,
    )

    # TODO: Fetch Project CRD to get image tag and configuration
    # TODO: Create Deployment
    # TODO: Create Service
    # TODO: Create Ingress with cert-manager annotations
    # TODO: Create HPA if autoscaling is enabled

    return {
        "conditions": [
            {
                "type": "Ready",
                "status": "False",
                "reason": "Initializing",
                "message": "Environment is being initialized",
            }
        ],
    }


@kopf.on.update("kapsa-project.io", "v1alpha1", "environments")
async def environment_updated(
    spec: Dict[str, Any],
    name: str,
    namespace: str,
    old: Dict[str, Any],
    new: Dict[str, Any],
    **kwargs: object,
) -> Dict[str, Any]:
    """Handle Environment updates."""
    logger.info(
        "environment_updated",
        environment=name,
        namespace=namespace,
    )

    # TODO: Update Deployment if runtime config changed
    # TODO: Update Service if needed
    # TODO: Update Ingress if domain changed
    # TODO: Update HPA if autoscaling config changed

    return {
        "conditions": [
            {
                "type": "Ready",
                "status": "True",
                "reason": "Updated",
                "message": "Environment updated successfully",
            }
        ],
    }


@kopf.on.delete("kapsa-project.io", "v1alpha1", "environments")
async def environment_deleted(
    spec: Dict[str, Any],
    name: str,
    namespace: str,
    **kwargs: object,
) -> None:
    """Handle Environment deletion."""
    logger.info(
        "environment_deleted",
        environment=name,
        namespace=namespace,
    )

    # Kubernetes garbage collection will clean up owned resources
    # (Deployment, Service, Ingress, HPA) via ownerReferences
