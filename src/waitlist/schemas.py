"""Waitlist domain Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class WaitlistRequest(BaseModel):
    """Schema for waitlist submission request."""

    email: EmailStr = Field(..., description="Email address (required)")
    name: str | None = Field(None, max_length=255, description="Name (optional)")
    message: str | None = Field(None, description="Message (optional)")


class WaitlistResponse(BaseModel):
    """Schema for waitlist entry response."""

    id: UUID
    email: str
    name: str | None
    message: str | None
    created_at: datetime
