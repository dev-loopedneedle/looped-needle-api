"""Global exception handlers for the FastAPI application."""

import logging

from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.audits.exceptions import (
    AuditNotFoundError as AuditsAuditNotFoundError,
)
from src.audits.exceptions import (
    AuditPublishedError,
)
from src.auth.exceptions import AccessDeniedError, AuthenticationError, ServiceUnavailableError
from src.brands.exceptions import BrandNotFoundError, ReferentialIntegrityError
from src.core.schemas import ErrorResponse
from src.exceptions import BaseAPIException
from src.waitlist.exceptions import WaitlistEntryExistsError


def _create_error_response(
    error: str,
    message: str,
    status_code: int,
    request_id: str | None = None,
    detail: str | None = None,
) -> JSONResponse:
    """
    Create a standardized error response.

    Args:
        error: Error type or code
        message: Human-readable error message
        status_code: HTTP status code
        request_id: Optional request identifier for tracing
        detail: Optional additional context about the error

    Returns:
        JSONResponse with standardized error format
    """
    error_response = ErrorResponse(
        error=error,
        message=message,
        status_code=status_code,
        request_id=request_id,
        detail=detail,
    )
    return JSONResponse(
        status_code=status_code,
        content=error_response.model_dump(exclude_none=True),
    )


def register_exception_handlers(app) -> None:
    """Register all exception handlers with the FastAPI app."""

    @app.exception_handler(BaseAPIException)
    async def base_api_exception_handler(request: Request, exc: BaseAPIException):
        """Handle base API exceptions."""
        request_id = getattr(request.state, "request_id", None)
        return _create_error_response(
            error=exc.__class__.__name__,
            message=exc.message,
            status_code=exc.status_code,
            request_id=request_id,
        )

    @app.exception_handler(ReferentialIntegrityError)
    async def referential_integrity_handler(request: Request, exc: ReferentialIntegrityError):
        """Handle referential integrity errors."""
        request_id = getattr(request.state, "request_id", None)
        return _create_error_response(
            error="ReferentialIntegrityError",
            message=exc.message,
            status_code=status.HTTP_409_CONFLICT,
            request_id=request_id,
            detail="Cannot delete this entity because it is referenced by other entities.",
        )

    @app.exception_handler(BrandNotFoundError)
    async def brand_not_found_handler(request: Request, exc: BrandNotFoundError):
        """Handle brand not found errors."""
        request_id = getattr(request.state, "request_id", None)
        return _create_error_response(
            error="BrandNotFound",
            message=exc.message,
            status_code=status.HTTP_404_NOT_FOUND,
            request_id=request_id,
        )

    @app.exception_handler(AuditsAuditNotFoundError)
    async def audits_audit_not_found_handler(request: Request, exc: AuditsAuditNotFoundError):
        """Handle audits domain audit not found errors."""
        request_id = getattr(request.state, "request_id", None)
        return _create_error_response(
            error="AuditNotFound",
            message=exc.message,
            status_code=status.HTTP_404_NOT_FOUND,
            request_id=request_id,
        )

    @app.exception_handler(AuditPublishedError)
    async def audit_published_handler(request: Request, exc: AuditPublishedError):
        """Handle audit published errors."""
        request_id = getattr(request.state, "request_id", None)
        return _create_error_response(
            error="AuditPublished",
            message=exc.message,
            status_code=status.HTTP_400_BAD_REQUEST,
            request_id=request_id,
        )

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(request: Request, exc: AuthenticationError):
        """Handle authentication errors."""
        request_id = getattr(request.state, "request_id", None)
        return _create_error_response(
            error="AuthenticationError",
            message=exc.message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            request_id=request_id,
        )

    @app.exception_handler(ServiceUnavailableError)
    async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError):
        """Handle service unavailable errors."""
        request_id = getattr(request.state, "request_id", None)
        return _create_error_response(
            error="ServiceUnavailable",
            message=exc.message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            request_id=request_id,
        )

    @app.exception_handler(AccessDeniedError)
    async def access_denied_handler(request: Request, exc: AccessDeniedError):
        """Handle access denied errors."""
        request_id = getattr(request.state, "request_id", None)
        return _create_error_response(
            error="AccessDenied",
            message=exc.message,
            status_code=status.HTTP_403_FORBIDDEN,
            request_id=request_id,
        )

    @app.exception_handler(WaitlistEntryExistsError)
    async def waitlist_entry_exists_handler(request: Request, exc: WaitlistEntryExistsError):
        """Handle waitlist entry already exists errors."""
        request_id = getattr(request.state, "request_id", None)
        return _create_error_response(
            error="WaitlistEntryExists",
            message=exc.message,
            status_code=status.HTTP_409_CONFLICT,
            request_id=request_id,
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception):
        """Handle 404 errors."""
        request_id = getattr(request.state, "request_id", None)
        return _create_error_response(
            error="NotFound",
            message=f"Endpoint {request.url.path} not found",
            status_code=status.HTTP_404_NOT_FOUND,
            request_id=request_id,
            detail="The requested endpoint does not exist. Please check the URL and API documentation at /docs.",
        )

    @app.exception_handler(500)
    async def internal_server_error_handler(request: Request, exc: Exception):
        """Handle 500 errors."""
        logger = logging.getLogger(__name__)
        request_id = getattr(request.state, "request_id", None)
        logger.error(
            f"Internal server error: {exc}", exc_info=True, extra={"request_id": request_id}
        )
        return _create_error_response(
            error="InternalServerError",
            message="An internal server error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=request_id,
            detail="An unexpected error occurred while processing your request. Please try again later or contact support if the issue persists.",
        )
