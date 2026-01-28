"""Brands domain service layer."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_workflows.models import AuditWorkflow, AuditWorkflowStatus
from src.audits.models import Audit
from src.auth.dependencies import UserContext
from src.auth.exceptions import AccessDeniedError
from src.brands.exceptions import BrandNotFoundError, ReferentialIntegrityError
from src.brands.models import Brand
from src.brands.schemas import BrandCreate, BrandListQuery, BrandUpdate, CategoryScore

logger = logging.getLogger(__name__)


class BrandService:
    """Service for brand operations."""

    @staticmethod
    async def create_brand(
        db: AsyncSession,
        brand_data: BrandCreate,
        current_user: UserContext,
    ) -> Brand:
        """
        Create a new brand.

        Args:
            db: Database session
            brand_data: Brand data
            current_user: Current user context

        Returns:
            Created brand
        """
        brand = Brand(**brand_data.model_dump(), user_id=current_user.profile.id)
        db.add(brand)
        await db.commit()
        await db.refresh(brand)
        return brand

    @staticmethod
    async def get_brand(
        db: AsyncSession,
        brand_id: UUID,
        current_user: UserContext | None = None,
    ) -> Brand:
        """
        Get brand by ID.

        Args:
            db: Database session
            brand_id: Brand ID
            current_user: Current user context (optional)

        Returns:
            Brand

        Raises:
            BrandNotFoundError: If brand not found
            AccessDeniedError: If user doesn't have access
        """
        result = await db.execute(
            select(Brand).where(Brand.id == brand_id, Brand.deleted_at.is_(None))
        )
        brand = result.scalar_one_or_none()
        if not brand:
            raise BrandNotFoundError(str(brand_id))
        if (
            current_user
            and current_user.role != "admin"
            and brand.user_id
            and brand.user_id != current_user.profile.id
        ):
            raise AccessDeniedError("Access denied for this brand")
        return brand

    @staticmethod
    async def get_brand_by_user(
        db: AsyncSession,
        user_id: UUID,
    ) -> Brand | None:
        """
        Get brand by owning user_id.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Brand or None if not found
        """
        result = await db.execute(
            select(Brand).where(
                Brand.user_id == user_id,
                Brand.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_brands(
        db: AsyncSession,
        query: BrandListQuery,
        current_user: UserContext,
    ) -> tuple[list[Brand], int]:
        """
        List brands with pagination.

        Args:
            db: Database session
            query: Query parameters
            current_user: Current user context

        Returns:
            Tuple of (brands, total count)
        """
        stmt = select(Brand).where(Brand.deleted_at.is_(None))
        count_stmt = select(func.count()).select_from(Brand).where(Brand.deleted_at.is_(None))

        # Non-admin users are restricted to their own brand
        if not current_user.role == "admin":
            stmt = stmt.where(Brand.user_id == current_user.profile.id)
            count_stmt = count_stmt.where(Brand.user_id == current_user.profile.id)

        total_result = await db.execute(count_stmt)
        total = total_result.scalar_one()

        stmt = stmt.order_by(Brand.created_at.desc()).limit(query.limit).offset(query.offset)

        result = await db.execute(stmt)
        brands = result.scalars().all()

        return list(brands), total

    @staticmethod
    async def update_brand(
        db: AsyncSession,
        brand_id: UUID,
        update_data: BrandUpdate,
        current_user: UserContext,
    ) -> Brand:
        """
        Update a brand.

        Args:
            db: Database session
            brand_id: Brand ID
            update_data: Update data
            current_user: Current user context

        Returns:
            Updated brand

        Raises:
            BrandNotFoundError: If brand not found
            AccessDeniedError: If user doesn't have access
        """
        brand = await BrandService.get_brand(db, brand_id, current_user)

        update_dict = update_data.model_dump(exclude_unset=True)
        if update_dict:
            update_dict["updated_at"] = datetime.utcnow()
            for key, value in update_dict.items():
                setattr(brand, key, value)

            await db.commit()
            await db.refresh(brand)

        return brand

    @staticmethod
    async def delete_brand(
        db: AsyncSession,
        brand_id: UUID,
        current_user: UserContext,
    ) -> None:
        """
        Soft delete a brand (if not referenced).

        Args:
            db: Database session
            brand_id: Brand ID
            current_user: Current user context

        Raises:
            BrandNotFoundError: If brand not found
            ReferentialIntegrityError: If brand is referenced
        """
        brand = await BrandService.get_brand(db, brand_id, current_user)

        # Check if brand is referenced by audits
        result = await db.execute(select(Audit).where(Audit.brand_id == str(brand_id)))
        if result.scalar_one_or_none():
            raise ReferentialIntegrityError("brand", str(brand_id), "audits")

        # Soft delete
        brand.deleted_at = datetime.utcnow()
        await db.commit()

    @staticmethod
    async def get_dashboard_summary(
        db: AsyncSession,
        brand_id: UUID,
    ) -> dict[str, int]:
        """
        Get dashboard summary metrics for a brand.

        Args:
            db: Database session
            brand_id: Brand ID

        Returns:
            Dictionary with totalAudits and completedAudits counts

        Raises:
            SQLAlchemyError: If database query fails
        """
        try:
            # Count total audits
            total_stmt = select(func.count(Audit.id)).where(Audit.brand_id == brand_id)
            total_result = await db.execute(total_stmt)
            total_audits = total_result.scalar_one() or 0

            # Count completed audits (audits with PROCESSING_COMPLETE workflow)
            completed_stmt = (
                select(func.count(func.distinct(Audit.id)))
                .select_from(Audit)
                .join(AuditWorkflow, Audit.id == AuditWorkflow.audit_id)
                .where(
                    Audit.brand_id == brand_id,
                    AuditWorkflow.status == AuditWorkflowStatus.PROCESSING_COMPLETE,
                )
            )
            completed_result = await db.execute(completed_stmt)
            completed_audits = completed_result.scalar_one() or 0

            return {
                "totalAudits": total_audits,
                "completedAudits": completed_audits,
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error getting dashboard summary for brand {brand_id}: {e}")
            raise

    @staticmethod
    async def get_latest_completed_audit(
        db: AsyncSession,
        brand_id: UUID,
    ) -> tuple[Audit, AuditWorkflow] | None:
        """
        Get the latest completed audit for a brand.

        Args:
            db: Database session
            brand_id: Brand ID

        Returns:
            Tuple of (Audit, AuditWorkflow) or None if no completed audits exist

        Raises:
            SQLAlchemyError: If database query fails
        """
        try:
            stmt = (
                select(Audit, AuditWorkflow)
                .join(AuditWorkflow, Audit.id == AuditWorkflow.audit_id)
                .where(
                    Audit.brand_id == brand_id,
                    AuditWorkflow.status == AuditWorkflowStatus.PROCESSING_COMPLETE,
                )
                .order_by(AuditWorkflow.updated_at.desc(), Audit.created_at.desc())
                .limit(1)
            )
            result = await db.execute(stmt)
            row = result.first()
            if row:
                return (row[0], row[1])
            return None
        except SQLAlchemyError as e:
            logger.error(f"Database error getting latest completed audit for brand {brand_id}: {e}")
            raise

    @staticmethod
    def extract_category_scores(category_scores_dict: dict[str, Any] | None) -> list[CategoryScore]:
        """
        Extract category scores from JSONB dictionary.

        Supports both old format (int) and new format (dict with score and hasClaims).

        Args:
            category_scores_dict: Dictionary with category scores (ENVIRONMENTAL, SOCIAL, etc.)
                Old format: {"ENVIRONMENTAL": 75}
                New format: {"ENVIRONMENTAL": {"score": 75, "hasClaims": true}}

        Returns:
            List of CategoryScore objects
        """
        if not category_scores_dict or not isinstance(category_scores_dict, dict):
            return []

        category_scores = []
        valid_categories = ["ENVIRONMENTAL", "SOCIAL", "CIRCULARITY", "TRANSPARENCY"]

        for category in valid_categories:
            if category in category_scores_dict:
                score_data = category_scores_dict[category]

                # Handle new format: {"score": int, "hasClaims": bool}
                if isinstance(score_data, dict):
                    score_value = score_data.get("score")
                    has_claims = score_data.get(
                        "hasClaims", True
                    )  # Default to True for backward compat

                    if isinstance(score_value, (int, float)) and 0 <= score_value <= 100:
                        category_scores.append(
                            CategoryScore(
                                category=category,
                                score=int(score_value),
                                hasClaims=bool(has_claims),
                            )
                        )
                    else:
                        logger.warning(
                            f"Invalid category score for {category}: {score_value} "
                            f"(expected int/float between 0-100)"
                        )
                # Handle old format: int (backward compatibility)
                elif isinstance(score_data, (int, float)) and 0 <= score_data <= 100:
                    # For old format, assume hasClaims=True (we can't know for sure)
                    category_scores.append(
                        CategoryScore(
                            category=category,
                            score=int(score_data),
                            hasClaims=True,
                        )
                    )
                else:
                    logger.warning(
                        f"Invalid category score format for {category}: {score_data} "
                        f"(expected int/float between 0-100 or dict with score and hasClaims)"
                    )

        return category_scores

    @staticmethod
    def map_workflow_status(workflow_status: str | None) -> str:
        """
        Map workflow status to user-friendly display status.

        Args:
            workflow_status: Workflow status string or None

        Returns:
            User-friendly status string
        """
        if not workflow_status:
            return "Generated"

        status_mapping = {
            AuditWorkflowStatus.PROCESSING_COMPLETE: "Completed",
            AuditWorkflowStatus.PROCESSING: "Processing",
            AuditWorkflowStatus.GENERATED: "Generated",
            AuditWorkflowStatus.PROCESSING_FAILED: "Failed",
        }

        return status_mapping.get(workflow_status, "Generated")

    @staticmethod
    async def get_recent_audits(
        db: AsyncSession,
        brand_id: UUID,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Get recent workflows for a brand.

        Args:
            db: Database session
            brand_id: Brand ID
            limit: Maximum number of workflows to return (default: 3)

        Returns:
            List of recent workflow dictionaries with audit info, status and category scores

        Raises:
            SQLAlchemyError: If database query fails
        """
        try:
            # Query workflows ordered by created_at (most recent first), joined with audits
            stmt = (
                select(
                    AuditWorkflow,
                    Audit,
                )
                .join(Audit, Audit.id == AuditWorkflow.audit_id)
                .where(Audit.brand_id == brand_id)
                .order_by(AuditWorkflow.created_at.desc())
                .limit(limit)
            )

            result = await db.execute(stmt)
            rows = result.all()

            recent_workflows = []
            for row in rows:
                workflow = row[0]
                audit = row[1]

                product_name, target_market = BrandService.extract_product_info(audit.audit_data)
                status = BrandService.map_workflow_status(workflow.status)

                # Only include category scores, overall_score, and certification if status is "Completed"
                category_scores_list = None
                workflow_overall_score = None
                workflow_certification = None
                if status == "Completed":
                    category_scores_list = [
                        cs.model_dump()
                        for cs in BrandService.extract_category_scores(workflow.category_scores)
                    ]
                    workflow_overall_score = workflow.overall_score
                    workflow_certification = workflow.certification

                recent_workflows.append(
                    {
                        "workflowId": str(workflow.id),
                        "auditId": str(audit.id),
                        "productName": product_name,
                        "targetMarket": target_market,
                        "status": status,
                        "categoryScores": category_scores_list,
                        "overallScore": workflow_overall_score,
                        "certification": workflow_certification,
                        "createdAt": workflow.created_at,
                    }
                )

            return recent_workflows
        except SQLAlchemyError as e:
            logger.error(f"Database error getting recent workflows for brand {brand_id}: {e}")
            raise

    @staticmethod
    def extract_product_info(audit_data: dict[str, Any] | None) -> tuple[str | None, str | None]:
        """
        Extract product name and target market from audit_data JSONB.

        Args:
            audit_data: Audit data dictionary

        Returns:
            Tuple of (product_name, target_market)
        """
        if not audit_data:
            return (None, None)

        product_info = audit_data.get("productInfo")
        if not product_info or not isinstance(product_info, dict):
            return (None, None)

        product_name = product_info.get("productName")
        target_market = product_info.get("targetMarket")

        return (
            str(product_name) if product_name else None,
            str(target_market) if target_market else None,
        )

    @staticmethod
    async def get_dashboard_data(
        db: AsyncSession,
        current_user: UserContext,
    ) -> dict:
        """
        Get dashboard data for the authenticated user's brand.

        Args:
            db: Database session
            current_user: Current user context

        Returns:
            Dictionary with summary, latestAuditScores, and recentAuditWorkflows

        Raises:
            BrandNotFoundError: If brand not found for user
            SQLAlchemyError: If database query fails
        """
        # Get user's brand
        brand = await BrandService.get_brand_by_user(db, current_user.profile.id)
        if not brand:
            logger.warning(f"Brand not found for user {current_user.profile.id}")
            raise BrandNotFoundError("Brand not found for user")

        try:
            # Get summary metrics (User Story 1)
            summary = await BrandService.get_dashboard_summary(db, brand.id)

            # Get latest completed audit scores (User Story 2)
            latest_audit_result = await BrandService.get_latest_completed_audit(db, brand.id)
            latest_audit_scores = None

            if latest_audit_result:
                audit, workflow = latest_audit_result
                product_name, target_market = BrandService.extract_product_info(audit.audit_data)
                category_scores = BrandService.extract_category_scores(workflow.category_scores)

                # Handle edge case: null category_scores
                if not category_scores:
                    logger.debug(f"Audit {audit.id} has no valid category scores")

                latest_audit_scores = {
                    "auditId": str(audit.id),
                    "workflowId": str(workflow.id),
                    "productName": product_name,
                    "targetMarket": target_market,
                    "completedAt": workflow.updated_at or workflow.created_at,
                    "categoryScores": [cs.model_dump() for cs in category_scores],
                    "overallScore": workflow.overall_score,
                    "certification": workflow.certification,
                }

            # Get recent workflows list (User Story 3)
            recent_workflows = await BrandService.get_recent_audits(db, brand.id, limit=3)

            return {
                "summary": summary,
                "latestAuditScores": latest_audit_scores,
                "recentAuditWorkflows": recent_workflows,
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error getting dashboard data for brand {brand.id}: {e}")
            raise
