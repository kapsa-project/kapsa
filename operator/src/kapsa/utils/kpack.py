"""Utility functions for kpack integration."""

from typing import Any, Dict


def create_kpack_image_spec(
    name: str,
    namespace: str,
    tag: str,
    git_url: str,
    git_revision: str = "main",
    service_account: str = "kpack-service-account",
    builder: str = "default",
) -> Dict[str, Any]:
    """
    Create a kpack Image resource specification.

    Args:
        name: Image name
        namespace: Namespace for the Image resource
        tag: Container image tag (e.g., registry.io/org/image:latest)
        git_url: Git repository URL
        git_revision: Git branch/tag/commit (default: main)
        service_account: ServiceAccount with registry credentials
        builder: ClusterBuilder or Builder reference

    Returns:
        kpack Image resource dict
    """
    return {
        "apiVersion": "kpack.io/v1alpha2",
        "kind": "Image",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {
                "app.kubernetes.io/name": name,
                "app.kubernetes.io/managed-by": "kapsa",
            },
        },
        "spec": {
            "tag": tag,
            "serviceAccountName": service_account,
            "builder": {
                "kind": "ClusterBuilder",
                "name": builder,
            },
            "source": {
                "git": {
                    "url": git_url,
                    "revision": git_revision,
                }
            },
        },
    }


def create_service_account_spec(
    name: str,
    namespace: str,
    docker_secret_name: str,
) -> Dict[str, Any]:
    """
    Create a ServiceAccount for kpack builds.

    Args:
        name: ServiceAccount name
        namespace: Namespace
        docker_secret_name: Name of docker-registry secret

    Returns:
        ServiceAccount resource dict
    """
    return {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {
                "app.kubernetes.io/managed-by": "kapsa",
            },
        },
        "secrets": [
            {
                "name": docker_secret_name,
            }
        ],
    }
