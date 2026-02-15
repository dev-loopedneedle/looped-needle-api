"""Pydantic schemas for admin dashboard API."""

from datetime import datetime

from pydantic import BaseModel, Field


class AdminDashboardSummary(BaseModel):
    """Platform-wide summary metrics."""

    active_clients: int = Field(
        ...,
        ge=0,
        alias="activeClients",
        serialization_alias="activeClients",
        description="Distinct brands with at least one audit",
    )
    audits_in_last_30_days: int = Field(
        ...,
        ge=0,
        alias="auditsInLast30Days",
        serialization_alias="auditsInLast30Days",
        description="Workflows completed in the last 30 days (UTC)",
    )
    total_completed_workflows: int = Field(
        ...,
        ge=0,
        alias="totalCompletedWorkflows",
        serialization_alias="totalCompletedWorkflows",
        description="Total completed workflows",
    )
    pass_rate: int = Field(
        ...,
        ge=0,
        le=100,
        alias="passRate",
        serialization_alias="passRate",
        description="Percentage of completed workflows with any certification",
    )

    model_config = {"populate_by_name": True}


class CertificationBreakdown(BaseModel):
    """Counts of completed workflows by certification level."""

    bronze: int = Field(..., ge=0, description="Completed workflows with Bronze")
    silver: int = Field(..., ge=0, description="Completed workflows with Silver")
    gold: int = Field(..., ge=0, description="Completed workflows with Gold")


class RecentWorkflowItem(BaseModel):
    """Single workflow in the recent workflows list."""

    workflow_id: str = Field(
        ...,
        alias="workflowId",
        serialization_alias="workflowId",
        description="Workflow UUID",
    )
    audit_id: str = Field(
        ...,
        alias="auditId",
        serialization_alias="auditId",
        description="Audit UUID",
    )
    product_name: str | None = Field(
        None,
        alias="productName",
        serialization_alias="productName",
        description="From audit audit_data.productInfo.productName",
    )
    target_market: str | None = Field(
        None,
        alias="targetMarket",
        serialization_alias="targetMarket",
        description="From audit audit_data.productInfo.targetMarket",
    )
    status: str = Field(..., description="Display status (Completed, Processing, etc.)")
    updated_at: datetime = Field(
        ...,
        alias="updatedAt",
        serialization_alias="updatedAt",
        description="Workflow updated_at",
    )

    model_config = {"populate_by_name": True}


class AdminDashboardResponse(BaseModel):
    """Full admin dashboard response."""

    summary: AdminDashboardSummary
    certification_breakdown: CertificationBreakdown = Field(
        ...,
        alias="certificationBreakdown",
        serialization_alias="certificationBreakdown",
    )
    recent_workflows: list[RecentWorkflowItem] = Field(
        ...,
        alias="recentWorkflows",
        serialization_alias="recentWorkflows",
        description="Up to 10 recent workflows by updated_at desc",
    )

    model_config = {"populate_by_name": True}
