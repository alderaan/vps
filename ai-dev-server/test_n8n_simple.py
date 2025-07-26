#!/usr/bin/env python3
"""
Simple n8n testing without importing server.py
"""

import asyncio
import os
import httpx
from typing import Dict, List, Optional
from pathlib import Path


def load_env_file():
    """Load environment variables from .env file."""
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value


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
            except httpx.HTTPError as e:
                print(f"n8n API request failed: {e}")
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

    async def search_workflows(self, query: str) -> List[Dict]:
        """Search n8n workflows by name or description."""
        workflows = await self.list_workflows()

        # Simple text search in name and description
        query_lower = query.lower()
        matches = []

        for workflow in workflows:
            name = workflow.get("name", "").lower()
            description = workflow.get("description", "").lower()

            if query_lower in name or query_lower in description:
                matches.append(workflow)

        return matches


async def test_n8n():
    """Test n8n functions directly."""

    # Load .env file first
    load_env_file()

    # Check env vars
    api_key = os.getenv("N8N_API_KEY")
    if not api_key:
        print("ERROR: N8N_API_KEY environment variable not set")
        print("Set it with: export N8N_API_KEY='your-key-here'")
        return

    base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678")
    print(f"Testing n8n at {base_url}")

    client = N8nClient(base_url, api_key)

    try:
        # Test list workflows with limit
        print("\n1. Listing first 5 workflows...")
        workflows = await client.list_workflows()
        limited_workflows = workflows[:5]  # Show only first 5
        print(f"Found {len(workflows)} total workflows, showing first {len(limited_workflows)}:")
        
        # Show just the essential info (name, ID, active status)
        for i, w in enumerate(limited_workflows):
            if isinstance(w, dict):
                name = w.get("name", "Unknown")
                wf_id = w.get("id", "No ID")
                active = w.get("active", False)
                print(f"  {i+1:2d}. {name} (ID: {wf_id}, Active: {active})")
            else:
                print(f"  {i+1:2d}. Raw item: {w}")

        # Test search for ai-dev-server
        print("\n2. Searching for 'ai-dev-server'...")
        search_results = await client.search_workflows("ai-dev-server")
        print(f"Found {len(search_results)} workflows matching 'ai-dev-server':")
        for w in search_results:
            print(f"  - {w.get('name')} (ID: {w.get('id')})")
        
        # Test get workflow details
        print("\n3. Getting details for 'Test ai-dev-server' workflow...")
        try:
            workflow_details = await client.get_workflow("slioElMNkvbyPgQ4")
            print(f"Workflow name: {workflow_details.get('name')}")
            print(f"Active: {workflow_details.get('active')}")
            print(f"Created: {workflow_details.get('createdAt')}")
            print(f"Updated: {workflow_details.get('updatedAt')}")
            print(f"Number of nodes: {len(workflow_details.get('nodes', []))}")
            
            # Show node names
            nodes = workflow_details.get('nodes', [])
            if nodes:
                print("Nodes:")
                for i, node in enumerate(nodes, 1):
                    node_name = node.get('name', 'Unknown')
                    node_type = node.get('type', 'Unknown')
                    print(f"  {i}. {node_name} ({node_type})")
        except Exception as e:
            print(f"Error getting workflow details: {e}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_n8n())
