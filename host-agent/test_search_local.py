#!/usr/bin/env python3
"""
Local test script for search functionality.
Tests the search module without needing the full FastAPI server.
"""
import asyncio
import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from host_agent.search import search_directory, get_files, SearchError


async def test_search():
    """Test the search functionality locally."""
    # Update this path to match your local setup
    BASE_PATH = "/Users/d.lucker/Code"
    
    print("=" * 60)
    print("Testing n8n Search Functionality")
    print("=" * 60)
    
    # Test 1: Search in n8n-docs
    print("\n1. Testing search in n8n-docs...")
    print("-" * 40)
    try:
        result = await search_directory(
            query="workflow",
            directory="n8n-docs",
            max_results=5,
            context_lines=1,
            base_path=BASE_PATH
        )
        print(f"✓ Found {result.total_matches} matches")
        print(f"✓ Results in {len(result.results)} files")
        if result.results:
            print(f"  First file: {result.results[0].file}")
            print(f"  Matches in first file: {len(result.results[0].matches)}")
            if result.results[0].matches:
                first_match = result.results[0].matches[0]
                print(f"  First match at line {first_match.line_number}: {first_match.content[:80]}...")
    except SearchError as e:
        print(f"✗ Search failed: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    # Test 2: Search in n8n-nodes-only
    print("\n2. Testing search in n8n-nodes-only...")
    print("-" * 40)
    try:
        result = await search_directory(
            query="executeWorkflowTrigger",
            directory="n8n-nodes-only",
            max_results=5,
            context_lines=2,
            base_path=BASE_PATH
        )
        print(f"✓ Found {result.total_matches} matches")
        print(f"✓ Results in {len(result.results)} files")
        if result.results:
            print(f"  First file: {result.results[0].file}")
            print(f"  Matches in first file: {len(result.results[0].matches)}")
    except SearchError as e:
        print(f"✗ Search failed: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    # Test 3: Get files
    print("\n3. Testing file retrieval...")
    print("-" * 40)
    try:
        # Try to get a README if it exists
        result = await get_files(
            directory="n8n-docs",
            files=["README.md", "docs/index.md"],  # Try common doc files
            base_path=BASE_PATH
        )
        print(f"✓ Retrieved {len(result.files)} files")
        print(f"✓ Errors: {len(result.errors)}")
        for file_content in result.files:
            print(f"  - {file_content.path}: {file_content.size} bytes")
        for error in result.errors:
            print(f"  ! {error['file']}: {error['error']}")
    except SearchError as e:
        print(f"✗ Get files failed: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
    
    # Test 4: Test ripgrep directly
    print("\n4. Testing ripgrep command...")
    print("-" * 40)
    try:
        import subprocess
        result = subprocess.run(
            ["rg", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✓ Ripgrep installed: {result.stdout.split()[0]} {result.stdout.split()[1]}")
        else:
            print("✗ Ripgrep not found or error")
    except FileNotFoundError:
        print("✗ Ripgrep not installed. Install with: brew install ripgrep")
    except Exception as e:
        print(f"✗ Error checking ripgrep: {e}")
    
    # Test 5: Path validation
    print("\n5. Testing path validation...")
    print("-" * 40)
    try:
        # Test path traversal protection
        result = await get_files(
            directory="n8n-docs",
            files=["../../../etc/passwd"],  # Should be blocked
            base_path=BASE_PATH
        )
        if result.errors:
            print("✓ Path traversal correctly blocked")
            print(f"  Error: {result.errors[0]['error']}")
        else:
            print("✗ WARNING: Path traversal not blocked!")
    except Exception as e:
        print(f"✓ Path traversal blocked with exception: {e}")
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print("\nIf all tests passed, the search functionality is ready for deployment.")
    print("If any tests failed, check:")
    print("1. Ripgrep is installed (brew install ripgrep)")
    print("2. The n8n-docs and n8n-nodes-only directories exist")
    print("3. The BASE_PATH is correct for your setup")


if __name__ == "__main__":
    asyncio.run(test_search())