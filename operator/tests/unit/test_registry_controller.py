"""Unit tests for Registry controller."""

import pytest

from kapsa.controllers.registry import (
    registry_created,
    registry_updated,
    registry_deleted,
)


@pytest.fixture
def registry_spec():
    """Sample Registry spec."""
    return {
        "type": "harbor",
        "endpoint": "https://harbor.corp.com",
        "auth": {
            "secretRef": {
                "name": "harbor-credentials",
                "namespace": "kapsa-system",
            }
        },
        "options": {
            "projectName": "infrastructure",
        },
        "imagePullSecret": {
            "name": "registry-pull-secret",
            "generatePerNamespace": True,
        },
    }


@pytest.fixture
def docker_registry_spec():
    """Sample Docker Hub registry spec."""
    return {
        "type": "docker",
        "endpoint": "https://index.docker.io/v1/",
        "auth": {
            "secretRef": {
                "name": "dockerhub-credentials",
                "namespace": "kapsa-system",
            }
        },
    }


@pytest.mark.asyncio
async def test_registry_created(registry_spec):
    """Test Registry creation handler."""
    result = await registry_created(
        spec=registry_spec,
        name="company-harbor",
        meta={},
    )

    # Verify status
    assert result["conditions"][0]["type"] == "Ready"
    assert result["conditions"][0]["status"] == "True"
    assert result["conditions"][0]["reason"] == "RegistryConfigured"
    assert "ready" in result["conditions"][0]["message"].lower()


@pytest.mark.asyncio
async def test_registry_created_docker_hub(docker_registry_spec):
    """Test Docker Hub registry creation."""
    result = await registry_created(
        spec=docker_registry_spec,
        name="dockerhub",
        meta={},
    )

    # Verify status
    assert result["conditions"][0]["type"] == "Ready"
    assert result["conditions"][0]["status"] == "True"


@pytest.mark.asyncio
async def test_registry_updated(registry_spec):
    """Test Registry update handler."""
    old_spec = registry_spec.copy()
    new_spec = registry_spec.copy()
    new_spec["options"]["projectName"] = "new-project"

    result = await registry_updated(
        spec=new_spec,
        name="company-harbor",
        old={"spec": old_spec},
        new={"spec": new_spec},
    )

    # Verify status
    assert result["conditions"][0]["type"] == "Ready"
    assert result["conditions"][0]["status"] == "True"
    assert result["conditions"][0]["reason"] == "RegistryUpdated"


@pytest.mark.asyncio
async def test_registry_deleted(registry_spec):
    """Test Registry deletion handler."""
    # Should complete without error
    await registry_deleted(
        spec=registry_spec,
        name="company-harbor",
    )
