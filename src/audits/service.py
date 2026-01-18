"""Audits domain service layer."""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import bindparam, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.audits.exceptions import AuditNotFoundError, AuditPublishedError
from src.audits.models import Audit, AuditStatus
from src.audits.schemas import AuditListQuery, CreateAuditRequest, UpdateAuditRequest
from src.auth.dependencies import UserContext
from src.auth.exceptions import AccessDeniedError
from src.brands.service import BrandService

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit operations."""

    @staticmethod
    async def create_audit(
        db: AsyncSession,
        audit_request: CreateAuditRequest,
        current_user: UserContext | None = None,
    ) -> Audit:
        """
        Create a new audit.

        Args:
            db: Database session
            audit_request: Audit creation request
            current_user: Current user context (optional)

        Returns:
            Audit: Created audit instance

        Raises:
            BrandNotFoundError: If brand_id doesn't exist (if validation needed)
        """
        # Validate brand exists and user has access
        await BrandService.get_brand(db, audit_request.brand_id, current_user)

        # Handle partial data - if audit_data is None, use empty dict
        audit_data_dict = {}
        if audit_request.audit_data is not None:
            audit_data_dict = audit_request.audit_data.model_dump(exclude_none=True)

        audit = Audit(
            brand_id=audit_request.brand_id,
            status=AuditStatus.DRAFT,  # Always create as DRAFT
            audit_data=audit_data_dict,
        )

        db.add(audit)
        await db.commit()
        await db.refresh(audit)

        logger.info(f"Created audit: id={audit.id}, brand_id={audit.brand_id}, status=DRAFT")
        return audit

    @staticmethod
    async def get_audit(db: AsyncSession, audit_id: str) -> Audit:
        """
        Get audit by ID.

        Args:
            db: Database session
            audit_id: Audit ID (UUID string)

        Returns:
            Audit: Audit instance

        Raises:
            AuditNotFoundError: If audit not found
        """
        try:
            audit_uuid = UUID(audit_id)
        except ValueError as err:
            raise AuditNotFoundError(audit_id) from err

        result = await db.execute(select(Audit).where(Audit.id == audit_uuid))
        audit = result.scalar_one_or_none()

        if not audit:
            raise AuditNotFoundError(audit_id)

        return audit

    @staticmethod
    async def verify_audit_access(
        db: AsyncSession,
        audit_id: UUID,
        current_user: UserContext,
    ) -> Audit:
        """
        Verify user has access to the audit and return it.

        Admins can access any audit. Brand users can only access audits from their brand.

        Args:
            db: Database session
            audit_id: Audit ID to verify access for
            current_user: Current user context

        Returns:
            Audit: Audit instance if access is granted

        Raises:
            AuditNotFoundError: If audit not found
            AccessDeniedError: If user doesn't have access to this audit
        """
        result = await db.execute(select(Audit).where(Audit.id == audit_id))
        audit = result.scalar_one_or_none()
        if not audit:
            raise AuditNotFoundError(str(audit_id))

        # Admin can access any audit
        if current_user.role == "admin":
            return audit

        # Brand users can only access audits from their brand
        brand = await BrandService.get_brand_by_user(db, current_user.profile.id)
        if not brand or brand.id != audit.brand_id:
            raise AccessDeniedError("Access denied to this audit")

        return audit

    @staticmethod
    async def update_audit(
        db: AsyncSession, audit_id: str, update_request: UpdateAuditRequest
    ) -> Audit:
        """
        Update an audit (only if not published).

        Args:
            db: Database session
            audit_id: Audit ID
            update_request: Update request (status cannot be set)

        Returns:
            Audit: Updated audit instance

        Raises:
            AuditNotFoundError: If audit not found
            AuditPublishedError: If audit is published
        """
        audit = await AuditService.get_audit(db, audit_id)

        # Prevent updates if audit is published
        if audit.status == AuditStatus.PUBLISHED:
            raise AuditPublishedError(str(audit.id))

        # Update fields if provided
        if update_request.brand_id is not None:
            # Validate brand exists (access control handled via audit's brand)
            await BrandService.get_brand(db, update_request.brand_id, None)
            audit.brand_id = update_request.brand_id

        if update_request.audit_data is not None:
            audit.audit_data = update_request.audit_data.model_dump(exclude_none=True)

        # Always set status back to DRAFT on update
        audit.status = AuditStatus.DRAFT
        audit.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(audit)

        logger.info(f"Updated audit: id={audit.id}, status=DRAFT")
        return audit

    @staticmethod
    async def publish_audit(db: AsyncSession, audit_id: str) -> Audit:
        """
        Publish an audit (set status to PUBLISHED).

        Args:
            db: Database session
            audit_id: Audit ID

        Returns:
            Audit: Published audit instance

        Raises:
            AuditNotFoundError: If audit not found
        """
        audit = await AuditService.get_audit(db, audit_id)

        audit.status = AuditStatus.PUBLISHED
        audit.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(audit)

        logger.info(f"Published audit: id={audit.id}, status=PUBLISHED")
        return audit

    @staticmethod
    async def list_audits(
        db: AsyncSession,
        query: AuditListQuery,
        current_user: UserContext | None = None,
    ) -> tuple[list[Audit], int]:
        """
        List audits with pagination and optional filtering.

        Args:
            db: Database session
            query: Query parameters (brand_id, status, scope, category, limit, offset)
            current_user: Current user context (optional, for access control)

        Returns:
            Tuple of (audits, total count)
        """
        stmt = select(Audit)
        count_stmt = select(func.count()).select_from(Audit)

        # Access control: Non-admin users can only see audits from their own brand
        if current_user and current_user.role != "admin":
            # Get user's brand
            brand = await BrandService.get_brand_by_user(db, current_user.profile.id)
            if not brand:
                # User has no brand, return empty result
                return [], 0
            # Force filter by user's brand (ignore any brand_id in query)
            stmt = stmt.where(Audit.brand_id == brand.id)
            count_stmt = count_stmt.where(Audit.brand_id == brand.id)
        elif query.brand_id is not None:
            # Admin users can optionally filter by brand_id
            # Validate brand exists (no access check needed for admins)
            await BrandService.get_brand(db, query.brand_id, None)
            stmt = stmt.where(Audit.brand_id == query.brand_id)
            count_stmt = count_stmt.where(Audit.brand_id == query.brand_id)
        # If admin and no brand_id provided, show all audits (no filter)

        # Filter by status if provided
        if query.status is not None:
            stmt = stmt.where(Audit.status == query.status)
            count_stmt = count_stmt.where(Audit.status == query.status)

        # Filter by scope (from audit_data.productInfo.auditScope) if provided
        if query.scope is not None:
            # Use PostgreSQL JSONB operators to filter nested field
            # Handles null audit_data and missing productInfo gracefully
            # The -> operator returns JSONB, ->> returns text
            scope_condition = text(
                "(audit_data->'productInfo'->>'auditScope') = :scope"
            ).bindparams(bindparam("scope", query.scope))
            stmt = stmt.where(scope_condition)
            count_stmt = count_stmt.where(scope_condition)

        # Filter by category (from audit_data.productInfo.productCategory) if provided
        if query.category is not None:
            # Use PostgreSQL JSONB operators to filter nested field
            # Handles null audit_data and missing productInfo gracefully
            category_condition = text(
                "(audit_data->'productInfo'->>'productCategory') = :category"
            ).bindparams(bindparam("category", query.category))
            stmt = stmt.where(category_condition)
            count_stmt = count_stmt.where(category_condition)

        # Get total count
        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        # Apply pagination and ordering
        stmt = stmt.order_by(Audit.created_at.desc()).limit(query.limit).offset(query.offset)

        result = await db.execute(stmt)
        audits = result.scalars().all()

        return list(audits), total
