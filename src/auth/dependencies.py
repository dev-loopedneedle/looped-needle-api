"""Authentication dependencies for FastAPI."""

import logging
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_engine.dependencies import get_audit_engine_db
from src.auth.clerk_client import ClerkClient
from src.auth.exceptions import AuthenticationError, ServiceUnavailableError
from src.auth.models import UserProfile
from src.auth.service import UserProfileService

logger = logging.getLogger(__name__)

security = HTTPBearer()


@dataclass
class UserContext:
    """User context with profile and role."""

    profile: UserProfile
    role: str | None = None


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_audit_engine_db)],
) -> UserContext:
    """
    Get current authenticated user from Clerk token.

    Args:
        credentials: HTTP Bearer token credentials
        db: Database session

    Returns:
        UserContext: User profile and role

    Raises:
        HTTPException: 401 if authentication fails, 503 if service unavailable
    """
    token = credentials.credentials

    try:
        # Initialize Clerk client and verify token
        clerk_client = ClerkClient()
        verified_token = clerk_client.verify_token(token)

        # Extract user ID from token claims (typically 'sub' field)
        clerk_user_id = str(
            verified_token.get("sub")
            or verified_token.get("id")
            or verified_token.get("user_id")
            or ""
        )
        if not clerk_user_id:
            logger.warning("Token missing user ID in claims")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user identifier",
            )

        # Extract public_metadata and role
        public_metadata = verified_token.get("public_metadata", {})
        role = public_metadata.get("role") if isinstance(public_metadata, dict) else None

        # Get or create user profile (idempotent)
        try:
            profile = await UserProfileService.get_or_create_user_profile(db, clerk_user_id)
        except Exception as e:
            logger.error(f"Failed to get or create user profile: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user profile",
            ) from e

        # Check if profile is active
        if not profile.is_active:
            logger.warning(f"Inactive profile attempted authentication: {clerk_user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive",
            )

        # Update last access timestamp
        await UserProfileService.update_last_access(db, profile.id)

        # Create user context with role
        user_context = UserContext(profile=profile, role=role)
        return user_context

    except AuthenticationError as e:
        logger.warning(f"Authentication error: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
        ) from e
    except ServiceUnavailableError as e:
        logger.error(f"Service unavailable: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=e.message,
        ) from e
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error during authentication: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed",
        ) from e


async def get_admin_user(
    current_user: Annotated[UserContext, Depends(get_current_user)],
) -> UserContext:
    """
    Dependency that ensures user has admin role.

    Args:
        current_user: Current authenticated user context

    Returns:
        UserContext: User context (guaranteed to have admin role)

    Raises:
        HTTPException: 403 if user is not admin
    """
    if not current_user.role or current_user.role != "admin":
        logger.warning(
            f"Non-admin user attempted admin access: {current_user.profile.clerk_user_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
