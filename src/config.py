"""Global configuration using Pydantic BaseSettings."""

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    postgres_server: str = "localhost"
    postgres_user: str = "postgres"
    postgres_password: str = ""
    postgres_db: str = "looped_needle"
    database_url: str = ""

    # API Configuration
    environment: str = "local"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = ""

    # CORS Configuration
    cors_origins: list[str] = ["*"]

    # OpenAI Configuration
    openai_api_key: str = ""

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

    @computed_field
    @property
    def computed_database_url(self) -> str:
        """Compute database URL if not explicitly provided."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_server}/{self.postgres_db}"
        )


settings = Settings()

# Use computed URL if database_url is empty
if not settings.database_url:
    settings.database_url = settings.computed_database_url
