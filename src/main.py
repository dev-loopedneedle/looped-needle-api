"""FastAPI application entry point."""

import json
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.audits.exceptions import AuditNotFoundError, AuditValidationError
from src.audits.router import router as audits_router
from src.config import settings
from src.database import engine
from src.exceptions import BaseAPIException
from src.health.router import router as health_router
from src.inference.exceptions import (
    AuditInstanceNotFoundError,
    AuditItemNotFoundError,
    BrandNotFoundError,
    CriterionNotFoundError,
    InferenceConflictError,
    InferenceValidationError,
    ProductNotFoundError,
    QuestionnaireNotFoundError,
    ReferentialIntegrityError,
    RuleNotFoundError,
    SupplyChainNodeNotFoundError,
)
from src.inference.router import router as inference_router


# Configure structured JSON logging
class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Add request ID if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


# Request ID middleware
class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to all requests."""

    async def dispatch(self, request: Request, call_next):
        """Add request ID to request and logs."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Add request ID to logger context
        logger = logging.getLogger()
        old_factory = logger.makeRecord

        def make_record_with_request_id(
            name, level, fn, lno, msg, args, exc_info, func=None, extra=None, sinfo=None
        ):
            rv = old_factory(name, level, fn, lno, msg, args, exc_info, func, extra, sinfo)
            rv.request_id = request_id
            return rv

        logger.makeRecord = make_record_with_request_id

        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            logger.makeRecord = old_factory


# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(message)s"
    if settings.log_format == "json"
    else "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
if settings.log_format == "json":
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logging.getLogger().handlers = [handler]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger = logging.getLogger(__name__)
    logger.info("Starting application")
    yield
    # Shutdown
    logger.info("Shutting down application")
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    description="FastAPI backend API for Looped Needle project",
    version=settings.version,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware
app.add_middleware(RequestIDMiddleware)


# Global exception handlers
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


@app.exception_handler(AuditNotFoundError)
async def audit_not_found_handler(request: Request, exc: AuditNotFoundError):
    """Handle audit not found errors."""
    request_id = getattr(request.state, "request_id", None)
    content = {
        "error": "AuditNotFound",
        "message": exc.message,
        "status_code": status.HTTP_404_NOT_FOUND,
        "detail": "The requested audit record does not exist or has been deleted.",
    }
    if request_id:
        content["request_id"] = request_id
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=content,
    )


@app.exception_handler(AuditValidationError)
async def audit_validation_handler(request: Request, exc: AuditValidationError):
    """Handle audit validation errors."""
    request_id = getattr(request.state, "request_id", None)
    content = {
        "error": "AuditValidationError",
        "message": exc.message,
        "status_code": status.HTTP_400_BAD_REQUEST,
        "detail": "The provided audit record data is invalid. Please check the request payload and try again.",
    }
    if request_id:
        content["request_id"] = request_id
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
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


# Inference domain exception handlers
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


@app.exception_handler(ProductNotFoundError)
async def product_not_found_handler(request: Request, exc: ProductNotFoundError):
    """Handle product not found errors."""
    request_id = getattr(request.state, "request_id", None)
    content = {
        "error": "ProductNotFound",
        "message": exc.message,
        "status_code": status.HTTP_404_NOT_FOUND,
    }
    if request_id:
        content["request_id"] = request_id
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=content)


@app.exception_handler(SupplyChainNodeNotFoundError)
async def supply_chain_node_not_found_handler(request: Request, exc: SupplyChainNodeNotFoundError):
    """Handle supply chain node not found errors."""
    request_id = getattr(request.state, "request_id", None)
    content = {
        "error": "SupplyChainNodeNotFound",
        "message": exc.message,
        "status_code": status.HTTP_404_NOT_FOUND,
    }
    if request_id:
        content["request_id"] = request_id
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=content)


@app.exception_handler(CriterionNotFoundError)
async def criterion_not_found_handler(request: Request, exc: CriterionNotFoundError):
    """Handle criterion not found errors."""
    request_id = getattr(request.state, "request_id", None)
    content = {
        "error": "CriterionNotFound",
        "message": exc.message,
        "status_code": status.HTTP_404_NOT_FOUND,
    }
    if request_id:
        content["request_id"] = request_id
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=content)


@app.exception_handler(RuleNotFoundError)
async def rule_not_found_handler(request: Request, exc: RuleNotFoundError):
    """Handle rule not found errors."""
    request_id = getattr(request.state, "request_id", None)
    content = {
        "error": "RuleNotFound",
        "message": exc.message,
        "status_code": status.HTTP_404_NOT_FOUND,
    }
    if request_id:
        content["request_id"] = request_id
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=content)


@app.exception_handler(QuestionnaireNotFoundError)
async def questionnaire_not_found_handler(request: Request, exc: QuestionnaireNotFoundError):
    """Handle questionnaire not found errors."""
    request_id = getattr(request.state, "request_id", None)
    content = {
        "error": "QuestionnaireNotFound",
        "message": exc.message,
        "status_code": status.HTTP_404_NOT_FOUND,
    }
    if request_id:
        content["request_id"] = request_id
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=content)


@app.exception_handler(AuditInstanceNotFoundError)
async def audit_instance_not_found_handler(request: Request, exc: AuditInstanceNotFoundError):
    """Handle audit instance not found errors."""
    request_id = getattr(request.state, "request_id", None)
    content = {
        "error": "AuditInstanceNotFound",
        "message": exc.message,
        "status_code": status.HTTP_404_NOT_FOUND,
    }
    if request_id:
        content["request_id"] = request_id
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=content)


@app.exception_handler(AuditItemNotFoundError)
async def audit_item_not_found_handler(request: Request, exc: AuditItemNotFoundError):
    """Handle audit item not found errors."""
    request_id = getattr(request.state, "request_id", None)
    content = {
        "error": "AuditItemNotFound",
        "message": exc.message,
        "status_code": status.HTTP_404_NOT_FOUND,
    }
    if request_id:
        content["request_id"] = request_id
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=content)


@app.exception_handler(InferenceValidationError)
async def inference_validation_handler(request: Request, exc: InferenceValidationError):
    """Handle inference validation errors."""
    request_id = getattr(request.state, "request_id", None)
    content = {
        "error": "InferenceValidationError",
        "message": exc.message,
        "status_code": status.HTTP_400_BAD_REQUEST,
    }
    if request_id:
        content["request_id"] = request_id
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content=content)


@app.exception_handler(InferenceConflictError)
async def inference_conflict_handler(request: Request, exc: InferenceConflictError):
    """Handle inference conflict errors."""
    request_id = getattr(request.state, "request_id", None)
    content = {
        "error": "InferenceConflictError",
        "message": exc.message,
        "status_code": status.HTTP_409_CONFLICT,
    }
    if request_id:
        content["request_id"] = request_id
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=content)


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


# Register routers
app.include_router(health_router)
app.include_router(audits_router)
app.include_router(inference_router)


# Root endpoint
@app.get(
    "/",
    summary="Root endpoint",
    description="API information and available endpoints",
)
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.project_name,
        "version": settings.version,
        "docs": "/docs",
        "health": "/health",
        "api_prefix": settings.api_v1_prefix,
    }
