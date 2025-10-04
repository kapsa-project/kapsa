"""DomainPool CRD controller."""

from typing import Any, Dict

import kopf

from kapsa.logging import get_logger

logger = get_logger(__name__)


@kopf.on.create("kapsa-project.io", "v1alpha1", "domainpools")
async def domainpool_created(
    spec: Dict[str, Any],
    name: str,
    meta: kopf.Meta,
    **kwargs: object,
) -> Dict[str, Any]:
    """Handle DomainPool creation."""
    base_domains = spec.get("baseDomains", [])
    logger.info(
        "domainpool_created",
        domainpool=name,
        base_domains=base_domains,
    )

    # TODO: Validate cert-manager ClusterIssuer/Issuer exists
    # TODO: Initialize domain allocation tracking

    return {
        "conditions": [
            {
                "type": "Ready",
                "status": "True",
                "reason": "DomainPoolConfigured",
                "message": f"DomainPool {name} is configured with {len(base_domains)} base domain(s)",
            }
        ],
        "allocatedDomains": [],
        "availableDomains": base_domains,
    }


@kopf.on.update("kapsa-project.io", "v1alpha1", "domainpools")
async def domainpool_updated(
    spec: Dict[str, Any],
    name: str,
    old: Dict[str, Any],
    new: Dict[str, Any],
    status: Dict[str, Any],
    **kwargs: object,
) -> Dict[str, Any]:
    """Handle DomainPool updates."""
    base_domains = spec.get("baseDomains", [])
    logger.info(
        "domainpool_updated",
        domainpool=name,
        base_domains=base_domains,
    )

    # TODO: Handle base domain additions/removals
    # TODO: Update allocated domains if base domains changed

    return {
        "conditions": [
            {
                "type": "Ready",
                "status": "True",
                "reason": "DomainPoolUpdated",
                "message": f"DomainPool {name} updated",
            }
        ],
        "availableDomains": base_domains,
    }


@kopf.on.delete("kapsa-project.io", "v1alpha1", "domainpools")
async def domainpool_deleted(
    spec: Dict[str, Any],
    name: str,
    **kwargs: object,
) -> None:
    """Handle DomainPool deletion."""
    logger.info("domainpool_deleted", domainpool=name)

    # TODO: Check if any projects are still using this domain pool
    # TODO: Emit warning event if domains are still allocated
