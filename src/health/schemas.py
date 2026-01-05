"""Health check schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class HealthCheck(BaseModel):
    """Individual health check result."""

    status: str
    message: str | None = None


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    timestamp: datetime
    version: str
    checks: dict[str, Any] | None = None

