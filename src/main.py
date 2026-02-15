"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.admin.router import router as admin_dashboard_router
from src.audit_workflows.router import router as audit_workflows_router
from src.audits.router import router as audits_router
from src.auth.router import router as auth_router
from src.brands.router import router as brands_router
from src.config import settings
from src.core.exception_handlers import register_exception_handlers
from src.core.logging import setup_logging
from src.core.middleware import RequestIDMiddleware
from src.database import engine
from src.evidence_submissions.admin_router import router as evidence_admin_router
from src.evidence_submissions.router import router as evidence_submissions_router
from src.experimental.router import router as experimental_router
from src.health.router import router as health_router
from src.rules.admin_router import router as admin_router
from src.rules.router import router as rules_router
from src.waitlist.router import router as waitlist_router

load_dotenv()

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

app.add_middleware(RequestIDMiddleware)

register_exception_handlers(app)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(brands_router)
app.include_router(audits_router)
app.include_router(audit_workflows_router)
app.include_router(evidence_submissions_router)
app.include_router(experimental_router)
app.include_router(admin_router)
app.include_router(admin_dashboard_router)
app.include_router(evidence_admin_router)
app.include_router(rules_router)
app.include_router(waitlist_router)


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
