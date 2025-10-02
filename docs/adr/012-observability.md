# ADR-012 — Observability

- **Decision**: Logs: stdout/stderr. Metrics: Prometheus endpoint for controller + ServiceMonitors for apps.
- **Implication**: Admins integrate with existing observability stack.
