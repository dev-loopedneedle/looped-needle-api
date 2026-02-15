"""Admin dashboard service: platform-wide metrics and recent workflows."""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin.constants import PROCESSING_COMPLETE, RECENT_WORKFLOWS_LIMIT
from src.audit_workflows.models import AuditWorkflow, AuditWorkflowStatus
from src.audits.models import Audit
from src.brands.models import Brand


# Display labels for workflow status (spec: "Completed" | "Processing" | "Generated" | "Failed")
STATUS_LABELS = {
    AuditWorkflowStatus.PROCESSING_COMPLETE: "Completed",
    AuditWorkflowStatus.PROCESSING: "Processing",
    AuditWorkflowStatus.GENERATED: "Generated",
    AuditWorkflowStatus.PROCESSING_FAILED: "Failed",
}


def _extract_product_info(audit_data: dict[str, Any] | None) -> tuple[str | None, str | None]:
    """Extract productName and targetMarket from audit_data.productInfo."""
    if not audit_data:
        return (None, None)
    product_info = audit_data.get("productInfo")
    if not product_info or not isinstance(product_info, dict):
        return (None, None)
    product_name = product_info.get("productName")
    target_market = product_info.get("targetMarket")
    return (
        str(product_name) if product_name else None,
        str(target_market) if target_market else None,
    )


async def get_dashboard_data(db: AsyncSession) -> dict[str, Any]:
    """
    Build admin dashboard: summary metrics, certification breakdown, recent workflows.

    Uses existing tables only (brands, audits, audit_workflows). All counts use
    status = PROCESSING_COMPLETE for "completed" workflows; 30d window uses UTC.
    """
    now_utc = datetime.now(timezone.utc)
    cutoff_30d = now_utc - timedelta(days=30)

    # --- Active clients: distinct brands with at least one audit, brand not deleted
    active_clients_q = (
        select(func.count(func.distinct(Audit.brand_id)))
        .select_from(Audit)
        .join(Brand, Audit.brand_id == Brand.id)
        .where(Brand.deleted_at.is_(None))
    )
    active_clients_result = await db.execute(active_clients_q)
    active_clients = active_clients_result.scalar_one() or 0

    # --- Completed workflows: total and in last 30 days (by updated_at UTC)
    total_q = select(func.count()).select_from(AuditWorkflow).where(
        AuditWorkflow.status == PROCESSING_COMPLETE
    )
    total_result = await db.execute(total_q)
    total_completed = total_result.scalar_one() or 0

    in_30d_q = select(func.count()).select_from(AuditWorkflow).where(
        AuditWorkflow.status == PROCESSING_COMPLETE,
        AuditWorkflow.updated_at.isnot(None),
        AuditWorkflow.updated_at >= cutoff_30d,
    )
    in_30d_result = await db.execute(in_30d_q)
    audits_in_last_30_days = in_30d_result.scalar_one() or 0

    # --- Pass rate: (workflows with any certification) / total_completed * 100, 0 if 0
    certified_q = select(func.count()).select_from(AuditWorkflow).where(
        AuditWorkflow.status == PROCESSING_COMPLETE,
        AuditWorkflow.certification.isnot(None),
    )
    certified_result = await db.execute(certified_q)
    certified_count = certified_result.scalar_one() or 0
    pass_rate = (certified_count * 100 // total_completed) if total_completed else 0
    pass_rate = min(100, pass_rate)

    # --- Certification breakdown (Bronze, Silver, Gold)
    bronze_q = select(func.count()).select_from(AuditWorkflow).where(
        AuditWorkflow.status == PROCESSING_COMPLETE,
        AuditWorkflow.certification == "Bronze",
    )
    silver_q = select(func.count()).select_from(AuditWorkflow).where(
        AuditWorkflow.status == PROCESSING_COMPLETE,
        AuditWorkflow.certification == "Silver",
    )
    gold_q = select(func.count()).select_from(AuditWorkflow).where(
        AuditWorkflow.status == PROCESSING_COMPLETE,
        AuditWorkflow.certification == "Gold",
    )
    bronze_result = await db.execute(bronze_q)
    silver_result = await db.execute(silver_q)
    gold_result = await db.execute(gold_q)
    bronze = bronze_result.scalar_one() or 0
    silver = silver_result.scalar_one() or 0
    gold = gold_result.scalar_one() or 0

    # --- Recent workflows: join workflow + audit, order by workflow.updated_at DESC, limit 10
    recent_q = (
        select(AuditWorkflow, Audit)
        .join(Audit, AuditWorkflow.audit_id == Audit.id)
        .order_by(
            AuditWorkflow.updated_at.desc().nulls_last(),
            AuditWorkflow.created_at.desc(),
        )
        .limit(RECENT_WORKFLOWS_LIMIT)
    )
    recent_result = await db.execute(recent_q)
    rows = recent_result.all()

    recent_workflows = []
    for workflow, audit in rows:
        product_name, target_market = _extract_product_info(audit.audit_data)
        status_label = STATUS_LABELS.get(workflow.status, workflow.status or "Unknown")
        updated_at = workflow.updated_at or workflow.created_at
        recent_workflows.append(
            {
                "workflow_id": str(workflow.id),
                "audit_id": str(audit.id),
                "product_name": product_name,
                "target_market": target_market,
                "status": status_label,
                "updated_at": updated_at,
            }
        )

    return {
        "summary": {
            "active_clients": active_clients,
            "audits_in_last_30_days": audits_in_last_30_days,
            "total_completed_workflows": total_completed,
            "pass_rate": pass_rate,
        },
        "certification_breakdown": {"bronze": bronze, "silver": silver, "gold": gold},
        "recent_workflows": recent_workflows,
    }
