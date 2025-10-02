# ADR-007 — Runtime

- **Decision**: Default runtime = Kubernetes core resources.
- **Implementation**: Deployment + Service + Ingress (NGINX first, Gateway API later).
- **Implication**: Language/runtime agnostic; supports legacy backends, multiple ports, sidecars.
- **Future**: Optional adapter for Knative.
