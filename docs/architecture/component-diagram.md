# Component Diagram

## High-Level Architecture

```mermaid
graph TB
    subgraph "Developer Interface"
        DEV[Developer]
        PROJECT[Project CRD]
    end

    subgraph "Kapsa Control Plane"
        OPERATOR[Kapsa Operator<br/>Python + Kopf]
        RECONCILER[Reconciliation Loop]
    end

    subgraph "Platform Resources"
        DOMAINPOOL[DomainPool CRD]
        REGISTRY[Registry CRD]
    end

    subgraph "Build Subsystem"
        KPACK[kpack]
        BUILDER[Builder Images]
    end

    subgraph "Runtime Environment"
        ENV[Environment CRD]
        DEPLOY[Deployment]
        SVC[Service]
        ING[Ingress]
        CERTMGR[cert-manager]
    end

    subgraph "External Systems"
        GIT[Git Repository]
        REG[Container Registry<br/>Harbor/GitLab/etc]
        ESO[External Secrets<br/>ESO/Vault/Sealed]
    end

    DEV -->|kubectl apply| PROJECT
    PROJECT --> OPERATOR
    OPERATOR --> RECONCILER

    RECONCILER -->|poll| GIT
    RECONCILER -->|allocate domain| DOMAINPOOL
    RECONCILER -->|read registry config| REGISTRY
    RECONCILER -->|trigger build| KPACK
    RECONCILER -->|create/update| ENV

    KPACK -->|use| BUILDER
    KPACK -->|clone| GIT
    KPACK -->|push image| REG

    ENV --> DEPLOY
    ENV --> SVC
    ENV --> ING

    ING -->|request cert| CERTMGR
    DEPLOY -->|reference| ESO

    CERTMGR -.->|provision TLS| ING
```

## Component Interaction Details

### Kapsa Operator

**Watches:**

- Project CRDs (all namespaces or configured namespaces)
- Environment CRDs (owned by Projects)
- DomainPool CRDs (cluster-scoped)
- Registry CRDs (cluster-scoped or namespace-scoped)

**Creates/Manages:**

- Namespaces (one per Project)
- ServiceAccounts (one per Project)
- Environment CRDs (per configured environment in Project)
- kpack Image resources (trigger builds)

**Reconciliation Triggers:**

- Project CRD create/update/delete
- Git repository changes (detected via polling)
- Environment CRD status changes
- kpack Image build completion

### Environment Controller

The Environment CRD is reconciled by the Kapsa operator to create runtime resources.

**Reads:**

- Environment spec (replicas, ports, ingress rules, resource limits)
- Project spec (image repository, domain configuration)
- DomainPool (to validate/allocate subdomains)

**Creates:**

- Deployment (application pods)
- Service (cluster networking)
- Ingress (external routing + TLS)
- HorizontalPodAutoscaler (optional, if autoscaling configured)

### Build Flow

```mermaid
sequenceDiagram
    participant OP as Kapsa Operator
    participant KP as kpack
    participant GIT as Git Repo
    participant REG as Registry

    OP->>KP: Create/Update Image CRD
    KP->>GIT: Clone source code
    KP->>KP: Detect build method<br/>(Dockerfile or Buildpack)
    KP->>KP: Execute build
    KP->>REG: Push image with tag
    KP->>OP: Update Image status<br/>(latestImage field)
    OP->>OP: Trigger Environment<br/>reconciliation
```

### Domain Allocation Flow

```mermaid
sequenceDiagram
    participant PR as Project CRD
    participant OP as Kapsa Operator
    participant DP as DomainPool
    participant ENV as Environment

    PR->>OP: spec.subdomain: "myapp"
    OP->>DP: Query available base domains
    DP->>OP: Return: ["apps.corp.com"]
    OP->>ENV: Allocate: myapp.apps.corp.com
    ENV->>ENV: Create Ingress with host
```

## Preview Environment Architecture

```mermaid
graph TB
    subgraph "Project: api-service"
        PROJ[Project CRD<br/>previewEnvironments: true]
    end

    subgraph "Permanent Environments"
        ENV_DEV[Environment: dev<br/>dev.api.apps.corp.com]
        ENV_PROD[Environment: prod<br/>api.apps.corp.com]
    end

    subgraph "Preview Environments (Ephemeral)"
        ENV_PR1[Environment: feat-auth<br/>feat-auth.api.apps.corp.com<br/>TTL: 7d]
        ENV_PR2[Environment: fix-bug<br/>fix-bug.api.apps.corp.com<br/>TTL: 7d]
    end

    PROJ --> ENV_DEV
    PROJ --> ENV_PROD
    PROJ -.->|branch detected| ENV_PR1
    PROJ -.->|branch detected| ENV_PR2

    style ENV_PR1 stroke-dasharray: 5 5
    style ENV_PR2 stroke-dasharray: 5 5
```

**Preview Environment Lifecycle:**

1. Operator detects new branch in git repository
2. Creates ephemeral Environment CRD with `ownerReferences` to Project
3. Environment gets unique subdomain: `<branch-name>.<project-name>.<base-domain>`
4. On branch deletion or merge: Environment is deleted
5. On TTL expiry (default 7 days): Environment is deleted
6. Kubernetes garbage collection removes all child resources

## Platform Administrator Setup

```mermaid
graph LR
    ADMIN[Platform Admin]

    ADMIN -->|1. Configure| DOMAINPOOL[DomainPool CRD<br/>Base domains + cert-manager issuer]
    ADMIN -->|2. Configure| REGISTRY[Registry CRD<br/>Harbor/GitLab endpoint + creds]
    ADMIN -->|3. Configure| SECRETS[Secret Store<br/>ESO/Vault configuration]

    DOMAINPOOL -.->|used by| DEVS[Developers]
    REGISTRY -.->|used by| DEVS
    SECRETS -.->|used by| DEVS

    style ADMIN fill:#e1f5ff
    style DEVS fill:#fff4e1
```

Platform administrators set up infrastructure resources once; developers consume them via CRD references.
