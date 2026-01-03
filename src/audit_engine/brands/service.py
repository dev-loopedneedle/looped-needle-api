"""Brands domain service layer."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_engine.brands.schemas import (
    BrandCreate,
    BrandListQuery,
    BrandUpdate,
    ProductCreate,
    SupplyChainNodeCreate,
)
from src.audit_engine.exceptions import BrandNotFoundError, ReferentialIntegrityError
from src.audit_engine.models import Brand, Product, SupplyChainNode
from src.audit_engine.utils import check_brand_references
from src.auth.dependencies import UserContext
from src.auth.exceptions import AccessDeniedError


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

        Returns:
            Brand

        Raises:
            BrandNotFoundError: If brand not found
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

        Returns:
            Updated brand

        Raises:
            BrandNotFoundError: If brand not found
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
        Soft delete a brand (if not referenced by audit instances).

        Args:
            db: Database session
            brand_id: Brand ID

        Raises:
            BrandNotFoundError: If brand not found
            ReferentialIntegrityError: If brand is referenced by audit instances
        """
        brand = await BrandService.get_brand(db, brand_id, current_user)

        # Check if brand is referenced
        is_referenced, reference_type = await check_brand_references(db, str(brand_id))
        if is_referenced:
            raise ReferentialIntegrityError("brand", str(brand_id), reference_type)

        # Soft delete
        brand.deleted_at = datetime.utcnow()
        await db.commit()


class ProductService:
    """Service for product operations."""

    @staticmethod
    async def create_product(
        db: AsyncSession,
        brand_id: UUID,
        product_data: ProductCreate,
        current_user: UserContext,
    ) -> Product:
        """
        Create a new product.

        Args:
            db: Database session
            brand_id: Brand ID
            product_data: Product data

        Returns:
            Created product

        Raises:
            BrandNotFoundError: If brand not found
        """
        # Verify brand exists and ownership
        await BrandService.get_brand(db, brand_id, current_user)

        product = Product(brand_id=brand_id, **product_data.model_dump())
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product

    @staticmethod
    async def get_products_by_brand(
        db: AsyncSession,
        brand_id: UUID,
        current_user: UserContext,
    ) -> list[Product]:
        """
        Get all products for a brand.

        Args:
            db: Database session
            brand_id: Brand ID

        Returns:
            List of products

        Raises:
            BrandNotFoundError: If brand not found
        """
        # Verify brand exists and ownership
        await BrandService.get_brand(db, brand_id, current_user)

        result = await db.execute(
            select(Product).where(Product.brand_id == brand_id, Product.deleted_at.is_(None))
        )
        products = result.scalars().all()
        return list(products)


class SupplyChainNodeService:
    """Service for supply chain node operations."""

    @staticmethod
    async def create_node(
        db: AsyncSession,
        brand_id: UUID,
        node_data: SupplyChainNodeCreate,
        current_user: UserContext,
    ) -> SupplyChainNode:
        """
        Create a new supply chain node.

        Args:
            db: Database session
            brand_id: Brand ID
            node_data: Supply chain node data

        Returns:
            Created supply chain node

        Raises:
            BrandNotFoundError: If brand not found
        """
        # Verify brand exists and ownership
        await BrandService.get_brand(db, brand_id, current_user)

        node = SupplyChainNode(brand_id=brand_id, **node_data.model_dump())
        db.add(node)
        await db.commit()
        await db.refresh(node)
        return node

    @staticmethod
    async def get_nodes_by_brand(
        db: AsyncSession,
        brand_id: UUID,
        current_user: UserContext,
    ) -> list[SupplyChainNode]:
        """
        Get all supply chain nodes for a brand.

        Args:
            db: Database session
            brand_id: Brand ID

        Returns:
            List of supply chain nodes

        Raises:
            BrandNotFoundError: If brand not found
        """
        # Verify brand exists and ownership
        await BrandService.get_brand(db, brand_id, current_user)

        result = await db.execute(
            select(SupplyChainNode).where(
                SupplyChainNode.brand_id == brand_id, SupplyChainNode.deleted_at.is_(None)
            )
        )
        nodes = result.scalars().all()
        return list(nodes)

