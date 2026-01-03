"""Schemas for brand-related resources (brands, products, supply chain)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.audit_engine.constants import MAX_PAGE_LIMIT, CompanySize


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


class ProductCreate(BaseModel):
    """Schema for creating a product."""

    name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    materials_composition: list[dict[str, Any]] = Field(
        ..., description="Materials composition with percentages"
    )
    manufacturing_processes: list[str] = Field(
        default_factory=list, description="Manufacturing processes"
    )


class ProductResponse(BaseModel):
    """Schema for product response."""

    id: UUID
    brand_id: UUID
    name: str
    category: str
    materials_composition: list[dict[str, Any]]
    manufacturing_processes: list[str]
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class SupplyChainNodeCreate(BaseModel):
    """Schema for creating a supply chain node."""

    role: str = Field(..., description="Node role (e.g., CutAndSew, FabricMill)")
    country: str = Field(..., description="ISO country code")
    tier_level: int = Field(..., gt=0, description="Tier level (1, 2, 3, etc.)")


class SupplyChainNodeResponse(BaseModel):
    """Schema for supply chain node response."""

    id: UUID
    brand_id: UUID
    role: str
    country: str
    tier_level: int
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


__all__ = [
    "BrandCreate",
    "BrandUpdate",
    "BrandResponse",
    "BrandListQuery",
    "BrandListResponse",
    "ProductCreate",
    "ProductResponse",
    "SupplyChainNodeCreate",
    "SupplyChainNodeResponse",
]

