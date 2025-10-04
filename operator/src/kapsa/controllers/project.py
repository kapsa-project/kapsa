"""Project CRD controller."""

import asyncio
from typing import Any, Dict, Optional

import kopf
from kubernetes import client
from kubernetes.client.rest import ApiException

from kapsa.logging import get_logger
from kapsa.metrics import project_reconcile_duration, project_reconcile_total, project_total

logger = get_logger(__name__)


@kopf.on.create("kapsa-project.io", "v1alpha1", "projects")
async def project_created(
    spec: Dict[str, Any],
    name: str,
    namespace: str,
    meta: kopf.Meta,
    **kwargs: object,
) -> Dict[str, Any]:
    """Handle Project creation."""
    logger.info(
        "project_created",
        project=name,
        namespace=namespace,
        repository=spec.get("repository", {}).get("url"),
    )

    # Increment metrics
    project_total.labels(namespace=namespace).inc()

    # Create dedicated namespace for this project
    await create_project_namespace(name, namespace, meta)

    # Initial status
    return {
        "conditions": [
            {
                "type": "Ready",
                "status": "False",
                "reason": "Initializing",
                "message": "Project is being initialized",
            }
        ],
        "environments": [],
    }


@kopf.on.update("kapsa-project.io", "v1alpha1", "projects")
async def project_updated(
    spec: Dict[str, Any],
    status: Dict[str, Any],
    name: str,
    namespace: str,
    **kwargs: object,
) -> Dict[str, Any]:
    """Handle Project updates."""
    logger.info(
        "project_updated",
        project=name,
        namespace=namespace,
    )

    with project_reconcile_duration.labels(namespace=namespace, project=name).time():
        try:
            # Reconcile environments based on spec
            await reconcile_environments(spec, name, namespace)

            # Update status
            project_reconcile_total.labels(
                namespace=namespace, project=name, status="success"
            ).inc()

            return {
                "conditions": [
                    {
                        "type": "Ready",
                        "status": "True",
                        "reason": "Reconciled",
                        "message": "Project successfully reconciled",
                    }
                ],
            }

        except Exception as e:
            logger.error(
                "project_reconcile_failed",
                project=name,
                namespace=namespace,
                error=str(e),
            )
            project_reconcile_total.labels(
                namespace=namespace, project=name, status="error"
            ).inc()

            return {
                "conditions": [
                    {
                        "type": "Ready",
                        "status": "False",
                        "reason": "ReconciliationFailed",
                        "message": f"Reconciliation failed: {str(e)}",
                    }
                ],
            }


@kopf.on.delete("kapsa-project.io", "v1alpha1", "projects")
async def project_deleted(
    name: str,
    namespace: str,
    **kwargs: object,
) -> None:
    """Handle Project deletion."""
    logger.info(
        "project_deleted",
        project=name,
        namespace=namespace,
    )

    # Cleanup project namespace
    await delete_project_namespace(name, namespace)


@kopf.timer("kapsa-project.io", "v1alpha1", "projects", interval=300, idle=60)
async def project_poll_git(
    spec: Dict[str, Any],
    status: Dict[str, Any],
    name: str,
    namespace: str,
    patch: kopf.Patch,
    **kwargs: object,
) -> None:
    """Periodically poll git repository for changes."""
    repository_spec = spec.get("repository", {})
    poll_interval = repository_spec.get("pollInterval", 300)

    # Adjust timer interval based on spec
    if poll_interval != 300:
        logger.debug(
            "git_poll_interval_adjusted",
            project=name,
            namespace=namespace,
            interval=poll_interval,
        )

    logger.debug(
        "git_poll_triggered",
        project=name,
        namespace=namespace,
        repository=repository_spec.get("url"),
    )

    # TODO: Implement git polling logic
    # 1. Clone/fetch repository
    # 2. Check for new commits on tracked branches
    # 3. If new commit found, trigger build
    # 4. Update status.latestCommit


async def create_project_namespace(
    project_name: str, parent_namespace: str, owner_meta: kopf.Meta
) -> None:
    """Create a dedicated namespace for the project."""
    v1 = client.CoreV1Api()
    namespace_name = f"{project_name}-ns"

    namespace = client.V1Namespace(
        metadata=client.V1ObjectMeta(
            name=namespace_name,
            labels={
                "kapsa-project.io/project": project_name,
                "kapsa-project.io/managed-by": "kapsa-operator",
            },
            annotations={
                "kapsa-project.io/parent-namespace": parent_namespace,
            },
        )
    )

    try:
        v1.create_namespace(namespace)
        logger.info(
            "namespace_created",
            namespace=namespace_name,
            project=project_name,
        )
    except ApiException as e:
        if e.status == 409:  # Already exists
            logger.debug(
                "namespace_already_exists",
                namespace=namespace_name,
                project=project_name,
            )
        else:
            raise


async def delete_project_namespace(project_name: str, parent_namespace: str) -> None:
    """Delete the project's dedicated namespace."""
    v1 = client.CoreV1Api()
    namespace_name = f"{project_name}-ns"

    try:
        v1.delete_namespace(namespace_name)
        logger.info(
            "namespace_deleted",
            namespace=namespace_name,
            project=project_name,
        )
    except ApiException as e:
        if e.status == 404:  # Not found
            logger.debug(
                "namespace_not_found",
                namespace=namespace_name,
                project=project_name,
            )
        else:
            logger.error(
                "namespace_deletion_failed",
                namespace=namespace_name,
                project=project_name,
                error=str(e),
            )


async def reconcile_environments(
    spec: Dict[str, Any], project_name: str, namespace: str
) -> None:
    """Reconcile Environment CRDs based on Project spec."""
    environments = spec.get("environments", [])

    logger.info(
        "reconciling_environments",
        project=project_name,
        namespace=namespace,
        count=len(environments),
    )

    # TODO: Implement environment reconciliation
    # 1. For each environment in spec, create/update Environment CRD
    # 2. Handle preview environments if enabled
    # 3. Clean up removed environments

    for env_spec in environments:
        env_name = env_spec.get("name")
        logger.debug(
            "reconciling_environment",
            project=project_name,
            environment=env_name,
            namespace=namespace,
        )
