"""Unit tests for DomainPool controller."""

import pytest

from kapsa.controllers.domainpool import (
    domainpool_created,
    domainpool_updated,
    domainpool_deleted,
)


@pytest.fixture
def domainpool_spec():
    """Sample DomainPool spec."""
    return {
        "baseDomains": [
            "apps.corp.com",
            "dev.corp.com",
        ],
        "certManager": {
            "issuerRef": {
                "name": "letsencrypt-prod",
                "kind": "ClusterIssuer",
            },
            "challengeType": "http01",
        },
        "allocationPolicy": {
            "strategy": "round-robin",
        },
    }


@pytest.fixture
def dns_domainpool_spec():
    """Sample DomainPool with DNS-01 challenge."""
    return {
        "baseDomains": [
            "*.apps.corp.com",
        ],
        "certManager": {
            "issuerRef": {
                "name": "letsencrypt-prod",
                "kind": "ClusterIssuer",
            },
            "challengeType": "dns01",
            "dnsProvider": {
                "name": "cloudflare",
                "credentialsSecretRef": {
                    "name": "cloudflare-api-token",
                    "namespace": "kapsa-system",
                },
            },
        },
    }


@pytest.mark.asyncio
async def test_domainpool_created(domainpool_spec):
    """Test DomainPool creation handler."""
    result = await domainpool_created(
        spec=domainpool_spec,
        name="corporate-apps",
        meta={},
    )

    # Verify status
    assert result["conditions"][0]["type"] == "Ready"
    assert result["conditions"][0]["status"] == "True"
    assert result["conditions"][0]["reason"] == "DomainPoolConfigured"
    assert "2 base domain" in result["conditions"][0]["message"]

    # Verify domain tracking
    assert result["allocatedDomains"] == []
    assert result["availableDomains"] == ["apps.corp.com", "dev.corp.com"]


@pytest.mark.asyncio
async def test_domainpool_created_single_domain(dns_domainpool_spec):
    """Test DomainPool creation with single wildcard domain."""
    result = await domainpool_created(
        spec=dns_domainpool_spec,
        name="wildcard-apps",
        meta={},
    )

    # Verify status
    assert result["conditions"][0]["type"] == "Ready"
    assert result["conditions"][0]["status"] == "True"
    assert "1 base domain" in result["conditions"][0]["message"]


@pytest.mark.asyncio
async def test_domainpool_updated(domainpool_spec):
    """Test DomainPool update handler."""
    old_spec = domainpool_spec.copy()
    new_spec = domainpool_spec.copy()
    new_spec["baseDomains"].append("staging.corp.com")

    result = await domainpool_updated(
        spec=new_spec,
        name="corporate-apps",
        old={"spec": old_spec},
        new={"spec": new_spec},
        status={
            "allocatedDomains": [],
            "availableDomains": ["apps.corp.com", "dev.corp.com"],
        },
    )

    # Verify status
    assert result["conditions"][0]["type"] == "Ready"
    assert result["conditions"][0]["status"] == "True"
    assert result["conditions"][0]["reason"] == "DomainPoolUpdated"

    # Verify updated domains
    assert len(result["availableDomains"]) == 3
    assert "staging.corp.com" in result["availableDomains"]


@pytest.mark.asyncio
async def test_domainpool_deleted(domainpool_spec):
    """Test DomainPool deletion handler."""
    # Should complete without error
    await domainpool_deleted(
        spec=domainpool_spec,
        name="corporate-apps",
    )
