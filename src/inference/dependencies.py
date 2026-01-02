"""Inference engine domain dependencies."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db


async def get_inference_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for inference database sessions.

    Yields:
        AsyncSession: Database session
    """
    async for session in get_db():
        yield session
