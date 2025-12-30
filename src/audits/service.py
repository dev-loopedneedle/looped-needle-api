"""Audits domain service layer."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audits.exceptions import AuditNotFoundError
from src.audits.models import Audit
from src.audits.schemas import AuditRecordCreate, AuditRecordListQuery, AuditRecordUpdate


class AuditService:
    """Service for audit record operations."""

    @staticmethod
    async def create(
        db: AsyncSession,
        audit_data: AuditRecordCreate,
    ) -> Audit:
        """
        Create a new audit record.

        Args:
            db: Database session
            audit_data: Audit record data

        Returns:
            Created audit record
        """
        audit = Audit(**audit_data.model_dump())
        db.add(audit)
        await db.commit()
        await db.refresh(audit)
        return audit

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        audit_id: UUID,
    ) -> Audit:
        """
        Get audit record by ID.

        Args:
            db: Database session
            audit_id: Audit record ID

        Returns:
            Audit record

        Raises:
            AuditNotFoundError: If audit record not found
        """
        result = await db.execute(select(Audit).where(Audit.id == audit_id))
        audit = result.scalar_one_or_none()
        if not audit:
            raise AuditNotFoundError(str(audit_id))
        return audit

    @staticmethod
    async def list(
        db: AsyncSession,
        query: AuditRecordListQuery,
    ) -> tuple[list[Audit], int]:
        """
        List audit records with filtering and pagination.

        Args:
            db: Database session
            query: Query parameters

        Returns:
            Tuple of (audit records, total count)
        """
        # Build query
        stmt = select(Audit)
        count_stmt = select(func.count()).select_from(Audit)

        # Apply filters
        if query.name:
            stmt = stmt.where(Audit.name.ilike(f"%{query.name}%"))
            count_stmt = count_stmt.where(Audit.name.ilike(f"%{query.name}%"))

        if query.created_after:
            stmt = stmt.where(Audit.created_at >= query.created_after)
            count_stmt = count_stmt.where(Audit.created_at >= query.created_after)

        if query.created_before:
            stmt = stmt.where(Audit.created_at <= query.created_before)
            count_stmt = count_stmt.where(Audit.created_at <= query.created_before)

        # Get total count
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        stmt = stmt.order_by(Audit.created_at.desc()).limit(query.limit).offset(query.offset)

        # Execute query
        result = await db.execute(stmt)
        audits = result.scalars().all()

        return list(audits), total

    @staticmethod
    async def update(
        db: AsyncSession,
        audit_id: UUID,
        update_data: AuditRecordUpdate,
    ) -> Audit:
        """
        Update an audit record.

        Args:
            db: Database session
            audit_id: Audit record ID
            update_data: Update data

        Returns:
            Updated audit record

        Raises:
            AuditNotFoundError: If audit record not found
        """
        audit = await AuditService.get_by_id(db, audit_id)

        # Update fields
        update_dict = update_data.model_dump(exclude_unset=True)
        if update_dict:
            update_dict["updated_at"] = datetime.utcnow()
            for key, value in update_dict.items():
                setattr(audit, key, value)

            await db.commit()
            await db.refresh(audit)

        return audit

    @staticmethod
    async def delete(
        db: AsyncSession,
        audit_id: UUID,
    ) -> None:
        """
        Delete an audit record.

        Args:
            db: Database session
            audit_id: Audit record ID

        Raises:
            AuditNotFoundError: If audit record not found
        """
        audit = await AuditService.get_by_id(db, audit_id)
        await db.delete(audit)
        await db.commit()
