"""Authentication domain service layer."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import UserProfile

logger = logging.getLogger(__name__)


class UserProfileService:
    """Service for user profile operations."""

    @staticmethod
    async def get_or_create_user_profile(db: AsyncSession, clerk_user_id: str) -> UserProfile:
        """
        Get or create user profile with idempotent creation.

        Args:
            db: Database session
            clerk_user_id: Clerk user identifier

        Returns:
            UserProfile: Existing or newly created user profile

        Raises:
            IntegrityError: If unique constraint violation occurs (should be handled by caller)
        """
        # Try to get existing profile
        result = await db.execute(
            select(UserProfile).where(UserProfile.clerk_user_id == clerk_user_id)
        )
        profile = result.scalar_one_or_none()

        if profile:
            return profile

        # Create new profile
        profile = UserProfile(clerk_user_id=clerk_user_id, is_active=True)
        db.add(profile)
        try:
            await db.commit()
            await db.refresh(profile)
            logger.info(f"Created user profile for clerk_user_id: {clerk_user_id}")
            return profile
        except IntegrityError:
            # Another request created the profile concurrently
            await db.rollback()
            # Retry to get the existing profile
            result = await db.execute(
                select(UserProfile).where(UserProfile.clerk_user_id == clerk_user_id)
            )
            profile = result.scalar_one()
            logger.info(f"Retrieved existing user profile for clerk_user_id: {clerk_user_id}")
            return profile

    @staticmethod
    async def update_last_access(db: AsyncSession, user_id: UUID) -> None:
        """
        Update last access timestamp for user profile.

        Args:
            db: Database session
            user_id: User profile ID
        """
        result = await db.execute(select(UserProfile).where(UserProfile.id == user_id))
        profile = result.scalar_one_or_none()

        if profile:
            profile.last_access_at = datetime.utcnow()
            await db.commit()
            await db.refresh(profile)

    @staticmethod
    async def get_user_profile(db: AsyncSession, user_id: UUID) -> UserProfile | None:
        """
        Get user profile by ID.

        Args:
            db: Database session
            user_id: User profile ID

        Returns:
            UserProfile or None if not found
        """
        result = await db.execute(select(UserProfile).where(UserProfile.id == user_id))
        return result.scalar_one_or_none()
