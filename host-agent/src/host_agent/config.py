from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    bearer_token: str
    host: str = "0.0.0.0"
    port: int = 9000
    backup_script_path: str = "/home/david/backup-n8n-workflows.sh"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()