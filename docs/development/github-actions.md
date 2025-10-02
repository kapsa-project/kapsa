# GitHub Actions CI/CD

Kapsa uses GitHub Actions for continuous integration and deployment. This document describes the workflows and how to use them.

## Workflows

### 1. Build and Push Operator Image

**File:** `.github/workflows/build-operator.yaml`

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Tags starting with `v*`

**What it does:**
- Builds the Kapsa operator Docker image
- Pushes to GitHub Container Registry (`ghcr.io/kapsa-project/kapsa`)
- Creates multi-arch images (linux/amd64, linux/arm64)
- Tags images based on:
  - Branch name (e.g., `main`, `develop`)
  - PR number (e.g., `pr-123`)
  - Semantic version (e.g., `0.1.0`, `0.1`, `0`)
  - Commit SHA (e.g., `main-abc123d`)
  - `latest` for main branch
- Generates build attestations for supply chain security

**Environment variables:**
- `REGISTRY`: `ghcr.io`
- `IMAGE_NAME`: `kapsa-project/kapsa`

**Permissions required:**
- `contents: read`
- `packages: write`

### 2. Helm Chart CI/CD

**File:** `.github/workflows/helm-chart.yaml`

**Triggers:**
- Push to `main` or `develop` with changes in `helm/kapsa/**`
- Pull requests with changes in `helm/kapsa/**`
- Tags starting with `v*`

**What it does:**

**Lint and Test Job:**
- Lints Helm chart with `helm lint`
- Templates chart to verify rendering
- Runs `chart-testing` (ct) for advanced linting
- Creates a `kind` cluster for PR integration tests
- Installs chart in test cluster (PR only)

**Package and Publish Job:**
- Packages Helm chart as `.tgz`
- Pushes to GitHub Container Registry (`oci://ghcr.io/kapsa-project/charts/kapsa`)
- Uploads chart artifact for releases
- Only runs on `main` branch or version tags

**Configuration:**
- Chart testing config: `.github/ct.yaml`
- Additional Helm repos: jetstack (cert-manager)

### 3. Release Automation

**File:** `.github/workflows/release.yaml`

**Triggers:**
- Tags starting with `v*` (e.g., `v0.1.0`, `v1.0.0-alpha.1`)

**What it does:**
- Packages Helm chart
- Generates release notes with installation instructions
- Creates GitHub Release
- Attaches Helm chart `.tgz` as release asset
- Marks as prerelease if tag contains `alpha`, `beta`, or `rc`

**Release notes include:**
- Installation instructions (Helm + operator image)
- Prerequisites list
- Links to documentation
- Changelog reference

### 4. Documentation Validation

**File:** `.github/workflows/docs.yaml`

**Triggers:**
- Push to `main` with changes in `docs/**` or `README.md`
- Pull requests with doc changes

**What it does:**
- Lints Markdown files with `markdownlint`
- Validates internal and external links
- Runs spell check (configurable)

**Configuration:**
- Markdown link check: `.github/markdown-link-check.json`
- Spell check: `.github/spellcheck-config.yaml`
- Custom dictionary: `.github/wordlist.txt`

## Using the Workflows

### Building Operator Images

**On main branch:**
```bash
git checkout main
git commit -m "feat: add new feature"
git push origin main
# Creates: ghcr.io/kapsa-project/kapsa:main
# Creates: ghcr.io/kapsa-project/kapsa:latest
# Creates: ghcr.io/kapsa-project/kapsa:main-<sha>
```

**On feature branch:**
```bash
git checkout -b feature/new-feature
git commit -m "feat: implement feature"
git push origin feature/new-feature
# Creates PR
# Image built but NOT pushed (PR validation only)
```

**For release:**
```bash
git tag v0.1.0
git push origin v0.1.0
# Creates: ghcr.io/kapsa-project/kapsa:0.1.0
# Creates: ghcr.io/kapsa-project/kapsa:0.1
# Creates: ghcr.io/kapsa-project/kapsa:0
```

### Publishing Helm Charts

**Automatic publishing:**
- Chart is automatically published to GHCR on merge to `main`
- Published as: `oci://ghcr.io/kapsa-project/charts/kapsa`

**Manual packaging:**
```bash
helm package helm/kapsa
# Creates: kapsa-<version>.tgz
```

**Testing locally:**
```bash
# Lint
helm lint helm/kapsa

# Template
helm template test-release helm/kapsa --debug

# Install in test cluster
kind create cluster --name kapsa-test
helm install kapsa helm/kapsa
```

### Creating Releases

**Version tagging:**
```bash
# Update Chart.yaml and version references
vim helm/kapsa/Chart.yaml  # Update version: 0.1.0
vim helm/kapsa/values.yaml  # Update image tag: "0.1.0"

# Commit version bump
git commit -am "chore: bump version to 0.1.0"
git push origin main

# Create and push tag
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

**Tag format:**
- Production: `v1.0.0`, `v1.2.3`
- Pre-release: `v1.0.0-alpha.1`, `v1.0.0-beta.2`, `v1.0.0-rc.1`

**GitHub Release will:**
- Create release page
- Attach Helm chart `.tgz`
- Generate release notes
- Mark as prerelease if applicable

### Using Published Images

**Operator image:**
```bash
# Latest
docker pull ghcr.io/kapsa-project/kapsa:latest

# Specific version
docker pull ghcr.io/kapsa-project/kapsa:0.1.0

# Branch
docker pull ghcr.io/kapsa-project/kapsa:main
```

**Helm chart:**
```bash
# Install from GHCR
helm install kapsa oci://ghcr.io/kapsa-project/charts/kapsa --version 0.1.0

# Pull chart
helm pull oci://ghcr.io/kapsa-project/charts/kapsa --version 0.1.0
```

## Secrets and Permissions

### Required Secrets

**None!** All workflows use `GITHUB_TOKEN` which is automatically provided.

### Required Permissions

Repository settings → Actions → General → Workflow permissions:
- ✅ Read and write permissions
- ✅ Allow GitHub Actions to create and approve pull requests

Package settings:
- ✅ Inherit access from repository (automatic)

## Cache and Optimization

### Docker Build Cache
- Uses GitHub Actions cache (`type=gha`)
- Speeds up subsequent builds
- Automatically managed

### Helm Chart Cache
- chart-testing caches Helm repos
- Dependencies cached between runs

## Debugging Workflows

### View workflow runs
```bash
# Using GitHub CLI
gh run list
gh run view <run-id>
gh run watch <run-id>
```

### Local testing

**Act (run GitHub Actions locally):**
```bash
# Install act
brew install act  # macOS
# or download from https://github.com/nektos/act

# Run workflow
act push -j build

# Run with secrets
act -s GITHUB_TOKEN=<token>
```

**Helm chart testing:**
```bash
# Install chart-testing
brew install chart-testing

# Lint
ct lint --config .github/ct.yaml --charts helm/kapsa

# Install in kind
kind create cluster
ct install --config .github/ct.yaml --charts helm/kapsa
```

## Troubleshooting

### Build fails with "permission denied"
- Check repository settings → Actions → Workflow permissions
- Ensure "Read and write permissions" is enabled

### Helm chart push fails
- Verify chart version is unique
- Check if chart already exists: `helm pull oci://ghcr.io/kapsa-project/charts/kapsa --version <version>`

### Image not appearing in packages
- Check package visibility (should be public)
- Verify workflow completed successfully
- Wait a few minutes for GHCR to sync

### Release not created
- Ensure tag starts with `v`
- Check if release already exists
- Verify `GITHUB_TOKEN` has write permissions

## Best Practices

1. **Always test locally** before pushing:
   ```bash
   helm lint helm/kapsa
   helm template test helm/kapsa
   ```

2. **Use semantic versioning**:
   - `v1.0.0` - major release
   - `v0.1.0` - minor release
   - `v0.0.1` - patch release
   - `v1.0.0-alpha.1` - pre-release

3. **Update CHANGELOG.md** before releasing

4. **Test in kind cluster** before tagging:
   ```bash
   kind create cluster --name kapsa-test
   helm install kapsa helm/kapsa
   kubectl get pods -n kapsa-system
   ```

5. **Review workflow logs** for warnings

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Container Registry](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
- [Helm OCI Support](https://helm.sh/docs/topics/registries/)
- [chart-testing](https://github.com/helm/chart-testing)
