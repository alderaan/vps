#!/bin/bash
# Deploy n8n-workflows - Called by GitHub Actions workflow

set -e

echo "=== N8N Workflows Deployment Started ==="
echo "Timestamp: $(date)"

# Configuration
DOCKER_COMPOSE_DIR="/home/david/vps/docker-compose/n8n-workflows"
REGISTRY_URL="registry.correlion.ai/n8n-workflows:latest"
SERVICE_NAME="n8n-workflows"

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
sleep 15

# Check service health
echo "Checking service health..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ Service is running"
    
    # Show container status
    echo ""
    echo "Container status:"
    docker-compose ps
    
    # Test health endpoint
    if curl -f -s http://127.0.0.1:8001/health > /dev/null 2>&1; then
        echo "✅ Health check passed"
        
        # Test API endpoint
        if curl -f -s http://127.0.0.1:8001/api/stats > /dev/null 2>&1; then
            echo "✅ API endpoint responding"
            
            # Show quick stats
            STATS=$(curl -s http://127.0.0.1:8001/api/stats)
            TOTAL=$(echo "$STATS" | grep -o '"total":[0-9]*' | cut -d':' -f2)
            echo "📊 Database contains $TOTAL workflows"
        else
            echo "⚠️ API endpoint not responding yet"
        fi
    else
        echo "⚠️ Health check failed - service may still be starting"
    fi
else
    echo "❌ Service failed to start properly"
    echo "Container logs:"
    docker-compose logs --tail=20
    exit 1
fi

echo ""
echo "=== N8N Workflows Deployment Complete ==="
echo "Timestamp: $(date)"