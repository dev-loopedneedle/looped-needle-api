"""Schemas for brand resources."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.brands.constants import MAX_PAGE_LIMIT, CompanySize


class BrandCreate(BaseModel):
    """Schema for creating a brand."""

    name: str = Field(..., max_length=255, description="Brand name")
    registration_country: str = Field(..., description="ISO country code")
    company_size: CompanySize = Field(..., description="Company size")
    target_markets: list[str] = Field(..., description="Array of ISO country codes")


class BrandUpdate(BaseModel):
    """Schema for updating a brand."""

    name: str | None = Field(None, max_length=255, description="Brand name")
    registration_country: str | None = Field(None, description="ISO country code")
    company_size: CompanySize | None = Field(None, description="Company size")
    target_markets: list[str] | None = Field(None, description="Array of ISO country codes")


class BrandResponse(BaseModel):
    """Schema for brand response."""

    id: UUID
    name: str
    registration_country: str
    company_size: CompanySize
    target_markets: list[str]
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


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


