"""Authentication domain Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserProfileResponse(BaseModel):
    """User profile response schema."""

    id: UUID
    clerk_user_id: str
    is_active: bool
    role: str | None = Field(None, description="User role from Clerk public_metadata")
    created_at: datetime
    updated_at: datetime | None = None
    last_access_at: datetime | None = None
    brand: "BrandResponse | None" = Field(
        default=None, description="Brand associated with this user profile"
    )

    model_config = {"from_attributes": True}


# Import BrandResponse after UserProfileResponse to avoid circular imports
from src.brands.schemas import BrandResponse  # noqa: E402

# Update forward reference
UserProfileResponse.model_rebuild()

