# System Architecture Overview

## Architecture Principles

Kapsa follows these core architectural principles:

1. **Kubernetes-native**: All resources are Kubernetes custom resources; no external control plane
2. **Declarative**: Developers declare desired state; the operator reconciles to reality
3. **Modular integration**: Works with existing enterprise infrastructure (registries, secret managers, ingress controllers)
4. **Single responsibility**: Each component does one thing well
5. **Reference-only secrets**: No secret storage in CRDs; integrates with existing secret management solutions

## System Components

### Control Plane

#### Kapsa Operator

- **Technology**: Python + Kopf (Kubernetes Operator Framework)
- **Responsibility**: Reconcile Project CRDs into running deployments
- **Namespace**: `kapsa-system`
- **Key Operations**:
  - Watch Project, Environment, DomainPool, Registry CRDs
  - Trigger builds via kpack when source changes detected
  - Create and manage Environment resources
  - Allocate domains from DomainPool
  - Generate Kubernetes runtime resources (Deployment, Service, Ingress)
  - Manage preview environment lifecycle

### Build Subsystem

#### kpack

- **Responsibility**: In-cluster container image builds
- **Build Strategies**:
  - Dockerfile-based builds
  - Cloud Native Buildpacks (automatic runtime detection)
- **Features**:
  - Build caching for fast iterations
  - Multi-stage build support
  - Source-to-image automation

### Runtime Subsystem

#### Kubernetes Core Resources

- **Deployment**: Application pod management, scaling, rolling updates
- **Service**: Internal cluster networking and load balancing
- **Ingress**: HTTP(S) routing and external exposure (NGINX-based in v1)

#### cert-manager

- **Responsibility**: Automatic TLS certificate provisioning
- **Issuance Methods**:
  - HTTP-01 challenge (default)
  - DNS-01 challenge (optional, for wildcard certs)

### Platform Resources

#### DomainPool

- **Managed by**: Platform administrators
- **Purpose**: Define available base domains for application routing
- **Scope**: Cluster-wide
- **References**: cert-manager ClusterIssuer for TLS

#### Registry

- **Managed by**: Platform administrators
- **Purpose**: Define container registry endpoints and credentials
- **Supported Registries**: Harbor, GitLab Container Registry, Docker Hub, AWS ECR, GCR, ACR
- **Scope**: Cluster-wide or namespace-scoped

## Data Flow

### Developer Workflow

```
1. Developer creates/updates Project CRD
2. Kapsa operator detects change
3. Operator polls git repository for latest commit
4. On source change:
   a. Trigger kpack build
   b. kpack builds image and pushes to configured Registry
   c. Operator creates/updates Environment resources
   d. Environment controller creates Deployment, Service, Ingress
   e. cert-manager provisions TLS certificate
   f. Application is live at allocated domain
```

### Preview Environment Workflow

```
1. Project has `previewEnvironments: true`
2. Operator polls repository and detects feature branch
3. Operator creates ephemeral Environment for branch
4. Environment gets subdomain: <branch>.<project>.<domain-pool-base>
5. On branch merge/deletion or TTL expiry:
   a. Operator destroys Environment
   b. Namespace and all resources cleaned up
```

## Tenancy and Isolation

- **Model**: Single-tenant, namespace-per-project
- **Isolation**: Each Project gets dedicated Kubernetes namespace
- **RBAC**: ServiceAccount per project with minimal permissions
- **Resource Limits**: Optional ResourceQuotas per namespace (admin-configured)

## Source Code Triggers

- **v1 (MVP)**: Git repository polling at configurable intervals
- **Future**: Webhook-based triggers (GitHub, GitLab, Bitbucket)

## Configuration and Secrets

- **Pattern**: Reference-only model
- **Integration**: Works with existing secret management:
  - External Secrets Operator (ESO)
  - HashiCorp Vault
  - Sealed Secrets
  - Kubernetes native Secrets
- **CRD Fields**: `configMapRefs[]`, `secretRefs[]` only—no inline secrets

## Observability

### Logs

- **Application**: stdout/stderr captured by Kubernetes
- **Operator**: Structured logging to stdout

### Metrics

- **Operator**: Prometheus endpoint for controller metrics
- **Applications**: Optional ServiceMonitor CRDs for Prometheus scraping

### Events

- Kubernetes Events for major state transitions
- Status conditions on CRD `.status` fields

## Deployment Strategy

- **v1**: Kubernetes rolling updates (default)
- **Future**: Optional Argo Rollouts for canary, blue-green deployments

## Security Baseline

- **Namespace Isolation**: Per-project namespaces
- **ServiceAccount**: Dedicated per project with minimal RBAC
- **Network Policies**: Not enforced by Kapsa (cluster admin responsibility)
- **Pod Security**: Not enforced by Kapsa (cluster admin responsibility)
- **Secret Access**: Via reference only; secrets managed externally

## Scalability Considerations

- **Horizontal Scaling**: Operator can run with leader election for HA
- **Build Parallelism**: kpack supports concurrent builds
- **Resource Management**: ResourceQuotas prevent namespace resource exhaustion
- **Domain Management**: DomainPool supports multiple base domains for distribution
