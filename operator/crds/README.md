# Kapsa Custom Resource Definitions (CRDs)

This directory contains the Custom Resource Definitions for Kapsa.

## Installation

### Install CRDs individually

```bash
kubectl apply -f https://raw.githubusercontent.com/kapsa-project/kapsa/main/crds/project.yaml
kubectl apply -f https://raw.githubusercontent.com/kapsa-project/kapsa/main/crds/environment.yaml
kubectl apply -f https://raw.githubusercontent.com/kapsa-project/kapsa/main/crds/domainpool.yaml
kubectl apply -f https://raw.githubusercontent.com/kapsa-project/kapsa/main/crds/registry.yaml
```

### Install all at once (from local clone)

```bash
kubectl apply -f crds/
```

### Verify installation

```bash
kubectl get crds | grep kapsa-project.io
```

Expected output:

```txt
domainpools.kapsa-project.io
environments.kapsa-project.io
projects.kapsa-project.io
registries.kapsa-project.io
```

## CRD Descriptions

### Project

Developer-facing CRD for defining applications. Specifies repository, build strategy, registry, domain, and environments.

**Scope**: Namespaced
**API Group**: kapsa-project.io
**Version**: v1alpha1

### Environment

Operator-managed CRD representing deployment targets (dev, staging, prod, preview).

**Scope**: Namespaced
**API Group**: kapsa-project.io
**Version**: v1alpha1

### DomainPool

Platform admin CRD defining available base domains for routing and TLS configuration.

**Scope**: Cluster
**API Group**: kapsa-project.io
**Version**: v1alpha1

### Registry

Platform admin CRD defining container registry endpoints and credentials.

**Scope**: Cluster
**API Group**: kapsa-project.io
**Version**: v1alpha1

## Upgrading CRDs

**Important**: Helm does not upgrade CRDs. When upgrading Kapsa, you must manually apply updated CRDs:

```bash
# Before upgrading Helm chart
kubectl apply -f https://raw.githubusercontent.com/kapsa-project/kapsa/v0.2.0/crds/project.yaml
kubectl apply -f https://raw.githubusercontent.com/kapsa-project/kapsa/v0.2.0/crds/environment.yaml
kubectl apply -f https://raw.githubusercontent.com/kapsa-project/kapsa/v0.2.0/crds/domainpool.yaml
kubectl apply -f https://raw.githubusercontent.com/kapsa-project/kapsa/v0.2.0/crds/registry.yaml

# Then upgrade the Helm chart
helm upgrade kapsa kapsa/kapsa --version 0.2.0
```

## Uninstalling

**Warning**: Deleting CRDs will delete all custom resources of that type.

```bash
kubectl delete crd projects.kapsa-project.io
kubectl delete crd environments.kapsa-project.io
kubectl delete crd domainpools.kapsa-project.io
kubectl delete crd registries.kapsa-project.io
```

## Development

These CRDs are also included in the Helm chart at `helm/kapsa/templates/crds/` for convenience during installation. The canonical source is this `crds/` directory.

When modifying CRDs:

1. Edit files in `crds/`
2. Copy to `helm/kapsa/templates/crds/` and add Helm templating if needed
3. Test installation with both methods
