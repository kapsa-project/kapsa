# Vision

## Project Description

Kapsa is an **open-source, Kubernetes-native deployment platform** that brings **push-to-deploy simplicity** to self-hosted infrastructure.
It empowers organizations to provide their developers with a streamlined deployment experience while maintaining full control over infrastructure, ensuring **privacy compliance**, and integrating with **existing enterprise tooling**.

Developers describe their application using a **single Kubernetes custom resource** (`Project`) with declarative configuration:

- Repository location
- Build strategy (Dockerfile or Buildpacks)
- Target environments (e.g., dev, staging, prod)
- Domain configuration

The platform automatically orchestrates:

- In-cluster image builds
- Registry push operations
- Kubernetes deployments with service exposure
- TLS certificate provisioning and domain routing
- Ephemeral preview environments for feature branches

## Goal

Kapsa delivers a **managed PaaS experience within self-hosted Kubernetes infrastructure**:

- **Developer simplicity:** `kubectl apply -f project.yaml` triggers the entire deployment pipeline. No proprietary CLIs, dashboards, or external services required.
- **Platform team control:** Infrastructure administrators define registries, domain pools, and ingress controllers once; developers consume these resources through clean CRD-based abstractions.
- **Modular integration:** Built to work with existing corporate infrastructure—Harbor, GitLab Container Registry, HashiCorp Vault, External Secrets Operator, NGINX Ingress, cert-manager, and other standard Kubernetes ecosystem tools.
- **Privacy and compliance:** Runs entirely within your Kubernetes clusters. No external API calls, no vendor telemetry, full air-gap support for regulated environments.

## Non-Goals (v1)

- Database or queue provisioning (out of scope).
- Custom notification integrations (Slack, GitHub status, etc).
- Web UI or CLI (future work, not MVP).
- Multi-cluster federation (single cluster focus for now).
- Enforcing pod security or strict policies (leave to cluster admins).

## Roadmap (high-level)

- **MVP (v1alpha1):**
  - Poll repos for changes
  - In-cluster builds via kpack
  - Deployments + Services + Ingress (NGINX)
  - cert-manager TLS
  - DomainPool CRD for subdomain allocation
  - Ephemeral preview environments
- **Future:**
  - Webhook triggers
  - Argo Rollouts for progressive delivery
  - Knative runtime adapter for scale-to-zero
  - Notifications & status reporting
  - Multi-cluster support
  - CLI / Web UI
