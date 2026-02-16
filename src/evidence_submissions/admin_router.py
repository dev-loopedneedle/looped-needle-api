"""Admin endpoints for evidence submissions."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import UserContext
from src.cloud_storage.gcs_client import get_gcs_client
from src.database import get_db
from src.evidence_submissions.models import EvidenceSubmission
from src.evidence_submissions.schemas import DownloadUrlResponse, EvidenceEvaluationReportResponse
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


@router.get(
    "/evidence-submissions/{submission_id}/download-url",
    response_model=DownloadUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Get signed download URL (Admin only)",
    description="Generate a signed URL to download or view an evidence submission file. "
    "PDFs and images display in the browser; other files download. Admin access required.",
)
async def get_evidence_download_url(
    submission_id: UUID,
    _: UserContext = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
) -> DownloadUrlResponse:
    """
    Get a signed download URL for an evidence submission file.

    Validates admin user, loads the submission, and generates a time-limited
    signed URL for the GCS object. Frontend can open this URL in a new tab.
    """
    submission = await db.get(EvidenceSubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Evidence submission not found")

    file_path = submission.file_path.lstrip("/")
    if not file_path:
        raise HTTPException(
            status_code=404,
            detail="Evidence submission has no valid file path",
        )

    gcs_client = get_gcs_client()
    exists = await gcs_client.file_exists(file_path)
    if not exists:
        raise HTTPException(
            status_code=404,
            detail="File not found in storage",
        )

    try:
        download_url = await gcs_client.generate_download_signed_url(file_path)
        return DownloadUrlResponse(download_url=download_url)
    except Exception as e:
        logger.error(f"Failed to generate download URL for submission {submission_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate download URL",
        ) from e

