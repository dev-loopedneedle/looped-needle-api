"""Authentication domain router."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import UserContext, get_current_user
from src.auth.schemas import UserProfileResponse
from src.brands.schemas import BrandResponse
from src.brands.service import BrandService
from src.database import get_db

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current user profile",
    description="Retrieve the authenticated user's profile information including role and associated brand",
)
async def get_me(
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfileResponse:
    """
    Get current authenticated user profile.

    Returns:
        UserProfileResponse: User profile with role information and associated brand
    """
    # Fetch brand associated with this user profile
    brand = await BrandService.get_brand_by_user(db, current_user.profile.id)
    brand_response = BrandResponse.model_validate(brand) if brand else None

    return UserProfileResponse(
        id=current_user.profile.id,
        clerk_user_id=current_user.profile.clerk_user_id,
        is_active=current_user.profile.is_active,
        role=current_user.role,
        created_at=current_user.profile.created_at,
        updated_at=current_user.profile.updated_at,
        last_access_at=current_user.profile.last_access_at,
        brand=brand_response,
    )
