# Development Documentation

This directory contains documentation for Kapsa developers and contributors.

## Quick Links

- [GitHub Actions CI/CD](github-actions.md) - Workflows, builds, and releases

## Project Structure

```
kapsa/
├── .github/
│   ├── workflows/           # GitHub Actions workflows
│   │   ├── build-operator.yaml   # Build and push operator image
│   │   ├── helm-chart.yaml       # Lint, test, publish Helm chart
│   │   ├── release.yaml          # Automated releases
│   │   └── docs.yaml             # Documentation validation
│   ├── ct.yaml              # chart-testing configuration
│   ├── dependabot.yml       # Dependency updates
│   └── FUNDING.yml          # Funding/sponsorship info
├── docs/
│   ├── project/            # Project vision and roadmap
│   ├── architecture/       # System architecture docs
│   ├── adr/               # Architecture Decision Records
│   ├── development/       # This directory
│   └── installation.md    # Installation guide
├── helm/kapsa/            # Helm chart
│   ├── Chart.yaml
│   ├── values.yaml
│   ├── templates/
│   │   ├── crds/         # CRD definitions
│   │   ├── operator/     # Operator resources
│   │   └── monitoring/   # Prometheus integration
│   └── README.md
├── operator/              # Operator code (Python + Kopf)
│   └── Dockerfile
├── CLAUDE.md             # AI development guide
├── CHANGELOG.md          # Version history
└── README.md             # Main readme
```

## Development Workflow

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/kapsa-project/kapsa.git
   cd kapsa
   ```

2. **Install development tools**
   ```bash
   # Helm
   brew install helm

   # chart-testing
   brew install chart-testing

   # kind (for testing)
   brew install kind

   # kubectl
   brew install kubectl
   ```

### Working on Helm Chart

1. **Make changes to chart**
   ```bash
   vim helm/kapsa/templates/...
   ```

2. **Lint chart**
   ```bash
   helm lint helm/kapsa
   ```

3. **Template and verify**
   ```bash
   helm template test-release helm/kapsa --debug | less
   ```

4. **Test in kind cluster**
   ```bash
   kind create cluster --name kapsa-dev
   helm install kapsa helm/kapsa
   kubectl get pods -n kapsa-system
   ```

5. **Clean up**
   ```bash
   helm uninstall kapsa
   kind delete cluster --name kapsa-dev
   ```

### Working on Operator

1. **Set up Python environment**
   ```bash
   cd operator
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run tests**
   ```bash
   pytest
   ```

3. **Build Docker image locally**
   ```bash
   docker build -t kapsa:dev .
   ```

4. **Test in kind cluster**
   ```bash
   kind create cluster --name kapsa-dev
   kind load docker-image kapsa:dev --name kapsa-dev

   # Install with local image
   helm install kapsa ../helm/kapsa \
     --set operator.image.repository=kapsa \
     --set operator.image.tag=dev \
     --set operator.image.pullPolicy=Never
   ```

### Working on Documentation

1. **Edit documentation**
   ```bash
   vim docs/architecture/overview.md
   ```

2. **Lint Markdown** (optional)
   ```bash
   npx markdownlint-cli2 "**/*.md"
   ```

3. **Check links** (optional)
   ```bash
   npx markdown-link-check README.md
   ```

## CI/CD Pipeline

### Automatic Builds

**On every push to main/develop:**
- Operator image built and pushed to `ghcr.io/kapsa-project/kapsa:<branch>`
- Helm chart linted and validated

**On pull requests:**
- Operator image built (not pushed)
- Helm chart tested in kind cluster
- Documentation validated

**On version tags (e.g., v0.1.0):**
- Operator image tagged with version
- Helm chart packaged and published to GHCR
- GitHub Release created with artifacts

### Manual Releases

1. **Update version**
   ```bash
   # Update Chart.yaml
   vim helm/kapsa/Chart.yaml
   # version: 0.2.0
   # appVersion: "0.2.0"

   # Update values.yaml
   vim helm/kapsa/values.yaml
   # tag: "0.2.0"

   # Update CHANGELOG
   vim CHANGELOG.md
   ```

2. **Commit and tag**
   ```bash
   git add .
   git commit -m "chore: bump version to 0.2.0"
   git push origin main

   git tag -a v0.2.0 -m "Release v0.2.0"
   git push origin v0.2.0
   ```

3. **GitHub Actions will:**
   - Build operator image: `ghcr.io/kapsa-project/kapsa:0.2.0`
   - Publish Helm chart: `oci://ghcr.io/kapsa-project/charts/kapsa`
   - Create GitHub Release with notes

## Published Artifacts

### Container Images

- **Registry**: GitHub Container Registry (GHCR)
- **Base URL**: `ghcr.io/kapsa-project/kapsa`
- **Tags**:
  - `latest` - latest from main branch
  - `main` - latest from main branch
  - `develop` - latest from develop branch
  - `0.1.0` - specific version
  - `0.1` - major.minor
  - `0` - major
  - `main-abc123d` - commit SHA

### Helm Charts

- **Registry**: GitHub Container Registry (OCI)
- **Base URL**: `oci://ghcr.io/kapsa-project/charts/kapsa`
- **Versions**: Semantic versioning (e.g., 0.1.0)

**Install:**
```bash
helm install kapsa oci://ghcr.io/kapsa-project/charts/kapsa --version 0.1.0
```

## Testing

### Unit Tests

```bash
cd operator
pytest tests/unit/
```

### Integration Tests

```bash
cd operator
pytest tests/integration/
```

### E2E Tests

```bash
# Create test cluster
kind create cluster --name kapsa-e2e

# Install Kapsa
helm install kapsa helm/kapsa

# Run E2E tests
pytest tests/e2e/

# Cleanup
kind delete cluster --name kapsa-e2e
```

## Code Style

### Python (Operator)

- **Formatter**: Black
- **Linter**: Ruff
- **Type checker**: mypy

```bash
black .
ruff check .
mypy .
```

### YAML (Helm Charts, CRDs)

- **Linter**: yamllint

```bash
yamllint helm/kapsa/
```

### Markdown (Documentation)

- **Linter**: markdownlint

```bash
npx markdownlint-cli2 "**/*.md"
```

## Contributing Guidelines

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/my-feature`
3. **Make changes and test locally**
4. **Lint and format code**
5. **Commit with conventional commits**:
   - `feat:` - new feature
   - `fix:` - bug fix
   - `docs:` - documentation
   - `chore:` - maintenance
   - `test:` - testing
6. **Push and create PR**
7. **Address review comments**
8. **Squash and merge**

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Helm Documentation](https://helm.sh/docs/)
- [Kopf Documentation](https://kopf.readthedocs.io/)
- [Kubernetes Operator Best Practices](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/)
- [kpack Documentation](https://github.com/buildpacks-community/kpack)
- [cert-manager Documentation](https://cert-manager.io/docs/)

## Getting Help

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas
- **Documentation**: Check docs/ directory
- **CLAUDE.md**: AI-assisted development guide
