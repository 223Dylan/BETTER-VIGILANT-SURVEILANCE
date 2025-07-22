# CI/CD Pipeline

This repository includes a comprehensive CI/CD pipeline using GitHub Actions with the following workflows:

## Workflows

### 1. **CI/CD Pipeline** (`.github/workflows/ci-cd.yml`)
**Triggers:** Push to `master`/`main` branches, Pull Requests
- **Backend Testing:** Python 3.9, 3.10, 3.11 compatibility
- **Frontend Testing:** Node.js 18, ESLint, TypeScript compilation
- **Security Scanning:** Trivy vulnerability scanner
- **Docker Build:** Multi-platform images (amd64, arm64)
- **Deployment:** Automatic deployment to production (configurable)

### 2. **Release** (`.github/workflows/release.yml`)
**Triggers:** Git tags starting with `v*` (e.g., `v1.0.0`)
- Builds and publishes Docker images
- Creates GitHub releases automatically
- Tags images with version numbers

### 3. **Code Quality** (`.github/workflows/code-quality.yml`)
**Triggers:** Pull Requests
- **Python Analysis:** Bandit security scan, Safety vulnerability check, Pylint
- **Frontend Analysis:** TypeScript checks, dependency analysis, bundle size
- **SonarCloud Integration:** Code quality metrics and technical debt analysis

### 4. **Dependabot** (`.github/dependabot.yml`)
**Triggers:** Weekly schedule
- **Monday:** Python dependencies (pip)
- **Tuesday:** Node.js dependencies (npm)
- **Wednesday:** Docker dependencies
- **Thursday:** GitHub Actions dependencies

## Setup Instructions

### 1. Repository Secrets
Add these secrets in your GitHub repository settings:

```bash
# Required for SonarCloud (optional)
SONAR_TOKEN=your_sonarcloud_token

# Required for deployment (if using SSH deployment)
HOST=your_server_host
USERNAME=your_server_username
KEY=your_private_key
```

### 2. Enable Container Registry
The workflows use GitHub Container Registry (ghcr.io) which is enabled by default.

### 3. Protection Rules (Recommended)
Set up branch protection rules for `master`/`main`:
- Require status checks to pass
- Require up-to-date branches
- Include administrators

## Docker Images

Docker images are automatically built and pushed to:
```
ghcr.io/223dylan/better-vigilant-surveilance:latest
ghcr.io/223dylan/better-vigilant-surveilance:v1.0.0
```

## Customization

### Frontend Scripts
Ensure your `package.json` includes:
```json
{
  "scripts": {
    "build": "react-scripts build",
    "test": "react-scripts test",
    "lint": "eslint src --ext .js,.jsx,.ts,.tsx"
  }
}
```

### Python Requirements
Make sure your `requirements.txt` includes all necessary dependencies.

### Deployment
To enable automatic deployment:
1. Uncomment the SSH deployment section in `ci-cd.yml`
2. Add the required secrets (HOST, USERNAME, KEY)
3. Modify the deployment script for your specific needs

## Quality Gates

The pipeline includes several quality gates:
- All tests must pass
- Code must pass linting checks
- Security scans must not find critical issues
- Docker builds must succeed
- TypeScript compilation must succeed

## Creating Releases

To create a new release:
```bash
git tag v1.0.0
git push origin v1.0.0
```

This will trigger the release workflow and create:
- A new GitHub release
- Docker images tagged with the version number
