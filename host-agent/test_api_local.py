#!/usr/bin/env python3
"""
Test the Host Agent API endpoints locally.
Run the host agent first: uv run python src/host_agent/main.py
"""
import asyncio
import httpx
import json
import os
from typing import Dict, Any

# Configuration
HOST_AGENT_URL = "http://127.0.0.1:9000"
BEARER_TOKEN = os.getenv("BEARER_TOKEN", "test-token-123")


async def test_endpoint(
    method: str,
    endpoint: str,
    data: Dict[str, Any] = None,
    expected_status: int = 200
) -> Dict:
    """Test a single API endpoint."""
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {BEARER_TOKEN}",
            "Content-Type": "application/json"
        }
        
        try:
            if method == "GET":
                response = await client.get(
                    f"{HOST_AGENT_URL}{endpoint}",
                    headers=headers
                )
            elif method == "POST":
                response = await client.post(
                    f"{HOST_AGENT_URL}{endpoint}",
                    headers=headers,
                    json=data
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == expected_status:
                print(f"  ✓ Expected status code")
                if response.content:
                    return response.json()
            else:
                print(f"  ✗ Unexpected status code (expected {expected_status})")
                print(f"  Response: {response.text}")
                
        except httpx.ConnectError:
            print(f"  ✗ Cannot connect to {HOST_AGENT_URL}")
            print(f"  Make sure host agent is running: uv run python src/host_agent/main.py")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    return {}


async def main():
    """Run all API tests."""
    print("=" * 60)
    print("Host Agent API Tests")
    print("=" * 60)
    print(f"URL: {HOST_AGENT_URL}")
    print(f"Token: {BEARER_TOKEN[:10]}...")
    print()
    
    # Test 1: Health check (no auth required)
    print("1. Testing health endpoint...")
    print("-" * 40)
    result = await test_endpoint("GET", "/health")
    if result:
        print(f"  Response: {json.dumps(result, indent=2)}")
    
    # Test 2: Search n8n-docs
    print("\n2. Testing search in n8n-docs...")
    print("-" * 40)
    search_data = {
        "query": "workflow",
        "directory": "n8n-docs",
        "max_results": 3,
        "context_lines": 1
    }
    result = await test_endpoint("POST", "/search", search_data)
    if result:
        print(f"  Total matches: {result.get('total_matches', 0)}")
        print(f"  Files with matches: {len(result.get('results', []))}")
        if result.get('results'):
            first_file = result['results'][0]
            print(f"  First file: {first_file['file']}")
            print(f"  Matches in first file: {len(first_file['matches'])}")
    
    # Test 3: Search n8nio
    print("\n3. Testing search in n8nio...")
    print("-" * 40)
    search_data = {
        "query": "execute",
        "directory": "n8nio",
        "max_results": 3,
        "context_lines": 0
    }
    result = await test_endpoint("POST", "/search", search_data)
    if result:
        print(f"  Total matches: {result.get('total_matches', 0)}")
        print(f"  Files with matches: {len(result.get('results', []))}")
    
    # Test 4: Get files
    print("\n4. Testing file retrieval...")
    print("-" * 40)
    get_files_data = {
        "directory": "n8n-docs",
        "files": ["README.md"]  # Adjust based on what exists
    }
    result = await test_endpoint("POST", "/get_files", get_files_data)
    if result:
        print(f"  Files retrieved: {len(result.get('files', []))}")
        print(f"  Errors: {len(result.get('errors', []))}")
        for file_info in result.get('files', []):
            print(f"    - {file_info['path']}: {file_info['size']} bytes")
        for error in result.get('errors', []):
            print(f"    ! {error['file']}: {error['error']}")
    
    # Test 5: Invalid directory
    print("\n5. Testing error handling (invalid directory)...")
    print("-" * 40)
    search_data = {
        "query": "test",
        "directory": "invalid-dir",
        "max_results": 1
    }
    result = await test_endpoint("POST", "/search", search_data, expected_status=400)
    
    # Test 6: Path traversal protection
    print("\n6. Testing security (path traversal)...")
    print("-" * 40)
    get_files_data = {
        "directory": "n8n-docs",
        "files": ["../../../etc/passwd"]
    }
    result = await test_endpoint("POST", "/get_files", get_files_data)
    if result and result.get('errors'):
        print(f"  ✓ Path traversal blocked: {result['errors'][0]['error']}")
    elif result and result.get('files'):
        print(f"  ✗ WARNING: Path traversal not blocked!")
    
    # Test 7: Authentication
    print("\n7. Testing authentication...")
    print("-" * 40)
    print("  Testing with invalid token...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{HOST_AGENT_URL}/search",
                headers={
                    "Authorization": "Bearer invalid-token",
                    "Content-Type": "application/json"
                },
                json={"query": "test", "directory": "n8n-docs"}
            )
            if response.status_code == 401:
                print("  ✓ Invalid token correctly rejected")
            else:
                print(f"  ✗ Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("\nTo run the host agent locally:")
    print("1. cd /Users/d.lucker/Code/vps/host-agent")
    print("2. Create .env file with BEARER_TOKEN=test-token-123")
    print("3. uv sync")
    print("4. uv run python src/host_agent/main.py")
    print("\nThen run this test script in another terminal:")
    print("  python test_api_local.py")


if __name__ == "__main__":
    asyncio.run(main())