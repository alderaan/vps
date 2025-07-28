#!/bin/bash
# Deploy ai-dev-server - Called by GitHub Actions workflow

set -e

echo "=== AI Dev Server Deployment Started ==="
echo "Timestamp: $(date)"

# Configuration
DOCKER_COMPOSE_DIR="/home/david/vps/docker-compose/ai-dev-server"
REGISTRY_URL="registry.correlion.ai/ai-dev-server:latest"
SERVICE_NAME="ai-dev-server"

# Change to docker-compose directory
cd "$DOCKER_COMPOSE_DIR"

echo "Current working directory: $(pwd)"

# Pull the latest image
echo "Pulling latest image: $REGISTRY_URL"
docker-compose pull

# Stop the current service
echo "Stopping current service..."
docker-compose down

# Start the service with new image
echo "Starting service with new image..."
docker-compose up -d

# Wait a moment for service to start
echo "Waiting for service to initialize..."
sleep 10

# Check service health
echo "Checking service health..."
if docker-compose ps | grep -q "Up.*healthy\|Up.*running"; then
    echo "✅ Service is running and healthy"
    
    # Show container status
    echo ""
    echo "Container status:"
    docker-compose ps
    
    # Test health endpoint if available
    if curl -f -s http://127.0.0.1:8080/health > /dev/null 2>&1; then
        echo "✅ Health check passed"
    else
        echo "⚠️  Health check failed - service may still be starting"
    fi
else
    echo "❌ Service failed to start properly"
    echo "Container logs:"
    docker-compose logs --tail=20
    exit 1
fi

echo ""
echo "=== AI Dev Server Deployment Complete ==="
echo "Timestamp: $(date)"