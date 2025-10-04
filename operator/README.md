# Kapsa Operator

Python-based Kubernetes operator for Kapsa, built with [Kopf](https://kopf.readthedocs.io/).

## Architecture

The operator watches four Custom Resource Definitions:

- **Project** - Developer-facing application definitions
- **Environment** - Operator-managed deployment targets
- **DomainPool** - Cluster-scoped domain configuration (admin-managed)
- **Registry** - Cluster-scoped registry endpoints (admin-managed)

## Project Structure

```txt
operator/
├── src/kapsa/
│   ├── main.py              # Operator entry point
│   ├── config.py            # Configuration management
│   ├── logging.py           # Structured logging setup
│   ├── metrics.py           # Prometheus metrics
│   ├── controllers/         # Kopf handlers for CRDs
│   │   └── project.py       # Project controller
│   ├── utils/               # Utility modules
│   └── models/              # Data models
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── Dockerfile               # Container image
├── requirements.txt         # Python dependencies
├── setup.py                 # Package setup
└── pyproject.toml          # Tool configuration
```

## Development Setup

### Prerequisites

- Python 3.11+
- Access to a Kubernetes cluster (≥1.30)
- kubectl configured
- cert-manager installed (for TLS certificates)
- kpack installed (for image builds)
- cert-manager ClusterIssuer configured (e.g., Let's Encrypt)

### Local Development

1. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Configure environment variables**

   ```bash
   export KAPSA_LOG_LEVEL=DEBUG
   export KAPSA_LOG_FORMAT=console
   export KAPSA_METRICS_PORT=8080
   ```

4. **Run operator locally**

   ```bash
   kopf run --all-namespaces src/kapsa/main.py
   ```

   Or with verbose logging:

   ```bash
   kopf run --all-namespaces --verbose src/kapsa/main.py
   ```

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy src/
```

## Building and Deploying

### Build Docker Image

```bash
# Build
docker build -t kapsa-operator:dev .

# Test locally
docker run --rm kapsa-operator:dev
```

### Deploy to Kubernetes

```bash
# Build and load into kind
kind create cluster --name kapsa-dev
kind load docker-image kapsa-operator:dev --name kapsa-dev

# Install via Helm with custom image
helm install kapsa ../helm/kapsa \
  --set operator.image.repository=kapsa-operator \
  --set operator.image.tag=dev \
  --set operator.image.pullPolicy=Never
```

### Deploy to Production

```bash
# Tag and push to registry
docker tag kapsa-operator:dev ghcr.io/yourorg/kapsa:0.1.0
docker push ghcr.io/yourorg/kapsa:0.1.0

# Install via Helm
helm install kapsa ../helm/kapsa \
  --set operator.image.tag=0.1.0
```

## Configuration

Environment variables (prefix with `KAPSA_`):

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | `INFO` |
| `LOG_FORMAT` | Log format (json/console) | `json` |
| `DEFAULT_POLL_INTERVAL` | Default git poll interval (seconds) | `300` |
| `RECONCILIATION_TIMEOUT` | Reconciliation timeout (seconds) | `600` |
| `METRICS_PORT` | Prometheus metrics port | `8080` |
| `METRICS_ENABLED` | Enable metrics server | `true` |
| `NAMESPACE` | Operator namespace | `kapsa-system` |
| `KPACK_BUILDER_IMAGE` | Default kpack builder | `paketobuildpacks/builder:base` |
| `KPACK_SERVICE_ACCOUNT` | kpack service account | `kapsa-build` |

## Debugging

### Watch Events

```bash
# Watch all Kapsa events
kubectl get events --all-namespaces --field-selector involvedObject.apiVersion=kapsa-project.io/v1alpha1 -w

# Watch Project events
kubectl get events --field-selector involvedObject.kind=Project -w
```

### Inspect Resources

```bash
# List all Projects
kubectl get projects --all-namespaces

# Describe Project
kubectl describe project my-app

# View Project status
kubectl get project my-app -o jsonpath='{.status}' | jq .

# List Environments
kubectl get environments --all-namespaces
```
