# Kapsa

> **⚠️ Early Stage / Design Phase & mostly vibe-coded**
> This project is currently in active design and documentation phase. Much of this project is created using tools like ChatGPT, Claude and others.

**Kapsa** is an open-source, Kubernetes-native deployment platform that brings push-to-deploy simplicity to self-hosted infrastructure.

Built for organizations that want to provide their developers with a streamlined deployment experience while maintaining full control over infrastructure, ensuring privacy compliance, and integrating with existing enterprise tooling.

## What is Kapsa?

Kapsa transforms Kubernetes into a developer-friendly deployment platform. Developers describe their application with a single custom resource, and Kapsa handles the rest:

```yaml
apiVersion: kapsa-project.io/v1alpha1
kind: Project
metadata:
  name: my-api
spec:
  repository:
    url: https://github.com/myorg/my-api
    branch: main
  build:
    strategy: buildpack
  registry:
    name: company-harbor
  domain:
    subdomain: api
    domainPoolRef: corporate-apps
  environments:
    - name: prod
      branch: main
      autoSync: true
```

Kapsa automatically:

- Builds container images in-cluster (Dockerfile or Buildpacks)
- Pushes to your configured registry (Harbor, GitLab, etc.)
- Deploys to Kubernetes with rolling updates
- Provisions TLS certificates via cert-manager
- Exposes applications with valid HTTPS domains
- Creates ephemeral preview environments for feature branches

## Key Features

### Developer Experience

- **Single CRD interface**: `kubectl apply -f project.yaml` is all it takes
- **Auto-sync deployments**: Push to git ➡️ automatic builds and deployments
- **Preview environments**: Ephemeral environments for every feature branch
- **Zero config builds**: Automatic runtime detection via Cloud Native Buildpacks

### Platform Team Control

- **Modular integration**: Works with existing infrastructure (Harbor, GitLab Registry, Vault, ESO, NGINX, cert-manager)
- **Namespace isolation**: Each project gets its own namespace with RBAC
- **Domain management**: Platform admins define base domains; developers get subdomains
- **Registry abstraction**: Support for Harbor, GitLab, Docker Hub, ECR, GCR, ACR

### Privacy & Compliance

- **Self-hosted**: Runs entirely within your Kubernetes clusters
- **No external dependencies**: No vendor APIs, no telemetry
- **Air-gap ready**: Works in disconnected environments
- **Reference-only secrets**: Integrates with existing secret management (Vault, ESO, Sealed Secrets)

## Architecture

Kapsa is built on four core Custom Resource Definitions:

| CRD             | Scope     | Managed By      | Purpose                                          |
| --------------- | --------- | --------------- | ------------------------------------------------ |
| **Project**     | Namespace | Developers      | Application definition, repository, environments |
| **Environment** | Namespace | Operator        | Runtime configuration for deployment targets     |
| **DomainPool**  | Cluster   | Platform Admins | Available base domains for routing               |
| **Registry**    | Cluster   | Platform Admins | Container registry endpoints and credentials     |

### How It Works

```txt
Developer creates Project CRD
         ⬇️
Operator polls git repository
         ⬇️
On source change: trigger kpack build
         ⬇️
kpack builds image ➡️ pushes to Registry
         ⬇️
Operator creates Environment CRDs
         ⬇️
Environment ➡️ Deployment, Service, Ingress
         ⬇️
cert-manager provisions TLS certificate
         ⬇️
Application live at allocated domain
```

See [docs/architecture/](docs/architecture/) for detailed architecture documentation.

## Quick Start

### Prerequisites

- Kubernetes cluster (≥1.30)
- kpack installed
- cert-manager installed
- Container registry (Harbor, GitLab, etc.)

### Installation

Install Kapsa:

```bash
# 1. Install CRDs (Custom Resource Definitions)
kubectl apply -f crds/

# 2. Install kpack (required - must be installed separately)
kubectl apply -f https://github.com/buildpacks-community/kpack/releases/download/v0.17.0/release-0.17.0.yaml

# OR install cert-manager separately if you prefer
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.15.0/cert-manager.yaml
```

For detailed installation instructions, see [Installation Guide](docs/installation.md).

### Platform Admin Setup

1. **Create a cert-manager ClusterIssuer** (if not already configured)

   Kapsa requires a ClusterIssuer for automatic TLS certificate provisioning. Create one using Let's Encrypt or your preferred CA:

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

2. **Create a DomainPool**

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

3. **Create a Registry**

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
   ```

### Developer Workflow

1. **Create a Project**

   ```yaml
   apiVersion: kapsa-project.io/v1alpha1
   kind: Project
   metadata:
     name: my-app
   spec:
     repository:
       url: https://github.com/myorg/my-app
       branch: main
       pollInterval: 300
     build:
       strategy: buildpack
     registry:
       name: company-harbor
       imageRepository: myteam/my-app
     domain:
       subdomain: my-app
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
       ttl: 168h # 7 days
       branches:
         include: ["feature/*"]
   ```

2. **Apply the configuration**

   ```bash
   kubectl apply -f project.yaml
   ```

3. **Monitor deployment**

   ```bash
   kubectl get project my-app -o yaml
   kubectl get environments
   ```

4. **Access your application**
   - Production: `https://my-app.apps.corp.com`
   - Dev: `https://dev.my-app.apps.corp.com`
   - Preview (feature/new-api): `https://feature-new-api.my-app.apps.corp.com`

## Technology Stack

- **Operator Framework**: Python + Kopf
- **Build System**: kpack (Cloud Native Buildpacks + Dockerfile support)
- **Runtime**: Kubernetes core (Deployment, Service, Ingress)
- **TLS**: cert-manager (HTTP-01 or DNS-01 challenges)
- **Ingress**: NGINX (Gateway API support planned)

## Documentation

- **[Installation Guide](docs/installation.md)**: Detailed installation and setup instructions
- **[Vision](docs/project/vision.md)**: Project goals, use cases, roadmap
- **[Architecture](docs/architecture/)**: System design, components, CRD schemas, sequence diagrams
- **[ADRs](docs/adr/)**: Architecture Decision Records (001-015)
- **[CLAUDE.md](CLAUDE.md)**: Development guide for AI-assisted coding

## Roadmap

### v1 (MVP - v1alpha1)

- Architecture and design complete
- Operator implementation (Python + Kopf)
- kpack integration for builds
- Environment reconciliation (Deployment, Service, Ingress)
- Domain allocation from DomainPool
- cert-manager TLS integration
- Preview environment lifecycle management
- Git repository polling

### Future

- Webhook-based triggers (GitHub, GitLab, Bitbucket)
- Argo Rollouts integration (canary, blue-green deployments)
- Knative runtime adapter (scale-to-zero)
- Notification integrations (Slack, GitHub status)
- Multi-cluster support
- Web UI and CLI
- Database/queue provisioning

## Non-Goals (v1)

- Database or message queue provisioning
- Custom notification integrations
- Web UI or CLI (future work)
- Multi-cluster federation
- Pod security policy enforcement (left to cluster admins)

## Contributing

This project is in early stages. We're currently focused on:

1. Finalizing CRD schemas
2. Implementing the core operator
3. Building integration tests

Interested in contributing? Check out the [Architecture Documentation](docs/architecture/) and [ADRs](docs/adr/) to understand the design decisions.

## License

[not decided yet]

---

**Built for platform teams who want to provide a great developer experience without giving up control.**
