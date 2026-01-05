"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.audits.router import router as audits_router
from src.auth.router import router as auth_router
from src.brands.router import router as brands_router
from src.config import settings
from src.core.exception_handlers import register_exception_handlers
from src.core.logging import setup_logging
from src.core.middleware import RequestIDMiddleware
from src.database import engine
from src.health.router import router as health_router
from src.waitlist.router import router as waitlist_router

# Setup logging first
setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
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
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request ID middleware
app.add_middleware(RequestIDMiddleware)

# Register exception handlers
register_exception_handlers(app)

# Register routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(brands_router)
app.include_router(audits_router)
app.include_router(waitlist_router)


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
