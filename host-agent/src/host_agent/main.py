import logging
import sys
from pathlib import Path

# Add src to path for direct execution
if __name__ == "__main__":
    src_path = Path(__file__).parent.parent
    sys.path.insert(0, str(src_path))

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

try:
    from .config import settings
    from .backup import backup_n8n_workflows, BackupError
    from .search import (
        search_directory, get_files, SearchError,
        SearchRequest, SearchResponse,
        GetFilesRequest, GetFilesResponse
    )
except ImportError:
    # Fallback for direct execution
    from host_agent.config import settings
    from host_agent.backup import backup_n8n_workflows, BackupError
    from host_agent.search import (
        search_directory, get_files, SearchError,
        SearchRequest, SearchResponse,
        GetFilesRequest, GetFilesResponse
    )

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HostAgent",
    description="Local host-level operations API",
    version="1.0.0"
)

security = HTTPBearer()


class BackupResponse(BaseModel):
    status: str
    timestamp: str
    message: str


class ErrorResponse(BaseModel):
    detail: str
    timestamp: str


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify bearer token authentication."""
    if credentials.credentials != settings.bearer_token:
        logger.warning(f"Invalid token attempt from request")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )
    return credentials.credentials


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "HostAgent"}


@app.post("/backup/n8n", response_model=BackupResponse)
async def run_n8n_backup(token: str = Depends(verify_token)):
    """
    Backup N8N workflows to git repository.
    
    Requires valid Bearer token in Authorization header.
    """
    try:
        logger.info("Starting N8N backup process")
        result = await backup_n8n_workflows()
        logger.info("N8N backup completed successfully")
        return BackupResponse(**result)
        
    except BackupError as e:
        logger.error(f"Backup failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Backup operation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest, token: str = Depends(verify_token)):
    """
    Search for content in n8n-docs or n8nio directories using ripgrep.
    
    Args:
        request: Search parameters including query, directory, max_results, and context_lines
        
    Returns:
        SearchResponse with matching results
        
    Requires valid Bearer token in Authorization header.
    """
    try:
        logger.info(f"Searching for '{request.query}' in {request.directory}")
        result = await search_directory(
            query=request.query,
            directory=request.directory,
            max_results=request.max_results,
            context_lines=request.context_lines
        )
        logger.info(f"Search found {result.total_matches} matches")
        return result
        
    except SearchError as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Search operation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during search: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


@app.post("/get_files", response_model=GetFilesResponse)
async def get_files_endpoint(request: GetFilesRequest, token: str = Depends(verify_token)):
    """
    Retrieve full content of specified files from n8n-docs or n8nio directories.
    
    Args:
        request: Request with directory and list of file paths
        
    Returns:
        GetFilesResponse with file contents
        
    Requires valid Bearer token in Authorization header.
    """
    try:
        logger.info(f"Retrieving {len(request.files)} files from {request.directory}")
        result = await get_files(
            directory=request.directory,
            files=request.files
        )
        logger.info(f"Retrieved {len(result.files)} files successfully, {len(result.errors)} errors")
        return result
        
    except SearchError as e:
        logger.error(f"Get files failed: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Get files operation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error getting files: {e}")
        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )


def main():
    """Entry point for the HostAgent service."""
    import uvicorn
    uvicorn.run(
        "host_agent.main:app",
        host=settings.host,
        port=settings.port,
        reload=False
    )


if __name__ == "__main__":
    main()