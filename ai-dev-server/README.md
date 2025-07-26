# FastMCP + FastAPI Server

Combined FastAPI + FastMCP server providing both web API endpoints and MCP (Model Context Protocol) functionality in a single deployment.

## Tech Stack

- **FastMCP 2.10.6** - MCP protocol 1.12.0 implementation
- **FastAPI** - Web framework with OpenAPI docs
- **Python 3.11+** - Managed by uv package manager
- **Streamable HTTP Transport** - March 2025 MCP standard

## Quick Start

```bash
# Start server (background)
nohup uv run server.py > server.log 2>&1 & echo $!

# Kill server
pkill -f server.py

# Test endpoints
curl -s http://127.0.0.1:8080/health
curl -s http://127.0.0.1:8080/docs  # OpenAPI docs
```

## API Endpoints

**FastAPI Endpoints:**
- `/health` - Health check
- `/ready` - Readiness check  
- `/` - Service info
- `/auth` - Dev authentication
- `/docs` - OpenAPI documentation

**MCP Endpoint:** `/llm/mcp/`
- 3 tools: `hello_world`, `echo`, `get_status`
- Requires proper session management
- Uses JSON-RPC 2.0 protocol

## MCP Usage

### Adding to Claude Code

```bash
# Add server to Claude Code's MCP configuration
claude mcp add --transport http hello-world-server http://127.0.0.1:8080/llm/mcp
```

### Manual Testing via cURL

```bash
# 1. Initialize session  
curl -X POST http://127.0.0.1:8080/llm/mcp/ \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}'

# 2. Send initialized notification (extract session ID from response)
curl -X POST http://127.0.0.1:8080/llm/mcp/ \
  -H "mcp-session-id: SESSION_ID" \
  -d '{"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}'

# 3. List tools
curl -X POST http://127.0.0.1:8080/llm/mcp/ \
  -H "mcp-session-id: SESSION_ID" \
  -d '{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}'

# 4. Call tool
curl -X POST http://127.0.0.1:8080/llm/mcp/ \
  -H "mcp-session-id: SESSION_ID" \
  -d '{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "hello_world", "arguments": {}}}'
```

## Critical Implementation Notes

### FastAPI + FastMCP Integration Key Learnings

**1. Lifespan Management is Critical**
- Must pass `lifespan=mcp_app.lifespan` to FastAPI constructor
- Without this, MCP session management fails completely

**2. 307 Redirect Prevention**
- FastAPI's default `redirect_slashes=True` breaks MCP endpoints
- Always use `redirect_slashes=False` in FastAPI constructor
- Prevents `/llm/mcp` → `/llm/mcp/` redirect loops

**3. Correct Endpoint Path Structure**
- When mounting MCP app at `/llm`, the actual MCP endpoint is `/llm/mcp/`
- The trailing slash is required for streamable HTTP transport
- Mount path + `/mcp/` = actual MCP endpoint

**4. Required HTTP Headers for MCP**
- MCP streamable HTTP requires: `Accept: application/json, text/event-stream`
- Without both content types, requests return 406 Not Acceptable
- `Content-Type: application/json` also required

**5. Working FastAPI + FastMCP Pattern**
```python
mcp = FastMCP("Server Name")
mcp_app = mcp.http_app()
app = FastAPI(lifespan=mcp_app.lifespan, redirect_slashes=False)
app.mount("/llm", mcp_app)
# MCP endpoint: /llm/mcp/
```

**6. MCP Transport Methods**
- MCP supports 3 official transports: STDIO (local), SSE (deprecated), and Streamable HTTP (current standard)
- We use Streamable HTTP via `mcp.http_app()` which is the March 2025 best practice for remote servers

Streamable HTTP allows remote network access with session management, bidirectional communication (server can stream responses via SSE), JSON-RPC 2.0 protocol messaging, and stateful context preservation across requests. Unlike regular HTTP, it maintains persistent sessions with unique IDs and supports both immediate responses and streaming for long-running operations, making it ideal for AI agent integrations that need reliable context and real-time communication.

## Production Deployment with Authentication

### Setting up Caddy Reverse Proxy with Basic Auth

The server can be secured behind Caddy with HTTP Basic Authentication.

**1. Generate password hash:**
```bash
AI_DEV_SERVER_PASSWORD_HASH=$(caddy hash-password --plaintext your_password)
echo $AI_DEV_SERVER_PASSWORD_HASH
```

**2. Configure systemd environment:**
```bash
sudo systemctl edit caddy
```

Add the following content:
```ini
[Service]
Environment="AI_DEV_SERVER_PASSWORD_HASH=your_hash_from_step_1"
```

**3. Add to Caddyfile:**
```caddyfile
ai-dev.your-domain.com {
    encode gzip zstd
    
    basic_auth /llm/* {
        admin {env.AI_DEV_SERVER_PASSWORD_HASH}
    }
    
    reverse_proxy localhost:8080
    
    header {
        Strict-Transport-Security "max-age=31536000;"
        X-XSS-Protection "1; mode=block"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        Referrer-Policy "strict-origin-when-cross-origin"
    }
}
```

**4. Restart services:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart caddy
```

**5. Access with authentication:**
- URL: `https://ai-dev.your-domain.com/llm/mcp/`
- Add `Authorization: Basic base64(admin:your_password)` header to all MCP requests

## Docker Deployment

### Standard Deployment

```bash
# Deploy via VPS deployment script
cd /home/david/vps
./deploy.sh

# Or manually with Docker Compose
cd docker-compose/ai-dev-server
docker-compose up -d

# Health check
curl http://localhost:8080/health
```

### Docker Networking Requirements

The ai-dev-server container needs to communicate with host services (HostAgent):

```yaml
# docker-compose/ai-dev-server/docker-compose.yml
services:
  ai-dev-server:
    container_name: ai-dev-server
    extra_hosts:
      - "host.docker.internal:host-gateway"  # Enable host access
    networks:
      - supabase  # Connect to supabase network for service discovery
    environment:
      - HOST_AGENT_BEARER_TOKEN=${HOST_AGENT_BEARER_TOKEN}
```

**Host Service Communication:**
- Uses `host.docker.internal:9000` to reach HostAgent
- HostAgent must bind to `0.0.0.0:9000` (not `127.0.0.1`)
- Required for n8n workflow backup functionality

### Manual Build

```bash
# Build manually
docker build -t ai-dev-server .
docker run -p 127.0.0.1:8080:8080 \
  --add-host host.docker.internal:host-gateway \
  ai-dev-server
```

## Package Management

Uses `uv` package manager:
- Dependencies: `pyproject.toml`
- Lock file: `uv.lock`
- Virtual environment: `.venv/`