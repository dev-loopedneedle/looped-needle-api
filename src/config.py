"""Global configuration using Pydantic BaseSettings."""

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


settings = Settings()
