"""Schemas for brand resources."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.brands.constants import MAX_PAGE_LIMIT, CompanySize


class BrandCreate(BaseModel):
    """Schema for creating a brand."""

    name: str = Field(..., max_length=255, description="Brand name")
    registration_country: str = Field(
        ..., alias="registrationCountry", serialization_alias="registrationCountry", description="ISO country code"
    )
    company_size: CompanySize = Field(
        ..., alias="companySize", serialization_alias="companySize", description="Company size"
    )
    target_markets: list[str] = Field(
        ..., alias="targetMarkets", serialization_alias="targetMarkets", description="Array of ISO country codes"
    )

    model_config = {"populate_by_name": True}


class BrandUpdate(BaseModel):
    """Schema for updating a brand."""

    name: str | None = Field(None, max_length=255, description="Brand name")
    registration_country: str | None = Field(
        None, alias="registrationCountry", serialization_alias="registrationCountry", description="ISO country code"
    )
    company_size: CompanySize | None = Field(
        None, alias="companySize", serialization_alias="companySize", description="Company size"
    )
    target_markets: list[str] | None = Field(
        None, alias="targetMarkets", serialization_alias="targetMarkets", description="Array of ISO country codes"
    )

    model_config = {"populate_by_name": True}


class BrandResponse(BaseModel):
    """Schema for brand response."""

    id: UUID
    name: str
    registration_country: str = Field(..., alias="registrationCountry", serialization_alias="registrationCountry")
    company_size: CompanySize = Field(..., alias="companySize", serialization_alias="companySize")
    target_markets: list[str] = Field(..., alias="targetMarkets", serialization_alias="targetMarkets")
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime | None = Field(None, alias="updatedAt", serialization_alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Map snake_case model fields to camelCase API fields."""
        if hasattr(obj, "__dict__"):
            data = dict(obj.__dict__)
            # Map fields to camelCase
            field_mappings = {
                "registration_country": "registrationCountry",
                "company_size": "companySize",
                "target_markets": "targetMarkets",
                "created_at": "createdAt",
                "updated_at": "updatedAt",
            }
            for old_key, new_key in field_mappings.items():
                if old_key in data:
                    data[new_key] = data.pop(old_key)
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


class BrandListQuery(BaseModel):
    """Schema for brand list query parameters."""

    limit: int = Field(
        default=20, ge=1, le=MAX_PAGE_LIMIT, description="Maximum number of records to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of records to skip")


class BrandListResponse(BaseModel):
    """Schema for paginated brand list response."""

    items: list[BrandResponse]
    total: int
    limit: int
    offset: int


