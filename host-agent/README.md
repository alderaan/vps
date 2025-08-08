# HostAgent

A secure FastAPI service for local host-level operations on VPS infrastructure. Runs locally on the VPS and provides authenticated HTTP endpoints for privileged tasks like backing up n8n workflows.

## Overview

HostAgent provides a secure API interface for Docker containers to request host-level operations. Currently supports n8n workflow backups to git repositories.

## Features

- **Secure Authentication**: Bearer token authentication for all operations
- **Docker Integration**: Accessible from Docker containers via host.docker.internal
- **Modern Stack**: Built with FastAPI, Pydantic, and uv package manager
- **Systemd Service**: Runs as a managed service with security restrictions
- **Health Monitoring**: Health check endpoint for service monitoring
- **n8n Search**: Fast ripgrep-powered search across n8n docs and TypeScript nodes
- **File Operations**: Secure file retrieval with path traversal protection

## Project Structure

```
host-agent/
├── src/host_agent/
│   ├── __init__.py
│   ├── main.py          # FastAPI app with auth & endpoints
│   ├── config.py        # Pydantic settings management 
│   └── backup.py        # Backup script execution
├── systemd/
│   └── host-agent.service  # Systemd service configuration
├── .env.example         # Configuration template
├── pyproject.toml       # uv dependency management
└── README.md
```

## API Endpoints

### Health Check
```http
GET /health
```
No authentication required. Returns service status.

**Response:**
```json
{
  "status": "healthy",
  "service": "HostAgent"
}
```

### n8n Backup
```http
POST /backup/n8n
Authorization: Bearer YOUR_TOKEN
```
Triggers n8n workflow backup using the existing backup script.

### n8n Documentation Search
```http
POST /search
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
```
Search n8n documentation and TypeScript nodes using ripgrep.

**Request Body:**
```json
{
  "query": "workflow trigger",
  "directory": "n8n-docs",
  "max_results": 30,
  "context_lines": 2
}
```

**Response:** Search results with file paths, line numbers, content matches, and context.

### File Retrieval
```http
POST /get_files
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
```
Retrieve full content of multiple files from n8n directories.

**Request Body:**
```json
{
  "directory": "n8nio", 
  "files": ["path/to/file1.ts", "path/to/file2.md"]
}
```

**Response:** File contents with metadata and any errors encountered.

**Success Response:**
```json
{
  "status": "success",
  "timestamp": "2025-01-26 15:30:45",
  "message": "N8N workflows backed up successfully",
  "output": "Backup process completed!"
}
```

**Error Response:**
```json
{
  "detail": "Backup operation failed: [error details]"
}
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BEARER_TOKEN` | *(required)* | Authentication token for API access |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `9000` | Server port |
| `BACKUP_SCRIPT_PATH` | `/home/david/backup-n8n-workflows.sh` | Path to backup script |

## Quick Start

### Local Development

```bash
# Clone and navigate to directory
cd vps/host-agent

# Copy and configure environment
cp .env.example .env
# Edit .env with your configuration

# Install dependencies
uv sync

# Run server
uv run python src/host_agent/main.py

# Test endpoints
curl http://127.0.0.1:9000/health
curl -X POST http://127.0.0.1:9000/backup/n8n \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Production Deployment

### Prerequisites

- Python 3.9+
- uv package manager
- Docker (for n8n container operations)
- Git (for backup operations)
- Existing backup-n8n-workflows.sh script

### Installation Steps

1. **Deploy via script (recommended):**
   ```bash
   cd /home/david/vps
   ./deploy.sh
   ```

2. **Or manual installation:**
   ```bash
   # Install uv if not present
   curl -LsSf https://astral.sh/uv/install.sh | sh
   source ~/.bashrc

   # Configure environment
   cd /home/david/vps/host-agent
   cp .env.example .env
   nano .env  # Add your configuration

   # Install dependencies
   uv sync

   # Install systemd service
   sudo cp systemd/host-agent.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable host-agent
   sudo systemctl start host-agent

   # Verify
   sudo systemctl status host-agent
   curl http://127.0.0.1:9000/health
   ```

## Docker Integration

### Container Access

HostAgent is configured to accept connections from Docker containers:

- Service binds to `0.0.0.0:9000` (configured in settings)
- Containers access via `http://host.docker.internal:9000`
- Bearer token authentication required

### Example from Container

```bash
curl -X POST http://host.docker.internal:9000/backup/n8n \
  -H "Authorization: Bearer $HOST_AGENT_BEARER_TOKEN"
```

## Security Configuration

### Systemd Service Security

The service runs with the following security restrictions:

- **User/Group**: Runs as `david` user (non-root)
- **Memory Limit**: 512MB
- **CPU Quota**: 50%
- **Filesystem Access**: Read-only home, strict system protection
- **Write Access**: Limited to specific paths for backups
- **Private Tmp**: Isolated temporary directory

### Network Security

- Port 9000 not exposed externally (UFW firewall)
- Bearer token required for all operations
- Service accessible only from localhost and Docker containers

## Monitoring

### Service Logs
```bash
# View live logs
sudo journalctl -u host-agent -f

# View recent logs
sudo journalctl -u host-agent -n 100
```

### Service Management
```bash
# Check status
sudo systemctl status host-agent

# Restart service
sudo systemctl restart host-agent

# Stop service
sudo systemctl stop host-agent
```

### Health Monitoring
```bash
# Manual check
curl http://127.0.0.1:9000/health

# Continuous monitoring
watch -n 5 curl -s http://127.0.0.1:9000/health
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs for errors
sudo journalctl -u host-agent -n 50

# Test configuration
cd /home/david/vps/host-agent
uv run python -c "from src.host_agent.config import settings; print('Config OK')"

# Check permissions
ls -la /home/david/vps/host-agent
ls -la /home/david/backup-n8n-workflows.sh
```

### Authentication Errors

- Verify `BEARER_TOKEN` in `.env` matches client requests
- Check for extra whitespace or special characters in token
- Ensure Authorization header format: `Bearer YOUR_TOKEN`

### Backup Failures

```bash
# Test backup script directly
bash /home/david/vps/backup-n8n-workflows.sh

# Check Docker access
docker ps | grep n8n

# Verify script permissions
ls -la /home/david/vps/backup-n8n-workflows.sh
```

### Container Connection Issues

- Verify HostAgent is running: `sudo systemctl status host-agent`
- Check binding address is `0.0.0.0` in config
- Test from container: `docker exec [container] curl http://host.docker.internal:9000/health`

## Development

### Adding New Endpoints

1. Add endpoint to `main.py`:
   ```python
   @app.post("/your-operation")
   async def your_operation(token: str = Depends(verify_token)):
       # Your logic here
       return {"status": "success"}
   ```

2. Add any new settings to `config.py`:
   ```python
   class Settings(BaseSettings):
       your_setting: str = "default_value"
   ```

3. Update and restart service:
   ```bash
   cd /home/david/vps
   ./deploy.sh
   ```

### Interactive API Documentation

When running locally, access interactive API docs at:
- Swagger UI: http://127.0.0.1:9000/docs
- ReDoc: http://127.0.0.1:9000/redoc

## Dependencies

- **fastapi** >= 0.116.1 - Web framework
- **pydantic-settings** >= 2.10.1 - Configuration management
- **python-dotenv** >= 1.1.1 - Environment file support
- **uvicorn** >= 0.35.0 - ASGI server

## License

This project is part of VPS infrastructure management tools.