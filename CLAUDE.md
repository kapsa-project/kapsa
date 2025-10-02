# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Kapsa** is an open-source, Kubernetes-native deployment platform that provides a push-to-deploy experience for self-hosted infrastructure. It's designed for corporations that want to offer their developers a streamlined deployment workflow (similar to managed PaaS platforms) while maintaining full control over their infrastructure, ensuring privacy compliance, and integrating with existing enterprise tooling.

### Core Concepts

- **Kubernetes-native**: Everything is a CRD; no external control plane
- **Modular integration**: Works with existing enterprise infrastructure (Harbor, GitLab Registry, Vault, ESO, cert-manager, NGINX)
- **Reference-only secrets**: No secret storage in CRDs; integrates with existing secret management
- **Namespace-per-project isolation**: Each Project gets its own Kubernetes namespace

### Technology Stack

- **Operator**: Python + Kopf (Kubernetes Operator Framework) - ADR-001
- **Build System**: kpack (Dockerfile and Cloud Native Buildpacks) - ADR-005
- **Runtime**: Kubernetes core resources (Deployment, Service, Ingress) - ADR-007
- **TLS**: cert-manager with HTTP-01 or DNS-01 challenges - ADR-010
- **Triggers**: Git repository polling (webhooks in future) - ADR-004

## Architecture

### CRD Model (ADR-003)

Kapsa defines four primary CRDs:

1. **Project** (namespace-scoped, developer-facing)
   - Defines application, repository, build strategy, environments
   - References DomainPool and Registry CRDs
   - Managed by developers via `kubectl apply`

2. **Environment** (namespace-scoped, operator-managed)
   - Created by operator based on Project spec
   - Represents specific deployment target (dev/staging/prod/preview)
   - Reconciled into Deployment, Service, Ingress

3. **DomainPool** (cluster-scoped, admin-managed)
   - Defines available base domains for routing
   - References cert-manager ClusterIssuer
   - Handles subdomain allocation

4. **Registry** (cluster-scoped, admin-managed)
   - Defines container registry endpoints (Harbor, GitLab, etc.)
   - Stores credentials via Secret references (not inline)

### Control Flow

```
Developer creates Project CRD
  ↓
Operator polls git repository
  ↓
On source change: trigger kpack build
  ↓
kpack builds image → pushes to Registry
  ↓
Operator creates/updates Environment CRDs
  ↓
Environment → Deployment, Service, Ingress
  ↓
cert-manager provisions TLS certificate
  ↓
Application live at allocated domain
```

### Preview Environments (ADR-011)

- Ephemeral environments for feature branches
- Enabled via `Project.spec.previewEnvironments.enabled: true`
- Lifecycle: Created on branch detection, destroyed on merge/delete or TTL expiry
- Subdomain pattern: `<branch>.<project>.<base-domain>`

## Key Architectural Decisions

Refer to ADRs in `docs/adr/` for detailed rationale. Key decisions:

- **ADR-001**: Python + Kopf for v1 (allows fast iteration; clean CRD design for later Go migration)
- **ADR-002**: Single-tenant, namespace-per-project (simple RBAC, easy isolation)
- **ADR-003**: Four CRD model (Project, Environment, DomainPool, Registry)
- **ADR-004**: Git polling for triggers (no Git provider dependency; webhooks later)
- **ADR-005**: kpack for builds (supports Dockerfile and Buildpacks with caching)
- **ADR-006**: Registry abstraction (modular, supports Harbor/GitLab/Docker/ECR/GCR/ACR)
- **ADR-007**: Kubernetes core runtime (Deployment + Service + Ingress; language-agnostic)
- **ADR-008**: Kubernetes rolling updates (Argo Rollouts for canary/blue-green later)
- **ADR-009**: Reference-only config/secrets (integrates with ESO/Vault/SealedSecrets)
- **ADR-010**: cert-manager for TLS (DomainPool defines bases; HTTP-01 default, DNS-01 optional)
- **ADR-011**: Ephemeral preview environments (flag-enabled, TTL-based cleanup)
- **ADR-012**: Structured logging + Prometheus metrics (integrates with existing observability)
- **ADR-013**: Namespace + ServiceAccount per project (minimal RBAC; no PSA/NetworkPolicy enforcement)
- **ADR-014**: Kubernetes ≥1.30, single cluster, CNI-agnostic
- **ADR-015**: CRDs start as v1alpha1 (backwards-compatible evolution)

## Documentation Structure

- **`docs/project/vision.md`**: Product vision, goals, non-goals, roadmap
- **`docs/architecture/`**: System architecture documentation
  - `overview.md`: Components, data flows, tenancy, observability
  - `component-diagram.md`: Visual architecture (Mermaid diagrams)
  - `crd-schemas.md`: Detailed CRD specs with YAML examples
  - `sequence-diagram.md`: Deployment flows, preview lifecycles, error handling
- **`docs/adr/`**: Architecture Decision Records (numbered 001-015)

## Working with This Codebase

### Documentation Standards

- **ADRs**: Concise decision records (Decision, Rationale, Implication format)
- **Architecture docs**: Technical and precise; use Mermaid for diagrams
- **CRD schemas**: Include full YAML examples with inline comments
- **Avoid vendor comparisons**: Position as "Kubernetes-native deployment platform" not "alternative to X"

### CRD Design Principles

1. **No inline secrets**: Always use `secretRef` or `configMapRef`
2. **Status conditions**: Follow Kubernetes conventions (Ready, BuildSucceeded, etc.)
3. **Owner references**: Preview Environments owned by Project (garbage collection)
4. **Declarative spec**: Developers declare desired state; operator reconciles
5. **Namespace isolation**: Each Project gets dedicated namespace

### Future Work (Not in v1)

- Database/queue provisioning
- Notification integrations (Slack, GitHub status)
- Web UI or CLI
- Multi-cluster federation
- Webhook-based triggers
- Argo Rollouts integration
- Knative runtime adapter

## Current State

This is a **documentation-first project**. The architecture and design are defined, but implementation has not started. When implementing:

1. Start with CRD definitions (v1alpha1)
2. Implement basic operator reconciliation loop (Kopf)
3. Integrate kpack for builds
4. Implement Environment → Deployment/Service/Ingress reconciliation
5. Add domain allocation from DomainPool
6. Implement preview environment lifecycle
7. Add observability (structured logging, Prometheus metrics)

The project follows a modular, incremental approach—each component can be developed and tested independently.

## Common Commands

### Helm Chart Development

```bash
# Lint the Helm chart
helm lint helm/kapsa

# Template and verify chart rendering
helm template test-release helm/kapsa --debug

# Test installation in local kind cluster
kind create cluster --name kapsa-dev
helm install kapsa helm/kapsa
kubectl get pods -n kapsa-system

# Cleanup
helm uninstall kapsa
kind delete cluster --name kapsa-dev
```

### Working with CRDs

CRD definitions are located in `helm/kapsa/templates/crds/`:

- `project.yaml` - Developer-facing application definition
- `environment.yaml` - Operator-managed environment resources
- `domainpool.yaml` - Cluster-scoped domain configuration
- `registry.yaml` - Cluster-scoped registry endpoints

### Operator Development (Future)

The operator directory doesn't exist yet. When implementing:

```bash
# Set up Python environment
cd operator
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run tests
pytest

# Build Docker image
docker build -t kapsa:dev .
```

### GitHub Actions

The project uses GitHub Actions for CI/CD:

- `.github/workflows/build-operator.yaml` - Builds and pushes operator image to GHCR
- `.github/workflows/docs.yaml` - Validates documentation

Images are published to `ghcr.io/kapsa-project/kapsa`.
