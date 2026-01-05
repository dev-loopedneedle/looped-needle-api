"""Waitlist domain service layer."""

import logging

from sqlalchemy import select
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
