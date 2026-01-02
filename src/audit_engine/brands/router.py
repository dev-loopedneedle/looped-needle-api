"""Brands domain router."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_engine.brands.schemas import (
    BrandCreate,
    BrandListQuery,
    BrandListResponse,
    BrandResponse,
    BrandUpdate,
    ProductCreate,
    ProductResponse,
    SupplyChainNodeCreate,
    SupplyChainNodeResponse,
)
from src.audit_engine.brands.service import (
    BrandService,
    ProductService,
    SupplyChainNodeService,
)
from src.audit_engine.dependencies import get_audit_engine_db

router = APIRouter(prefix="/api/v1", tags=["brands"])
logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str | None:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", None)


# Brand endpoints
@router.post(
    "/brands",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create brand",
    description="Create a new brand profile with company details",
)
async def create_brand(
    request: Request,
    brand_data: BrandCreate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> BrandResponse:
    """Create a new brand."""
    request_id = _get_request_id(request)
    logger.info(f"Creating brand: name={brand_data.name}", extra={"request_id": request_id})
    brand = await BrandService.create_brand(db, brand_data)
    return BrandResponse.model_validate(brand)


@router.get(
    "/brands",
    response_model=BrandListResponse,
    summary="List brands",
    description="Retrieve a paginated list of brands",
)
async def list_brands(
    request: Request,
    limit: int = Query(default=20, ge=1, le=50, description="Maximum number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    db: AsyncSession = Depends(get_audit_engine_db),
) -> BrandListResponse:
    """List brands with pagination."""
    request_id = _get_request_id(request)
    logger.info(f"Listing brands: limit={limit}, offset={offset}", extra={"request_id": request_id})
    query = BrandListQuery(limit=limit, offset=offset)
    brands, total = await BrandService.list_brands(db, query)
    return BrandListResponse(
        items=[BrandResponse.model_validate(brand) for brand in brands],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get(
    "/brands/{brand_id}",
    response_model=BrandResponse,
    summary="Get brand",
    description="Retrieve a specific brand by ID",
)
async def get_brand(
    request: Request,
    brand_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> BrandResponse:
    """Get brand by ID."""
    request_id = _get_request_id(request)
    logger.info(f"Getting brand: id={brand_id}", extra={"request_id": request_id})
    brand = await BrandService.get_brand(db, brand_id)
    return BrandResponse.model_validate(brand)


@router.put(
    "/brands/{brand_id}",
    response_model=BrandResponse,
    summary="Update brand",
    description="Update an existing brand profile",
)
async def update_brand(
    request: Request,
    brand_id: UUID,
    brand_data: BrandUpdate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> BrandResponse:
    """Update brand."""
    request_id = _get_request_id(request)
    logger.info(f"Updating brand: id={brand_id}", extra={"request_id": request_id})
    brand = await BrandService.update_brand(db, brand_id, brand_data)
    return BrandResponse.model_validate(brand)


@router.delete(
    "/brands/{brand_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete brand",
    description="Soft delete a brand (if not referenced by audit instances)",
)
async def delete_brand(
    request: Request,
    brand_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> None:
    """Delete brand (soft delete)."""
    request_id = _get_request_id(request)
    logger.info(f"Deleting brand: id={brand_id}", extra={"request_id": request_id})
    await BrandService.delete_brand(db, brand_id)


# Product endpoints
@router.post(
    "/brands/{brand_id}/products",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
    description="Create a new product for a brand",
)
async def create_product(
    request: Request,
    brand_id: UUID,
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> ProductResponse:
    """Create a new product."""
    request_id = _get_request_id(request)
    logger.info(
        f"Creating product for brand: brand_id={brand_id}", extra={"request_id": request_id}
    )
    product = await ProductService.create_product(db, brand_id, product_data)
    return ProductResponse.model_validate(product)


@router.get(
    "/brands/{brand_id}/products",
    response_model=list[ProductResponse],
    summary="List products",
    description="Retrieve all products for a brand",
)
async def list_products(
    request: Request,
    brand_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> list[ProductResponse]:
    """List products for a brand."""
    request_id = _get_request_id(request)
    logger.info(
        f"Listing products for brand: brand_id={brand_id}", extra={"request_id": request_id}
    )
    products = await ProductService.get_products_by_brand(db, brand_id)
    return [ProductResponse.model_validate(product) for product in products]


# Supply Chain Node endpoints
@router.post(
    "/brands/{brand_id}/supply-chain-nodes",
    response_model=SupplyChainNodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create supply chain node",
    description="Create a new supply chain node for a brand",
)
async def create_supply_chain_node(
    request: Request,
    brand_id: UUID,
    node_data: SupplyChainNodeCreate,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> SupplyChainNodeResponse:
    """Create a new supply chain node."""
    request_id = _get_request_id(request)
    logger.info(
        f"Creating supply chain node for brand: brand_id={brand_id}",
        extra={"request_id": request_id},
    )
    node = await SupplyChainNodeService.create_node(db, brand_id, node_data)
    return SupplyChainNodeResponse.model_validate(node)


@router.get(
    "/brands/{brand_id}/supply-chain-nodes",
    response_model=list[SupplyChainNodeResponse],
    summary="List supply chain nodes",
    description="Retrieve all supply chain nodes for a brand",
)
async def list_supply_chain_nodes(
    request: Request,
    brand_id: UUID,
    db: AsyncSession = Depends(get_audit_engine_db),
) -> list[SupplyChainNodeResponse]:
    """List supply chain nodes for a brand."""
    request_id = _get_request_id(request)
    logger.info(
        f"Listing supply chain nodes for brand: brand_id={brand_id}",
        extra={"request_id": request_id},
    )
    nodes = await SupplyChainNodeService.get_nodes_by_brand(db, brand_id)
    return [SupplyChainNodeResponse.model_validate(node) for node in nodes]

