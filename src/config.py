"""Global configuration using Pydantic BaseSettings."""

import json
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    # DATABASE_URL is required for database connection
    # Format: postgresql+asyncpg://user:password@host:port/dbname
    database_url: str = ""

    # API Configuration
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = ""

    # CORS Configuration
    cors_origins: list[str] = ["*"]

    # OpenAI Configuration
    openai_api_key: str = ""

    # Clerk Configuration
    clerk_secret_key: str = ""
    clerk_publishable_key: str = ""
    # Optional: used by Clerk request authentication (azp/authorized parties checks)
    clerk_authorized_parties: list[str] = []

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "json"

    # Application Settings
    project_name: str = "Looped Needle API"
    version: str = "1.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("clerk_authorized_parties", mode="before")
    @classmethod
    def _parse_clerk_authorized_parties(cls, v: Any) -> Any:
        """
        Allow CLERK_AUTHORIZED_PARTIES to be provided as:
        - CSV: "https://app.example.com,https://staging.example.com"
        - JSON list: ["https://app.example.com", "https://staging.example.com"]
        """
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                try:
                    parsed = json.loads(s)
                    return parsed
                except json.JSONDecodeError:
                    # Fall back to CSV parsing if JSON is malformed
                    pass
            return [part.strip() for part in s.split(",") if part.strip()]
        return v


settings = Settings()
