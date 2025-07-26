#!/bin/bash

# N8N Workflow Backup Script
# This script exports workflows from N8N container and backs them up to git

# Configuration
BACKUP_DIR="/home/david/n8n-workflows-backup"
EXPORT_PATH="/tmp/workflows"

# Function to find N8N container name
find_n8n_container() {
    local container_name=$(docker ps --format "table {{.Names}}\t{{.Image}}" | grep "n8nio/n8n" | awk '{print $1}' | head -1)
    if [ -z "$container_name" ]; then
        echo "Error: No running container found with n8nio/n8n image"
        exit 1
    fi
    echo "$container_name"
}

# Get container name automatically
echo "Finding N8N container..."
CONTAINER_NAME=$(find_n8n_container)
echo "Found container: $CONTAINER_NAME"

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Creating backup directory..."
    mkdir -p "$BACKUP_DIR"
    cd "$BACKUP_DIR"
    git init
    echo "# N8N Workflows Backup" > README.md
    echo "Automated backup of N8N workflows" >> README.md
    git add README.md
    git commit -m "Initial commit"
    echo "Please add your git remote: git remote add origin <your-repo-url>"
    echo "Then run this script again."
    exit 0
fi

# Export workflows from N8N container
echo "Exporting workflows..."
docker exec $CONTAINER_NAME n8n export:workflow --all --backup --output=$EXPORT_PATH

# Copy exported files to git directory
echo "Copying to git repository..."
docker cp $CONTAINER_NAME:$EXPORT_PATH/. $BACKUP_DIR/

# Clean up temp files in container
docker exec $CONTAINER_NAME rm -rf $EXPORT_PATH

# Git operations
cd $BACKUP_DIR
git add .
if git diff --staged --quiet; then
    echo "No changes to commit"
else
    git commit -m "Workflow backup - $(date '+%Y-%m-%d %H:%M:%S')"
    if git remote get-url origin >/dev/null 2>&1; then
        git push
        echo "Backup completed and pushed to Git"
    else
        echo "Backup committed locally. No remote configured for push."
    fi
fi

echo "Backup process completed!"