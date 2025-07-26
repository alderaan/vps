import subprocess
import logging
from pathlib import Path
from datetime import datetime

try:
    from .config import settings
except ImportError:
    from host_agent.config import settings

logger = logging.getLogger(__name__)


class BackupError(Exception):
    """Raised when backup operations fail."""
    pass


async def backup_n8n_workflows() -> dict:
    """
    Backup N8N workflows using existing backup script.
    
    Returns:
        dict: Status information about the backup operation
        
    Raises:
        BackupError: If backup process fails
    """
    try:
        backup_script = Path(settings.backup_script_path)
        
        # Ensure backup script exists
        if not backup_script.exists():
            logger.error(f"Backup script does not exist: {backup_script}")
            raise BackupError(f"Backup script not found: {backup_script}")
        
        # Run the existing backup script
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Running backup script: {backup_script}")
        
        result = subprocess.run(
            ["bash", str(backup_script)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout for full backup process
        )
        
        if result.returncode != 0:
            error_msg = f"Backup script failed with exit code {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"
            logger.error(error_msg)
            raise BackupError(error_msg)
        
        logger.info("Backup completed successfully")
        logger.info(f"Script output: {result.stdout}")
        
        return {
            "status": "success",
            "timestamp": timestamp,
            "message": "N8N workflows backed up successfully",
            "output": result.stdout.strip()
        }
        
    except subprocess.TimeoutExpired as e:
        error_msg = f"Backup operation timed out after 5 minutes: {e}"
        logger.error(error_msg)
        raise BackupError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during backup: {e}"
        logger.error(error_msg)
        raise BackupError(error_msg)