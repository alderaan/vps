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

# Enable auto-start on boot
echo "Enabling auto-start on system boot..."
SERVICE_NAME=$(sudo systemctl list-units --type=service | grep actions.runner | awk '{print $1}' | head -n1)
if [ -n "$SERVICE_NAME" ]; then
    sudo systemctl enable "$SERVICE_NAME"
    echo "✅ Auto-start enabled for $SERVICE_NAME"
else
    echo "⚠️  Could not find service name for auto-start. Run manually after setup:"
    echo "   sudo systemctl enable actions.runner.*"
fi

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
echo "✅ Service will auto-start on system boot."