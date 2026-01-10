"""Authentication domain Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserProfileResponse(BaseModel):
    """User profile response schema."""

    id: UUID
    clerk_user_id: str = Field(..., alias="clerkUserId", serialization_alias="clerkUserId")
    is_active: bool = Field(..., alias="isActive", serialization_alias="isActive")
    role: str | None = Field(None, description="User role from Clerk public_metadata")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt", serialization_alias="updatedAt")
    last_access_at: datetime | None = Field(
        None, alias="lastAccessAt", serialization_alias="lastAccessAt"
    )
    brand: "BrandResponse | None" = Field(
        default=None, description="Brand associated with this user profile"
    )

    model_config = {"from_attributes": True, "populate_by_name": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Map snake_case model fields to camelCase API fields."""
        if hasattr(obj, "__dict__"):
            data = dict(obj.__dict__)
            # Map fields to camelCase
            if "clerk_user_id" in data:
                data["clerkUserId"] = data.pop("clerk_user_id")
            if "is_active" in data:
                data["isActive"] = data.pop("is_active")
            if "created_at" in data:
                data["createdAt"] = data.pop("created_at")
            if "updated_at" in data:
                data["updatedAt"] = data.pop("updated_at")
            if "last_access_at" in data:
                data["lastAccessAt"] = data.pop("last_access_at")
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


# Import BrandResponse after UserProfileResponse to avoid circular imports
from src.brands.schemas import BrandResponse  # noqa: E402

# Update forward reference
UserProfileResponse.model_rebuild()

