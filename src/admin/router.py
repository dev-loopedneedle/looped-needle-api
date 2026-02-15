"""Admin dashboard router. Uses get_admin (rules.dependencies) for 403 when non-admin; get_db for DB session."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.schemas import (
    AdminDashboardResponse,
    AdminDashboardSummary,
    CertificationBreakdown,
    RecentWorkflowItem,
)
from src.admin.service import get_dashboard_data
from src.database import get_db
from src.rules.dependencies import get_admin

router = APIRouter(prefix="/api/v1/admin", tags=["admin", "admin-dashboard"])


@router.get(
    "/dashboard",
    status_code=status.HTTP_200_OK,
    summary="Get admin dashboard",
    description="Platform-wide metrics, certification breakdown, and recent workflows. Admin only.",
    response_model=AdminDashboardResponse,
)
async def get_dashboard(
    _: None = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminDashboardResponse:
    """Return platform-wide dashboard data (summary, certification breakdown, recent workflows)."""
    data = await get_dashboard_data(db)
    summary = AdminDashboardSummary(**data["summary"])
    certification_breakdown = CertificationBreakdown(**data["certification_breakdown"])
    recent_workflows = [
        RecentWorkflowItem(
            workflow_id=item["workflow_id"],
            audit_id=item["audit_id"],
            product_name=item["product_name"],
            target_market=item["target_market"],
            status=item["status"],
            updated_at=item["updated_at"],
        )
        for item in data["recent_workflows"]
    ]
    return AdminDashboardResponse(
        summary=summary,
        certification_breakdown=certification_breakdown,
        recent_workflows=recent_workflows,
    )
