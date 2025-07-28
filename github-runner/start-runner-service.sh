#!/bin/bash
# Start GitHub Actions Runner as a systemd service

set -e

RUNNER_USER="david"
RUNNER_HOME="/home/$RUNNER_USER"
RUNNER_DIR="$RUNNER_HOME/actions-runner"
SERVICE_NAME="github-actions-runner"

echo "=== Starting GitHub Actions Runner Service ==="

# Check if runner is configured
if [ ! -f "$RUNNER_DIR/.runner" ]; then
    echo "Error: Runner not configured yet!"
    echo "Please run the GitHub configuration command first:"
    echo "cd $RUNNER_DIR && ./config.sh --url https://github.com/OWNER/REPO --token YOUR_TOKEN"
    exit 1
fi

# Install the service
echo "Installing runner service..."
cd "$RUNNER_DIR"
sudo ./svc.sh install

# Start the service
echo "Starting runner service..."
sudo ./svc.sh start

# Check status
echo "Checking service status..."
sudo ./svc.sh status

echo ""
echo "=== Service Setup Complete ==="
echo ""
echo "Commands to manage the service:"
echo "  Status:  sudo ./svc.sh status"
echo "  Start:   sudo ./svc.sh start"
echo "  Stop:    sudo ./svc.sh stop"
echo "  Restart: sudo ./svc.sh stop && sudo ./svc.sh start"
echo ""
echo "Service will auto-start on system boot."