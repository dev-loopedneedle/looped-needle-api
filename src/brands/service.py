"""Brands domain service layer."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import UserContext
from src.auth.exceptions import AccessDeniedError
from src.brands.exceptions import BrandNotFoundError, ReferentialIntegrityError
from src.brands.models import Brand
from src.brands.schemas import BrandCreate, BrandListQuery, BrandUpdate


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
        from src.audits.models import Audit

        result = await db.execute(
            select(Audit).where(
                Audit.brand_id == str(brand_id)
            )
        )
        if result.scalar_one_or_none():
            raise ReferentialIntegrityError("brand", str(brand_id), "audits")

        # Soft delete
        brand.deleted_at = datetime.utcnow()
        await db.commit()


