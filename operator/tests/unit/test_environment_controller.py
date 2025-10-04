"""Unit tests for Environment controller."""

import pytest
from unittest.mock import patch

from kapsa.controllers.environment import (
    environment_created,
    environment_updated,
    environment_deleted,
)


@pytest.fixture
def environment_spec():
    """Sample Environment spec."""
    return {
        "projectRef": {
            "name": "my-app",
        },
        "type": "permanent",
        "branch": "main",
        "runtime": {
            "replicas": 2,
            "resources": {
                "limits": {
                    "cpu": "500m",
                    "memory": "512Mi",
                },
                "requests": {
                    "cpu": "100m",
                    "memory": "128Mi",
                },
            },
            "autoscaling": {
                "enabled": True,
                "minReplicas": 2,
                "maxReplicas": 10,
                "targetCPUUtilization": 80,
            },
        },
    }


@pytest.fixture
def preview_environment_spec():
    """Sample preview Environment spec."""
    return {
        "projectRef": {
            "name": "my-app",
        },
        "type": "preview",
        "branch": "feature/new-api",
    }


@pytest.mark.asyncio
async def test_environment_created(environment_spec):
    """Test Environment creation handler."""
    result = await environment_created(
        spec=environment_spec,
        name="my-app-dev",
        namespace="my-app-ns",
        meta={},
    )

    # Verify status
    assert result["conditions"][0]["type"] == "Ready"
    assert result["conditions"][0]["status"] == "False"
    assert result["conditions"][0]["reason"] == "Initializing"
    assert "initialized" in result["conditions"][0]["message"].lower()


@pytest.mark.asyncio
async def test_environment_created_preview(preview_environment_spec):
    """Test preview Environment creation."""
    result = await environment_created(
        spec=preview_environment_spec,
        name="my-app-preview-feature-new-api",
        namespace="my-app-ns",
        meta={},
    )

    # Verify status
    assert result["conditions"][0]["type"] == "Ready"
    assert result["conditions"][0]["status"] == "False"


@pytest.mark.asyncio
async def test_environment_updated(environment_spec):
    """Test Environment update handler."""
    result = await environment_updated(
        spec=environment_spec,
        name="my-app-dev",
        namespace="my-app-ns",
        old={},
        new={},
    )

    # Verify status
    assert result["conditions"][0]["type"] == "Ready"
    assert result["conditions"][0]["status"] == "True"
    assert result["conditions"][0]["reason"] == "Updated"


@pytest.mark.asyncio
async def test_environment_deleted(environment_spec):
    """Test Environment deletion handler."""
    # Should complete without error
    await environment_deleted(
        spec=environment_spec,
        name="my-app-dev",
        namespace="my-app-ns",
    )
