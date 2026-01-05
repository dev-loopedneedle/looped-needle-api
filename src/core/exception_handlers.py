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
from src.exceptions import BaseAPIException


def register_exception_handlers(app) -> None:
    """Register all exception handlers with the FastAPI app."""

    @app.exception_handler(BaseAPIException)
    async def base_api_exception_handler(request: Request, exc: BaseAPIException):
        """Handle base API exceptions."""
        request_id = getattr(request.state, "request_id", None)
        content = {
            "error": exc.__class__.__name__,
            "message": exc.message,
            "status_code": exc.status_code,
        }
        if request_id:
            content["request_id"] = request_id
        return JSONResponse(
            status_code=exc.status_code,
            content=content,
        )

    @app.exception_handler(ReferentialIntegrityError)
    async def referential_integrity_handler(request: Request, exc: ReferentialIntegrityError):
        """Handle referential integrity errors."""
        request_id = getattr(request.state, "request_id", None)
        content = {
            "error": "ReferentialIntegrityError",
            "message": exc.message,
            "status_code": status.HTTP_409_CONFLICT,
            "detail": "Cannot delete this entity because it is referenced by other entities.",
        }
        if request_id:
            content["request_id"] = request_id
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=content,
        )

    @app.exception_handler(BrandNotFoundError)
    async def brand_not_found_handler(request: Request, exc: BrandNotFoundError):
        """Handle brand not found errors."""
        request_id = getattr(request.state, "request_id", None)
        content = {
            "error": "BrandNotFound",
            "message": exc.message,
            "status_code": status.HTTP_404_NOT_FOUND,
        }
        if request_id:
            content["request_id"] = request_id
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=content)

    @app.exception_handler(AuditsAuditNotFoundError)
    async def audits_audit_not_found_handler(request: Request, exc: AuditsAuditNotFoundError):
        """Handle audits domain audit not found errors."""
        request_id = getattr(request.state, "request_id", None)
        content = {
            "error": "AuditNotFound",
            "message": exc.message,
            "status_code": status.HTTP_404_NOT_FOUND,
        }
        if request_id:
            content["request_id"] = request_id
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=content)

    @app.exception_handler(AuditPublishedError)
    async def audit_published_handler(request: Request, exc: AuditPublishedError):
        """Handle audit published errors."""
        request_id = getattr(request.state, "request_id", None)
        content = {
            "error": "AuditPublished",
            "message": exc.message,
            "status_code": status.HTTP_400_BAD_REQUEST,
        }
        if request_id:
            content["request_id"] = request_id
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=content)

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(request: Request, exc: AuthenticationError):
        """Handle authentication errors."""
        request_id = getattr(request.state, "request_id", None)
        content = {
            "error": "AuthenticationError",
            "message": exc.message,
            "status_code": status.HTTP_401_UNAUTHORIZED,
        }
        if request_id:
            content["request_id"] = request_id
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=content)

    @app.exception_handler(ServiceUnavailableError)
    async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError):
        """Handle service unavailable errors."""
        request_id = getattr(request.state, "request_id", None)
        content = {
            "error": "ServiceUnavailable",
            "message": exc.message,
            "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
        }
        if request_id:
            content["request_id"] = request_id
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=content)

    @app.exception_handler(AccessDeniedError)
    async def access_denied_handler(request: Request, exc: AccessDeniedError):
        """Handle access denied errors."""
        request_id = getattr(request.state, "request_id", None)
        content = {
            "error": "AccessDenied",
            "message": exc.message,
            "status_code": status.HTTP_403_FORBIDDEN,
        }
        if request_id:
            content["request_id"] = request_id
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content=content)

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception):
        """Handle 404 errors."""
        request_id = getattr(request.state, "request_id", None)
        content = {
            "error": "NotFound",
            "message": f"Endpoint {request.url.path} not found",
            "status_code": status.HTTP_404_NOT_FOUND,
            "detail": "The requested endpoint does not exist. Please check the URL and API documentation at /docs.",
        }
        if request_id:
            content["request_id"] = request_id
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=content,
        )

    @app.exception_handler(500)
    async def internal_server_error_handler(request: Request, exc: Exception):
        """Handle 500 errors."""
        logger = logging.getLogger(__name__)
        request_id = getattr(request.state, "request_id", None)
        logger.error(f"Internal server error: {exc}", exc_info=True, extra={"request_id": request_id})
        content = {
            "error": "InternalServerError",
            "message": "An internal server error occurred",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "detail": "An unexpected error occurred while processing your request. Please try again later or contact support if the issue persists.",
        }
        if request_id:
            content["request_id"] = request_id
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=content,
        )

