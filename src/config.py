"""Global configuration using Pydantic BaseSettings."""

import json
from typing import Any

from pydantic import Field, field_validator
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
    # Store as string to prevent Pydantic from auto-parsing as JSON
    allowed_origins_raw: str | None = Field(default=None, alias="allowed_origins", exclude=True)

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

    @property
    def allowed_origins(self) -> list[str]:
        """Parse allowed origins from raw string value."""
        raw = self.allowed_origins_raw
        if raw is None or raw == "":
            return ["*"]
        s = raw.strip()
        if not s:
            return ["*"]
        if s == "*":
            return ["*"]
        if s.startswith("["):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if item]
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        # Parse as CSV
        parts = [part.strip() for part in s.split(",") if part.strip()]
        return parts if parts else ["*"]

    @field_validator("allowed_origins_raw", mode="before")
    @classmethod
    def _parse_allowed_origins(cls, v: Any) -> str | None:
        """Convert allowed origins input to string for later parsing."""
        if v is None:
            return None
        if isinstance(v, list):
            # If already a list (from JSON parsing), convert back to CSV string
            return ",".join(str(item).strip() for item in v if item)
        if isinstance(v, str):
            return v
        return str(v) if v else None

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
                    pass
            return [part.strip() for part in s.split(",") if part.strip()]
        return v


settings = Settings()
