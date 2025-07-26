import logging
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from .config import settings
from .backup import backup_n8n_workflows, BackupError

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