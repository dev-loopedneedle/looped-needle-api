"""Rules domain router."""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import UserContext
from src.rules.constants import (
    EvidenceClaimCategory,
    EvidenceClaimType,
    RuleState,
)
from src.rules.dependencies import get_admin, get_session
from src.rules.exceptions import EvidenceClaimNotFoundError, RuleNotFoundError, RuleStateError
from src.rules.schemas import (
    EvidenceClaimCreate,
    EvidenceClaimListResponse,
    EvidenceClaimResponse,
    RuleCreate,
    RuleListResponse,
    RulePreviewRequest,
    RulePreviewResponse,
    RuleResponse,
    RuleUpdate,
)
from src.rules.service import RuleService
from src.rules.utils import generate_field_catalog, validate_and_evaluate_condition_tree

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/rules", tags=["rules"])


@router.post(
    "",
    response_model=RuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create draft rule",
)
async def create_rule(
    payload: RuleCreate,
    admin: UserContext = Depends(get_admin),
    db: AsyncSession = Depends(get_session),
) -> RuleResponse:
    try:
        rule = await RuleService.create_rule(
            db, payload, created_by=admin.profile.id if admin else None
        )
    except RuleStateError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    return RuleResponse.model_validate(rule, from_attributes=True)


@router.get(
    "",
    response_model=RuleListResponse,
    summary="List rules",
)
async def list_rules(
    state: str | None = Query(
        None, description="Filter by rule state (DRAFT, PUBLISHED, DISABLED)"
    ),
    code: str | None = Query(None, description="Filter by exact rule code"),
    search: str | None = Query(
        None, description="Search in rule name and code (case-insensitive partial match)"
    ),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: UserContext = Depends(get_admin),
    db: AsyncSession = Depends(get_session),
) -> RuleListResponse:
    # Normalize state to enum if provided
    rule_state: RuleState | None = None
    if state:
        state_upper = state.upper()
        try:
            rule_state = RuleState(state_upper)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid state: {state}. Must be one of: {', '.join([s.value for s in RuleState])}",
            ) from None
    rules, total = await RuleService.list_rules(
        db, state=rule_state, code=code, search=search, limit=limit, offset=offset
    )
    return RuleListResponse(
        items=[RuleResponse.model_validate(r, from_attributes=True) for r in rules],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/fields",
    summary="Get available fields for condition trees",
    description="Returns available field paths, operators, and field types that can be used in condition trees. Requires admin access.",
    response_model=None,
)
async def get_condition_fields(_: UserContext = Depends(get_admin)) -> Any:
    """Get available fields and operators for condition trees."""
    return generate_field_catalog()


@router.get(
    "/{rule_id}",
    response_model=RuleResponse,
    summary="Get rule",
)
async def get_rule(
    rule_id: UUID,
    _: UserContext = Depends(get_admin),
    db: AsyncSession = Depends(get_session),
) -> RuleResponse:
    try:
        rule = await RuleService.get_rule(db, rule_id)
    except RuleNotFoundError:
        raise HTTPException(status_code=404, detail="Rule not found") from None
    return RuleResponse.model_validate(rule, from_attributes=True)


@router.put(
    "/{rule_id}",
    response_model=RuleResponse,
    summary="Update draft rule",
)
async def update_rule(
    rule_id: UUID,
    payload: RuleUpdate,
    _: UserContext = Depends(get_admin),
    db: AsyncSession = Depends(get_session),
) -> RuleResponse:
    try:
        rule = await RuleService.update_rule(db, rule_id, payload)
    except RuleNotFoundError:
        raise HTTPException(status_code=404, detail="Rule not found") from None
    except RuleStateError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    return RuleResponse.model_validate(rule, from_attributes=True)


@router.post(
    "/{rule_id}/clone",
    response_model=RuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Clone rule to new draft version",
)
async def clone_rule(
    rule_id: UUID,
    _: UserContext = Depends(get_admin),
    db: AsyncSession = Depends(get_session),
) -> RuleResponse:
    try:
        rule = await RuleService.clone_rule(db, rule_id)
    except RuleNotFoundError:
        raise HTTPException(status_code=404, detail="Rule not found") from None
    return RuleResponse.model_validate(rule, from_attributes=True)


@router.post(
    "/{rule_id}/publish",
    response_model=RuleResponse,
    summary="Publish rule",
)
async def publish_rule(
    rule_id: UUID,
    _: UserContext = Depends(get_admin),
    db: AsyncSession = Depends(get_session),
) -> RuleResponse:
    try:
        rule = await RuleService.publish_rule(db, rule_id)
    except RuleNotFoundError:
        raise HTTPException(status_code=404, detail="Rule not found") from None
    except RuleStateError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    return RuleResponse.model_validate(rule, from_attributes=True)


@router.post(
    "/{rule_id}/disable",
    response_model=RuleResponse,
    summary="Disable rule",
)
async def disable_rule(
    rule_id: UUID,
    _: UserContext = Depends(get_admin),
    db: AsyncSession = Depends(get_session),
) -> RuleResponse:
    try:
        rule = await RuleService.disable_rule(db, rule_id)
    except RuleNotFoundError:
        raise HTTPException(status_code=404, detail="Rule not found") from None
    return RuleResponse.model_validate(rule, from_attributes=True)


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete rule",
    description="Delete a non-published rule (DRAFT or DISABLED only). Published rules cannot be deleted.",
)
async def delete_rule(
    rule_id: UUID,
    _: UserContext = Depends(get_admin),
    db: AsyncSession = Depends(get_session),
) -> None:
    """Delete a rule. Only non-published rules can be deleted."""
    try:
        await RuleService.delete_rule(db, rule_id)
    except RuleNotFoundError:
        raise HTTPException(status_code=404, detail="Rule not found") from None
    except RuleStateError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err


@router.post(
    "/preview",
    response_model=RulePreviewResponse,
    summary="Preview rule condition tree",
)
async def preview_rule(
    payload: RulePreviewRequest,
    _: UserContext = Depends(get_admin),
) -> RulePreviewResponse:
    valid, matched, errors = validate_and_evaluate_condition_tree(
        payload.conditionTree, payload.audit_data
    )
    return RulePreviewResponse(
        valid=valid,
        matched=matched,
        errors=errors,
    )


@router.post(
    "/evidence-claims",
    response_model=EvidenceClaimResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create evidence claim",
    description="Create a new reusable evidence claim definition. Requires admin access.",
)
async def create_evidence_claim(
    payload: EvidenceClaimCreate,
    admin: UserContext = Depends(get_admin),
    db: AsyncSession = Depends(get_session),
) -> EvidenceClaimResponse:
    """Create a new evidence claim."""
    try:
        claim = await RuleService.create_evidence_claim(
            db, payload, created_by=admin.profile.id if admin else None
        )
    except RuleStateError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err
    return EvidenceClaimResponse.model_validate(claim, from_attributes=True)


@router.get(
    "/evidence-claims",
    response_model=EvidenceClaimListResponse,
    summary="List evidence claims",
    description="Retrieve a paginated list of all reusable evidence claims. Requires admin access.",
)
async def list_evidence_claims(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    _: UserContext = Depends(get_admin),
    db: AsyncSession = Depends(get_session),
) -> EvidenceClaimListResponse:
    """List evidence claims with pagination."""
    claims, total = await RuleService.list_evidence_claims(db, limit=limit, offset=offset)
    return EvidenceClaimListResponse(
        items=[EvidenceClaimResponse.model_validate(c, from_attributes=True) for c in claims],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/evidence-claims/{claim_id}",
    response_model=EvidenceClaimResponse,
    summary="Get evidence claim",
    description="Retrieve a specific evidence claim by ID. Requires admin access.",
)
async def get_evidence_claim(
    claim_id: UUID,
    _: UserContext = Depends(get_admin),
    db: AsyncSession = Depends(get_session),
) -> EvidenceClaimResponse:
    """Get evidence claim by ID."""
    try:
        claim = await RuleService.get_evidence_claim(db, claim_id)
    except EvidenceClaimNotFoundError:
        raise HTTPException(status_code=404, detail="Evidence claim not found") from None
    return EvidenceClaimResponse.model_validate(claim, from_attributes=True)


@router.get(
    "/evidence-claim-categories",
    response_model=list[EvidenceClaimCategory],
    summary="List evidence claim categories",
)
async def list_categories(_: UserContext = Depends(get_admin)) -> list[EvidenceClaimCategory]:
    return list(EvidenceClaimCategory)


@router.get(
    "/evidence-claim-types",
    response_model=list[EvidenceClaimType],
    summary="List evidence claim types",
)
async def list_types(_: UserContext = Depends(get_admin)) -> list[EvidenceClaimType]:
    return list(EvidenceClaimType)


