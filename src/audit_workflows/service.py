"""Service layer for audit workflows domain."""

import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_workflows.models import (
    AuditWorkflow,
    AuditWorkflowRequiredClaim,
    AuditWorkflowRequiredClaimSource,
    AuditWorkflowRuleMatch,
    AuditWorkflowStatus,
)
from src.audits.exceptions import AuditNotFoundError
from src.audits.models import Audit
from src.rules.constants import RuleState
from src.rules.models import EvidenceClaim, Rule, RuleEvidenceClaim
from src.rules.utils import validate_and_evaluate_condition_tree

logger = logging.getLogger(__name__)


class WorkflowService:
    """Service for audit workflow operations."""

    @staticmethod
    async def generate_workflow(
        db: AsyncSession,
        audit_id: UUID,
        force: bool = False,
    ) -> AuditWorkflow:
        """
        Generate a new workflow generation for an audit.

        Workflows can be generated for both draft and published audits.
        Each call creates a new workflow generation. For published audits,
        the audit_data_snapshot captures the immutable audit data.

        Args:
            db: Database session
            audit_id: Audit ID
            force: Unused parameter (kept for API compatibility)

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

        # Get next generation number
        stmt = select(func.max(AuditWorkflow.generation)).where(
            AuditWorkflow.audit_id == audit_id
        )
        result = await db.execute(stmt)
        max_generation = result.scalar_one_or_none()
        next_generation = (max_generation or 0) + 1

        # Create new workflow generation (always create a new one)
        audit_data_snapshot = audit.audit_data.copy() if audit.audit_data else {}
        workflow = AuditWorkflow(
            audit_id=audit_id,
            generation=next_generation,
            status=AuditWorkflowStatus.GENERATED,
            generated_at=datetime.now(timezone.utc),
            engine_version="v1",
            audit_data_snapshot=audit_data_snapshot,
        )
        db.add(workflow)
        await db.flush()  # Get workflow.id

        # Load all published rules
        rules_stmt = select(Rule).where(Rule.state == RuleState.PUBLISHED)
        rules_result = await db.execute(rules_stmt)
        published_rules: list[Rule] = list(rules_result.scalars().all())

        logger.info(
            f"Generating workflow for audit {audit_id}, generation {next_generation}, "
            f"evaluating {len(published_rules)} published rules"
        )

        matched_rules: list[Rule] = []
        rule_matches: list[AuditWorkflowRuleMatch] = []

        # Evaluate each rule
        for rule in published_rules:
            try:
                valid, matched, errors = validate_and_evaluate_condition_tree(
                    rule.condition_tree, audit_data_snapshot
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
                        evaluated_at=datetime.now(timezone.utc),
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
                    evaluated_at=datetime.now(timezone.utc),
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
                    evaluated_at=datetime.now(timezone.utc),
                )
                rule_matches.append(match)
                logger.error(f"Error evaluating rule {rule.code} v{rule.version}: {error_msg}")

        # Collect evidence claims from matched rules (deduplicate)
        evidence_claim_ids: set[UUID] = set()
        rule_claim_map: dict[UUID, list[Rule]] = {}  # claim_id -> list of rules that require it
        claim_required_map: dict[UUID, bool] = {}  # claim_id -> required status (True if ANY rule requires it)

        for rule in matched_rules:
            # Load claims for this rule (both required and optional)
            claims_stmt = (
                select(EvidenceClaim, RuleEvidenceClaim.required)
                .join(RuleEvidenceClaim, RuleEvidenceClaim.evidence_claim_id == EvidenceClaim.id)
                .where(RuleEvidenceClaim.rule_id == rule.id)
            )
            claims_result = await db.execute(claims_stmt)
            claims_data = claims_result.all()

            for claim, required in claims_data:
                evidence_claim_ids.add(claim.id)
                if claim.id not in rule_claim_map:
                    rule_claim_map[claim.id] = []
                rule_claim_map[claim.id].append(rule)
                # If any rule requires it, mark as required
                if claim.id not in claim_required_map:
                    claim_required_map[claim.id] = required
                else:
                    # If already exists, set to True if ANY rule requires it
                    claim_required_map[claim.id] = claim_required_map[claim.id] or required

        # Create claims and sources
        workflow_claims: list[AuditWorkflowRequiredClaim] = []
        claim_sources: list[AuditWorkflowRequiredClaimSource] = []

        for claim_id in evidence_claim_ids:
            is_required = claim_required_map.get(claim_id, True)
            workflow_claim = AuditWorkflowRequiredClaim(
                audit_workflow_id=workflow.id,
                evidence_claim_id=claim_id,
                required=is_required,
                status="REQUIRED",  # Keep status for backward compatibility
            )
            workflow_claims.append(workflow_claim)
            db.add(workflow_claim)
            await db.flush()  # Get workflow_claim.id

            # Add sources
            for rule in rule_claim_map[claim_id]:
                source = AuditWorkflowRequiredClaimSource(
                    audit_workflow_required_claim_id=workflow_claim.id,
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
        count_stmt = select(func.count()).select_from(AuditWorkflow).where(
            AuditWorkflow.audit_id == audit_id
        )
        count_result = await db.execute(count_stmt)
        total = count_result.scalar_one() or 0

        # Get paginated workflows (ordered by generation descending - newest first)
        stmt = (
            select(AuditWorkflow)
            .where(AuditWorkflow.audit_id == audit_id)
            .order_by(AuditWorkflow.generation.desc())
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

