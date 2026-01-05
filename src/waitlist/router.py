"""Waitlist domain router."""

import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_request_id
from src.database import get_db
from src.waitlist.schemas import WaitlistRequest, WaitlistResponse
from src.waitlist.service import WaitlistService

router = APIRouter(prefix="/api/v1", tags=["waitlist"])
logger = logging.getLogger(__name__)


@router.post(
    "/waitlist",
    response_model=WaitlistResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Join waitlist",
    description="Add an email to the waitlist with optional name and message",
)
async def join_waitlist(
    request: WaitlistRequest,
    request_id: str | None = Depends(get_request_id),
    db: AsyncSession = Depends(get_db),
) -> WaitlistResponse:
    """
    Add an email to the waitlist.

    Args:
        request: Waitlist submission request with email, optional name and message
        request_id: Request ID for logging
        db: Database session

    Returns:
        WaitlistResponse: Created waitlist entry
    """
    logger.info(
        f"Adding email to waitlist: {request.email}",
        extra={"request_id": request_id},
    )
    entry = await WaitlistService.add_to_waitlist(db, request)
    return WaitlistResponse.model_validate(entry.model_dump())

