"""Search functionality for n8n documentation and TypeScript nodes."""
import asyncio
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SearchMatch(BaseModel):
    """A single search match within a file."""
    line_number: int
    content: str
    context_before: List[str] = []
    context_after: List[str] = []


class SearchResult(BaseModel):
    """Search result for a single file."""
    file: str
    matches: List[SearchMatch]


class SearchRequest(BaseModel):
    """Request model for search endpoint."""
    query: str = Field(..., description="Search query term")
    directory: Literal["n8n-docs", "n8n-nodes-only"] = Field(..., description="Directory to search in")
    max_results: int = Field(50, description="Maximum number of results to return", ge=1, le=200)
    context_lines: int = Field(2, description="Number of context lines before/after match", ge=0, le=5)


class SearchResponse(BaseModel):
    """Response model for search endpoint."""
    results: List[SearchResult]
    total_matches: int
    truncated: bool = False


class GetFilesRequest(BaseModel):
    """Request model for get_files endpoint."""
    directory: Literal["n8n-docs", "n8n-nodes-only"] = Field(..., description="Directory to get files from")
    files: List[str] = Field(..., description="List of file paths to retrieve", min_items=1, max_items=20)


class FileContent(BaseModel):
    """Content of a single file."""
    path: str
    content: str
    size: int


class GetFilesResponse(BaseModel):
    """Response model for get_files endpoint."""
    files: List[FileContent]
    errors: List[Dict[str, str]] = []


class SearchError(Exception):
    """Custom exception for search operations."""
    pass


async def search_directory(
    query: str,
    directory: str,
    max_results: int = 50,
    context_lines: int = 2,
    base_path: str = "/home/david/vps"
) -> SearchResponse:
    """
    Search for a query in the specified directory using ripgrep.
    
    Args:
        query: Search term
        directory: Directory name (n8n-docs or n8n-nodes-only)
        max_results: Maximum number of results
        context_lines: Number of context lines
        base_path: Base path for the VPS directory
        
    Returns:
        SearchResponse with results
        
    Raises:
        SearchError: If search operation fails
    """
    # Validate directory
    if directory not in ["n8n-docs", "n8n-nodes-only"]:
        raise SearchError(f"Invalid directory: {directory}")
    
    full_path = Path(base_path) / directory
    
    # Check if directory exists
    if not full_path.exists():
        raise SearchError(f"Directory not found: {full_path}")
    
    # Build ripgrep command
    # Using JSON output format for structured results
    cmd = [
        "rg",
        "--json",  # JSON output format
        "--max-count", str(max_results),  # Limit results
        "--context", str(context_lines),  # Context lines
        "--no-heading",  # Don't group by file
        "--line-number",  # Include line numbers
        "--color", "never",  # No color codes
        "--",  # End of options
        query,  # Search query
        str(full_path)  # Directory to search
    ]
    
    try:
        # Execute ripgrep
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode not in [0, 1]:  # 0 = matches found, 1 = no matches
            logger.error(f"Ripgrep error: {stderr.decode()}")
            raise SearchError(f"Search failed: {stderr.decode()}")
        
        # Parse JSON output
        results = {}
        total_matches = 0
        
        for line in stdout.decode().strip().split('\n'):
            if not line:
                continue
                
            try:
                data = json.loads(line)
                
                if data.get("type") == "match":
                    # Extract file path relative to search directory
                    file_path = Path(data["data"]["path"]["text"])
                    relative_path = file_path.relative_to(full_path)
                    file_key = str(relative_path)
                    
                    if file_key not in results:
                        results[file_key] = []
                    
                    # Create match entry
                    match = SearchMatch(
                        line_number=data["data"]["line_number"],
                        content=data["data"]["lines"]["text"].rstrip()
                    )
                    
                    results[file_key].append(match)
                    total_matches += 1
                    
                elif data.get("type") == "context":
                    # Add context lines to the last match
                    if results:
                        file_path = Path(data["data"]["path"]["text"])
                        relative_path = file_path.relative_to(full_path)
                        file_key = str(relative_path)
                        
                        if file_key in results and results[file_key]:
                            last_match = results[file_key][-1]
                            context_line = data["data"]["lines"]["text"].rstrip()
                            line_num = data["data"]["line_number"]
                            
                            # Determine if this is before or after context
                            if line_num < last_match.line_number:
                                last_match.context_before.append(context_line)
                            else:
                                last_match.context_after.append(context_line)
                                
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to parse ripgrep output line: {e}")
                continue
        
        # Convert to response format
        search_results = [
            SearchResult(file=file_path, matches=matches)
            for file_path, matches in results.items()
        ]
        
        # Check if results were truncated
        truncated = total_matches >= max_results
        
        return SearchResponse(
            results=search_results,
            total_matches=total_matches,
            truncated=truncated
        )
        
    except Exception as e:
        logger.error(f"Search operation failed: {e}")
        raise SearchError(f"Search operation failed: {str(e)}")


async def get_files(
    directory: str,
    files: List[str],
    base_path: str = "/home/david/vps"
) -> GetFilesResponse:
    """
    Retrieve full content of specified files.
    
    Args:
        directory: Directory name (n8n-docs or n8n-nodes-only)
        files: List of file paths relative to directory
        base_path: Base path for the VPS directory
        
    Returns:
        GetFilesResponse with file contents
        
    Raises:
        SearchError: If operation fails
    """
    # Validate directory
    if directory not in ["n8n-docs", "n8n-nodes-only"]:
        raise SearchError(f"Invalid directory: {directory}")
    
    full_base_path = Path(base_path) / directory
    
    # Check if directory exists
    if not full_base_path.exists():
        raise SearchError(f"Directory not found: {full_base_path}")
    
    file_contents = []
    errors = []
    
    for file_path in files:
        try:
            # Construct full path and validate it's within allowed directory
            full_file_path = (full_base_path / file_path).resolve()
            
            # Security check: ensure file is within the allowed directory
            if not str(full_file_path).startswith(str(full_base_path.resolve())):
                errors.append({
                    "file": file_path,
                    "error": "Path traversal attempt detected"
                })
                continue
            
            # Check if file exists
            if not full_file_path.exists():
                errors.append({
                    "file": file_path,
                    "error": "File not found"
                })
                continue
            
            # Check if it's a file (not directory)
            if not full_file_path.is_file():
                errors.append({
                    "file": file_path,
                    "error": "Path is not a file"
                })
                continue
            
            # Read file content
            try:
                content = full_file_path.read_text(encoding='utf-8')
                size = full_file_path.stat().st_size
                
                file_contents.append(FileContent(
                    path=file_path,
                    content=content,
                    size=size
                ))
            except UnicodeDecodeError:
                # Try reading as binary and convert
                try:
                    content = full_file_path.read_bytes().decode('utf-8', errors='replace')
                    size = full_file_path.stat().st_size
                    
                    file_contents.append(FileContent(
                        path=file_path,
                        content=content,
                        size=size
                    ))
                except Exception as e:
                    errors.append({
                        "file": file_path,
                        "error": f"Failed to read file: {str(e)}"
                    })
                    
        except Exception as e:
            errors.append({
                "file": file_path,
                "error": f"Unexpected error: {str(e)}"
            })
    
    return GetFilesResponse(
        files=file_contents,
        errors=errors
    )