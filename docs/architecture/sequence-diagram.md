# Sequence Diagrams

## 1. Initial Project Deployment

Complete flow from Project creation to live application.

```mermaid
sequenceDiagram
    actor Dev as Developer
    participant KC as kubectl
    participant API as K8s API Server
    participant OP as Kapsa Operator
    participant GIT as Git Repository
    participant KP as kpack
    participant REG as Container Registry
    participant CM as cert-manager
    participant K8S as Kubernetes

    Dev->>KC: kubectl apply -f project.yaml
    KC->>API: Create Project CRD
    API->>OP: Watch event: Project created

    Note over OP: Reconciliation starts

    OP->>API: Create namespace for project
    OP->>API: Create ServiceAccount
    OP->>GIT: Poll repository (get latest commit)
    GIT->>OP: Return: commit SHA abc123d

    OP->>API: Create kpack Image CRD
    API->>KP: Watch event: Image created

    KP->>GIT: Clone repository at abc123d
    KP->>KP: Detect build strategy<br/>(Dockerfile or Buildpack)
    KP->>KP: Build container image
    KP->>REG: Push image:<br/>harbor.corp.com/myapp/api:abc123d
    KP->>API: Update Image.status.latestImage

    API->>OP: Watch event: Image build complete

    loop For each environment in spec.environments
        OP->>API: Create Environment CRD
        API->>OP: Watch event: Environment created

        OP->>API: Query DomainPool for base domain
        OP->>OP: Allocate subdomain:<br/>dev.api.apps.corp.com

        OP->>API: Create Deployment
        OP->>API: Create Service
        OP->>API: Create Ingress with TLS

        API->>CM: Watch event: Ingress needs cert
        CM->>CM: Request certificate via ACME HTTP-01
        CM->>API: Create Secret with TLS cert

        API->>K8S: Schedule pods
        K8S->>K8S: Pull image from registry
        K8S->>K8S: Start application pods

        K8S->>API: Update Deployment status: Ready
        API->>OP: Watch event: Deployment ready

        OP->>API: Update Environment.status:<br/>phase=Running, url=https://dev.api.apps.corp.com
    end

    OP->>API: Update Project.status:<br/>conditions=[Ready=True]

    Dev->>Dev: Access application at<br/>https://dev.api.apps.corp.com
```

## 2. Source Code Update (Auto-Sync)

Flow when git repository changes are detected.

```mermaid
sequenceDiagram
    participant OP as Kapsa Operator
    participant GIT as Git Repository
    participant KP as kpack
    participant REG as Container Registry
    participant K8S as Kubernetes (Deployment)

    Note over OP: Poll timer triggers (every 5min)

    OP->>GIT: Check for new commits on 'main'
    GIT->>OP: New commit: def456e

    OP->>OP: Compare with status.latestCommit (abc123d)
    OP->>OP: Detect change

    OP->>KP: Update Image CRD with new commit
    KP->>GIT: Clone repository at def456e
    KP->>KP: Rebuild image (use cache where possible)
    KP->>REG: Push image:<br/>harbor.corp.com/myapp/api:def456e
    KP->>OP: Update Image.status.latestImage

    OP->>OP: Identify environments with autoSync=true<br/>and branch='main'

    loop For each auto-sync environment
        OP->>K8S: Update Deployment.spec.template.spec.containers[].image
        K8S->>K8S: Rolling update<br/>(terminate old pods, start new)
        K8S->>OP: Deployment status: Ready
        OP->>OP: Update Environment.status.image
    end

    OP->>OP: Update Project.status.latestCommit = def456e
```

## 3. Preview Environment Creation

Flow when feature branch is detected.

```mermaid
sequenceDiagram
    participant OP as Kapsa Operator
    participant GIT as Git Repository
    participant KP as kpack
    participant REG as Container Registry
    participant API as K8s API Server
    participant CM as cert-manager

    Note over OP: Poll timer triggers

    OP->>GIT: List branches
    GIT->>OP: Branches: [main, develop, feature/new-api]

    OP->>OP: Check Project.spec.previewEnvironments.enabled=true
    OP->>OP: Match branch against include/exclude patterns
    OP->>OP: Detect new branch: feature/new-api

    OP->>KP: Create Image CRD for branch
    KP->>GIT: Clone feature/new-api at commit xyz789a
    KP->>KP: Build image
    KP->>REG: Push image:<br/>harbor.corp.com/myapp/api:feature-new-api-xyz789a
    KP->>OP: Image ready

    OP->>API: Create Environment CRD
    Note over OP: metadata.labels[type]=preview<br/>spec.type=preview<br/>spec.branch=feature/new-api<br/>status.expiresAt=now+7d

    OP->>OP: Allocate subdomain:<br/>feature-new-api.api.apps.corp.com

    OP->>API: Create Deployment
    OP->>API: Create Service
    OP->>API: Create Ingress

    API->>CM: Request TLS certificate
    CM->>OP: Certificate ready

    OP->>API: Update Environment.status:<br/>phase=Running<br/>url=https://feature-new-api.api.apps.corp.com

    Note over OP: Preview environment is live
```

## 4. Preview Environment Cleanup

Flow when preview environment expires or branch is deleted.

```mermaid
sequenceDiagram
    participant OP as Kapsa Operator
    participant GIT as Git Repository
    participant API as K8s API Server
    participant K8S as Kubernetes

    alt Branch deleted/merged
        OP->>GIT: List branches
        GIT->>OP: feature/new-api not found
        OP->>OP: Mark preview environment for deletion
    else TTL expired
        OP->>OP: Check Environment.status.expiresAt
        OP->>OP: Current time > expiresAt
        OP->>OP: Mark preview environment for deletion
    end

    OP->>API: Delete Environment CRD

    Note over K8S: Kubernetes garbage collection<br/>(ownerReferences cleanup)

    K8S->>K8S: Delete Deployment (cascading)
    K8S->>K8S: Delete Service
    K8S->>K8S: Delete Ingress
    K8S->>K8S: Delete Pods

    Note over OP: Preview environment cleaned up

    OP->>OP: Update Project.status<br/>(remove preview from environment list)
```

## 5. Platform Admin: Initial Setup

One-time setup flow for platform administrators.

```mermaid
sequenceDiagram
    actor Admin as Platform Admin
    participant KC as kubectl
    participant API as K8s API Server
    participant OP as Kapsa Operator
    participant CM as cert-manager
    participant REG as Container Registry

    Note over Admin: Install Kapsa operator
    Admin->>KC: kubectl apply -f kapsa-operator.yaml
    KC->>API: Create Namespace, Deployment, RBAC
    API->>OP: Operator starts, begin watching CRDs

    Note over Admin: Configure cert-manager issuer
    Admin->>KC: kubectl apply -f clusterissuer.yaml
    KC->>API: Create ClusterIssuer (letsencrypt-prod)
    API->>CM: ClusterIssuer ready

    Note over Admin: Create DomainPool
    Admin->>KC: kubectl apply -f domainpool.yaml
    KC->>API: Create DomainPool CRD
    API->>OP: Watch event: DomainPool created
    OP->>CM: Verify ClusterIssuer exists
    CM->>OP: Issuer is ready
    OP->>API: Update DomainPool.status: Ready=True

    Note over Admin: Create Registry
    Admin->>KC: kubectl create secret<br/>harbor-push-credentials
    Admin->>KC: kubectl apply -f registry.yaml
    KC->>API: Create Registry CRD
    API->>OP: Watch event: Registry created
    OP->>REG: Test connectivity and auth
    REG->>OP: Authentication successful
    OP->>API: Update Registry.status:<br/>verified=true, Ready=True

    Note over Admin: Platform ready for developers
```

## 6. Secret Management Integration (ESO Example)

Flow showing how external secrets are referenced (not stored in CRDs).

```mermaid
sequenceDiagram
    actor Dev as Developer
    participant API as K8s API Server
    participant OP as Kapsa Operator
    participant ESO as External Secrets Operator
    participant VAULT as HashiCorp Vault
    participant POD as Application Pod

    Note over Dev: Developer creates ExternalSecret
    Dev->>API: Create ExternalSecret CRD<br/>(pointing to Vault path)
    API->>ESO: Watch event: ExternalSecret created
    ESO->>VAULT: Fetch secret from path<br/>/apps/api-service/prod
    VAULT->>ESO: Return secret data
    ESO->>API: Create Kubernetes Secret<br/>(api-secrets-prod)

    Note over Dev: Developer creates Project
    Dev->>API: Create Project CRD
    API->>OP: Watch event: Project created

    OP->>API: Create Environment CRD<br/>spec.secretRefs=[{name: api-secrets-prod}]

    OP->>API: Create Deployment<br/>with envFrom: secretRef

    API->>POD: Start pod with secret mounted
    POD->>API: Read secret from environment variables

    Note over POD: Application has access to secrets<br/>No secrets stored in Kapsa CRDs
```

## 7. Build Failure Handling

Flow when kpack build fails.

```mermaid
sequenceDiagram
    participant OP as Kapsa Operator
    participant GIT as Git Repository
    participant KP as kpack
    participant API as K8s API Server

    OP->>GIT: Detect new commit: bad123f
    OP->>KP: Update Image CRD
    KP->>GIT: Clone repository
    KP->>KP: Start build
    KP->>KP: Build fails<br/>(compilation error)

    KP->>API: Update Image.status:<br/>conditions=[Ready=False]<br/>reason=BuildFailed<br/>message="npm install failed: ..."

    API->>OP: Watch event: Image build failed

    OP->>API: Update Project.status:<br/>conditions=[BuildSucceeded=False]<br/>reason=BuildFailed<br/>message=<error details>

    Note over OP: Existing environments continue running<br/>with previous successful image

    OP->>OP: Do NOT update Environment image

    Note over OP: Wait for next commit or manual intervention
```

## Key Timing and Behaviors

### Poll Intervals

- **Git repository polling**: Default 5 minutes (configurable per Project)
- **Reconciliation loop**: Triggered on CRD changes + periodic resync (10 minutes)

### Retry Behavior

- **Build failures**: No automatic retry; wait for next commit
- **Deployment failures**: Kubernetes handles pod restarts
- **Registry push failures**: kpack retries with exponential backoff

### Cleanup Behavior

- **Preview environments**: Deleted when branch removed OR TTL expires
- **Environment deletion**: Kubernetes garbage collection via `ownerReferences`
- **Namespace deletion**: Manual (platform admin must delete Project CRD)
