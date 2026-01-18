"""Admin endpoints for evidence submissions."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import UserContext
from src.database import get_db
from src.evidence_submissions.models import EvidenceSubmission
from src.evidence_submissions.schemas import EvidenceEvaluationReportResponse
from src.rules.dependencies import get_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin", "evidence-submissions"])


@router.get(
    "/evidence-submissions/{submission_id}/evaluation-report",
    response_model=EvidenceEvaluationReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get full evidence evaluation report (Admin only)",
    description="Retrieve the complete Gemini evaluation report for a specific evidence submission. "
    "This includes the full gemini_evaluation_response with all analysis details. Admin access required.",
)
async def get_evidence_evaluation_report(
    submission_id: UUID,
    current_user: UserContext = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
) -> EvidenceEvaluationReportResponse:
    """
    Get full evidence evaluation report for admin.

    Returns the complete Gemini evaluation response including:
    - Overall verdict and reasoning
    - Claim evaluations
    - Authenticity analysis
    - Visual analysis
    - Issuer analysis
    - And all other evaluation details
    """
    submission = await db.get(EvidenceSubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Evidence submission not found")

    return EvidenceEvaluationReportResponse(
        submission_id=submission.id,
        file_name=submission.file_name,
        status=submission.status,
        gemini_evaluation_response=submission.gemini_evaluation_response,
        match_decision=submission.match_decision,
        confidence_score=submission.confidence_score,
        overall_verdict_reason=submission.overall_verdict_reason,
        processing_started_at=submission.processing_started_at,
        processing_completed_at=submission.processing_completed_at,
    )

