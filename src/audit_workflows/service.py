"""Service layer for audit workflows domain."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_workflows.models import (
    AuditWorkflow,
    AuditWorkflowClaim,
    AuditWorkflowClaimSource,
    AuditWorkflowRuleMatch,
    AuditWorkflowStatus,
)
from src.audit_workflows.schemas import ClaimResponse, RuleMatchResponse
from src.audits.exceptions import AuditNotFoundError
from src.audits.models import Audit
from src.database import AsyncSessionLocal
from src.evidence_submissions.constants import SubmissionStatus
from src.evidence_submissions.models import EvidenceSubmission
from src.evidence_submissions.schemas import EvidenceEvaluationSummary
from src.evidence_submissions.service import SubmissionService
from src.rules.constants import RuleState
from src.rules.models import EvidenceClaim, Rule, RuleEvidenceClaim
from src.rules.utils import validate_and_evaluate_condition_tree

logger = logging.getLogger(__name__)


class WorkflowSubmissionService:
    """Service for workflow submission operations."""

    @staticmethod
    async def update_workflow_status_to_processing(
        db: AsyncSession,
        workflow_id: UUID,
    ) -> AuditWorkflow:
        """
        Update workflow status to PROCESSING.

        Args:
            db: Database session
            workflow_id: Workflow ID

        Returns:
            AuditWorkflow: Updated workflow

        Raises:
            Exception: If workflow not found
        """
        result = await db.execute(select(AuditWorkflow).where(AuditWorkflow.id == workflow_id))
        workflow = result.scalar_one_or_none()

        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow.status = AuditWorkflowStatus.PROCESSING
        workflow.updated_at = datetime.now(UTC)

        await db.commit()
        await db.refresh(workflow)

        logger.info(f"Updated workflow {workflow_id} status to PROCESSING")
        return workflow

    @staticmethod
    async def process_workflow_submissions_background(
        workflow_id: UUID,
        submission_ids: list[UUID],
    ) -> None:
        """
        Background task to process workflow submissions with error handling.

        Creates its own database session and handles errors gracefully,
        updating workflow status to PROCESSING_FAILED on failure.

        Args:
            workflow_id: Workflow ID
            submission_ids: List of submission IDs to process
        """
        logger.info(
            f"Background task started: Processing workflow {workflow_id} with {len(submission_ids)} submission(s)"
        )
        # Use context manager to ensure session is always closed
        async with AsyncSessionLocal() as db_session:
            try:
                await SubmissionService.process_workflow_submissions(
                    db_session, workflow_id, submission_ids
                )
                await db_session.commit()
                logger.info(f"Background task completed successfully for workflow {workflow_id}")
            except Exception as e:
                logger.error(
                    f"Error in background processing task for workflow {workflow_id}: {e}",
                    exc_info=True,
                )
                try:
                    await db_session.rollback()
                    logger.debug(f"Rolled back database session for workflow {workflow_id}")
                except Exception as rollback_error:
                    logger.error(
                        f"Failed to rollback database session for workflow {workflow_id}: {rollback_error}",
                        exc_info=True,
                    )

        # Update workflow status in a separate session to avoid transaction issues
        try:
            async with AsyncSessionLocal() as status_db:
                workflow = await status_db.get(AuditWorkflow, workflow_id)
                if workflow:
                    workflow.status = AuditWorkflowStatus.PROCESSING_FAILED
                    workflow.updated_at = datetime.now(UTC)
                    await status_db.commit()
                    logger.info(
                        f"Updated workflow {workflow_id} status to PROCESSING_FAILED after error"
                    )
        except Exception as status_error:
            logger.error(
                f"Failed to update workflow {workflow_id} status after background task error: {status_error}",
                exc_info=True,
            )

    @staticmethod
    async def update_workflow_status_after_processing(
        db: AsyncSession,
        workflow_id: UUID,
    ) -> AuditWorkflow | None:
        """
        Calculate and update workflow status based on submission statuses.

        Args:
            db: Database session
            workflow_id: Workflow ID

        Returns:
            AuditWorkflow: Updated workflow, or None if not found
        """
        # Get all submissions for workflow
        submissions_result = await db.execute(
            select(EvidenceSubmission).where(EvidenceSubmission.audit_workflow_id == workflow_id)
        )
        submissions = list(submissions_result.scalars().all())

        if not submissions:
            # No submissions, keep current status
            workflow = await db.get(AuditWorkflow, workflow_id)
            return workflow if workflow else None

        # Count submissions by status
        processing_count = sum(
            1
            for s in submissions
            if s.status in [SubmissionStatus.PENDING_PROCESSING, SubmissionStatus.PROCESSING]
        )
        failed_count = sum(
            1
            for s in submissions
            if s.status in [SubmissionStatus.PROCESSING_FAILED, SubmissionStatus.REJECTED]
        )
        completed_count = sum(
            1
            for s in submissions
            if s.status
            in [
                SubmissionStatus.PROCESSING_COMPLETE,
                SubmissionStatus.ACCEPTED,
                SubmissionStatus.NEEDS_REVIEW,  # Needs review is a completed processing state
            ]
        )

        # Log submission status breakdown for debugging
        status_breakdown = {}
        failed_submissions_details = []
        for s in submissions:
            status_breakdown[s.status] = status_breakdown.get(s.status, 0) + 1
            if s.status in [SubmissionStatus.PROCESSING_FAILED, SubmissionStatus.REJECTED]:
                failed_submissions_details.append({
                    "submission_id": str(s.id),
                    "file_name": s.file_name,
                    "status": s.status,
                    "error_message": s.error_message,
                    "claim_id": str(s.audit_workflow_claim_id),
                })

        logger.info(
            f"Workflow {workflow_id} status update - Submissions breakdown:\n"
            f"  - Total submissions: {len(submissions)}\n"
            f"  - Processing: {processing_count} (PENDING_PROCESSING or PROCESSING)\n"
            f"  - Completed: {completed_count} (PROCESSING_COMPLETE, ACCEPTED, or NEEDS_REVIEW)\n"
            f"  - Failed: {failed_count} (PROCESSING_FAILED or REJECTED)\n"
            f"  - Status breakdown: {status_breakdown}"
        )

        if failed_submissions_details:
            logger.warning(
                f"Workflow {workflow_id} has {failed_count} failed submission(s): "
                f"{failed_submissions_details}"
            )

        # Determine workflow status
        workflow = await db.get(AuditWorkflow, workflow_id)
        if not workflow:
            return None

        old_status = workflow.status
        if processing_count > 0:
            # Still processing
            workflow.status = AuditWorkflowStatus.PROCESSING
        elif failed_count > 0:
            # At least one failed
            workflow.status = AuditWorkflowStatus.PROCESSING_FAILED
        elif completed_count == len(submissions):
            # All completed successfully
            workflow.status = AuditWorkflowStatus.PROCESSING_COMPLETE
        else:
            # Mixed state - keep PROCESSING
            workflow.status = AuditWorkflowStatus.PROCESSING

        workflow.updated_at = datetime.now(UTC)
        await db.commit()
        await db.refresh(workflow)

        logger.info(
            f"Updated workflow {workflow_id} status: {old_status} → {workflow.status} "
            f"(processing={processing_count}, completed={completed_count}, failed={failed_count}, total={len(submissions)})"
        )

        if failed_count > 0:
            logger.warning(
                f"Workflow {workflow_id} marked as PROCESSING_FAILED due to {failed_count} failed submission(s). "
                f"Check submission error messages for details."
            )

        return workflow


class WorkflowService:
    """Service for audit workflow operations."""

    @staticmethod
    async def generate_workflow(
        db: AsyncSession,
        audit_id: UUID,
    ) -> AuditWorkflow:
        """
        Generate a new workflow for an audit.

        Workflows can be generated for both draft and published audits.
        Each audit has one workflow.

        Args:
            db: Database session
            audit_id: Audit ID

        Returns:
            AuditWorkflow: Generated workflow

        Raises:
            AuditNotFoundError: If audit not found
        """
        # Load audit
        audit_result = await db.execute(select(Audit).where(Audit.id == audit_id))
        audit = audit_result.scalar_one_or_none()
        if not audit:
            raise AuditNotFoundError(str(audit_id))

        # Create new workflow
        workflow = AuditWorkflow(
            audit_id=audit_id,
            status=AuditWorkflowStatus.GENERATED,
            engine_version="v1",
        )
        db.add(workflow)
        await db.flush()  # Get workflow.id

        # Load all published rules
        rules_stmt = select(Rule).where(Rule.state == RuleState.PUBLISHED)
        rules_result = await db.execute(rules_stmt)
        published_rules: list[Rule] = list(rules_result.scalars().all())

        logger.info(
            f"Generating workflow for audit {audit_id}, "
            f"evaluating {len(published_rules)} published rules"
        )

        matched_rules: list[Rule] = []
        rule_matches: list[AuditWorkflowRuleMatch] = []

        # Evaluate each rule using current audit data
        audit_data = audit.audit_data if audit.audit_data else {}
        for rule in published_rules:
            try:
                valid, matched, errors = validate_and_evaluate_condition_tree(
                    rule.condition_tree, audit_data
                )
                if not valid:
                    # Condition tree invalid - record error, continue
                    match = AuditWorkflowRuleMatch(
                        audit_workflow_id=workflow.id,
                        rule_id=rule.id,
                        rule_code=rule.code,
                        rule_version=rule.version,
                        matched=False,
                        error=f"Condition tree validation failed: {', '.join(errors)}",
                        evaluated_at=datetime.now(UTC),
                    )
                    rule_matches.append(match)
                    logger.warning(
                        f"Rule {rule.code} v{rule.version} condition tree invalid: {', '.join(errors)}"
                    )
                    continue

                if matched:
                    matched_rules.append(rule)

                match = AuditWorkflowRuleMatch(
                    audit_workflow_id=workflow.id,
                    rule_id=rule.id,
                    rule_code=rule.code,
                    rule_version=rule.version,
                    matched=bool(matched),
                    error=None,
                    evaluated_at=datetime.now(UTC),
                )
                rule_matches.append(match)

            except Exception as err:  # noqa: BLE001
                # Unexpected error - log and continue
                error_msg = str(err)
                match = AuditWorkflowRuleMatch(
                    audit_workflow_id=workflow.id,
                    rule_id=rule.id,
                    rule_code=rule.code,
                    rule_version=rule.version,
                    matched=False,
                    error=error_msg,
                    evaluated_at=datetime.now(UTC),
                )
                rule_matches.append(match)
                logger.error(f"Error evaluating rule {rule.code} v{rule.version}: {error_msg}")

        # Collect evidence claims from matched rules (deduplicate)
        evidence_claim_ids: set[UUID] = set()
        rule_claim_map: dict[UUID, list[Rule]] = {}  # claim_id -> list of rules that require it

        for rule in matched_rules:
            # Load claims for this rule
            claims_stmt = (
                select(EvidenceClaim)
                .join(RuleEvidenceClaim, RuleEvidenceClaim.evidence_claim_id == EvidenceClaim.id)
                .where(RuleEvidenceClaim.rule_id == rule.id)
            )
            claims_result = await db.execute(claims_stmt)
            claims_data = claims_result.scalars().all()

            for claim in claims_data:
                evidence_claim_ids.add(claim.id)
                if claim.id not in rule_claim_map:
                    rule_claim_map[claim.id] = []
                rule_claim_map[claim.id].append(rule)

        # Create claims and sources
        workflow_claims: list[AuditWorkflowClaim] = []
        claim_sources: list[AuditWorkflowClaimSource] = []

        for claim_id in evidence_claim_ids:
            workflow_claim = AuditWorkflowClaim(
                audit_workflow_id=workflow.id,
                evidence_claim_id=claim_id,
                status="REQUIRED",  # Keep status for backward compatibility
            )
            workflow_claims.append(workflow_claim)
            db.add(workflow_claim)
            await db.flush()  # Get workflow_claim.id

            # Add sources
            for rule in rule_claim_map[claim_id]:
                source = AuditWorkflowClaimSource(
                    audit_workflow_claim_id=workflow_claim.id,
                    rule_id=rule.id,
                    rule_code=rule.code,
                    rule_version=rule.version,
                )
                claim_sources.append(source)
                db.add(source)

        # Add all rule matches
        for match in rule_matches:
            db.add(match)

        await db.commit()
        await db.refresh(workflow)

        logger.info(
            f"Workflow {workflow.id} generated: {len(matched_rules)}/{len(published_rules)} rules matched, "
            f"{len(workflow_claims)} claims, {len(rule_matches)} rule evaluations"
        )

        return workflow

    @staticmethod
    async def list_workflows(
        db: AsyncSession,
        audit_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[AuditWorkflow], int]:
        """
        List workflows for an audit with pagination.

        Args:
            db: Database session
            audit_id: Audit ID
            limit: Maximum number of workflows to return
            offset: Number of workflows to skip

        Returns:
            Tuple of (list of workflows, total count)
        """
        # Get total count
        count_stmt = (
            select(func.count())
            .select_from(AuditWorkflow)
            .where(AuditWorkflow.audit_id == audit_id)
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar_one() or 0

        # Get paginated workflows (ordered by created_at descending - newest first)
        stmt = (
            select(AuditWorkflow)
            .where(AuditWorkflow.audit_id == audit_id)
            .order_by(AuditWorkflow.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        workflows = list(result.scalars().all())

        return workflows, total

    @staticmethod
    async def get_workflow_by_id(
        db: AsyncSession,
        audit_id: UUID,
        workflow_id: UUID,
    ) -> AuditWorkflow | None:
        """
        Get specific workflow by ID, verifying it belongs to the audit.

        Args:
            db: Database session
            audit_id: Audit ID
            workflow_id: Workflow ID

        Returns:
            AuditWorkflow or None if not found or doesn't belong to audit
        """
        workflow = await db.get(AuditWorkflow, workflow_id)
        if workflow and workflow.audit_id == audit_id:
            return workflow
        return None

    @staticmethod
    async def verify_claim_belongs_to_workflow(
        db: AsyncSession,
        claim_id: UUID,
        workflow_id: UUID,
    ) -> AuditWorkflowClaim | None:
        """
        Verify that a claim exists and belongs to the specified workflow.

        Args:
            db: Database session
            claim_id: Claim ID to verify
            workflow_id: Workflow ID to verify against

        Returns:
            AuditWorkflowClaim if found and belongs to workflow, None otherwise
        """
        claim_result = await db.execute(
            select(AuditWorkflowClaim).where(
                AuditWorkflowClaim.id == claim_id,
                AuditWorkflowClaim.audit_workflow_id == workflow_id,
            )
        )
        return claim_result.scalar_one_or_none()

    @staticmethod
    async def build_workflow_response(
        db: AsyncSession,
        workflow: AuditWorkflow,
    ) -> dict:
        """
        Build a complete workflow response with claims, rule matches, and evidence evaluations.

        Args:
            db: Database session
            workflow: Workflow to build response for

        Returns:
            Dictionary with workflow data ready for WorkflowResponse schema
        """
        # Load claims with evidence claim details and sources
        claims_stmt = (
            select(AuditWorkflowClaim, EvidenceClaim)
            .join(EvidenceClaim, AuditWorkflowClaim.evidence_claim_id == EvidenceClaim.id)
            .where(AuditWorkflowClaim.audit_workflow_id == workflow.id)
        )
        claims_result = await db.execute(claims_stmt)
        claims_data = claims_result.all()

        claims: list[ClaimResponse] = []
        for workflow_claim, evidence_claim in claims_data:
            # Load sources
            sources_stmt = select(AuditWorkflowClaimSource).where(
                AuditWorkflowClaimSource.audit_workflow_claim_id == workflow_claim.id
            )
            sources_result = await db.execute(sources_stmt)
            sources_data = sources_result.scalars().all()

            # Load rule names
            rule_ids = [s.rule_id for s in sources_data]
            rules_stmt = select(Rule).where(Rule.id.in_(rule_ids))
            rules_result = await db.execute(rules_stmt)
            rules_map = {r.id: r for r in rules_result.scalars().all()}

            sources = [
                {
                    "rule_id": s.rule_id,
                    "rule_code": s.rule_code,
                    "rule_name": rules_map[s.rule_id].name if s.rule_id in rules_map else "Unknown",
                    "rule_version": s.rule_version,
                }
                for s in sources_data
            ]

            claims.append(
                ClaimResponse(
                    id=workflow_claim.id,
                    evidence_claim_id=evidence_claim.id,
                    evidence_claim_name=evidence_claim.name,
                    evidence_claim_description=evidence_claim.description,
                    evidence_claim_category=evidence_claim.category,
                    evidence_claim_type=evidence_claim.type,
                    evidence_claim_weight=float(evidence_claim.weight),
                    sources=sources,
                    created_at=workflow_claim.created_at,
                    updated_at=workflow_claim.updated_at,
                )
            )

        # Load rule matches
        matches_stmt = select(AuditWorkflowRuleMatch).where(
            AuditWorkflowRuleMatch.audit_workflow_id == workflow.id
        )
        matches_result = await db.execute(matches_stmt)
        matches_data = matches_result.scalars().all()

        rule_matches = [
            RuleMatchResponse(
                rule_id=m.rule_id,
                rule_code=m.rule_code,
                rule_version=m.rule_version,
                matched=m.matched,
                error=m.error,
                evaluated_at=m.evaluated_at,
            )
            for m in matches_data
        ]

        # Load evidence evaluations
        evidence_submissions_stmt = select(EvidenceSubmission).where(
            EvidenceSubmission.audit_workflow_id == workflow.id
        )
        evidence_submissions_result = await db.execute(evidence_submissions_stmt)
        evidence_submissions = evidence_submissions_result.scalars().all()

        evidence_evaluations = (
            [
                EvidenceEvaluationSummary(
                    submission_id=sub.id,
                    status=str(sub.status),
                    overall_verdict=sub.gemini_evaluation_response.get("overallVerdict")
                    if sub.gemini_evaluation_response
                    else None,
                    confidence_score=sub.confidence_score,
                    file_name=sub.file_name,
                )
                for sub in evidence_submissions
            ]
            if evidence_submissions
            else None
        )

        return {
            "id": workflow.id,
            "audit_id": workflow.audit_id,
            "status": workflow.status,
            "engine_version": workflow.engine_version,
            "claims": claims,
            "rule_matches": rule_matches,
            "evidence_evaluations": evidence_evaluations,
            "created_at": workflow.created_at,
            "updated_at": workflow.updated_at,
        }
