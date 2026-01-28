"""Audit workflows domain router."""

import logging
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_workflows.schemas import (
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowSubmissionRequest,
    WorkflowSubmissionResponse,
    WorkflowSummary,
)
from src.audit_workflows.service import WorkflowService, WorkflowSubmissionService
from src.audits.service import AuditService
from src.auth.dependencies import UserContext, get_current_user
from src.cloud_storage.gcs_client import get_gcs_client
from src.database import get_db
from src.evidence_submissions.constants import MAX_FILE_SIZE_BYTES, SUPPORTED_MIME_TYPES
from src.evidence_submissions.exceptions import FileNotFoundError, InvalidFileError
from src.evidence_submissions.models import EvidenceSubmission
from src.evidence_submissions.schemas import UploadUrlRequest, UploadUrlResponse
from src.evidence_submissions.service import SubmissionService
from src.rules.dependencies import get_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/audits", tags=["audit-workflows"])


@router.post(
    "/{audit_id}/workflow/generate",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate audit workflow",
    description="Generate a new workflow for an audit. Works for both draft and published audits.",
)
async def generate_workflow(
    audit_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    """Generate a new workflow for an audit."""
    await AuditService.verify_audit_access(db, audit_id, current_user)
    workflow = await WorkflowService.generate_workflow(db, audit_id)

    workflow_data = await WorkflowService.build_workflow_response(db, workflow)
    return WorkflowResponse(**workflow_data)


@router.get(
    "/{audit_id}/workflows",
    response_model=WorkflowListResponse,
    summary="List audit workflows",
    description="Retrieve a paginated list of workflows for an audit, ordered by creation date (newest first).",
)
async def list_workflows(
    audit_id: UUID,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of workflows to return"),
    offset: int = Query(0, ge=0, description="Number of workflows to skip"),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowListResponse:
    """List workflows for an audit."""
    await AuditService.verify_audit_access(db, audit_id, current_user)

    workflows, total = await WorkflowService.list_workflows(
        db, audit_id, limit=limit, offset=offset
    )

    return WorkflowListResponse(
        items=[WorkflowSummary.model_validate(w, from_attributes=True) for w in workflows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{audit_id}/workflows/{workflow_id}/upload-url",
    response_model=UploadUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate GCS upload URL for evidence file",
    description="Generate a signed URL for direct upload to Google Cloud Storage. Frontend uses this URL to upload files directly to GCS without exposing credentials.",
)
async def generate_upload_url(
    audit_id: UUID,
    workflow_id: UUID,
    request: UploadUrlRequest,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UploadUrlResponse:
    """
    Generate signed URL for GCS file upload.

    Validates file type, size, and that the claim belongs to the workflow.
    Optionally handles file replacement if previousFilePath is provided.
    """
    audit = await AuditService.verify_audit_access(db, audit_id, current_user)

    # Verify workflow exists and belongs to audit
    workflow = await WorkflowService.get_workflow_by_id(db, audit_id, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Verify claim exists and belongs to workflow
    claim = await WorkflowService.verify_claim_belongs_to_workflow(
        db, request.claim_id, workflow_id
    )
    if not claim:
        raise HTTPException(
            status_code=404,
            detail=f"Claim {request.claim_id} not found or does not belong to workflow",
        )

    # Validate file type
    if request.mime_type not in SUPPORTED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(SUPPORTED_MIME_TYPES)}",
        )

    # Validate file size
    if request.file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES} bytes (50MB)",
        )

    # Handle file replacement if previousFilePath provided
    gcs_client = get_gcs_client()

    if request.previous_file_path:
        # Validate previous file path belongs to same workflow
        if not gcs_client.validate_path_belongs_to_workflow(
            request.previous_file_path, audit.brand_id, audit_id, workflow_id
        ):
            raise HTTPException(
                status_code=400,
                detail="Previous file path does not belong to this workflow",
            )

        # Delete old file
        try:
            await gcs_client.delete_file(request.previous_file_path)
        except Exception as e:
            logger.warning(f"Failed to delete previous file {request.previous_file_path}: {e}")
            # Continue anyway - new file will overwrite if same path

    # Generate GCS path
    file_path = gcs_client.generate_gcs_path(
        brand_id=audit.brand_id,
        audit_id=audit_id,
        workflow_id=workflow_id,
        filename=request.file_name,
    )

    # Generate signed upload URL
    try:
        upload_url, expires_at = await gcs_client.generate_upload_signed_url(
            file_path=file_path,
            content_type=request.mime_type,
        )
    except Exception as e:
        logger.error(f"Failed to generate signed URL: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate signed URL: {str(e)}",
        ) from e

    return UploadUrlResponse(
        upload_url=upload_url,
        file_path=file_path,
        expires_at=expires_at.isoformat(),
    )


@router.post(
    "/{audit_id}/workflows/{workflow_id}/submit",
    response_model=WorkflowSubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit workflow with evidence files",
    description="Submit an entire workflow with evidence file paths for multiple claims. Creates submission records and updates workflow status to PROCESSING. Each workflow represents one complete, immutable submission attempt. If the workflow already has submissions, it cannot be resubmitted.",
)
async def submit_workflow(
    audit_id: UUID,
    workflow_id: UUID,
    request: WorkflowSubmissionRequest,
    background_tasks: BackgroundTasks,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowSubmissionResponse:
    """
    Submit workflow with evidence files.

    Validates file paths, creates submission records, and queues background processing.
    Workflows are immutable once submissions are created.
    """
    await AuditService.verify_audit_access(db, audit_id, current_user)

    # Verify workflow exists and belongs to audit
    workflow = await WorkflowService.get_workflow_by_id(db, audit_id, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    # Check if workflow already has submissions (immutability check)
    existing_submissions_count = await db.execute(
        select(func.count(EvidenceSubmission.id)).where(
            EvidenceSubmission.audit_workflow_id == workflow_id
        )
    )
    count = existing_submissions_count.scalar() or 0

    if count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow {workflow_id} already has submissions and is immutable. Cannot resubmit to the same workflow.",
        )

    file_paths = [submission.file_path for submission in request.submissions]
    try:
        await SubmissionService.validate_file_paths(db, file_paths)
    except (FileNotFoundError, InvalidFileError) as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    submission_ids = []
    logger.info(
        f"Creating submissions for workflow {workflow_id}: "
        f"{len(request.submissions)} file(s) provided"
    )

    for submission_info in request.submissions:
        # Verify claim exists and belongs to workflow
        claim = await WorkflowService.verify_claim_belongs_to_workflow(
            db, submission_info.claim_id, workflow_id
        )
        if not claim:
            raise HTTPException(
                status_code=400,
                detail=f"Claim {submission_info.claim_id} not found or does not belong to workflow",
            )

        logger.info(
            f"Creating submission for claim {submission_info.claim_id}: {submission_info.file_name}"
        )

        try:
            submission = await SubmissionService.create_submissions_for_workflow(
                db=db,
                workflow_id=workflow_id,
                claim_id=submission_info.claim_id,
                file_path=submission_info.file_path,
                file_name=submission_info.file_name,
                file_size=submission_info.file_size,
                mime_type=submission_info.mime_type,
            )
            submission_ids.append(submission.id)
            logger.info(f"Created submission {submission.id} for claim {submission_info.claim_id}")
        except InvalidFileError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    updated_workflow = await WorkflowSubmissionService.update_workflow_status_to_processing(
        db, workflow_id
    )

    background_tasks.add_task(
        WorkflowSubmissionService.process_workflow_submissions_background,
        workflow_id,
        submission_ids,
    )

    return WorkflowSubmissionResponse(
        workflow_id=workflow_id,
        status=updated_workflow.status,
        submission_ids=submission_ids,
        message=f"Workflow submitted successfully. {len(submission_ids)} submission(s) queued for processing.",
    )


@router.get(
    "/{audit_id}/workflows/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Get specific audit workflow",
    description="Retrieve a specific workflow by ID for an audit, including required evidence claims and rule matches.",
)
async def get_workflow_by_id(
    audit_id: UUID,
    workflow_id: UUID,
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    """Get specific workflow by ID for an audit."""
    await AuditService.verify_audit_access(db, audit_id, current_user)

    workflow = await WorkflowService.get_workflow_by_id(db, audit_id, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow_data = await WorkflowService.build_workflow_response(db, workflow)
    return WorkflowResponse(**workflow_data)


@router.post(
    "/{audit_id}/workflows/{workflow_id}/recalculate-scores",
    response_model=WorkflowResponse,
    status_code=status.HTTP_200_OK,
    summary="Recalculate workflow scores (Admin only)",
    description="Recalculate overall_score and certification for a completed workflow. "
    "Useful for workflows completed before the migration or if scores need recalculation.",
    tags=["admin", "audit-workflows"],
)
async def recalculate_workflow_scores(
    audit_id: UUID,
    workflow_id: UUID,
    current_user: UserContext = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    """Recalculate overall_score and certification for a workflow (Admin only)."""
    await AuditService.verify_audit_access(db, audit_id, current_user)

    workflow = await WorkflowSubmissionService.recalculate_workflow_scores(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    workflow_data = await WorkflowService.build_workflow_response(db, workflow)
    return WorkflowResponse(**workflow_data)
