#!/usr/bin/env python3
"""
Direct testing script for n8n functions without MCP layer.
"""

import asyncio
import os
from server import N8nClient


async def test_n8n_functions():
    """Test n8n functions directly."""
    
    # Make sure env vars are set
    if not os.getenv("N8N_API_KEY"):
        print("ERROR: N8N_API_KEY environment variable not set")
        return
    
    # Create n8n client directly
    n8n_base_url = os.getenv("N8N_BASE_URL", "http://localhost:5678")
    n8n_api_key = os.getenv("N8N_API_KEY")
    client = N8nClient(n8n_base_url, n8n_api_key)
    
    print("Testing n8n functions directly...")
    
    try:
        # Test list workflows
        print("\n1. Testing list_workflows()...")
        workflows = await client.list_workflows()
        print(f"Found {len(workflows)} workflows")
        for w in workflows:
            name = w.get('name', 'Unknown')
            wf_id = w.get('id', 'No ID')
            active = w.get('active', False)
            print(f"  - {name} (ID: {wf_id}, Active: {active})")
        
        # Test search manually
        print("\n2. Testing search for 'ai'...")
        query = "ai"
        query_lower = query.lower()
        matches = []
        
        for workflow in workflows:
            name = workflow.get("name", "").lower()
            description = workflow.get("description", "").lower()
            
            if query_lower in name or query_lower in description:
                matches.append(workflow)
        
        print(f"Found {len(matches)} workflows matching 'ai'")
        for w in matches:
            print(f"  - {w.get('name')} (ID: {w.get('id')})")
            
        # Test search for ai-dev-server specifically
        print("\n3. Testing search for 'ai-dev-server'...")
        query = "ai-dev-server"
        query_lower = query.lower()
        matches = []
        
        for workflow in workflows:
            name = workflow.get("name", "").lower()
            description = workflow.get("description", "").lower()
            
            if query_lower in name or query_lower in description:
                matches.append(workflow)
        
        print(f"Found {len(matches)} workflows matching 'ai-dev-server'")
        for w in matches:
            print(f"  - {w.get('name')} (ID: {w.get('id')})")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_n8n_functions())