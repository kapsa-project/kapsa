"""Shared pytest configuration and fixtures."""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_kubernetes_client():
    """Mock Kubernetes client."""
    return MagicMock()


@pytest.fixture
def sample_project_spec():
    """Sample Project CRD specification."""
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
            "name": "default-registry",
            "imageRepository": "myorg/myapp",
        },
        "domain": {
            "subdomain": "app",
            "domainPoolRef": "default",
        },
        "environments": [
            {
                "name": "prod",
                "branch": "main",
                "autoSync": True,
            }
        ],
    }


@pytest.fixture
def sample_environment_spec():
    """Sample Environment CRD specification."""
    return {
        "projectRef": {
            "name": "test-project",
        },
        "type": "permanent",
        "branch": "main",
        "runtime": {
            "replicas": 1,
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
        },
    }


@pytest.fixture
def sample_registry_spec():
    """Sample Registry CRD specification."""
    return {
        "type": "harbor",
        "endpoint": "https://harbor.example.com",
        "auth": {
            "secretRef": {
                "name": "harbor-credentials",
                "namespace": "kapsa-system",
            }
        },
    }


@pytest.fixture
def sample_domainpool_spec():
    """Sample DomainPool CRD specification."""
    return {
        "baseDomains": [
            "apps.example.com",
        ],
        "certManager": {
            "issuerRef": {
                "name": "letsencrypt-prod",
                "kind": "ClusterIssuer",
            },
            "challengeType": "http01",
        },
    }
