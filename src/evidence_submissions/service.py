"""Service layer for evidence submissions domain."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_workflows.models import AuditWorkflowClaim
from src.cloud_storage.gcs_client import get_gcs_client
from src.evidence_submissions.constants import (
    MAX_FILE_SIZE_BYTES,
    SUPPORTED_MIME_TYPES,
    SubmissionStatus,
)
from src.evidence_submissions.exceptions import InvalidFileError
from src.evidence_submissions.gemini_evaluation import (
    process_workflow_submissions_concurrently,
)
from src.evidence_submissions.models import EvidenceSubmission
from src.rules.constants import EvidenceClaimCategory, EvidenceClaimType
from src.rules.models import EvidenceClaim

logger = logging.getLogger(__name__)


class SubmissionService:
    """Service for evidence submission operations."""

    @staticmethod
    async def validate_file_paths(
        db: AsyncSession,
        file_paths: list[str],
    ) -> None:
        """
        Validate that file paths exist in Google Cloud Storage.

        Args:
            db: Database session
            file_paths: List of file paths to validate

        Raises:
            InvalidFileError: If any file path is invalid or file doesn't exist
        """
        gcs_client = get_gcs_client()

        for file_path in file_paths:
            if not file_path or not file_path.strip():
                raise InvalidFileError(f"Invalid file path: {file_path}")

            # Validate file exists in GCS
            exists = await gcs_client.file_exists(file_path)
            if not exists:
                raise InvalidFileError(f"File not found in GCS: {file_path}")

    @staticmethod
    async def create_submissions_for_workflow(
        db: AsyncSession,
        workflow_id: UUID,
        claim_id: UUID,
        file_path: str,
        file_name: str,
        file_size: int | None = None,
        mime_type: str | None = None,
    ) -> EvidenceSubmission:
        """
        Create a submission record for a workflow.

        Args:
            db: Database session
            workflow_id: Workflow ID
            claim_id: Claim ID
            file_path: Storage path to the file
            file_name: Original file name
            file_size: File size in bytes
            mime_type: MIME type

        Returns:
            EvidenceSubmission: Created submission record
        """
        # Validate file size if provided
        if file_size is not None and file_size > MAX_FILE_SIZE_BYTES:
            raise InvalidFileError(
                f"File size {file_size} exceeds maximum {MAX_FILE_SIZE_BYTES} bytes"
            )

        # Validate MIME type if provided
        if mime_type is not None and mime_type not in SUPPORTED_MIME_TYPES:
            raise InvalidFileError(f"Unsupported MIME type: {mime_type}")

        submission = EvidenceSubmission(
            audit_workflow_id=workflow_id,
            audit_workflow_claim_id=claim_id,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            status=SubmissionStatus.PENDING_PROCESSING,
        )

        db.add(submission)
        await db.commit()
        await db.refresh(submission)

        logger.info(
            f"Created submission {submission.id} for workflow {workflow_id}, claim {claim_id}"
        )
        return submission

    @staticmethod
    async def evaluate_submission_match(
        db: AsyncSession,
        submission: EvidenceSubmission,
        claim: AuditWorkflowClaim,
    ) -> tuple[str, int, dict[str, Any]]:
        """
        Evaluate evidence submission against claim requirements.

        Args:
            db: Database session
            submission: Evidence submission to evaluate
            claim: Claim to match against

        Returns:
            Tuple of (match_decision, confidence_score, evaluation_reasons)
        """
        # Load evidence claim definition
        evidence_claim_result = await db.get(EvidenceClaim, claim.evidence_claim_id)
        if not evidence_claim_result:
            return "NO_MATCH", 0, {"error": "Evidence claim definition not found"}

        evidence_claim = evidence_claim_result

        matched_fields: list[str] = []
        missing_fields: list[str] = []
        mismatches: list[dict[str, Any]] = []

        # Helper function to get enum value (handles both enum and string)
        def get_enum_value(value: EvidenceClaimType | EvidenceClaimCategory | str) -> str:
            """Get string value from enum or return string directly."""
            if isinstance(value, (EvidenceClaimType, EvidenceClaimCategory)):
                return value.value
            return str(value)

        # Check document type match
        if submission.document_type_detected:
            claim_type_str = get_enum_value(evidence_claim.type)
            if submission.document_type_detected.upper() == claim_type_str.upper():
                matched_fields.append("document_type")
            else:
                mismatches.append(
                    {
                        "field": "document_type",
                        "expected": claim_type_str,
                        "detected": submission.document_type_detected,
                    }
                )

        # Check category match
        if submission.category_detected:
            claim_category_str = get_enum_value(evidence_claim.category)
            if submission.category_detected.upper() == claim_category_str.upper():
                matched_fields.append("category")
            else:
                mismatches.append(
                    {
                        "field": "category",
                        "expected": claim_category_str,
                        "detected": submission.category_detected,
                    }
                )

        # Check key fields presence (if extracted_fields available)
        if submission.extracted_fields:
            # Check for issuer, dates, IDs based on claim type
            claim_type_str = get_enum_value(evidence_claim.type)
            if claim_type_str in ["CERTIFICATE", "INVOICE"]:
                if not submission.extracted_fields.get("issuer"):
                    missing_fields.append("issuer")
                else:
                    matched_fields.append("issuer")

                if not submission.extracted_fields.get("issue_date"):
                    missing_fields.append("issue_date")

        # Calculate confidence score
        total_checks = len(matched_fields) + len(missing_fields) + len(mismatches)
        if total_checks == 0:
            confidence_score = 50  # Neutral if no checks possible
        else:
            match_ratio = len(matched_fields) / total_checks if total_checks > 0 else 0
            mismatch_penalty = len(mismatches) * 0.3  # Each mismatch reduces confidence
            confidence_score = int((match_ratio * 100) - (mismatch_penalty * 100))
            confidence_score = max(0, min(100, confidence_score))

        # Determine match decision
        if len(mismatches) > 0:
            match_decision = "NO_MATCH"
        elif confidence_score >= 60:
            match_decision = "MATCH"
        else:
            match_decision = "NEEDS_REVIEW"

        evaluation_reasons = {
            "matched": matched_fields,
            "missing": missing_fields,
            "mismatches": mismatches,
        }

        return match_decision, confidence_score, evaluation_reasons

    @staticmethod
    def calculate_confidence_score(
        matched_fields: list[str],
        missing_fields: list[str],
        mismatches: list[dict[str, Any]],
    ) -> int:
        """
        Calculate confidence score (0-100) based on match evaluation.

        Args:
            matched_fields: List of fields that matched
            missing_fields: List of required fields that were missing
            mismatches: List of mismatched fields

        Returns:
            Confidence score from 0 to 100
        """
        total_checks = len(matched_fields) + len(missing_fields) + len(mismatches)
        if total_checks == 0:
            return 50  # Neutral if no checks possible

        match_ratio = len(matched_fields) / total_checks if total_checks > 0 else 0
        mismatch_penalty = len(mismatches) * 0.3  # Each mismatch reduces confidence
        missing_penalty = (
            len(missing_fields) * 0.1
        )  # Each missing field reduces confidence slightly

        confidence_score = int(
            (match_ratio * 100) - (mismatch_penalty * 100) - (missing_penalty * 100)
        )
        return max(0, min(100, confidence_score))

    @staticmethod
    def generate_evaluation_reasons(
        matched_fields: list[str],
        missing_fields: list[str],
        mismatches: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generate structured reasons for match decision.

        Args:
            matched_fields: List of fields that matched
            missing_fields: List of required fields that were missing
            mismatches: List of mismatched fields with expected/detected values

        Returns:
            Dictionary with evaluation reasons
        """
        return {
            "matched": matched_fields,
            "missing": missing_fields,
            "mismatches": mismatches,
        }

    @staticmethod
    async def process_workflow_submissions(
        db: AsyncSession,
        workflow_id: UUID,
        submission_ids: list[UUID],
    ) -> None:
        """
        Process all submissions for a workflow concurrently using Gemini evaluation.

        Delegates to the Gemini evaluation service for concurrent processing.

        Args:
            db: Database session (used only for final workflow status update)
            workflow_id: Workflow ID
            submission_ids: List of submission IDs to process
        """
        await process_workflow_submissions_concurrently(db, workflow_id, submission_ids)
