# Kapsa Operator

Python-based Kubernetes operator for Kapsa, built with [Kopf](https://kopf.readthedocs.io/).

## Architecture

The operator watches four Custom Resource Definitions:

- **Project** - Developer-facing application definitions
- **Environment** - Operator-managed deployment targets
- **DomainPool** - Cluster-scoped domain configuration (admin-managed)
- **Registry** - Cluster-scoped registry endpoints (admin-managed)

## Project Structure

```
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
- Access to a Kubernetes cluster
- kubectl configured

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

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/kapsa --cov-report=html

# Run specific test file
pytest tests/unit/test_project.py

# Run with verbose output
pytest -v
```

### Code Quality

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

## Monitoring

### Metrics

The operator exposes Prometheus metrics on port 8080:

```bash
# View metrics
curl http://localhost:8080/metrics

# In cluster
kubectl port-forward -n kapsa-system svc/kapsa-operator-metrics 8080:8080
curl http://localhost:8080/metrics
```

Available metrics:

- `kapsa_projects_total` - Total number of Projects
- `kapsa_project_reconcile_total` - Project reconciliation attempts
- `kapsa_project_reconcile_duration_seconds` - Reconciliation duration
- `kapsa_environments_total` - Total number of Environments
- `kapsa_builds_total` - Build attempts
- `kapsa_git_poll_total` - Git poll attempts

### Health Checks

```bash
# Liveness probe
curl http://localhost:8080/healthz

# In cluster
kubectl port-forward -n kapsa-system deploy/kapsa-operator 8080:8080
curl http://localhost:8080/healthz
```

### Logs

```bash
# View operator logs
kubectl logs -n kapsa-system -l app.kubernetes.io/name=kapsa-operator -f

# With structured JSON output
kubectl logs -n kapsa-system -l app.kubernetes.io/name=kapsa-operator -f | jq .
```

## Debugging

### Enable Debug Logging

```bash
# Set via Helm values
helm upgrade kapsa ../helm/kapsa \
  --set operator.logging.level=DEBUG
```

### Watch Events

```bash
# Watch all Kapsa events
kubectl get events --all-namespaces --field-selector involvedObject.apiVersion=kapsa.io/v1alpha1 -w

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

## Current Implementation Status

### ✅ Implemented

- Basic operator scaffolding with Kopf
- Project CRD handlers (create/update/delete)
- Structured logging with structlog
- Prometheus metrics
- Configuration management
- Namespace creation per project
- Git polling timer (stub)

### 🚧 In Progress / TODO

- Git repository polling and commit detection
- kpack build integration
- Environment CRD reconciliation
- Deployment/Service/Ingress creation
- Domain allocation from DomainPool
- Preview environment lifecycle
- Registry integration
- Secret management

## Contributing

See [Development Documentation](../docs/development/) for contribution guidelines.

## Troubleshooting

### Operator crashes on startup

Check CRDs are installed:

```bash
kubectl get crds | grep kapsa.io
```

### Reconciliation not working

1. Check operator logs for errors
2. Verify RBAC permissions
3. Check resource status conditions

### Metrics not available

1. Verify metrics port is not blocked
2. Check `KAPSA_METRICS_ENABLED=true`
3. Review ServiceMonitor configuration
