# ADR-002 — Tenancy & Isolation Model

- **Decision**: Single tenant; each Project gets its own namespace.
- **Implication**: Easy RBAC, optional quotas, no multi-tenant auth complexity in v1.
