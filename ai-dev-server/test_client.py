#!/usr/bin/env python3
import asyncio
from fastmcp import Client

async def test_hello_server():
    """Test the hello_server.py MCP server functionality."""
    print("Testing Hello World MCP Server...")
    
    async with Client("./hello_server.py") as client:
        # List available tools
        print("\n1. Listing available tools:")
        tools = await client.list_tools()
        for tool in tools:
            print(f"   - {tool.name}: {tool.description}")
        
        # Call the hello_world tool
        print("\n2. Calling hello_world tool:")
        result = await client.call_tool("hello_world", {})
        print(f"   Result: {result.data}")
        
        # Get server info
        print("\n3. Server initialization info:")
        init_result = client.initialize_result
        print(f"   Server name: {init_result.serverInfo.name}")
        print(f"   Server version: {init_result.serverInfo.version}")
        
    print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_hello_server())