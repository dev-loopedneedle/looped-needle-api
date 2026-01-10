"""Dependencies for rules domain."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import UserContext, get_admin_user
from src.database import get_db


async def get_admin(
    current_user: UserContext = Depends(get_admin_user),
) -> UserContext:
    """Ensure caller is admin."""
    return current_user


async def get_session(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    """Provide DB session."""
    return db
