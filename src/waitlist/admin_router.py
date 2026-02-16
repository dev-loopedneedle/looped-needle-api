"""Admin endpoints for waitlist."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import UserContext
from src.database import get_db
from src.rules.dependencies import get_admin
from src.waitlist.schemas import WaitlistListResponse, WaitlistResponse
from src.waitlist.service import WaitlistService

router = APIRouter(prefix="/api/v1/admin", tags=["admin", "waitlist"])


@router.get(
    "/waitlist",
    response_model=WaitlistListResponse,
    status_code=status.HTTP_200_OK,
    summary="List waitlist entries (Admin only)",
    description="Retrieve a paginated list of all waitlist entries. Admin access required.",
)
async def list_waitlist(
    _: UserContext = Depends(get_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of entries to return"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
) -> WaitlistListResponse:
    """List all waitlist entries with pagination."""
    entries, total = await WaitlistService.list_waitlist(db, limit=limit, offset=offset)
    items = [WaitlistResponse.model_validate(e) for e in entries]
    return WaitlistListResponse(items=items, total=total, limit=limit, offset=offset)
