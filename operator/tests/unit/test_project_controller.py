"""Unit tests for Project controller."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from kubernetes.client.rest import ApiException

from kapsa.controllers.project import (
    project_created,
    project_updated,
    project_deleted,
    create_project_namespace,
    delete_project_namespace,
    create_kpack_resources,
)


@pytest.fixture
def project_spec():
    """Sample Project spec."""
    return {
        "repository": {
            "url": "https://github.com/example/app",
            "branch": "main",
            "pollInterval": 300,
        },
        "build": {
            "strategy": "buildpack",
        },
        "registry": {
            "name": "company-harbor",
            "imageRepository": "myteam/my-app",
        },
        "domain": {
            "subdomain": "api",
            "domainPoolRef": "corporate-apps",
        },
        "environments": [
            {
                "name": "dev",
                "branch": "develop",
                "autoSync": True,
            },
            {
                "name": "prod",
                "branch": "main",
                "autoSync": False,
            },
        ],
    }


@pytest.fixture
def project_meta():
    """Sample Project metadata."""
    return {
        "name": "my-app",
        "namespace": "default",
        "uid": "test-uid-123",
        "apiVersion": "kapsa-project.io/v1alpha1",
    }


@pytest.mark.asyncio
async def test_project_created(project_spec, project_meta):
    """Test Project creation handler."""
    with patch(
        "kapsa.controllers.project.create_project_namespace"
    ) as mock_create_ns, patch(
        "kapsa.controllers.project.create_kpack_resources"
    ) as mock_create_kpack:
        mock_create_ns.return_value = "my-app-ns"

        result = await project_created(
            spec=project_spec,
            name="my-app",
            namespace="default",
            meta=project_meta,
        )

        # Verify namespace was created
        mock_create_ns.assert_called_once_with("my-app", "default", project_meta)

        # Verify kpack resources were created
        mock_create_kpack.assert_called_once_with(
            project_spec, "my-app", "my-app-ns", project_meta
        )

        # Verify status returned
        assert result["conditions"][0]["type"] == "Ready"
        assert result["conditions"][0]["status"] == "False"
        assert result["conditions"][0]["reason"] == "Initializing"


@pytest.mark.asyncio
async def test_project_updated(project_spec):
    """Test Project update handler."""
    with patch(
        "kapsa.controllers.project.reconcile_environments"
    ) as mock_reconcile_env, patch(
        "kapsa.controllers.project.reconcile_kpack_resources"
    ) as mock_reconcile_kpack:
        result = await project_updated(
            spec=project_spec,
            status={},
            name="my-app",
            namespace="default",
        )

        # Verify environments were reconciled
        mock_reconcile_env.assert_called_once_with(project_spec, "my-app", "default")

        # Verify kpack resources were reconciled
        mock_reconcile_kpack.assert_called_once_with(project_spec, "my-app", "my-app-ns")

        # Verify success status
        assert result["conditions"][0]["type"] == "Ready"
        assert result["conditions"][0]["status"] == "True"
        assert result["conditions"][0]["reason"] == "Reconciled"


@pytest.mark.asyncio
async def test_project_updated_error_handling(project_spec):
    """Test Project update handler error handling."""
    with patch(
        "kapsa.controllers.project.reconcile_environments"
    ) as mock_reconcile_env:
        mock_reconcile_env.side_effect = Exception("Test error")

        result = await project_updated(
            spec=project_spec,
            status={},
            name="my-app",
            namespace="default",
        )

        # Verify error status
        assert result["conditions"][0]["type"] == "Ready"
        assert result["conditions"][0]["status"] == "False"
        assert result["conditions"][0]["reason"] == "ReconciliationFailed"
        assert "Test error" in result["conditions"][0]["message"]


@pytest.mark.asyncio
async def test_project_deleted():
    """Test Project deletion handler."""
    with patch("kapsa.controllers.project.delete_project_namespace") as mock_delete_ns:
        await project_deleted(name="my-app", namespace="default")

        mock_delete_ns.assert_called_once_with("my-app", "default")


@pytest.mark.asyncio
async def test_create_project_namespace(project_meta):
    """Test project namespace creation."""
    with patch("kapsa.controllers.project.client.CoreV1Api") as mock_v1:
        mock_api = MagicMock()
        mock_v1.return_value = mock_api

        namespace_name = await create_project_namespace(
            "my-app", "default", project_meta
        )

        # Verify namespace was created
        assert namespace_name == "my-app-ns"
        mock_api.create_namespace.assert_called_once()

        # Verify namespace spec
        call_args = mock_api.create_namespace.call_args[0][0]
        assert call_args.metadata.name == "my-app-ns"
        assert call_args.metadata.labels["kapsa-project.io/project"] == "my-app"


@pytest.mark.asyncio
async def test_create_project_namespace_already_exists(project_meta):
    """Test namespace creation when it already exists."""
    with patch("kapsa.controllers.project.client.CoreV1Api") as mock_v1:
        mock_api = MagicMock()
        mock_v1.return_value = mock_api
        mock_api.create_namespace.side_effect = ApiException(status=409)

        namespace_name = await create_project_namespace(
            "my-app", "default", project_meta
        )

        # Should not raise error, just return namespace name
        assert namespace_name == "my-app-ns"


@pytest.mark.asyncio
async def test_delete_project_namespace():
    """Test project namespace deletion."""
    with patch("kapsa.controllers.project.client.CoreV1Api") as mock_v1:
        mock_api = MagicMock()
        mock_v1.return_value = mock_api

        await delete_project_namespace("my-app", "default")

        mock_api.delete_namespace.assert_called_once_with("my-app-ns")


@pytest.mark.asyncio
async def test_delete_project_namespace_not_found():
    """Test namespace deletion when it doesn't exist."""
    with patch("kapsa.controllers.project.client.CoreV1Api") as mock_v1:
        mock_api = MagicMock()
        mock_v1.return_value = mock_api
        mock_api.delete_namespace.side_effect = ApiException(status=404)

        # Should not raise error
        await delete_project_namespace("my-app", "default")


@pytest.mark.asyncio
async def test_create_kpack_resources(project_spec, project_meta):
    """Test kpack resource creation."""
    with patch("kapsa.controllers.project.client.CoreV1Api") as mock_v1, patch(
        "kapsa.controllers.project.client.ApiClient"
    ) as mock_api_client, patch(
        "kapsa.controllers.project.DynamicClient"
    ) as mock_dyn_client:
        # Setup mocks
        mock_v1_api = MagicMock()
        mock_v1.return_value = mock_v1_api

        mock_dyn = MagicMock()
        mock_dyn_client.return_value = mock_dyn
        mock_kpack_api = MagicMock()
        mock_dyn.resources.get.return_value = mock_kpack_api

        await create_kpack_resources(project_spec, "my-app", "my-app-ns", project_meta)

        # Verify ServiceAccount was created
        mock_v1_api.create_namespaced_service_account.assert_called_once()
        sa_call = mock_v1_api.create_namespaced_service_account.call_args
        assert sa_call[0][0] == "my-app-ns"  # namespace
        assert sa_call[0][1]["metadata"]["name"] == "my-app-kpack-sa"

        # Verify kpack Image was created
        mock_kpack_api.create.assert_called_once()
        image_call = mock_kpack_api.create.call_args
        assert image_call[1]["namespace"] == "my-app-ns"
        image_spec = image_call[1]["body"]
        assert image_spec["metadata"]["name"] == "my-app"
        assert image_spec["spec"]["source"]["git"]["url"] == "https://github.com/example/app"
        assert image_spec["spec"]["source"]["git"]["revision"] == "main"


@pytest.mark.asyncio
async def test_create_kpack_resources_no_git_url(project_meta):
    """Test kpack resource creation without git URL."""
    spec_no_git = {
        "repository": {},
        "registry": {"name": "test-registry"},
    }

    with patch("kapsa.controllers.project.client.CoreV1Api"):
        # Should return early without creating resources
        await create_kpack_resources(spec_no_git, "my-app", "my-app-ns", project_meta)
        # No assertions needed - just verify it doesn't crash


@pytest.mark.asyncio
async def test_create_kpack_resources_no_registry(project_meta):
    """Test kpack resource creation without registry."""
    spec_no_registry = {
        "repository": {"url": "https://github.com/example/app"},
        "registry": {},
    }

    with patch("kapsa.controllers.project.client.CoreV1Api"):
        # Should return early without creating resources
        await create_kpack_resources(
            spec_no_registry, "my-app", "my-app-ns", project_meta
        )
        # No assertions needed - just verify it doesn't crash
