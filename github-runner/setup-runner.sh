#!/bin/bash
# Setup GitHub Actions Self-Hosted Runner on VPS

set -e

echo "=== GitHub Actions Self-Hosted Runner Setup ==="

# Configuration
RUNNER_USER="david"
RUNNER_HOME="/home/$RUNNER_USER"
RUNNER_DIR="$RUNNER_HOME/actions-runner"
RUNNER_VERSION="2.321.0"  # Update to latest version as needed

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root. Run as user: $RUNNER_USER"
   exit 1
fi

# Create runner directory
echo "Creating runner directory at $RUNNER_DIR..."
mkdir -p "$RUNNER_DIR"
cd "$RUNNER_DIR"

# Download and extract GitHub Actions runner
echo "Downloading GitHub Actions runner v$RUNNER_VERSION..."
curl -o actions-runner-linux-x64-$RUNNER_VERSION.tar.gz -L "https://github.com/actions/runner/releases/download/v$RUNNER_VERSION/actions-runner-linux-x64-$RUNNER_VERSION.tar.gz"

echo "Extracting runner..."
tar xzf ./actions-runner-linux-x64-$RUNNER_VERSION.tar.gz

# Install dependencies
echo "Installing dependencies..."
sudo ./bin/installdependencies.sh

echo ""
echo "=== Runner Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Go to your GitHub repository settings"
echo "2. Navigate to Settings > Actions > Runners"
echo "3. Click 'New self-hosted runner'"
echo "4. Follow the configuration commands shown (./config.sh)"
echo "5. Run this script to start the runner service:"
echo "   ./start-runner-service.sh"
echo ""
echo "Runner directory: $RUNNER_DIR"