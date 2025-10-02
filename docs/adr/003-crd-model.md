# ADR-003 — CRD Model

- **Decision**: Define these CRDs:
  - `Project` (top-level: repo, build, registry, domains, envs, preview toggle).
  - `Environment` (runtime: replicas, autoscaling, ports, ingress, config refs).
  - `DomainPool` (admin-provided base domains + cert-manager issuer).
  - `Registry` (admin-provided registry endpoint + creds).
- **Implication**: Devs interact only with `Project`; admins provide `DomainPool` and `Registry`.
