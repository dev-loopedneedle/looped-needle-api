"""Questionnaires domain router."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_engine.dependencies import get_audit_engine_db
from src.audit_engine.questionnaires.schemas import (
    QuestionnaireDefinitionCreate,
    QuestionnaireDefinitionResponse,
    QuestionnaireListQuery,
    QuestionnaireListResponse,
)
from src.audit_engine.questionnaires.service import QuestionnaireService

router = APIRouter(prefix="/api/v1", tags=["questionnaires"])
logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str | None:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", None)


# Questionnaire endpoints
@router.post(
    "/questionnaires",
    response_model=QuestionnaireDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create questionnaire",
    description="Create a new questionnaire definition",
)
async def create_questionnaire(
    request: Request,
    questionnaire_data: QuestionnaireDefinitionCreate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> QuestionnaireDefinitionResponse:
    """Create a new questionnaire definition."""
    request_id = _get_request_id(request)
    logger.info(
        f"Creating questionnaire: name={questionnaire_data.name}", extra={"request_id": request_id}
    )
    questionnaire = await QuestionnaireService.create_questionnaire(db, questionnaire_data)
    return QuestionnaireDefinitionResponse.model_validate(questionnaire)


@router.get(
    "/questionnaires",
    response_model=QuestionnaireListResponse,
    summary="List questionnaires",
    description="Retrieve a paginated list of questionnaire definitions",
)
async def list_questionnaires(
    request: Request,
    is_active: bool | None = Query(None, description="Filter by active status"),
    limit: int = Query(default=20, ge=1, le=50, description="Maximum number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_audit_engine_db),
) -> QuestionnaireListResponse:
    """List questionnaires with pagination."""
    request_id = _get_request_id(request)
    logger.info(
        f"Listing questionnaires: is_active={is_active}, limit={limit}, offset={offset}",
        extra={"request_id": request_id},
    )
    query = QuestionnaireListQuery(is_active=is_active, limit=limit, offset=offset)
    questionnaires, total = await QuestionnaireService.list_active_questionnaires(db, query)
    return QuestionnaireListResponse(
        items=[QuestionnaireDefinitionResponse.model_validate(q) for q in questionnaires],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get(
    "/questionnaires/{questionnaire_id}",
    response_model=QuestionnaireDefinitionResponse,
    summary="Get questionnaire",
    description="Retrieve a specific questionnaire definition by ID",
)
async def get_questionnaire(
    request: Request,
    questionnaire_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> QuestionnaireDefinitionResponse:
    """Get questionnaire by ID."""
    request_id = _get_request_id(request)
    logger.info(f"Getting questionnaire: id={questionnaire_id}", extra={"request_id": request_id})
    questionnaire = await QuestionnaireService.get_questionnaire(db, questionnaire_id)
    return QuestionnaireDefinitionResponse.model_validate(questionnaire)
