"""Project CRD controller."""

import asyncio
from typing import Any, Dict, Optional

import kopf
from kubernetes import client
from kubernetes.client.rest import ApiException
from kubernetes.dynamic import DynamicClient

from kapsa.logging import get_logger
from kapsa.utils.kpack import create_kpack_image_spec, create_service_account_spec

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

    # Create dedicated namespace for this project
    project_namespace = await create_project_namespace(name, namespace, meta)

    # Create kpack resources
    await create_kpack_resources(spec, name, project_namespace, meta)

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

    try:
        # Reconcile environments based on spec
        await reconcile_environments(spec, name, namespace)

        # Reconcile kpack resources
        project_namespace = f"{name}-ns"
        await reconcile_kpack_resources(spec, name, project_namespace)

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
) -> str:
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

    return namespace_name


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


async def create_kpack_resources(
    spec: Dict[str, Any],
    project_name: str,
    project_namespace: str,
    owner_meta: kopf.Meta,
) -> None:
    """Create kpack Image and ServiceAccount resources."""
    v1 = client.CoreV1Api()
    api_client = client.ApiClient()
    dyn_client = DynamicClient(api_client)

    # Get repository configuration
    repository = spec.get("repository", {})
    git_url = repository.get("url")
    git_branch = repository.get("branch", "main")

    # Get registry configuration
    registry_spec = spec.get("registry", {})
    registry_name = registry_spec.get("name")
    image_repository = registry_spec.get("imageRepository", f"{project_name}")

    if not git_url:
        logger.warning(
            "no_git_url",
            project=project_name,
            message="Project does not have a git repository URL",
        )
        return

    if not registry_name:
        logger.warning(
            "no_registry",
            project=project_name,
            message="Project does not specify a registry",
        )
        return

    # TODO: Fetch Registry CRD to get actual registry endpoint
    # For now, use a placeholder
    image_tag = f"registry.example.com/{image_repository}:latest"

    # Create ServiceAccount with registry credentials
    service_account_name = f"{project_name}-kpack-sa"

    # TODO: Get docker secret from Registry CRD
    docker_secret_name = f"{registry_name}-credentials"

    sa_spec = create_service_account_spec(
        service_account_name, project_namespace, docker_secret_name
    )

    try:
        v1.create_namespaced_service_account(project_namespace, sa_spec)
        logger.info(
            "service_account_created",
            project=project_name,
            namespace=project_namespace,
            service_account=service_account_name,
        )
    except ApiException as e:
        if e.status == 409:  # Already exists
            logger.debug("service_account_already_exists", project=project_name)
        else:
            raise

    # Create kpack Image resource
    image_spec = create_kpack_image_spec(
        name=project_name,
        namespace=project_namespace,
        tag=image_tag,
        git_url=git_url,
        git_revision=git_branch,
        service_account=service_account_name,
        builder="default",  # TODO: Make configurable
    )

    # Add owner reference
    image_spec["metadata"]["ownerReferences"] = [
        {
            "apiVersion": f"{owner_meta['apiVersion']}",
            "kind": "Project",
            "name": owner_meta["name"],
            "uid": owner_meta["uid"],
            "controller": True,
            "blockOwnerDeletion": True,
        }
    ]

    try:
        # Get kpack Image resource
        kpack_api = dyn_client.resources.get(api_version="kpack.io/v1alpha2", kind="Image")
        kpack_api.create(namespace=project_namespace, body=image_spec)
        logger.info(
            "kpack_image_created",
            project=project_name,
            namespace=project_namespace,
            image=project_name,
        )
    except ApiException as e:
        if e.status == 409:  # Already exists
            logger.debug("kpack_image_already_exists", project=project_name)
        else:
            raise


async def reconcile_kpack_resources(
    spec: Dict[str, Any],
    project_name: str,
    project_namespace: str,
) -> None:
    """Reconcile kpack resources for the project."""
    # TODO: Update kpack Image if repository or registry changed
    # TODO: Handle Image deletion if project no longer needs builds
    pass
