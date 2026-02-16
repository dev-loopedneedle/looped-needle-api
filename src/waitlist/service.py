"""Waitlist domain service layer."""

import logging

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.waitlist.exceptions import WaitlistEntryExistsError
from src.waitlist.models import WaitlistEntry
from src.waitlist.schemas import WaitlistRequest

logger = logging.getLogger(__name__)


class WaitlistService:
    """Service for waitlist operations."""

    @staticmethod
    async def add_to_waitlist(
        db: AsyncSession,
        request: WaitlistRequest,
    ) -> WaitlistEntry:
        """
        Add an email to the waitlist.

        Args:
            db: Database session
            request: Waitlist submission request

        Returns:
            WaitlistEntry: Created waitlist entry

        Raises:
            WaitlistEntryExistsError: If email already exists in waitlist
        """
        # Check if email already exists
        result = await db.execute(select(WaitlistEntry).where(WaitlistEntry.email == request.email))
        existing_entry = result.scalar_one_or_none()

        if existing_entry:
            raise WaitlistEntryExistsError(request.email)

        # Create new waitlist entry
        entry = WaitlistEntry(
            email=request.email,
            name=request.name,
            message=request.message,
        )

        db.add(entry)
        try:
            await db.commit()
            await db.refresh(entry)
            logger.info(f"Added email to waitlist: {request.email}")
            return entry
        except IntegrityError as e:
            await db.rollback()
            # Check if it's a unique constraint violation
            if "waitlist_entries_email_key" in str(e.orig):
                raise WaitlistEntryExistsError(request.email) from e
            raise

    @staticmethod
    async def list_waitlist(
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[WaitlistEntry], int]:
        """
        List waitlist entries with pagination.

        Args:
            db: Database session
            limit: Maximum number of entries to return
            offset: Number of entries to skip

        Returns:
            Tuple of (list of entries, total count)
        """
        count_stmt = select(func.count()).select_from(WaitlistEntry)
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one() or 0

        stmt = (
            select(WaitlistEntry)
            .order_by(WaitlistEntry.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        entries = list(result.scalars().all())
        return entries, total
