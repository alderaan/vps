# Deployment Automation Plan - GitHub Actions Self-Hosted Runner

## Overview
Automate the ai-dev-server deployment pipeline using a GitHub Actions self-hosted runner on the VPS. This eliminates manual docker-compose commands and provides a professional CI/CD workflow at zero cost.

## Current Manual Process
1. `make docker-deploy` (builds & pushes to registry.correlion.ai)
2. SSH to VPS
3. `cd /path/to/docker-compose/ai-dev-server`
4. `docker-compose pull`
5. `docker-compose down && docker-compose up -d`

## Automated Process (Target)
1. Push code to GitHub
2. GitHub triggers workflow on VPS runner
3. Runner automatically builds, pushes, pulls, and redeploys
4. Zero manual intervention

## Architecture
```
Developer → Git Push → GitHub → Self-Hosted Runner (VPS) → Auto Deploy
```

## Implementation Components

### 1. Self-Hosted Runner Setup
- **Location:** `/home/david/actions-runner/` on VPS
- **Service:** Systemd service for auto-start
- **Registration:** One-time GitHub runner registration

### 2. GitHub Workflow
- **File:** `.github/workflows/deploy-ai-dev-server.yml`
- **Triggers:** Push to main branch, manual dispatch
- **Steps:** Build → Push → Pull → Deploy

### 3. VPS Scripts
- **Location:** `vps/github-runner/`
- **Files:**
  - `setup-runner.sh` - Initial runner installation
  - `deploy-ai-dev-server.sh` - Deployment script
  - `runner-service.sh` - Systemd service management

## Security Considerations
- Runner runs on VPS (secure local network)
- Docker registry credentials via environment variables
- No external secrets needed (runner has local docker access)

## Benefits
- **Free:** No GitHub Actions usage costs
- **Fast:** Local builds and deployments
- **Secure:** No external runner access needed
- **Professional:** Standard CI/CD workflow
- **Scalable:** Can add more services easily

## Setup Steps
1. Install runner software on VPS
2. Register runner with GitHub repository
3. Create GitHub workflow file
4. Configure environment variables
5. Test deployment
6. Enable systemd service for auto-start

## Fallback
Manual deployment via existing Makefile remains available as backup option.

## Next Steps
1. Create `vps/github-runner/` directory with setup scripts
2. Implement GitHub workflow file
3. Test deployment pipeline
4. Document operational procedures