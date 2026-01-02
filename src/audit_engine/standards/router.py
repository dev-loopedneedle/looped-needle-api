"""Standards domain router."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_engine.constants import SustainabilityDomain
from src.audit_engine.dependencies import get_audit_engine_db
from src.audit_engine.standards.schemas import (
    CriterionCreate,
    CriterionListQuery,
    CriterionListResponse,
    CriterionResponse,
    RuleCreate,
    RuleListResponse,
    RuleResponse,
    RuleUpdate,
)
from src.audit_engine.standards.service import CriterionService, RuleService

router = APIRouter(prefix="/api/v1", tags=["standards"])
logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str | None:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", None)


# Criterion endpoints
@router.post(
    "/criteria",
    response_model=CriterionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create criterion",
    description="Create a new sustainability criterion",
)
async def create_criterion(
    request: Request,
    criterion_data: CriterionCreate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> CriterionResponse:
    """Create a new sustainability criterion."""
    request_id = _get_request_id(request)
    logger.info(f"Creating criterion: code={criterion_data.code}", extra={"request_id": request_id})
    criterion = await CriterionService.create_criterion(db, criterion_data)
    return CriterionResponse.model_validate(criterion)


@router.get(
    "/criteria",
    response_model=CriterionListResponse,
    summary="List criteria",
    description="Retrieve a paginated list of sustainability criteria",
)
async def list_criteria(
    request: Request,
    domain: str | None = Query(
        None, description="Filter by domain (Social, Environmental, Governance)"
    ),
    limit: int = Query(default=20, ge=1, le=50, description="Maximum number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_audit_engine_db),
) -> CriterionListResponse:
    """List criteria with pagination."""
    request_id = _get_request_id(request)
    logger.info(
        f"Listing criteria: domain={domain}, limit={limit}, offset={offset}",
        extra={"request_id": request_id},
    )

    query = CriterionListQuery(
        domain=SustainabilityDomain(domain) if domain else None,
        limit=limit,
        offset=offset,
    )
    criteria, total = await CriterionService.list_criteria(db, query)
    return CriterionListResponse(
        items=[CriterionResponse.model_validate(criterion) for criterion in criteria],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get(
    "/criteria/{criterion_id}",
    response_model=CriterionResponse,
    summary="Get criterion",
    description="Retrieve a specific criterion by ID",
)
async def get_criterion(
    request: Request,
    criterion_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> CriterionResponse:
    """Get criterion by ID."""
    request_id = _get_request_id(request)
    logger.info(f"Getting criterion: id={criterion_id}", extra={"request_id": request_id})
    criterion = await CriterionService.get_criterion(db, criterion_id)
    return CriterionResponse.model_validate(criterion)


# Rule endpoints
@router.post(
    "/criteria/{criterion_id}/rules",
    response_model=RuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create rule",
    description="Create a new rule for a criterion",
)
async def create_rule(
    request: Request,
    criterion_id: UUID,
    rule_data: RuleCreate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> RuleResponse:
    """Create a new rule for a criterion."""
    request_id = _get_request_id(request)
    logger.info(
        f"Creating rule for criterion: criterion_id={criterion_id}",
        extra={"request_id": request_id},
    )
    rule = await RuleService.create_rule(db, criterion_id, rule_data)
    return RuleResponse.model_validate(rule)


@router.get(
    "/criteria/{criterion_id}/rules",
    response_model=RuleListResponse,
    summary="List rules",
    description="Retrieve all rules for a criterion, ordered by priority",
)
async def list_rules(
    request: Request,
    criterion_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> RuleListResponse:
    """List rules for a criterion."""
    request_id = _get_request_id(request)
    logger.info(
        f"Listing rules for criterion: criterion_id={criterion_id}",
        extra={"request_id": request_id},
    )
    rules = await RuleService.get_rules_by_criterion(db, criterion_id)
    return RuleListResponse(
        items=[RuleResponse.model_validate(rule) for rule in rules],
        total=len(rules),
    )


@router.get(
    "/rules/{rule_id}",
    response_model=RuleResponse,
    summary="Get rule",
    description="Retrieve a specific rule by ID",
)
async def get_rule(
    request: Request,
    rule_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> RuleResponse:
    """Get rule by ID."""
    request_id = _get_request_id(request)
    logger.info(f"Getting rule: id={rule_id}", extra={"request_id": request_id})
    rule = await RuleService.get_rule(db, rule_id)
    return RuleResponse.model_validate(rule)


@router.put(
    "/rules/{rule_id}",
    response_model=RuleResponse,
    summary="Update rule",
    description="Update an existing rule",
)
async def update_rule(
    request: Request,
    rule_id: UUID,
    rule_data: RuleUpdate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> RuleResponse:
    """Update rule."""
    request_id = _get_request_id(request)
    logger.info(f"Updating rule: id={rule_id}", extra={"request_id": request_id})
    rule = await RuleService.update_rule(db, rule_id, rule_data)
    return RuleResponse.model_validate(rule)

