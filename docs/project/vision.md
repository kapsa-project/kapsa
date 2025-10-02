# Vision

## Project Description

Kapsa is an **open-source, Kubernetes-native alternative to Vercel**.  
It empowers organizations to provide their developers with a simple way to deploy applications while keeping everything **self-hosted**, **privacy-compliant**, and **modular**.

Developers describe their app using a **single Kubernetes custom resource** (`Project`) with information such as:

- Repository location
- Build strategy (Dockerfile or Buildpacks)
- Desired environments (e.g., dev, staging, prod)
- Subdomain name

The system automatically:

- Builds the image in-cluster
- Pushes it to the configured registry
- Deploys it to Kubernetes
- Exposes it under a valid TLS domain
- Optionally creates ephemeral preview environments

## Goal

The goal is to offer a **“Vercel-like experience, but self-hosted and Kubernetes-native”**:

- **Simple for developers:** `kubectl apply -f project.yaml` is all it takes.
- **Flexible for platform teams:** Admins define registries, domains, and ingress controllers once; developers consume them through clean abstractions.
- **Modular by design:** Works with Harbor, GitLab registry, Vault, ESO, NGINX, cert-manager, and other existing corp-infra components.
- **Privacy-first:** Runs entirely within the company’s own Kubernetes clusters.

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
