#!/bin/bash

# 🚀 N8N Workflow Documentation - Node.js Launcher
# Quick setup and launch script

echo "🚀 N8N Workflow Documentation - Node.js Implementation"
echo "======================================================"

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 19+ first."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node --version)
echo "📦 Node.js version: $NODE_VERSION"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Initialize database if it doesn't exist
if [ ! -f "database/workflows.db" ]; then
    echo "🔄 Initializing database..."
    npm run init
fi

# Check if workflows directory has files
WORKFLOW_COUNT=$(find workflows -name "*.json" -type f | wc -l)
echo "📁 Found $WORKFLOW_COUNT workflow files"

if [ $WORKFLOW_COUNT -gt 0 ]; then
    echo "🔄 Indexing workflows..."
    npm run index
else
    echo "⚠️  No workflow files found in workflows/ directory"
    echo "   Place your N8N workflow JSON files in the workflows/ directory"
fi

# Start the server
echo "🌐 Starting server..."
echo "   Server will be available at: http://localhost:8000"
echo "   Press Ctrl+C to stop the server"
echo ""

npm start 