# HostAgent

A modern, secure FastAPI service for local host-level operations on VPS infrastructure. Designed to run locally on the VPS and provide authenticated HTTP endpoints for privileged tasks like backing up N8N workflows.

## Features

- **Secure**: Bearer token authentication, localhost-only binding
- **Modern**: Built with FastAPI, uv, and Pydantic settings
- **Clean**: Proper Python package structure with type hints
- **Robust**: Comprehensive error handling and logging
- **Observable**: Health check endpoint for monitoring
- **Configurable**: Environment-based configuration
- **Extensible**: Easy to add new host operations

## Project Structure

```
host-agent/
├── src/host_agent/
│   ├── __init__.py
│   ├── main.py          # FastAPI app with auth & endpoints
│   ├── config.py        # Pydantic settings management 
│   └── backup.py        # Calls existing backup scripts
├── systemd/
│   └── host-agent.service  # Modern systemd service
├── .env.example         # Configuration template
└── pyproject.toml       # uv dependency management
```

## Prerequisites

- Python 3.9+
- [uv](https://github.com/astral-sh/uv) package manager
- Docker (for N8N container operations)
- Git (for backup operations)
- Existing `backup-n8n-workflows.sh` script

## Local Development

1. **Setup:**
   ```bash
   cd vps/host-agent
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Run locally:**
   ```bash
   uv run python src/host_agent/main.py
   ```

4. **Test endpoints:**
   ```bash
   # Health check
   curl http://127.0.0.1:9000/health
   
   # Backup (requires Bearer token)
   curl -X POST http://127.0.0.1:9000/backup/n8n \
     -H "Authorization: Bearer YOUR_TOKEN"
   
   # Interactive API docs
   open http://127.0.0.1:9000/docs
   ```

## VPS Deployment

### Quick Deploy (Recommended)

After initial setup, use the deploy script for easy updates:

```bash
cd /home/david/vps
./deploy.sh
```

### Initial Setup

#### 1. Clone Project to VPS

```bash
# On VPS - one time setup
cd /home/david
git clone git@github.com:yourusername/vps.git
```

#### 2. Configure Environment

```bash
# On VPS
cd /home/david/vps/host-agent
cp .env.example .env
nano .env  # Add your real configuration
```

**Required .env variables:**
```bash
BEARER_TOKEN=your_secure_random_token_here
HOST=127.0.0.1
PORT=9000
BACKUP_SCRIPT_PATH=/home/david/vps/backup-n8n-workflows.sh
```

#### 3. Install Dependencies

```bash
# Ensure uv is installed
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Install dependencies
uv sync
```

#### 4. Setup Systemd Service

```bash
# Copy service file
sudo cp systemd/host-agent.service /etc/systemd/system/

# Edit service file paths if needed
sudo nano /etc/systemd/system/host-agent.service

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable host-agent
sudo systemctl start host-agent

# Check status
sudo systemctl status host-agent
```

#### 5. Verify Installation

```bash
# Check service is running
curl http://127.0.0.1:9000/health

# Test backup (replace TOKEN)
curl -X POST http://127.0.0.1:9000/backup/n8n \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## API Endpoints

### Health Check
```http
GET /health
```
Returns service status. No authentication required.

**Response:**
```json
{
  "status": "healthy",
  "service": "HostAgent"
}
```

### N8N Backup
```http
POST /backup/n8n
Authorization: Bearer YOUR_TOKEN
```
Triggers N8N workflow backup using the existing backup script.

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
  "detail": "Backup operation failed: [error details]",
  "timestamp": "2025-01-26 15:30:45"
}
```

## Configuration

All configuration is handled via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `BEARER_TOKEN` | *(required)* | Authentication token for API access |
| `HOST` | `127.0.0.1` | Server bind address (keep localhost for security) |
| `PORT` | `9000` | Server port |
| `BACKUP_SCRIPT_PATH` | `/home/david/vps/backup-n8n-workflows.sh` | Path to backup script |

## Security Features

- **Local-only binding**: Service only accepts connections from localhost
- **Bearer token authentication**: All operations require valid token
- **Systemd security**: Service runs with restricted permissions
- **Resource limits**: Memory and CPU limits configured
- **No privilege escalation**: Runs as regular user with Docker group access

## Monitoring & Logs

```bash
# View service logs
sudo journalctl -u host-agent -f

# Check service status
sudo systemctl status host-agent

# Monitor health endpoint
watch -n 5 curl -s http://127.0.0.1:9000/health
```

## Extending HostAgent

To add new operations:

1. **Add endpoint to `main.py`:**
   ```python
   @app.post("/your-operation")
   async def your_operation(token: str = Depends(verify_token)):
       # Your logic here
       return {"status": "success"}
   ```

2. **Add configuration if needed:**
   ```python
   # In config.py
   class Settings(BaseSettings):
       your_setting: str = "default_value"
   ```

3. **Restart service:**
   ```bash
   sudo systemctl restart host-agent
   ```

## Troubleshooting

### Service won't start
```bash
# Check service logs
sudo journalctl -u host-agent -n 50

# Check configuration
uv run python -c "import sys; sys.path.append('src'); from host_agent.config import settings; print('Config OK')"
```

### Backup fails
```bash
# Test backup script directly
bash /home/david/vps/backup-n8n-workflows.sh

# Check Docker access
docker ps | grep n8n
```

### Local development import errors
The code handles both package imports and direct execution. If you get import errors:
```bash
# Run with explicit path
PYTHONPATH=src uv run python -m host_agent.main

# Or run directly
uv run python src/host_agent/main.py
```

### Authentication errors
- Verify `BEARER_TOKEN` in `.env` matches client requests
- Check token doesn't have extra whitespace or special characters

## License

This project is part of VPS infrastructure management tools.