"""Audit engine root router - composes all bounded context routers."""

from fastapi import APIRouter

from src.audit_engine.audit_runs.router import router as audit_runs_router
from src.audit_engine.brands.router import router as brands_router
from src.audit_engine.questionnaires.router import router as questionnaires_router
from src.audit_engine.standards.router import router as standards_router

# Create root router (no prefix, sub-routers already have /api/v1)
router = APIRouter(tags=["audit-engine"])

# Include all bounded context routers
router.include_router(brands_router)
router.include_router(standards_router)
router.include_router(questionnaires_router)
router.include_router(audit_runs_router)
