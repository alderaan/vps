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
from datetime import datetime
from pathlib import Path
import json
from typing import Dict, List, Optional

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
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-N8N-API-KEY": api_key, "Content-Type": "application/json"}

    async def _request(
        self, method: str, endpoint: str, data: Optional[Dict] = None
    ) -> Dict:
        """Make HTTP request to n8n API."""
        url = f"{self.base_url}/api/v1{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data if data else None,
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                error_detail = ""
                try:
                    # Try to get the error details from response body
                    error_detail = e.response.text
                    # Try to parse as JSON if possible
                    try:
                        error_json = e.response.json()
                        error_detail = f"JSON: {error_json}"
                    except:
                        # If not JSON, keep the raw text
                        pass
                except:
                    pass

                logger.error(f"n8n API request failed: {e}")
                if error_detail:
                    logger.error(f"n8n error details: {error_detail}")

                raise Exception(f"n8n API error: {str(e)}\nDetails: {error_detail}")
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
mcp = FastMCP("David's FastMCP Server")


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
    """List all n8n workflows. Use this tool to search for workflows by filtering the results."""
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
            "updatedAt": w.get("updatedAt"),
        }
        for w in workflows
    ]


@mcp.tool
async def n8n_get_workflow(workflow_id: str) -> Dict:
    """Get specific n8n workflow by ID."""
    client = _get_n8n_client()
    return await client.get_workflow(workflow_id)


@mcp.tool
async def n8n_create_workflow_json(
    name: str,
    nodes_json: str,
    connections_json: str,
    settings_json: Optional[str] = None,
) -> Dict:
    """Create new n8n workflow using JSON strings.

    CRITICAL INSTRUCTION: Never attempt to set dummy credentials yourself. This leads to errors. Omit credentials entirely when creating new workflows.

    Args:
        name: Workflow name
        nodes_json: List of workflow nodes as JSON string
        connections_json: Node connections configuration as JSON string
        settings_json: Optional workflow settings as JSON string
    """
    client = _get_n8n_client()
    workflow_data = {
        "name": name,
        "nodes": json.loads(nodes_json),
        "connections": json.loads(connections_json),
        "settings": json.loads(settings_json) if settings_json else {},
    }

    # Save JSON to disk for debugging
    debug_dir = Path("/tmp/n8n-debug")
    debug_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_file = debug_dir / f"create_{name}_{timestamp}.json"

    with open(debug_file, "w") as f:
        json.dump(workflow_data, f, indent=2)
    logger.info(f"Saved workflow JSON to {debug_file} for debugging")

    try:
        result = await client.create_workflow(workflow_data)
        logger.info(f"Successfully created workflow: {result.get('id')}")
        return result
    except Exception as e:
        logger.error(f"Failed to create workflow. Debug JSON saved at: {debug_file}")
        raise


@mcp.tool
async def n8n_update_workflow_json(
    workflow_id: str,
    name: Optional[str] = None,
    nodes_json: Optional[str] = None,
    connections_json: Optional[str] = None,
    settings_json: Optional[str] = None,
    confirmed: bool = False,
) -> Dict:
    """Update existing n8n workflow using JSON strings.

      1. Don't include pinData - This field is not allowed when updating workflows
      2. Include the settings object in the json when updating.
      3. Don't include callerPolicy in the settings - This is an additional property that's not permitted in the settings object
      4. Never attempt to set new dummy credentials yourself. But always include credentials that already existed before your update.

    CONFIRMATION REQUIRED: This tool requires user confirmation to execute.
    First call with confirmed=false (default) to preview changes, then call again with confirmed=true to execute.

    Args:
        workflow_id: ID of workflow to update
        name: New workflow name (optional)
        nodes_json: New nodes list as JSON string (optional)
        connections_json: New connections as JSON string (optional)
        settings_json: New settings as JSON string (optional)
        confirmed: Set to true to actually execute the update (default: false for preview only)
    """
    client = _get_n8n_client()

    # Get current workflow to merge updates
    current = await client.get_workflow(workflow_id)

    workflow_data = {
        "name": name or current.get("name"),
        "nodes": json.loads(nodes_json) if nodes_json else current.get("nodes", []),
        "connections": (
            json.loads(connections_json)
            if connections_json
            else current.get("connections", {})
        ),
        "settings": (
            json.loads(settings_json) if settings_json else current.get("settings", {})
        ),
    }

    # If not confirmed, return preview only
    if not confirmed:
        return {
            "confirmation_required": True,
            "message": "PREVIEW ONLY - Workflow update not executed. Inform user of proposed changes first. If user agrees, call again with confirmed=true to execute.",
            "preview": {
                "workflow_id": workflow_id,
                "current_name": current.get("name"),
                "new_name": workflow_data["name"],
                "current_node_count": len(current.get("nodes", [])),
                "new_node_count": len(workflow_data["nodes"]),
                "changes_detected": {
                    "name_changed": workflow_data["name"] != current.get("name"),
                    "nodes_changed": nodes_json is not None,
                    "connections_changed": connections_json is not None,
                    "settings_changed": settings_json is not None,
                },
            },
            "to_execute": "Call this tool again with the same parameters and confirmed=true",
        }

    # Confirmed - proceed with actual update
    logger.info(f"CONFIRMED: Proceeding with workflow update for {workflow_id}")

    # Run backup before making any changes
    logger.info(f"Running backup before updating workflow {workflow_id}")
    backup_before_result = await _run_n8n_backup()

    # Save JSON to disk for debugging
    debug_dir = Path("/tmp/n8n-debug")
    debug_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    workflow_name = workflow_data.get("name", "unnamed").replace(" ", "_")
    debug_file = debug_dir / f"update_{workflow_id}_{workflow_name}_{timestamp}.json"

    with open(debug_file, "w") as f:
        json.dump(workflow_data, f, indent=2)
    logger.info(f"Saved workflow JSON to {debug_file} for debugging")

    try:
        # Update the workflow
        logger.info(f"Updating workflow {workflow_id}")
        update_result = await client.update_workflow(workflow_id, workflow_data)
        logger.info(f"Successfully updated workflow: {workflow_id}")

        # Run backup after successful update to preserve the new state
        logger.info(f"Running backup after updating workflow {workflow_id}")
        backup_after_result = await _run_n8n_backup()

        # Return combined result with both backup and update status
        return {
            "confirmed_execution": True,
            "backup_before_status": backup_before_result,
            "update_result": update_result,
            "backup_after_status": backup_after_result,
            "message": f"WORKFLOW UPDATED: Pre-update backup: {'success' if backup_before_result.get('success') else 'failed'}, workflow updated successfully, post-update backup: {'success' if backup_after_result.get('success') else 'failed'}",
            "debug_file": str(debug_file),
        }
    except Exception as e:
        logger.error(f"Failed to update workflow. Debug JSON saved at: {debug_file}")
        raise


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


# @mcp.tool
# async def n8n_search_workflows(query: str) -> List[Dict]:
#     """Search n8n workflows by name or description."""
#     client = _get_n8n_client()
#     workflows = await client.list_workflows()
#
#     # Simple text search in name and description
#     query_lower = query.lower()
#     matches = []
#
#     for workflow in workflows:
#         name = workflow.get("name", "").lower()
#         description = workflow.get("description", "").lower()
#
#         if query_lower in name or query_lower in description:
#             matches.append(workflow)
#
#     return matches


async def _run_n8n_backup() -> Dict:
    """Internal function to run n8n backup via HostAgent API."""
    logger.info("Starting n8n backup via HostAgent")
    try:
        # Get HostAgent bearer token from environment
        host_agent_token = os.getenv("HOST_AGENT_BEARER_TOKEN")
        if not host_agent_token:
            logger.error("HOST_AGENT_BEARER_TOKEN environment variable missing")
            return {
                "success": False,
                "error": "HOST_AGENT_BEARER_TOKEN environment variable is required",
            }

        logger.info("Calling HostAgent backup endpoint...")
        # Call HostAgent backup endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://host.docker.internal:9000/backup/n8n",
                headers={
                    "Authorization": f"Bearer {host_agent_token}",
                    "Content-Type": "application/json",
                },
                timeout=300,  # 5 minute timeout
            )

            if response.status_code == 200:
                logger.info("HostAgent backup completed successfully")
                result = response.json()
                return {
                    "success": True,
                    "status": result.get("status"),
                    "timestamp": result.get("timestamp"),
                    "message": result.get("message"),
                    "output": result.get("output"),
                }
            else:
                logger.error(
                    f"HostAgent backup failed with status {response.status_code}"
                )
                error_detail = response.text
                return {
                    "success": False,
                    "error": f"HostAgent API error ({response.status_code}): {error_detail}",
                }

    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "HostAgent backup request timed out after 5 minutes",
        }
    except httpx.ConnectError:
        return {
            "success": False,
            "error": "Could not connect to HostAgent service at http://host.docker.internal:9000",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error calling HostAgent: {str(e)}",
        }


@mcp.tool
async def n8n_backup_workflows() -> Dict:
    """Run the n8n workflow backup via HostAgent API to backup all workflows to git."""
    return await _run_n8n_backup()


# n8n documentation and TypeScript search tools
async def _call_host_agent_search(
    query: str, directory: str, max_results: int = 30, context_lines: int = 2
) -> Dict:
    """Internal function to call HostAgent search endpoint."""
    logger.info(f"Searching for '{query}' in {directory} via HostAgent")
    try:
        # Get HostAgent bearer token from environment
        host_agent_token = os.getenv("HOST_AGENT_BEARER_TOKEN")
        if not host_agent_token:
            logger.error("HOST_AGENT_BEARER_TOKEN environment variable missing")
            raise Exception("HOST_AGENT_BEARER_TOKEN environment variable is required")

        logger.info("Calling HostAgent search endpoint...")
        # Call HostAgent search endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://host.docker.internal:9000/search",
                headers={
                    "Authorization": f"Bearer {host_agent_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "query": query,
                    "directory": directory,
                    "max_results": max_results,
                    "context_lines": context_lines,
                },
                timeout=60,  # 1 minute timeout for search
            )

            if response.status_code == 200:
                logger.info("HostAgent search completed successfully")
                return response.json()
            else:
                logger.error(
                    f"HostAgent search failed with status {response.status_code}"
                )
                error_detail = response.text
                raise Exception(
                    f"HostAgent API error ({response.status_code}): {error_detail}"
                )

    except httpx.TimeoutException:
        raise Exception("HostAgent search request timed out after 60 seconds")
    except httpx.ConnectError:
        raise Exception(
            "Could not connect to HostAgent service at http://host.docker.internal:9000"
        )
    except Exception as e:
        if "HOST_AGENT_BEARER_TOKEN" in str(e):
            raise
        raise Exception(f"Unexpected error calling HostAgent: {str(e)}")


async def _call_host_agent_get_files(directory: str, files: List[str]) -> Dict:
    """Internal function to call HostAgent get_files endpoint."""
    logger.info(f"Getting {len(files)} files from {directory} via HostAgent")
    try:
        # Get HostAgent bearer token from environment
        host_agent_token = os.getenv("HOST_AGENT_BEARER_TOKEN")
        if not host_agent_token:
            logger.error("HOST_AGENT_BEARER_TOKEN environment variable missing")
            raise Exception("HOST_AGENT_BEARER_TOKEN environment variable is required")

        logger.info("Calling HostAgent get_files endpoint...")
        # Call HostAgent get_files endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://host.docker.internal:9000/get_files",
                headers={
                    "Authorization": f"Bearer {host_agent_token}",
                    "Content-Type": "application/json",
                },
                json={"directory": directory, "files": files},
                timeout=120,  # 2 minute timeout for file retrieval
            )

            if response.status_code == 200:
                logger.info("HostAgent get_files completed successfully")
                return response.json()
            else:
                logger.error(
                    f"HostAgent get_files failed with status {response.status_code}"
                )
                error_detail = response.text
                raise Exception(
                    f"HostAgent API error ({response.status_code}): {error_detail}"
                )

    except httpx.TimeoutException:
        raise Exception("HostAgent get_files request timed out after 120 seconds")
    except httpx.ConnectError:
        raise Exception(
            "Could not connect to HostAgent service at http://host.docker.internal:9000"
        )
    except Exception as e:
        if "HOST_AGENT_BEARER_TOKEN" in str(e):
            raise
        raise Exception(f"Unexpected error calling HostAgent: {str(e)}")


@mcp.tool
async def n8n_search_docs(
    query: str, max_results: int = 30, context_lines: int = 2
) -> Dict:
    """Search n8n documentation for general node information written for humans.

    This searches the official n8n documentation which explains how nodes work conceptually
    but may lack some technical implementation details. Use this to understand node purpose,
    basic configuration, and usage examples.

    Args:
        query: Search term to look for in n8n documentation
        max_results: Maximum number of results to return (default: 30, max: 200)
        context_lines: Number of context lines before/after match (default: 2, max: 5)

    Returns:
        Dict with search results including file paths, matches, and context
    """
    return await _call_host_agent_search(
        query=query,
        directory="n8n-docs",
        max_results=max_results,
        context_lines=context_lines,
    )


@mcp.tool
async def n8n_search_nodes(
    query: str, max_results: int = 30, context_lines: int = 2
) -> Dict:
    """Search the official n8n TypeScript source code used to construct node JSON schemas.

    This searches the actual TypeScript implementation files that define how n8n nodes work.
    Use this to understand the correct JSON schema structure, available parameters,
    validation rules, and implementation details for building workflows programmatically.

    Args:
        query: Search term to look for in TypeScript node implementations
        max_results: Maximum number of results to return (default: 30, max: 200)
        context_lines: Number of context lines before/after match (default: 2, max: 5)

    Returns:
        Dict with search results including file paths, matches, and context
    """
    return await _call_host_agent_search(
        query=query,
        directory="n8nio",
        max_results=max_results,
        context_lines=context_lines,
    )


@mcp.tool
async def n8n_get_files(directory: str, files: List[str]) -> Dict:
    """Retrieve full content of specified files from n8n-docs or n8nio.

    Args:
        directory: Either "n8n-docs" or "n8nio"
        files: List of file paths relative to the directory (max 20 files)

    Returns:
        Dict with file contents and any errors encountered
    """
    if directory not in ["n8n-docs", "n8nio"]:
        raise ValueError("directory must be either 'n8n-docs' or 'n8nio'")

    if len(files) > 20:
        raise ValueError("Maximum 20 files can be retrieved at once")

    return await _call_host_agent_get_files(directory=directory, files=files)


# n8n-workflows integration tools
N8N_WORKFLOWS_URL = "http://n8n-workflows:8000"  # Container-to-container communication (internal port stays 8000)


@mcp.tool
async def search_workflow_templates(
    query: str = "",
    category: str = "all",
    trigger: str = "all",
    complexity: str = "all",
    page: int = 1,
    per_page: int = 20,
) -> Dict:
    """Search a third-party collection of publicly available n8n workflow templates.

    This searches through community-contributed workflow examples to understand how
    n8n nodes are implemented in real-world use cases. Templates show practical
    implementation patterns but may use outdated node versions - the JSON might
    still work if the underlying schemas haven't changed significantly.

    Args:
        query: Search text (searches names, descriptions, integrations)
        category: Filter by category (messaging, ai_ml, database, etc.) or "all"
        trigger: Filter by trigger type (Manual, Webhook, Scheduled, Complex) or "all"
        complexity: Filter by complexity (low, medium, high) or "all"
        page: Page number for pagination
        per_page: Results per page (max 100)

    Returns:
        Dict with workflows list, total count, pagination info
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            params = {
                "q": query,
                "trigger": trigger,
                "complexity": complexity,
                "page": page,
                "per_page": per_page,
            }

            if category != "all":
                response = await client.get(
                    f"{N8N_WORKFLOWS_URL}/api/workflows/category/{category}",
                    params=params,
                )
            else:
                response = await client.get(
                    f"{N8N_WORKFLOWS_URL}/api/workflows", params=params
                )

            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        raise Exception("Cannot connect to n8n-workflows service. Is it running?")
    except httpx.HTTPError as e:
        raise Exception(f"Error searching workflow templates: {str(e)}")


@mcp.tool
async def get_workflow_template(filename: str) -> Dict:
    """Get detailed workflow template including raw JSON.

    Args:
        filename: The workflow filename (e.g., "0001_Telegram_Schedule_Automation_Scheduled.json")

    Returns:
        Dict with metadata and raw_json fields containing the complete workflow
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{N8N_WORKFLOWS_URL}/api/workflows/{filename}")
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        raise Exception("Cannot connect to n8n-workflows service. Is it running?")
    except httpx.HTTPError as e:
        if e.response.status_code == 404:
            raise Exception(f"Workflow template '{filename}' not found")
        raise Exception(f"Error getting workflow template: {str(e)}")


@mcp.tool
async def get_workflow_categories() -> Dict:
    """Get available workflow categories for filtering.

    Returns:
        Dict with categories list (messaging, ai_ml, database, etc.)
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{N8N_WORKFLOWS_URL}/api/categories")
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        raise Exception("Cannot connect to n8n-workflows service. Is it running?")
    except httpx.HTTPError as e:
        raise Exception(f"Error getting workflow categories: {str(e)}")


@mcp.tool
async def get_workflow_template_stats() -> Dict:
    """Get statistics about the workflow template database.

    Returns:
        Dict with total workflows, active count, trigger distribution, etc.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{N8N_WORKFLOWS_URL}/api/stats")
            response.raise_for_status()
            return response.json()
    except httpx.ConnectError:
        raise Exception("Cannot connect to n8n-workflows service. Is it running?")
    except httpx.HTTPError as e:
        raise Exception(f"Error getting workflow template stats: {str(e)}")


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
