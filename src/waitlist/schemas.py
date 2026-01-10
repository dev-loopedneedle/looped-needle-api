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
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")

    model_config = {"from_attributes": True, "populate_by_name": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Map snake_case model fields to camelCase API fields."""
        if hasattr(obj, "__dict__"):
            data = dict(obj.__dict__)
            if "created_at" in data:
                data["createdAt"] = data.pop("created_at")
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)
