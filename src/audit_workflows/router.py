"""Audit workflows domain router."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_workflows.models import AuditWorkflow
from src.audit_workflows.schemas import (
    ClaimResponse,
    RuleMatchResponse,
    WorkflowListResponse,
    WorkflowResponse,
    WorkflowSummary,
)
from src.audit_workflows.service import WorkflowService
from src.audits.exceptions import AuditNotFoundError
from src.auth.dependencies import UserContext, get_current_user
from src.brands.service import BrandService
from src.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/audits", tags=["audit-workflows"])


async def _verify_audit_access(
    db: AsyncSession,
    audit_id: UUID,
    current_user: UserContext,
) -> None:
    """Verify user has access to the audit (brand owner or admin)."""
    from sqlalchemy import select

    from src.audits.models import Audit

    audit_result = await db.execute(select(Audit).where(Audit.id == audit_id))
    audit = audit_result.scalar_one_or_none()
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    # Admin can access any audit
    if current_user.role == "admin":
        return

    # Brand users can only access audits from their brand
    brand = await BrandService.get_brand_by_user(db, current_user.profile.id)
    if not brand or brand.id != audit.brand_id:
        raise HTTPException(status_code=403, detail="Access denied to this audit")


@router.post(
    "/{audit_id}/workflow/generate",
    response_model=WorkflowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate audit workflow",
    description="Generate a new workflow generation for an audit. Works for both draft and published audits. Each call creates a new workflow generation. For published audits, the workflow uses a snapshot of the immutable audit data.",
)
async def generate_workflow(
    audit_id: UUID,
    force: bool = Query(False, description="Unused parameter (kept for API compatibility)"),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowResponse:
    """Generate a new workflow generation for an audit."""
    await _verify_audit_access(db, audit_id, current_user)

    try:
        workflow = await WorkflowService.generate_workflow(db, audit_id, force=force)
    except AuditNotFoundError:
        raise HTTPException(status_code=404, detail="Audit not found") from None

    return await _build_workflow_response(db, workflow)


async def _build_workflow_response(
    db: AsyncSession,
    workflow: AuditWorkflow,
) -> WorkflowResponse:
    """Build WorkflowResponse from AuditWorkflow model."""
    from sqlalchemy import select

    from src.audit_workflows.models import (
        AuditWorkflowRequiredClaim,
        AuditWorkflowRequiredClaimSource,
        AuditWorkflowRuleMatch,
    )
    from src.rules.models import EvidenceClaim, Rule

    # Load claims with evidence claim details and sources
    claims_stmt = (
        select(AuditWorkflowRequiredClaim, EvidenceClaim)
        .join(EvidenceClaim, AuditWorkflowRequiredClaim.evidence_claim_id == EvidenceClaim.id)
        .where(AuditWorkflowRequiredClaim.audit_workflow_id == workflow.id)
    )
    claims_result = await db.execute(claims_stmt)
    claims_data = claims_result.all()

    claims: list[ClaimResponse] = []
    for workflow_claim, evidence_claim in claims_data:
        # Load sources
        sources_stmt = select(AuditWorkflowRequiredClaimSource).where(
            AuditWorkflowRequiredClaimSource.audit_workflow_required_claim_id == workflow_claim.id
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
                required=workflow_claim.required,
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

    return WorkflowResponse(
        id=workflow.id,
        audit_id=workflow.audit_id,
        generation=workflow.generation,
        status=workflow.status,
        generated_at=workflow.generated_at,
        engine_version=workflow.engine_version,
        claims=claims,
        rule_matches=rule_matches,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


@router.get(
    "/{audit_id}/workflows",
    response_model=WorkflowListResponse,
    summary="List audit workflows",
    description="Retrieve a paginated list of workflows for an audit, ordered by generation (newest first).",
)
async def list_workflows(
    audit_id: UUID,
    limit: int = Query(20, ge=1, le=100, description="Maximum number of workflows to return"),
    offset: int = Query(0, ge=0, description="Number of workflows to skip"),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WorkflowListResponse:
    """List workflows for an audit."""
    await _verify_audit_access(db, audit_id, current_user)

    workflows, total = await WorkflowService.list_workflows(db, audit_id, limit=limit, offset=offset)

    return WorkflowListResponse(
        items=[WorkflowSummary.model_validate(w, from_attributes=True) for w in workflows],
        total=total,
        limit=limit,
        offset=offset,
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
    await _verify_audit_access(db, audit_id, current_user)

    workflow = await WorkflowService.get_workflow_by_id(db, audit_id, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return await _build_workflow_response(db, workflow)

