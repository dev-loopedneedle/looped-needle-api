"""Brands domain router."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import UserContext, get_current_user
from src.brands.exceptions import BrandNotFoundError
from src.brands.schemas import (
    BrandCreate,
    BrandListQuery,
    BrandListResponse,
    BrandResponse,
    BrandUpdate,
    DashboardResponse,
)
from src.brands.service import BrandService
from src.core.dependencies import get_request_id
from src.database import get_db

router = APIRouter(prefix="/api/v1", tags=["brands"])
logger = logging.getLogger(__name__)


@router.post(
    "/brands",
    response_model=BrandResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create brand",
    description="Create a new brand profile with company details",
)
async def create_brand(
    brand_data: BrandCreate,
    request_id: str | None = Depends(get_request_id),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BrandResponse:
    """Create a new brand."""
    logger.info(f"Creating brand: name={brand_data.name}", extra={"request_id": request_id})
    brand = await BrandService.create_brand(db, brand_data, current_user)
    return BrandResponse.model_validate(brand)


@router.get(
    "/brands",
    response_model=BrandListResponse,
    summary="List brands",
    description="Retrieve a paginated list of brands",
)
async def list_brands(
    limit: int = Query(default=20, ge=1, le=50, description="Maximum number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    request_id: str | None = Depends(get_request_id),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BrandListResponse:
    """List brands with pagination."""
    logger.info(f"Listing brands: limit={limit}, offset={offset}", extra={"request_id": request_id})
    query = BrandListQuery(limit=limit, offset=offset)
    brands, total = await BrandService.list_brands(db, query, current_user)
    return BrandListResponse(
        items=[BrandResponse.model_validate(brand) for brand in brands],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get(
    "/brands/dashboard",
    response_model=DashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get brand dashboard",
    description="Retrieve aggregated dashboard data for the authenticated user's brand, including summary metrics, latest audit scores, and recent audits list",
    tags=["brands"],
)
async def get_dashboard(
    request_id: str | None = Depends(get_request_id),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardResponse:
    """Get dashboard data for current user's brand."""
    logger.info("Getting dashboard data", extra={"request_id": request_id})
    try:
        dashboard_data = await BrandService.get_dashboard_data(db, current_user)
        return DashboardResponse.model_validate(dashboard_data)
    except BrandNotFoundError as e:
        logger.warning(f"Brand not found for user: {e}", extra={"request_id": request_id})
        raise


@router.get(
    "/brands/{brand_id}",
    response_model=BrandResponse,
    summary="Get brand",
    description="Retrieve a specific brand by ID",
)
async def get_brand(
    brand_id: UUID,
    request_id: str | None = Depends(get_request_id),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BrandResponse:
    """Get brand by ID."""
    logger.info(f"Getting brand: id={brand_id}", extra={"request_id": request_id})
    brand = await BrandService.get_brand(db, brand_id, current_user)
    return BrandResponse.model_validate(brand)


@router.put(
    "/brands/{brand_id}",
    response_model=BrandResponse,
    summary="Update brand",
    description="Update an existing brand profile",
)
async def update_brand(
    brand_id: UUID,
    brand_data: BrandUpdate,
    request_id: str | None = Depends(get_request_id),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BrandResponse:
    """Update brand."""
    logger.info(f"Updating brand: id={brand_id}", extra={"request_id": request_id})
    brand = await BrandService.update_brand(db, brand_id, brand_data, current_user)
    return BrandResponse.model_validate(brand)


@router.delete(
    "/brands/{brand_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete brand",
    description="Soft delete a brand (if not referenced)",
)
async def delete_brand(
    brand_id: UUID,
    request_id: str | None = Depends(get_request_id),
    current_user: UserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete brand (soft delete)."""
    logger.info(f"Deleting brand: id={brand_id}", extra={"request_id": request_id})
    await BrandService.delete_brand(db, brand_id, current_user)
