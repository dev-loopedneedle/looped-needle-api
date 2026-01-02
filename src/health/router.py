"""Health check router."""

import logging
from datetime import datetime

from fastapi import APIRouter, Request, status

from src.config import settings
from src.database import check_database_health
from src.health.schemas import HealthCheck, HealthResponse

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str | None:
    """Get request ID from request state."""
    return getattr(request.state, "request_id", None)


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if the API is running and healthy. Returns overall API health status including database connectivity. Useful for monitoring, load balancer health checks, and service discovery.",
    response_description="Health status response with API version, timestamp, and individual service checks.",
)
async def health_check(request: Request) -> HealthResponse:
    """
    Health check endpoint.

    Performs health checks on all critical services (database, etc.)
    and returns an overall health status. Returns 'healthy' only if all
    services are operational.
    """
    request_id = _get_request_id(request)
    logger.info("Health check requested", extra={"request_id": request_id})
    db_healthy = await check_database_health()
    overall_status = "healthy" if db_healthy else "unhealthy"

    logger.info(
        f"Health check completed: status={overall_status}, db_healthy={db_healthy}",
        extra={"request_id": request_id, "status": overall_status},
    )

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=settings.version,
        checks={
            "database": HealthCheck(
                status="healthy" if db_healthy else "unhealthy",
                message="Database connection check",
            ).model_dump(),
        },
    )


@router.get(
    "/health/db",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Database health check",
    description="Check if the database connection is healthy. Specifically tests database connectivity and returns detailed database health status. Useful for database-specific monitoring and troubleshooting.",
    response_description="Database health status response with connection check results.",
)
async def database_health_check(request: Request) -> HealthResponse:
    """
    Database health check endpoint.

    Performs a specific health check on the database connection.
    Tests connectivity and returns detailed database health status.
    """
    request_id = _get_request_id(request)
    logger.info("Database health check requested", extra={"request_id": request_id})
    db_healthy = await check_database_health()
    status_code = "healthy" if db_healthy else "unhealthy"

    logger.info(
        f"Database health check completed: status={status_code}",
        extra={"request_id": request_id, "db_status": status_code},
    )

    return HealthResponse(
        status=status_code,
        timestamp=datetime.utcnow(),
        version=settings.version,
        checks={
            "database": HealthCheck(
                status=status_code,
                message="Database connection check",
            ).model_dump(),
        },
    )
