#!/usr/bin/env python3
from fastmcp import FastMCP

# Create FastMCP instance
mcp = FastMCP("Hello World MCP Server")

@mcp.tool
def hello_world() -> str:
    """Returns a simple Hello World greeting."""
    return "Hello World, Meister"

if __name__ == "__main__":
    # Run the MCP server using STDIO transport
    mcp.run()