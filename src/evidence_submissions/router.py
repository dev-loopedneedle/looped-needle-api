"""Evidence submissions domain router."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_workflows.models import AuditWorkflow
from src.audits.service import AuditService
from src.auth.dependencies import UserContext, get_current_user
from src.database import get_db
from src.evidence_submissions.models import EvidenceSubmission
from src.evidence_submissions.schemas import (
    EvidenceSubmissionDetailResponse,
    EvidenceSubmissionResponse,
    Recommendation,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/audits", tags=["evidence-submissions"])


@router.get(
    "/{audit_id}/workflows/{workflow_id}/submissions",
    response_model=list[EvidenceSubmissionResponse],
    summary="List submissions for a workflow",
    description="Get all evidence submissions for a specific workflow, optionally filtered by status",
)
async def get_submissions_for_workflow(
    audit_id: UUID,
    workflow_id: UUID,
    status_filter: str | None = Query(
        None, alias="status", description="Filter by submission status"
    ),
    claim_id: UUID | None = Query(None, alias="claimId", description="Filter by claim ID"),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EvidenceSubmissionResponse]:
    """List submissions for a workflow."""
    await AuditService.verify_audit_access(db, audit_id, current_user)

    # Verify workflow exists and belongs to audit
    workflow = await db.get(AuditWorkflow, workflow_id)
    if not workflow or workflow.audit_id != audit_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Build query
    query = select(EvidenceSubmission).where(EvidenceSubmission.audit_workflow_id == workflow_id)

    if status_filter:
        query = query.where(EvidenceSubmission.status == status_filter)

    if claim_id:
        query = query.where(EvidenceSubmission.audit_workflow_claim_id == claim_id)

    query = query.order_by(EvidenceSubmission.created_at.desc())

    result = await db.execute(query)
    submissions = list(result.scalars().all())

    return [EvidenceSubmissionResponse.model_validate(s, from_attributes=True) for s in submissions]


@router.get(
    "/{audit_id}/workflows/{workflow_id}/submissions/{submission_id}",
    response_model=EvidenceSubmissionDetailResponse,
    summary="Get submission details",
    description="Get detailed information about a specific evidence submission including evaluation results",
)
async def get_submission_detail(
    audit_id: UUID,
    workflow_id: UUID,
    submission_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvidenceSubmissionDetailResponse:
    """Get submission details."""
    await AuditService.verify_audit_access(db, audit_id, current_user)

    # Verify workflow exists and belongs to audit
    workflow = await db.get(AuditWorkflow, workflow_id)
    if not workflow or workflow.audit_id != audit_id:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Get submission
    submission = await db.get(EvidenceSubmission, submission_id)
    if not submission or submission.audit_workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Submission not found")

    response_data = EvidenceSubmissionDetailResponse.model_validate(
        submission, from_attributes=True
    )

    if submission.evaluation_reasons:
        overall_verdict = submission.evaluation_reasons.get("overallVerdict", "").lower()
        if overall_verdict != "pass":
            recommendations_data = submission.evaluation_reasons.get("recommendations")
            if recommendations_data:
                response_data.recommendations = [
                    Recommendation(**rec) if isinstance(rec, dict) else rec
                    for rec in recommendations_data
                ]

    return response_data
