# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important - Don't Remove

### FastAPI + FastMCP Integration Key Learnings

**1. Lifespan Management is Critical**
- Must pass `lifespan=mcp_app.lifespan` to FastAPI constructor
- Without this, MCP session management fails completely

**2. 307 Redirect Prevention**
- FastAPI's default `redirect_slashes=True` breaks MCP endpoints
- Always use `redirect_slashes=False` in FastAPI constructor
- Prevents `/llm/mcp` → `/llm/mcp/` redirect loops
- Note: FastMCP itself may still show 307 redirects from `/llm/mcp` → `/llm/mcp/` which is expected behavior

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

## Server Implementation

The `server.py` integrates FastAPI and FastMCP:

```python
mcp = FastMCP("Server Name")
mcp_app = mcp.http_app()
app = FastAPI(lifespan=mcp_app.lifespan, redirect_slashes=False)
app.mount("/llm", mcp_app)
# MCP endpoint: /llm/mcp/
```

## Key Commands for Claude Code

**Environment Variables:**
```bash
export MCP_BEARER_TOKEN="your-secure-token-here"
```

**Claude MCP Add Command:**
```bash
claude mcp add --transport http ai-dev-server https://ai-dev.correlion.ai/llm/mcp/ --header "Authorization: Bearer $MCP_BEARER_TOKEN"
```

**Running server without hanging terminal:**
```bash
nohup uv run server.py > server.log 2>&1 & echo $!
pkill -f server.py
```