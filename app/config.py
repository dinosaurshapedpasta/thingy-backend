from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """
    Application configuration with environment variable support.

    Environment variables can be set in .env file or system environment.
    Example .env:
        DATABASE_URL=sqlite:///./app/data.db
        CORS_ORIGINS=http://localhost:3000,http://localhost:5173
        LOG_LEVEL=INFO
    """

    # Database
    database_url: str = "sqlite:///./app/data.db"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["GET", "POST", "PATCH", "DELETE"]
    cors_allow_headers: list[str] = ["Content-Type", "X-API-Key"]

    # API
    api_key_header_name: str = "X-API-Key"

    # Logging
    log_level: str = "INFO"

    # Application
    app_name: str = "Logistics Backend"
    app_version: str = "0.1.0"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


# Singleton instance
settings = Settings()
