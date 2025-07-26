#!/bin/bash
set -e

echo "🚀 Deploying VPS infrastructure..."

# Update from git
echo "📥 Pulling latest changes..."
git pull origin main

# Deploy HostAgent service
echo "⚙️  Updating HostAgent systemd service..."
sudo cp host-agent/systemd/host-agent.service /etc/systemd/system/
sudo systemctl daemon-reload

# Install/update dependencies
echo "📦 Installing HostAgent dependencies..."
cd host-agent
uv sync
cd ..

# Restart services
echo "🔄 Restarting HostAgent service..."
sudo systemctl restart host-agent

# Check status
echo "✅ Checking service status..."
sudo systemctl status host-agent --no-pager -l

echo ""
echo "🎉 Deployment complete!"
echo "💡 Check logs with: sudo journalctl -u host-agent -f"