# Kapsa Helm Chart

This Helm chart deploys Kapsa, a Kubernetes-native deployment platform with push-to-deploy simplicity.

## Prerequisites

- Kubernetes ≥1.30
- Helm 3.x
- kpack (for building images)
- cert-manager (for TLS certificates)

## Installation

### Quick Start

```bash
# 1. Install kpack (required - not available as Helm chart)
kubectl apply -f https://github.com/buildpacks-community/kpack/releases/download/v0.17.0/release-0.17.0.yaml

# 2. Install Kapsa (cert-manager can be bundled as dependency or installed separately)
# Option A: Install Kapsa with cert-manager bundled (default)
helm install kapsa ./kapsa

# Option B: Install cert-manager separately
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.15.0/cert-manager.yaml
helm install kapsa ./kapsa --set certManager.enabled=false

# Or install from GitHub Container Registry
helm install kapsa oci://ghcr.io/kapsa-project/charts/kapsa --version 0.1.0
```

### Custom Installation

```bash
# Create custom values file
cat > my-values.yaml <<EOF
operator:
  image:
    repository: ghcr.io/kapsa-project/kapsa
    tag: "0.1.0"

  replicas: 1

  logging:
    level: debug

  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 200m
      memory: 256Mi

monitoring:
  serviceMonitor:
    enabled: true
    labels:
      prometheus: kube-prometheus
EOF

# Install with custom values
helm install kapsa ./kapsa -f my-values.yaml
```

## Configuration

### Key Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| `operator.image.repository` | Operator container image | `ghcr.io/kapsa-project/kapsa` |
| `operator.image.tag` | Operator image tag | `0.1.0` |
| `operator.replicas` | Number of operator replicas | `1` |
| `operator.logging.level` | Log level (debug/info/warning/error) | `info` |
| `operator.reconciliation.defaultPollInterval` | Default git poll interval (seconds) | `300` |
| `namespace.name` | Operator namespace | `kapsa-system` |
| `crds.install` | Install CRDs with chart | `true` |
| `crds.keep` | Keep CRDs on uninstall | `true` |
| `kpack.namespace` | Namespace where kpack is installed | `kpack` |
| `certManager.enabled` | Install cert-manager as dependency | `true` |
| `certManager.installCRDs` | Install cert-manager CRDs | `true` |
| `monitoring.serviceMonitor.enabled` | Create ServiceMonitor for Prometheus | `false` |

See [values.yaml](values.yaml) for all configuration options.

## Usage

### Platform Admin Setup

1. **Create a cert-manager ClusterIssuer** (if not already configured):
   ```yaml
   apiVersion: cert-manager.io/v1
   kind: ClusterIssuer
   metadata:
     name: letsencrypt-prod
   spec:
     acme:
       server: https://acme-v02.api.letsencrypt.org/directory
       email: admin@example.com
       privateKeySecretRef:
         name: letsencrypt-prod
       solvers:
         - http01:
             ingress:
               class: nginx
   ```

2. **Create a DomainPool**:
   ```yaml
   apiVersion: kapsa-project.io/v1alpha1
   kind: DomainPool
   metadata:
     name: corporate-apps
   spec:
     baseDomains:
       - apps.corp.com
     certManager:
       issuerRef:
         name: letsencrypt-prod
         kind: ClusterIssuer
       challengeType: http01
   ```

3. **Create registry credentials Secret**:
   ```bash
   kubectl create secret docker-registry harbor-push-credentials \
     --docker-server=harbor.corp.com \
     --docker-username=robot-account \
     --docker-password=secret \
     -n kapsa-system
   ```

4. **Create a Registry**:
   ```yaml
   apiVersion: kapsa-project.io/v1alpha1
   kind: Registry
   metadata:
     name: company-harbor
   spec:
     type: harbor
     endpoint: https://harbor.corp.com
     auth:
       secretRef:
         name: harbor-push-credentials
         namespace: kapsa-system
     options:
       projectName: infrastructure
   ```

### Developer Workflow

Create a Project:

```yaml
apiVersion: kapsa-project.io/v1alpha1
kind: Project
metadata:
  name: my-api
spec:
  repository:
    url: https://github.com/myorg/my-api
    branch: main
    pollInterval: 300
  build:
    strategy: buildpack
  registry:
    name: company-harbor
    imageRepository: myteam/my-api
  domain:
    subdomain: api
    domainPoolRef: corporate-apps
  environments:
    - name: dev
      branch: develop
      autoSync: true
    - name: prod
      branch: main
      autoSync: false
  previewEnvironments:
    enabled: true
    ttl: 168h
    branches:
      include: ["feature/*", "fix/*"]
```

## Upgrading

```bash
# Upgrade to new version
helm upgrade kapsa ./kapsa -f my-values.yaml

# Upgrade CRDs manually (if needed)
kubectl apply -f crds/
```

## Uninstalling

```bash
# Uninstall the chart
helm uninstall kapsa

# CRDs are kept by default (helm.sh/resource-policy: keep)
# To remove CRDs manually:
kubectl delete crd projects.kapsa-project.io
kubectl delete crd environments.kapsa-project.io
kubectl delete crd domainpools.kapsa-project.io
kubectl delete crd registries.kapsa-project.io
```

## Monitoring

### Prometheus Integration

Enable ServiceMonitor for Prometheus Operator:

```yaml
monitoring:
  serviceMonitor:
    enabled: true
    interval: 30s
    labels:
      prometheus: kube-prometheus
```

### Metrics Endpoints

- Operator metrics: `http://kapsa-operator-metrics:8080/metrics`
- Health check: `http://kapsa-operator-metrics:8080/healthz`
- Ready check: `http://kapsa-operator-metrics:8080/readyz`

## Troubleshooting

### Check operator logs
```bash
kubectl logs -n kapsa-system -l app.kubernetes.io/name=kapsa-operator -f
```

### Verify CRDs
```bash
kubectl get crds | grep kapsa-project.io
```

### Check operator status
```bash
kubectl get deployment -n kapsa-system kapsa-operator
kubectl get pods -n kapsa-system
```

### Debug Project reconciliation
```bash
kubectl describe project my-app
kubectl get environments -n my-app-ns
```

## Development

### Local Testing

```bash
# Lint chart
helm lint ./kapsa

# Template chart (dry-run)
helm template kapsa ./kapsa --debug

# Install with dry-run
helm install kapsa ./kapsa --dry-run --debug
```

## License

[Add license here]
