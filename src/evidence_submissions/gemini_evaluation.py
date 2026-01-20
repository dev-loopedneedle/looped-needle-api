"""Gemini evaluation service for evidence submissions."""

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_workflows.models import AuditWorkflowClaim
from src.cloud_storage.gcs_client import get_gcs_client
from src.database import AsyncSessionLocal
from src.evidence_submissions.constants import MatchDecision, SubmissionStatus
from src.evidence_submissions.exceptions import ProcessingError
from src.evidence_submissions.models import EvidenceSubmission
from src.llm.gemini_client import get_gemini_client
from src.rules.models import EvidenceClaim

logger = logging.getLogger(__name__)

VERDICT_TO_DECISION = {
    "pass": MatchDecision.MATCH,
    "fail": MatchDecision.NO_MATCH,
    "needs_review": MatchDecision.NEEDS_REVIEW,
}

MAX_CONCURRENT_GEMINI_REQUESTS = 5


def _generate_claim_id(claim_id: UUID, offset: int = 0) -> int:
    """Generate a deterministic numeric ID from UUID."""
    return int(claim_id.int) % 1000000 + offset


async def evaluate_submission_with_gemini(
    db: AsyncSession,
    submission: EvidenceSubmission,
    claim: AuditWorkflowClaim,
) -> dict[str, Any]:
    """
    Evaluate a single evidence submission using Gemini API.

    Args:
        db: Database session
        submission: Evidence submission to evaluate
        claim: Claim for this submission

    Returns:
        Full Gemini evaluation response as dict

    Raises:
        ProcessingError: If evaluation fails
    """
    try:
        evidence_claim = await db.get(EvidenceClaim, claim.evidence_claim_id)
        if not evidence_claim:
            raise ProcessingError(f"Evidence claim {claim.evidence_claim_id} not found")

        claim_id_base = _generate_claim_id(claim.id)
        claims = [
            {
                "id": claim_id_base,
                "name": evidence_claim.type.value
                if hasattr(evidence_claim.type, "value")
                else str(evidence_claim.type),
                "value": evidence_claim.name,
            }
        ]

        # Add criteria as additional claims
        if evidence_claim.criteria:
            for idx, criterion in enumerate(evidence_claim.criteria, start=1):
                claims.append(
                    {
                        "id": _generate_claim_id(claim.id, offset=idx * 100),
                        "name": "CRITERION",
                        "value": criterion,
                    }
                )

        # Download file from GCS - ensure file_path doesn't start with /
        file_path = submission.file_path.lstrip("/")
        if not file_path:
            raise ProcessingError(
                f"Invalid file_path for submission {submission.id}: empty or only slashes"
            )

        logger.info(
            f"Processing submission {submission.id}: "
            f"File: {submission.file_name}, GCS path: {file_path}"
        )

        # Download file from GCS
        try:
            gcs_client = get_gcs_client()
            file_content = await gcs_client.download_file(file_path)
            if file_content is None:
                raise ProcessingError(
                    f"File not found in GCS: {file_path}. "
                    f"Please verify the file exists and is accessible."
                )
        except Exception as download_error:
            logger.error(
                f"Failed to download file from GCS: {file_path}. Error: {download_error}",
                exc_info=True,
            )
            raise ProcessingError(
                f"Failed to download file from GCS: {file_path}. Error: {download_error}"
            ) from download_error

        # Analyze document with Gemini
        gemini_client = get_gemini_client()
        evaluation_response = await gemini_client.analyze_document(
            file_content=file_content,
            mime_type=submission.mime_type or "application/pdf",
            name=submission.file_name,
            claims=claims,
        )

        return evaluation_response

    except Exception as e:
        logger.error(
            f"Gemini evaluation failed for submission {submission.id}: "
            f"File: {submission.file_name}, Path: {submission.file_path}, "
            f"Error Type: {type(e).__name__}, Error Message: {str(e)}",
            exc_info=True,
        )
        raise ProcessingError(f"Gemini evaluation failed: {str(e)}") from e


async def process_submission_evaluation(
    db: AsyncSession,
    submission_id: UUID,
) -> None:
    """
    Process a single submission evaluation with Gemini (atomic operation).

    Args:
        db: Database session
        submission_id: Submission ID to process
    """
    submission = await db.get(EvidenceSubmission, submission_id)
    if not submission:
        logger.error(f"Submission {submission_id} not found")
        return

    try:
        submission.status = SubmissionStatus.PROCESSING
        submission.processing_started_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(submission)

        claim = await db.get(AuditWorkflowClaim, submission.audit_workflow_claim_id)
        if not claim:
            raise ProcessingError(f"Claim {submission.audit_workflow_claim_id} not found")

        evaluation_response = await evaluate_submission_with_gemini(db, submission, claim)

        overall_verdict = evaluation_response.get("overallVerdict", "needs_review")
        confidence_score = evaluation_response.get("confidenceScore", 0)
        claim_evaluations = evaluation_response.get("claimEvaluations", [])
        extracted_content = evaluation_response.get("extractedContent", {})
        classification = evaluation_response.get("classification", {})

        match_decision = VERDICT_TO_DECISION.get(
            overall_verdict.lower(), MatchDecision.NEEDS_REVIEW
        )

        submission.gemini_evaluation_response = evaluation_response
        submission.match_decision = match_decision
        submission.confidence_score = confidence_score
        submission.overall_verdict_reason = evaluation_response.get("overallVerdictReason", "")

        # Extract legacy fields for backward compatibility
        submission.extracted_text = extracted_content.get("documentTitle", "") or ""
        submission.extracted_fields = {
            "issuer": extracted_content.get("issuingOrganization", ""),
            "issue_date": extracted_content.get("issueDate", ""),
            "expiration_date": extracted_content.get("expirationDate", ""),
            "certificate_id": extracted_content.get("documentNumber", ""),
        }
        submission.document_type_detected = classification.get("detectedType", "")
        submission.category_detected = classification.get("documentCategory", "")

        # Extract recommendations if verdict is not "pass"
        recommendations = []
        if overall_verdict.lower() != "pass":
            recommendations = evaluation_response.get("recommendations", [])

        evaluation_reasons = {
            "overallVerdict": overall_verdict,
            "overallVerdictReason": evaluation_response.get("overallVerdictReason", ""),
            "claimEvaluations": [
                {
                    "claimId": ce.get("claimId"),
                    "claimName": ce.get("claimName"),
                    "result": ce.get("result"),
                    "confidence": ce.get("confidence"),
                    "reasoning": ce.get("reasoning"),
                }
                for ce in claim_evaluations
            ],
        }
        # Only include recommendations if they exist and verdict is not "pass"
        if recommendations:
            evaluation_reasons["recommendations"] = recommendations
        submission.evaluation_reasons = evaluation_reasons

        if match_decision == MatchDecision.MATCH:
            submission.status = SubmissionStatus.PROCESSING_COMPLETE
        elif match_decision == MatchDecision.NEEDS_REVIEW:
            submission.status = SubmissionStatus.NEEDS_REVIEW
        else:
            submission.status = SubmissionStatus.PROCESSING_COMPLETE

        submission.processing_completed_at = datetime.now(UTC)
        await db.commit()

    except Exception as e:
        logger.error(
            f"Error processing submission {submission_id}: "
            f"Error Type: {type(e).__name__}, Error Message: {str(e)}",
            exc_info=True,
        )
        submission.status = SubmissionStatus.PROCESSING_FAILED
        submission.error_message = f"{type(e).__name__}: {str(e)}"
        submission.processing_completed_at = datetime.now(UTC)
        await db.commit()
        raise


async def process_workflow_submissions_concurrently(
    db: AsyncSession,
    workflow_id: UUID,
    submission_ids: list[UUID],
) -> None:
    """
    Process all submissions for a workflow concurrently with controlled concurrency.

    Args:
        db: Database session (used only for final workflow status update)
        workflow_id: Workflow ID
        submission_ids: List of submission IDs to process
    """
    from src.audit_workflows.service import WorkflowSubmissionService

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_GEMINI_REQUESTS)
    processed_count = 0
    failed_count = 0

    async def process_with_limit(submission_id: UUID) -> None:
        """Process a single submission with concurrency limit and its own DB session."""
        nonlocal processed_count, failed_count
        async with AsyncSessionLocal() as submission_db:
            try:
                async with semaphore:
                    await process_submission_evaluation(submission_db, submission_id)
                processed_count += 1
            except Exception as e:
                failed_count += 1
                logger.error(
                    f"Failed to process submission {submission_id} for workflow {workflow_id}: {e}",
                    exc_info=True,
                )
                try:
                    submission = await submission_db.get(EvidenceSubmission, submission_id)
                    if submission:
                        submission.status = SubmissionStatus.PROCESSING_FAILED
                        submission.error_message = f"Processing failed: {str(e)}"
                        submission.processing_completed_at = datetime.now(UTC)
                        await submission_db.commit()
                except Exception as update_error:
                    logger.error(
                        f"Failed to update submission {submission_id} status after error: {update_error}",
                        exc_info=True,
                    )
                    await submission_db.rollback()

    try:
        await asyncio.gather(
            *[process_with_limit(sid) for sid in submission_ids], return_exceptions=True
        )

        try:
            await WorkflowSubmissionService.update_workflow_status_after_processing(db, workflow_id)
        except Exception as status_update_error:
            logger.error(
                f"Failed to update workflow {workflow_id} status after processing: "
                f"Error Type: {type(status_update_error).__name__}, "
                f"Error Message: {str(status_update_error)}",
                exc_info=True,
            )
            # Re-raise to be caught by outer handler
            raise

    except Exception as e:
        logger.error(
            f"Critical error processing workflow {workflow_id} submissions: "
            f"Error Type: {type(e).__name__}, Error Message: {str(e)}",
            exc_info=True,
        )
        try:
            await WorkflowSubmissionService.update_workflow_status_after_processing(db, workflow_id)
        except Exception as status_error:
            logger.error(
                f"Failed to update workflow {workflow_id} status after error: "
                f"Error Type: {type(status_error).__name__}, Error Message: {str(status_error)}",
                exc_info=True,
            )
        raise
