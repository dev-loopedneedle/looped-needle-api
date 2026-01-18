"""Global configuration using Pydantic BaseSettings."""

from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    database_url: str = ""

    # API Configuration
    api_v1_prefix: str = "/api/v1"

    # CORS Configuration
    # Store as string to prevent Pydantic from auto-parsing as JSON
    allowed_origins_raw: str | None = Field(default=None, alias="allowed_origins", exclude=True)

    # Google Cloud Configuration
    google_application_credentials_json: str = ""

    # Google Cloud Storage Configuration
    gcs_bucket_name: str = "evidence"
    gcs_signed_url_expiration_minutes: int = 15

    # Gemini API Configuration
    gemini_api_key: str = ""
    gemini_model_name: str = "gemini-3-pro-preview"

    # Clerk Configuration
    clerk_secret_key: str = ""
    # Optional: used by Clerk request authentication (azp/authorized parties checks)
    clerk_authorized_parties: list[str] = []

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "pretty"  # Options: "pretty", "json", or "standard"

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
        """
        Parse allowed origins from CSV string (e.g., "http://localhost:3000,http://localhost:3001").

        Returns list of origins, or ["*"] if empty/None.
        """
        raw = self.allowed_origins_raw
        if raw is None or not raw.strip():
            return ["*"]

        s = raw.strip()
        if s == "*":
            return ["*"]

        # Parse as CSV
        parts = [part.strip() for part in s.split(",") if part.strip()]
        return parts if parts else ["*"]

    @field_validator("clerk_authorized_parties", mode="before")
    @classmethod
    def _parse_clerk_authorized_parties(cls, v: Any) -> list[str]:
        """Parse CLERK_AUTHORIZED_PARTIES from comma-separated string."""
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            parts = [part.strip() for part in v.split(",") if part.strip()]
            return parts
        return []


settings = Settings()
