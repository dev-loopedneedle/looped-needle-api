"""Authentication domain router."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_engine.dependencies import get_audit_engine_db
from src.auth.dependencies import UserContext, get_current_user
from src.auth.schemas import UserProfileResponse

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
    description="Retrieve the authenticated user's profile information including role",
)
async def get_me(
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_audit_engine_db),
) -> UserProfileResponse:
    """
    Get current authenticated user profile.

    Returns:
        UserProfileResponse: User profile with role information
    """
    return UserProfileResponse(
        id=current_user.profile.id,
        clerk_user_id=current_user.profile.clerk_user_id,
        is_active=current_user.profile.is_active,
        role=current_user.role,
        created_at=current_user.profile.created_at,
        updated_at=current_user.profile.updated_at,
        last_access_at=current_user.profile.last_access_at,
    )
