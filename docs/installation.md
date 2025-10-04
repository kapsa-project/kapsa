# Installation Guide

## Prerequisites

Before installing Kapsa, ensure you have:

1. **Kubernetes Cluster** (≥1.30)
   ```bash
   kubectl version --short
   ```

2. **Helm 3.x**
   ```bash
   helm version
   ```

3. **kpack** (for building container images)

   kpack must be installed separately as it's not available as a Helm chart:
   ```bash
   kubectl apply -f https://github.com/buildpacks-community/kpack/releases/download/v0.17.0/release-0.17.0.yaml
   ```

4. **cert-manager** (for TLS certificates)

   cert-manager can be bundled with Kapsa (default) or installed separately:
   ```bash
   # Option A: Let Kapsa install cert-manager via Helm dependency (recommended)
   # No action needed - installed automatically with Kapsa

   # Option B: Install manually and disable Kapsa's bundled cert-manager
   kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.15.0/cert-manager.yaml
   # Then install Kapsa with: --set certManager.enabled=false
   ```

5. **Ingress Controller** (NGINX recommended)
   ```bash
   helm install ingress-nginx ingress-nginx/ingress-nginx \
     --namespace ingress-nginx \
     --create-namespace
   ```

## Install CRDs

Custom Resource Definitions (CRDs) must be installed before the Kapsa operator:

```bash
# Install from repository root
kubectl apply -f crds/

# Or install from GitHub (for specific version)
kubectl apply -f https://raw.githubusercontent.com/kapsa-project/kapsa/main/crds/project.yaml
kubectl apply -f https://raw.githubusercontent.com/kapsa-project/kapsa/main/crds/environment.yaml
kubectl apply -f https://raw.githubusercontent.com/kapsa-project/kapsa/main/crds/domainpool.yaml
kubectl apply -f https://raw.githubusercontent.com/kapsa-project/kapsa/main/crds/registry.yaml
```

Verify CRD installation:

```bash
kubectl get crds | grep kapsa-project.io
```

Expected output:
```
domainpools.kapsa-project.io
environments.kapsa-project.io
projects.kapsa-project.io
registries.kapsa-project.io
```

## Install Kapsa

### Option 1: Default Installation

```bash
helm install kapsa ./helm/kapsa
```

### Option 2: Custom Configuration

Create a `values.yaml` file:

```yaml
operator:
  replicas: 1

  logging:
    level: info  # debug for development
    format: json

  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 100m
      memory: 128Mi

# Enable Prometheus monitoring
monitoring:
  serviceMonitor:
    enabled: true
    labels:
      prometheus: kube-prometheus

# Security context (Pod Security Standards compliant)
securityContext:
  operator:
    runAsNonRoot: true
    runAsUser: 65532
    fsGroup: 65532
```

Install with custom values:

```bash
helm install kapsa ./helm/kapsa -f values.yaml
```

### Option 3: Install from GitHub Container Registry

```bash
# Install from GHCR
helm install kapsa oci://ghcr.io/kapsa-project/charts/kapsa --version 0.1.0
```

## Verify Installation

Check that all components are running:

```bash
# Check operator deployment
kubectl get deployment -n kapsa-system
kubectl get pods -n kapsa-system

# Check CRDs
kubectl get crds | grep kapsa-project.io

# Expected output:
# domainpools.kapsa-project.io
# environments.kapsa-project.io
# projects.kapsa-project.io
# registries.kapsa-project.io

# Check operator logs
kubectl logs -n kapsa-system -l app.kubernetes.io/name=kapsa-operator -f
```

## Post-Installation Setup

### 1. Create a cert-manager ClusterIssuer

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

Apply:
```bash
kubectl apply -f clusterissuer.yaml
```

### 2. Create a DomainPool

```yaml
apiVersion: kapsa-project.io/v1alpha1
kind: DomainPool
metadata:
  name: corporate-apps
spec:
  baseDomains:
    - apps.corp.com
    - services.corp.com
  certManager:
    issuerRef:
      name: letsencrypt-prod
      kind: ClusterIssuer
    challengeType: http01
  allocationPolicy:
    strategy: round-robin
    reservedSubdomains:
      - www
      - admin
      - internal
```

Apply:
```bash
kubectl apply -f domainpool.yaml
```

### 3. Create Registry Credentials

For Harbor:
```bash
kubectl create secret docker-registry harbor-push-credentials \
  --docker-server=harbor.corp.com \
  --docker-username=robot-account \
  --docker-password=<robot-token> \
  -n kapsa-system
```

For GitLab Container Registry:
```bash
kubectl create secret docker-registry gitlab-registry-credentials \
  --docker-server=registry.gitlab.com \
  --docker-username=<username> \
  --docker-password=<deploy-token> \
  -n kapsa-system
```

For Docker Hub:
```bash
kubectl create secret docker-registry dockerhub-credentials \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=<username> \
  --docker-password=<password> \
  -n kapsa-system
```

### 4. Create a Registry

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
    robotAccount: "true"
  imagePullSecret:
    name: harbor-pull-secret
    generatePerNamespace: true
```

Apply:
```bash
kubectl apply -f registry.yaml
```

### 5. Verify Platform Resources

```bash
# Check DomainPool status
kubectl get domainpool corporate-apps -o yaml

# Check Registry status
kubectl get registry company-harbor -o yaml

# Both should have status.conditions[type=Ready].status = "True"
```

## Developer Quick Start

Create your first Project:

```yaml
apiVersion: kapsa-project.io/v1alpha1
kind: Project
metadata:
  name: hello-world
spec:
  repository:
    url: https://github.com/buildpacks/samples
    branch: main
    pollInterval: 300
  build:
    strategy: buildpack
    context: apps/node-app
  registry:
    name: company-harbor
    imageRepository: demo/hello-world
  domain:
    subdomain: hello
    domainPoolRef: corporate-apps
  environments:
    - name: dev
      branch: main
      autoSync: true
  previewEnvironments:
    enabled: false
```

Apply and monitor:
```bash
kubectl apply -f project.yaml

# Watch project status
kubectl get project hello-world -w

# Check created environment
kubectl get environments

# Check application URL
kubectl get project hello-world -o jsonpath='{.status.environments[0].url}'
```

## Upgrading Kapsa

```bash
# Upgrade to new version
helm upgrade kapsa ./helm/kapsa

# Upgrade with new values
helm upgrade kapsa ./helm/kapsa -f values.yaml

# CRDs are not automatically upgraded by Helm
# Upgrade CRDs manually if schema changes:
kubectl apply -f crds/
```

## Uninstalling

```bash
# Uninstall Kapsa operator
helm uninstall kapsa

# CRDs are retained by default (helm.sh/resource-policy: keep)
# To remove CRDs and all Projects/Environments:
kubectl delete crd projects.kapsa-project.io
kubectl delete crd environments.kapsa-project.io
kubectl delete crd domainpools.kapsa-project.io
kubectl delete crd registries.kapsa-project.io

# Remove namespace
kubectl delete namespace kapsa-system
```

## Troubleshooting

### Operator not starting

Check logs:
```bash
kubectl logs -n kapsa-system deployment/kapsa-operator
```

Common issues:
- Missing RBAC permissions
- Image pull errors
- kpack or cert-manager not installed

### Project stuck in "Pending"

```bash
# Check project status
kubectl describe project <name>

# Check operator logs
kubectl logs -n kapsa-system -l app.kubernetes.io/name=kapsa-operator --tail=100

# Check kpack Image resource
kubectl get images -n <project-namespace>
```

### Build failures

```bash
# Check kpack build logs
kubectl logs -n <project-namespace> <build-pod-name>

# Check Image status
kubectl describe image -n <project-namespace> <image-name>
```

### TLS certificate not issued

```bash
# Check cert-manager Certificate
kubectl get certificate -n <project-namespace>

# Check cert-manager events
kubectl describe certificate -n <project-namespace> <cert-name>

# Check ClusterIssuer status
kubectl describe clusterissuer letsencrypt-prod
```

### DNS/Ingress issues

```bash
# Check Ingress status
kubectl get ingress -n <project-namespace>

# Check Ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx

# Verify DNS resolution
nslookup <subdomain>.<base-domain>
```

## Advanced Configuration

### High Availability

Run multiple operator replicas with leader election:

```yaml
operator:
  replicas: 3

  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          podAffinityTerm:
            labelSelector:
              matchLabels:
                app.kubernetes.io/name: kapsa-operator
            topologyKey: kubernetes.io/hostname
```

### Custom Metrics and Monitoring

Enable Prometheus monitoring:

```yaml
operator:
  metrics:
    enabled: true
    port: 8080

monitoring:
  serviceMonitor:
    enabled: true
    interval: 30s
    labels:
      prometheus: kube-prometheus
```

Access metrics:
```bash
kubectl port-forward -n kapsa-system svc/kapsa-operator-metrics 8080:8080
curl http://localhost:8080/metrics
```

### Air-Gapped Installation

1. Pull and push images to internal registry:
   ```bash
   docker pull ghcr.io/kapsa-project/kapsa:0.1.0
   docker tag ghcr.io/kapsa-project/kapsa:0.1.0 internal-registry.corp.com/kapsa:0.1.0
   docker push internal-registry.corp.com/kapsa:0.1.0
   ```

2. Configure Helm values:
   ```yaml
   operator:
     image:
       repository: internal-registry.corp.com/kapsa-operator
       tag: "0.1.0"

   global:
     imagePullSecrets:
       - name: internal-registry-credentials
   ```

### Resource Quotas and Limits

Set resource limits for operator:

```yaml
operator:
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 200m
      memory: 256Mi
```

Configure default limits for project namespaces (via operator config):

```yaml
# Custom operator configuration
# (Implementation in operator code)
defaultResourceQuota:
  hard:
    requests.cpu: "10"
    requests.memory: "20Gi"
    persistentvolumeclaims: "5"
```

## Next Steps

- Read [Architecture Documentation](architecture/)
- Review [ADRs](adr/) for design decisions
- Join community discussions
- Report issues on GitHub
