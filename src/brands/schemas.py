"""Schemas for brand resources."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from src.brands.constants import MAX_PAGE_LIMIT, CompanySize


class BrandCreate(BaseModel):
    """Schema for creating a brand."""

    name: str = Field(..., max_length=255, description="Brand name")
    registration_country: str = Field(
        ...,
        alias="registrationCountry",
        serialization_alias="registrationCountry",
        description="ISO country code",
    )
    company_size: CompanySize = Field(
        ..., alias="companySize", serialization_alias="companySize", description="Company size"
    )
    target_markets: list[str] = Field(
        ...,
        alias="targetMarkets",
        serialization_alias="targetMarkets",
        description="Array of ISO country codes",
    )

    model_config = {"populate_by_name": True}


class BrandUpdate(BaseModel):
    """Schema for updating a brand."""

    name: str | None = Field(None, max_length=255, description="Brand name")
    registration_country: str | None = Field(
        None,
        alias="registrationCountry",
        serialization_alias="registrationCountry",
        description="ISO country code",
    )
    company_size: CompanySize | None = Field(
        None, alias="companySize", serialization_alias="companySize", description="Company size"
    )
    target_markets: list[str] | None = Field(
        None,
        alias="targetMarkets",
        serialization_alias="targetMarkets",
        description="Array of ISO country codes",
    )

    model_config = {"populate_by_name": True}


class BrandResponse(BaseModel):
    """Schema for brand response."""

    id: UUID
    name: str
    registration_country: str = Field(
        ..., alias="registrationCountry", serialization_alias="registrationCountry"
    )
    company_size: CompanySize = Field(..., alias="companySize", serialization_alias="companySize")
    target_markets: list[str] = Field(
        ..., alias="targetMarkets", serialization_alias="targetMarkets"
    )
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


# Dashboard schemas
class CategoryScore(BaseModel):
    """Category score schema."""

    category: str = Field(
        ..., description="Category name: ENVIRONMENTAL, SOCIAL, CIRCULARITY, or TRANSPARENCY"
    )
    score: int = Field(..., ge=0, le=100, description="Numeric score for the category (0-100)")
    hasClaims: bool = Field(
        ...,
        alias="hasClaims",
        serialization_alias="hasClaims",
        description="Whether this category had any evidence claims evaluated. False means no claims existed for this category.",
    )

    model_config = {"populate_by_name": True}


class DashboardSummary(BaseModel):
    """Dashboard summary metrics."""

    totalAudits: int = Field(
        ...,
        ge=0,
        alias="totalAudits",
        serialization_alias="totalAudits",
        description="Total number of audits for the brand",
    )
    completedAudits: int = Field(
        ...,
        ge=0,
        alias="completedAudits",
        serialization_alias="completedAudits",
        description="Number of audits with completed workflows",
    )

    model_config = {"populate_by_name": True}


class LatestAuditScores(BaseModel):
    """Latest completed audit scores."""

    auditId: str = Field(
        ...,
        alias="auditId",
        serialization_alias="auditId",
        description="UUID of the latest completed audit",
    )
    workflowId: str = Field(
        ...,
        alias="workflowId",
        serialization_alias="workflowId",
        description="UUID of the latest completed audit workflow",
    )
    productName: str | None = Field(
        None,
        alias="productName",
        serialization_alias="productName",
        description="Product name from audit data",
    )
    targetMarket: str | None = Field(
        None,
        alias="targetMarket",
        serialization_alias="targetMarket",
        description="Target market from audit data",
    )
    completedAt: datetime = Field(
        ...,
        alias="completedAt",
        serialization_alias="completedAt",
        description="Timestamp when the audit workflow was completed",
    )
    categoryScores: list[CategoryScore] = Field(
        ...,
        alias="categoryScores",
        serialization_alias="categoryScores",
        description="Category scores for the audit",
    )
    overallScore: int | None = Field(
        None,
        ge=0,
        le=100,
        alias="overallScore",
        serialization_alias="overallScore",
        description="Average percent of all category scores (0-100)",
    )
    certification: str | None = Field(
        None,
        alias="certification",
        serialization_alias="certification",
        description="Certification level: Bronze (>60%), Silver (>75%), Gold (>90%). Only awarded when data_completeness > 90",
    )

    model_config = {"populate_by_name": True}


class RecentAuditWorkflow(BaseModel):
    """Recent audit workflow information."""

    workflowId: str = Field(
        ...,
        alias="workflowId",
        serialization_alias="workflowId",
        description="UUID of the workflow",
    )
    auditId: str = Field(
        ..., alias="auditId", serialization_alias="auditId", description="UUID of the audit"
    )
    productName: str | None = Field(
        None,
        alias="productName",
        serialization_alias="productName",
        description="Product name from audit data",
    )
    targetMarket: str | None = Field(
        None,
        alias="targetMarket",
        serialization_alias="targetMarket",
        description="Target market from audit data",
    )
    status: str = Field(
        ..., description="User-friendly display status: Completed, Processing, Generated, or Failed"
    )
    categoryScores: list[CategoryScore] | None = Field(
        None,
        alias="categoryScores",
        serialization_alias="categoryScores",
        description="Category scores (only present if status is Completed)",
    )
    overallScore: int | None = Field(
        None,
        ge=0,
        le=100,
        alias="overallScore",
        serialization_alias="overallScore",
        description="Average percent of all category scores (0-100, only present if status is Completed)",
    )
    certification: str | None = Field(
        None,
        alias="certification",
        serialization_alias="certification",
        description="Certification level: Bronze (>60%), Silver (>75%), Gold (>90%). Only awarded when data_completeness > 90 (only present if status is Completed)",
    )
    createdAt: datetime = Field(
        ...,
        alias="createdAt",
        serialization_alias="createdAt",
        description="Timestamp when the workflow was created",
    )

    model_config = {"populate_by_name": True}


class DashboardResponse(BaseModel):
    """Dashboard response schema."""

    summary: DashboardSummary = Field(..., description="Summary metrics")
    latestAuditScores: LatestAuditScores | None = Field(
        None,
        alias="latestAuditScores",
        serialization_alias="latestAuditScores",
        description="Latest completed audit scores (null if no completed audits)",
    )
    recentAuditWorkflows: list[RecentAuditWorkflow] = Field(
        ...,
        alias="recentAuditWorkflows",
        serialization_alias="recentAuditWorkflows",
        description="List of up to 3 most recent workflows ordered by workflow updated_at (newest first)",
    )

    model_config = {"populate_by_name": True}
