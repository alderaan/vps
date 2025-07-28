# GitHub Actions Self-Hosted Runner Setup

This directory contains scripts to set up and manage a GitHub Actions self-hosted runner on the VPS for automated deployments.

## Files

- `setup-runner.sh` - Initial runner installation and setup
- `start-runner-service.sh` - Configure runner as systemd service
- `deploy-ai-dev-server.sh` - Deployment script called by GitHub Actions
- `README.md` - This documentation

## Setup Process

### 1. Install Runner
```bash
# On VPS as user 'david'
cd /home/david/vps/github-runner
chmod +x *.sh
./setup-runner.sh
```

### 2. Configure Runner
1. Go to GitHub repository Settings > Actions > Runners
2. Click "New self-hosted runner"
3. Follow the configuration commands shown, example:
```bash
cd /home/david/actions-runner
./config.sh --url https://github.com/OWNER/REPO --token GITHUB_TOKEN
```

### 3. Start Service
```bash
./start-runner-service.sh
```

### 4. Create GitHub Workflow
Add `.github/workflows/deploy-ai-dev-server.yml` to your repository (see below).

## GitHub Workflow File

Create this file in your repository:

```yaml
# .github/workflows/deploy-ai-dev-server.yml
name: Deploy AI Dev Server

on:
  push:
    branches: [ main ]
    paths: [ 'vps/ai-dev-server/**' ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: self-hosted
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
      
    - name: Build and push Docker image
      run: |
        cd vps/ai-dev-server
        docker buildx build --platform linux/amd64 -t registry.correlion.ai/ai-dev-server:latest --push .
        
    - name: Deploy to VPS
      run: |
        /home/david/vps/github-runner/deploy-ai-dev-server.sh
```

## Environment Variables

Ensure these are set on the VPS:
- `MCP_BEARER_TOKEN`
- `N8N_BASE_URL`
- `N8N_API_KEY`
- `HOST_AGENT_BEARER_TOKEN`

## Troubleshooting

### Check Runner Status
```bash
cd /home/david/actions-runner
sudo ./svc.sh status
```

### View Runner Logs
```bash
sudo journalctl -u actions.runner.* -f
```

### Restart Runner
```bash
cd /home/david/actions-runner
sudo ./svc.sh stop
sudo ./svc.sh start
```

### Test Deployment Manually
```bash
/home/david/vps/github-runner/deploy-ai-dev-server.sh
```

## Security Notes

- Runner runs with user 'david' privileges
- Has access to Docker daemon via user group
- Can access local docker-compose files
- No external network access required for deployment
- Registry push requires Docker registry credentials (configured via docker login)