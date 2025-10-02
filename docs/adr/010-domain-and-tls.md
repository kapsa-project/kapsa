# ADR-010 — Domains & TLS

- **Decision**: cert-manager for TLS; DomainPool defines valid bases.
- **Implication**: Devs only provide subdomains; operator handles cert issuance (HTTP-01 default, DNS-01 optional).
