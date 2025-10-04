"""Unit tests for kpack utility functions."""

import pytest

from kapsa.utils.kpack import (
    create_kpack_image_spec,
    create_service_account_spec,
)


def test_create_kpack_image_spec():
    """Test kpack Image spec creation."""
    image_spec = create_kpack_image_spec(
        name="my-app",
        namespace="my-app-ns",
        tag="harbor.corp.com/myteam/my-app:latest",
        git_url="https://github.com/myorg/my-app",
        git_revision="main",
        service_account="kpack-sa",
        builder="default",
    )

    # Verify basic structure
    assert image_spec["apiVersion"] == "kpack.io/v1alpha2"
    assert image_spec["kind"] == "Image"
    assert image_spec["metadata"]["name"] == "my-app"
    assert image_spec["metadata"]["namespace"] == "my-app-ns"

    # Verify labels
    assert image_spec["metadata"]["labels"]["app.kubernetes.io/name"] == "my-app"
    assert image_spec["metadata"]["labels"]["app.kubernetes.io/managed-by"] == "kapsa"

    # Verify spec
    assert image_spec["spec"]["tag"] == "harbor.corp.com/myteam/my-app:latest"
    assert image_spec["spec"]["serviceAccountName"] == "kpack-sa"
    assert image_spec["spec"]["builder"]["kind"] == "ClusterBuilder"
    assert image_spec["spec"]["builder"]["name"] == "default"

    # Verify source
    assert image_spec["spec"]["source"]["git"]["url"] == "https://github.com/myorg/my-app"
    assert image_spec["spec"]["source"]["git"]["revision"] == "main"


def test_create_kpack_image_spec_custom_revision():
    """Test kpack Image spec with custom git revision."""
    image_spec = create_kpack_image_spec(
        name="my-app",
        namespace="my-app-ns",
        tag="registry.io/app:v1.0.0",
        git_url="https://github.com/myorg/my-app",
        git_revision="v1.0.0",
        service_account="kpack-sa",
        builder="custom-builder",
    )

    # Verify custom revision
    assert image_spec["spec"]["source"]["git"]["revision"] == "v1.0.0"
    assert image_spec["spec"]["builder"]["name"] == "custom-builder"


def test_create_service_account_spec():
    """Test ServiceAccount spec creation."""
    sa_spec = create_service_account_spec(
        name="kpack-sa",
        namespace="my-app-ns",
        docker_secret_name="registry-credentials",
    )

    # Verify basic structure
    assert sa_spec["apiVersion"] == "v1"
    assert sa_spec["kind"] == "ServiceAccount"
    assert sa_spec["metadata"]["name"] == "kpack-sa"
    assert sa_spec["metadata"]["namespace"] == "my-app-ns"

    # Verify labels
    assert sa_spec["metadata"]["labels"]["app.kubernetes.io/managed-by"] == "kapsa"

    # Verify secrets
    assert len(sa_spec["secrets"]) == 1
    assert sa_spec["secrets"][0]["name"] == "registry-credentials"


def test_create_service_account_spec_different_secret():
    """Test ServiceAccount spec with different secret name."""
    sa_spec = create_service_account_spec(
        name="my-kpack-sa",
        namespace="test-ns",
        docker_secret_name="dockerhub-creds",
    )

    assert sa_spec["metadata"]["name"] == "my-kpack-sa"
    assert sa_spec["metadata"]["namespace"] == "test-ns"
    assert sa_spec["secrets"][0]["name"] == "dockerhub-creds"
