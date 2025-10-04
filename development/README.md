# Development Manifests

Plain Kubernetes manifests for rapid development and testing on kind clusters.

## Prerequisites

- kind cluster running
- Docker installed
- CRDs installed: `kubectl apply -f operator/crds/`
- kpack installed (if testing builds)

## Quick Start

### 1. Build and Load Image

```bash
# Build the operator image
cd ../operator
docker build -t kapsa-operator:latest .

# Load image into kind cluster
kind load docker-image kapsa-operator:latest
```

### 2. Deploy to Cluster

```bash
# Apply all manifests
kubectl apply -f .

# Or use kustomize
kubectl apply -k .
```

### 3. Verify Deployment

```bash
# Check operator pod
kubectl get pods -n kapsa-system

# View logs
kubectl logs -n kapsa-system -l app.kubernetes.io/name=kapsa-operator -f
```

## Configuration

- **Image**: `kapsa-operator:latest` (local build)
- **ImagePullPolicy**: `Never` (uses local image only)
- **Log Level**: `debug` (verbose logging)
- **Log Format**: `text` (easier to read than JSON)
- **Resources**: Lower requests for local testing
- **Metrics**: Disabled (will be added later)

## Cleanup

```bash
kubectl delete -f .
```
