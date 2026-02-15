"""Audits domain Pydantic schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer, field_validator


# Nested schemas
class ProductInfo(BaseModel):
    """Product information schema."""

    productName: str | None = Field(None, description="Product name (optional)")
    productCategory: str | None = Field(None, description="Product category (optional)")
    description: str | None = Field(None, description="Product description (optional)")
    auditScope: Literal["Single Product", "Collection", "Brand-wide"] | None = Field(
        None, description="Audit scope (optional)"
    )
    targetMarket: str | None = Field(None, description="Target market (optional)")

    @field_validator("description", "productName", "targetMarket", "productCategory")
    @classmethod
    def empty_string_to_none(cls, v: str | None) -> str | None:
        """Convert empty strings to None."""
        return None if v == "" else v


class Materials(BaseModel):
    """Materials schema."""

    primary: str | None = Field(None, description="Primary material (optional)")
    secondary: str | None = Field(None, description="Secondary material (optional)")
    recycledContent: float | None = Field(
        None, ge=0, le=100, description="Recycled content percentage (0-100, optional)"
    )
    originCountry: str | None = Field(None, description="Origin country (optional)")
    certifiedOrganic: bool = Field(default=False, description="Certified organic (default: false)")

    @field_validator("secondary", "originCountry", "primary")
    @classmethod
    def empty_string_to_none(cls, v: str | None) -> str | None:
        """Convert empty strings to None."""
        return None if v == "" else v


class Facility(BaseModel):
    """Facility information schema."""

    facilityName: str | None = Field(None, description="Facility name (optional)")
    city: str | None = Field(None, description="City (optional)")
    country: str | None = Field(None, description="Country (optional)")
    address: str | None = Field(None, description="Address (optional)")
    additionalNotes: str | None = Field(None, description="Additional notes (optional)")

    @field_validator("city", "country", "address", "additionalNotes", "facilityName")
    @classmethod
    def empty_string_to_none(cls, v: str | None) -> str | None:
        """Convert empty strings to None."""
        return None if v == "" else v


class Visibility(BaseModel):
    """Supply chain visibility schema."""

    tier1Documented: bool = Field(default=False, description="Tier 1 documented (default: false)")
    tier2Documented: bool = Field(default=False, description="Tier 2 documented (default: false)")
    tier3Documented: bool = Field(default=False, description="Tier 3 documented (default: false)")
    thirdPartyAudits: bool = Field(default=False, description="Third party audits (default: false)")


class SupplyChain(BaseModel):
    """Supply chain schema."""

    primaryManufacturingCountry: str | None = Field(
        None, description="Primary manufacturing country (optional)"
    )
    mainFactory: Facility | None = Field(None, description="Main factory (optional)")
    fabricSupplier: Facility | None = Field(None, description="Fabric supplier (optional)")
    dyehouse: Facility | None = Field(None, description="Dyehouse (optional)")
    printingFacility: Facility | None = Field(None, description="Printing facility (optional)")
    visibility: Visibility | None = Field(None, description="Visibility (optional)")


class Environmental(BaseModel):
    """Environmental sustainability schema."""

    chemicalManagement: bool = Field(
        default=False, description="Chemical management (default: false)"
    )
    waterTreatment: bool = Field(default=False, description="Water treatment (default: false)")
    wasteReduction: bool = Field(default=False, description="Waste reduction (default: false)")


class Social(BaseModel):
    """Social sustainability schema."""

    fairWage: bool = Field(default=False, description="Fair wage (default: false)")
    workerSafety: bool = Field(default=False, description="Worker safety (default: false)")


class Circularity(BaseModel):
    """Circularity schema."""

    takeBackProgram: bool = Field(default=False, description="Take back program (default: false)")
    repairService: bool = Field(default=False, description="Repair service (default: false)")
    designedForRecyclability: bool = Field(
        default=False, description="Designed for recyclability (default: false)"
    )
    durabilityTesting: bool = Field(
        default=False, description="Durability testing (default: false)"
    )
    careInstructions: bool = Field(default=False, description="Care instructions (default: false)")


class Sustainability(BaseModel):
    """Sustainability schema."""

    environmental: Environmental | None = Field(None, description="Environmental (optional)")
    primaryEnergySource: str | None = Field(None, description="Primary energy source (optional)")

    @field_validator("primaryEnergySource")
    @classmethod
    def empty_string_to_none_energy(cls, v: str | None) -> str | None:
        """Convert empty strings to None."""
        return None if v == "" else v

    social: Social | None = Field(None, description="Social (optional)")
    circularity: Circularity | None = Field(None, description="Circularity (optional)")


class AuditData(BaseModel):
    """Audit data schema."""

    productInfo: ProductInfo | None = Field(None, description="Product information (optional)")
    materials: Materials | None = Field(None, description="Materials (optional)")
    supplyChain: SupplyChain | None = Field(None, description="Supply chain (optional)")
    sustainability: Sustainability | None = Field(None, description="Sustainability (optional)")


# Request/Response schemas
class CreateAuditRequest(BaseModel):
    """Schema for creating an audit."""

    brand_id: UUID = Field(
        ..., alias="brandId", serialization_alias="brandId", description="Brand ID (required)"
    )
    audit_data: AuditData | None = Field(
        None,
        alias="auditData",
        serialization_alias="auditData",
        description="Audit data (optional for drafts)",
    )

    model_config = {"populate_by_name": True}


class UpdateAuditRequest(BaseModel):
    """Schema for updating an audit (status cannot be set directly)."""

    brand_id: UUID | None = Field(
        None, alias="brandId", serialization_alias="brandId", description="Brand ID (optional)"
    )
    audit_data: AuditData | None = Field(
        None,
        alias="auditData",
        serialization_alias="auditData",
        description="Audit data (optional)",
    )

    model_config = {"populate_by_name": True}


class AuditResponse(BaseModel):
    """Schema for audit response."""

    id: UUID
    brand_id: UUID = Field(..., alias="brandId", serialization_alias="brandId")
    status: Literal["DRAFT", "PUBLISHED"]
    audit_data: AuditData | None = Field(
        None,
        alias="auditData",
        serialization_alias="auditData",
        description="Audit data (optional for drafts)",
    )
    created_at: datetime = Field(..., alias="createdAt", serialization_alias="createdAt")
    updated_at: datetime | None = Field(
        None,
        alias="updatedAt",
        serialization_alias="updatedAt",
        description="Last update timestamp",
    )

    model_config = {"from_attributes": True, "populate_by_name": True}

    @field_serializer("id")
    def serialize_id(self, value: UUID) -> str:
        """Convert UUID to string."""
        return str(value)

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Map snake_case model fields to camelCase API fields."""
        if hasattr(obj, "__dict__"):
            data = dict(obj.__dict__)
            # Map fields to camelCase
            if "brand_id" in data:
                data["brandId"] = data.pop("brand_id")
            if "audit_data" in data:
                data["auditData"] = data.pop("audit_data")
            if "created_at" in data:
                data["createdAt"] = data.pop("created_at")
            if "updated_at" in data:
                data["updatedAt"] = data.pop("updated_at")
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


class AuditListQuery(BaseModel):
    """Schema for audit list query parameters."""

    brand_id: UUID | None = Field(None, description="Filter by brand ID (optional)")
    status: Literal["DRAFT", "PUBLISHED"] | None = Field(
        None, description="Filter by audit status (optional)"
    )
    scope: Literal["Single Product", "Collection", "Brand-wide"] | None = Field(
        None, description="Filter by audit scope from audit_data.productInfo.auditScope (optional)"
    )
    category: str | None = Field(
        None,
        description="Filter by product category from audit_data.productInfo.productCategory (optional)",
    )
    limit: int = Field(default=20, ge=1, le=50, description="Maximum number of records to return")
    offset: int = Field(default=0, ge=0, description="Number of records to skip")


class AuditListResponse(BaseModel):
    """Schema for paginated audit list response."""

    items: list[AuditResponse]
    total: int
    limit: int
    offset: int
