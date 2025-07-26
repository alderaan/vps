#!/usr/bin/env python3
"""
Combined FastAPI + FastMCP server for development and testing.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastmcp import FastMCP
import uvicorn
import asyncio
import logging
import os
import httpx
import subprocess
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bearer token for authentication - read from environment
BEARER_TOKEN = os.getenv("MCP_BEARER_TOKEN")
if not BEARER_TOKEN:
    logger.error("MCP_BEARER_TOKEN environment variable is required")
    raise ValueError("MCP_BEARER_TOKEN environment variable must be set")

# n8n configuration
N8N_BASE_URL = os.getenv("N8N_BASE_URL", "http://localhost:5678")
N8N_API_KEY = os.getenv("N8N_API_KEY")

class N8nClient:
    """Client for interacting with n8n API."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "X-N8N-API-KEY": api_key,
            "Content-Type": "application/json"
        }
    
    async def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make HTTP request to n8n API."""
        url = f"{self.base_url}/api/v1{endpoint}"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data if data else None,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"n8n API request failed: {e}")
                raise Exception(f"n8n API error: {str(e)}")
    
    async def list_workflows(self) -> List[Dict]:
        """Get list of all workflows."""
        response = await self._request("GET", "/workflows")
        # n8n API returns {data: [...]} format
        if isinstance(response, dict) and "data" in response:
            return response["data"]
        return response
    
    async def get_workflow(self, workflow_id: str) -> Dict:
        """Get specific workflow by ID."""
        return await self._request("GET", f"/workflows/{workflow_id}")
    
    async def create_workflow(self, workflow_data: Dict) -> Dict:
        """Create new workflow."""
        return await self._request("POST", "/workflows", workflow_data)
    
    async def update_workflow(self, workflow_id: str, workflow_data: Dict) -> Dict:
        """Update existing workflow."""
        return await self._request("PUT", f"/workflows/{workflow_id}", workflow_data)
    
    async def delete_workflow(self, workflow_id: str) -> Dict:
        """Delete workflow."""
        return await self._request("DELETE", f"/workflows/{workflow_id}")
    
    async def activate_workflow(self, workflow_id: str) -> Dict:
        """Activate workflow."""
        return await self._request("POST", f"/workflows/{workflow_id}/activate")
    
    async def deactivate_workflow(self, workflow_id: str) -> Dict:
        """Deactivate workflow."""
        return await self._request("POST", f"/workflows/{workflow_id}/deactivate")

# Create FastMCP server
mcp = FastMCP("Hello World Development Server")


@mcp.tool
def hello_world() -> str:
    """Returns a simple Hello World greeting."""
    return "Hello World from FastMCP!"


@mcp.tool
def echo(message: str) -> str:
    """Echoes back the provided message."""
    return f"Echo: {message}"


@mcp.tool
def get_status() -> dict:
    """Returns server status information."""
    return {
        "status": "running",
        "server": "FastMCP Development Server",
        "transport": "http",
    }


# n8n workflow management tools
def _get_n8n_client() -> N8nClient:
    """Get configured n8n client."""
    if not N8N_API_KEY:
        raise Exception("N8N_API_KEY environment variable is required")
    return N8nClient(N8N_BASE_URL, N8N_API_KEY)


@mcp.tool
async def n8n_list_workflows() -> List[Dict]:
    """List all n8n workflows."""
    client = _get_n8n_client()
    workflows = await client.list_workflows()
    
    # Return only essential fields to reduce output size
    return [
        {
            "id": w.get("id"),
            "name": w.get("name"),
            "active": w.get("active"),
            "isArchived": w.get("isArchived"),
            "createdAt": w.get("createdAt"),
            "updatedAt": w.get("updatedAt")
        }
        for w in workflows
    ]


@mcp.tool
async def n8n_get_workflow(workflow_id: str) -> Dict:
    """Get specific n8n workflow by ID."""
    client = _get_n8n_client()
    return await client.get_workflow(workflow_id)


@mcp.tool
async def n8n_create_workflow(name: str, nodes: List[Dict], connections: Dict, settings: Optional[Dict] = None) -> Dict:
    """Create new n8n workflow.
    
    Args:
        name: Workflow name
        nodes: List of workflow nodes
        connections: Node connections configuration
        settings: Optional workflow settings
    """
    client = _get_n8n_client()
    workflow_data = {
        "name": name,
        "nodes": nodes,
        "connections": connections,
        "settings": settings or {}
    }
    return await client.create_workflow(workflow_data)


@mcp.tool
async def n8n_update_workflow(workflow_id: str, name: Optional[str] = None, nodes: Optional[List[Dict]] = None, 
                             connections: Optional[Dict] = None, settings: Optional[Dict] = None) -> Dict:
    """Update existing n8n workflow.
    
    Args:
        workflow_id: ID of workflow to update
        name: New workflow name (optional)
        nodes: New nodes list (optional)
        connections: New connections (optional)
        settings: New settings (optional)
    """
    client = _get_n8n_client()
    
    # Get current workflow to merge updates
    current = await client.get_workflow(workflow_id)
    
    workflow_data = {
        "name": name or current.get("name"),
        "nodes": nodes or current.get("nodes", []),
        "connections": connections or current.get("connections", {}),
        "settings": settings or current.get("settings", {})
    }
    
    return await client.update_workflow(workflow_id, workflow_data)


@mcp.tool
async def n8n_delete_workflow(workflow_id: str) -> Dict:
    """Delete n8n workflow by ID."""
    client = _get_n8n_client()
    return await client.delete_workflow(workflow_id)


@mcp.tool
async def n8n_activate_workflow(workflow_id: str) -> Dict:
    """Activate n8n workflow to start execution."""
    client = _get_n8n_client()
    return await client.activate_workflow(workflow_id)


@mcp.tool
async def n8n_deactivate_workflow(workflow_id: str) -> Dict:
    """Deactivate n8n workflow to stop execution."""
    client = _get_n8n_client()
    return await client.deactivate_workflow(workflow_id)


@mcp.tool
async def n8n_search_workflows(query: str) -> List[Dict]:
    """Search n8n workflows by name or description."""
    client = _get_n8n_client()
    workflows = await client.list_workflows()
    
    # Simple text search in name and description
    query_lower = query.lower()
    matches = []
    
    for workflow in workflows:
        name = workflow.get("name", "").lower()
        description = workflow.get("description", "").lower()
        
        if query_lower in name or query_lower in description:
            matches.append(workflow)
    
    return matches


@mcp.tool
async def n8n_backup_workflows() -> Dict:
    """Run the n8n workflow backup via HostAgent API to backup all workflows to git."""
    try:
        # Get HostAgent bearer token from environment
        host_agent_token = os.getenv("HOST_AGENT_BEARER_TOKEN")
        if not host_agent_token:
            return {
                "success": False,
                "error": "HOST_AGENT_BEARER_TOKEN environment variable is required"
            }
        
        # Call HostAgent backup endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://host.docker.internal:9000/backup/n8n",
                headers={
                    "Authorization": f"Bearer {host_agent_token}",
                    "Content-Type": "application/json"
                },
                timeout=300  # 5 minute timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "status": result.get("status"),
                    "timestamp": result.get("timestamp"),
                    "message": result.get("message"),
                    "output": result.get("output")
                }
            else:
                error_detail = response.text
                return {
                    "success": False,
                    "error": f"HostAgent API error ({response.status_code}): {error_detail}"
                }
                
    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "HostAgent backup request timed out after 5 minutes"
        }
    except httpx.ConnectError:
        return {
            "success": False,
            "error": "Could not connect to HostAgent service at http://host.docker.internal:9000"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error calling HostAgent: {str(e)}"
        }


# Create the MCP's ASGI app (following FastMCP docs exactly)
mcp_app = mcp.http_app()

# Create FastAPI app with MCP lifespan (following FastMCP docs exactly)
app = FastAPI(
    title="FastMCP Development Server",
    description="Combined FastAPI + FastMCP server for development and testing",
    version="0.1.0",
    lifespan=mcp_app.lifespan,
    redirect_slashes=False,  # Prevents 307 redirects
)

# Add CORS middleware for browser testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],  # Required for MCP browser clients
)


# Authentication middleware - accepts both Bearer tokens and Basic auth passthrough
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Middleware to check authentication for MCP endpoints."""
    # Only protect /llm paths (MCP endpoints)
    if request.url.path.startswith("/llm"):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            logger.warning(f"Missing Authorization header for {request.url.path}")
            return JSONResponse(
                {"error": "Missing Authorization header"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Accept Bearer tokens
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            if token == BEARER_TOKEN:
                logger.info(f"Bearer token validated for {request.url.path}")
            else:
                logger.warning(f"Invalid Bearer token for {request.url.path}")
                return JSONResponse(
                    {"error": "Invalid Bearer token"},
                    status_code=401,
                    headers={"WWW-Authenticate": "Bearer"},
                )
        # Accept Basic auth (passthrough from Caddy)
        elif auth_header.startswith("Basic "):
            # If request reaches here, Caddy already validated basic auth
            logger.info(f"Basic auth validated by Caddy for {request.url.path}")
        else:
            logger.warning(
                f"Invalid Authorization header format for {request.url.path}"
            )
            return JSONResponse(
                {"error": "Invalid Authorization header format"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )

    response = await call_next(request)
    return response


# FastAPI health check endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    return {"status": "healthy", "service": "fastmcp-combined"}


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return {"status": "ready", "mcp": "available"}


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "FastMCP Development Server",
        "mcp_endpoint": "/llm/mcp",
        "health_check": "/health",
        "docs": "/docs",
    }


# Authentication endpoint (placeholder for development)
@app.post("/auth")
async def authenticate(credentials: dict):
    """Simple authentication endpoint for testing."""
    # This is just for development - implement proper auth for production
    if credentials.get("token") == "dev-token":
        return {
            "authenticated": True,
            "message": "Development authentication successful",
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


# Mount FastMCP exactly as per documentation
app.mount("/llm", mcp_app)
logger.info("FastMCP mounted at /llm - MCP endpoint available at /llm/mcp")


async def main():
    logger.info("Starting FastAPI + FastMCP combined server...")

    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8080,
        log_level="info",
        reload=False,  # Set to True for development auto-reload
    )

    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
