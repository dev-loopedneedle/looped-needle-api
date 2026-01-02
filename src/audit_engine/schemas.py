"""Aggregated Pydantic schemas for the audit engine domain.

This module re-exports schemas from bounded-context packages to preserve
compatibility for existing imports while enabling clearer ownership per
domain (brands, standards, questionnaires, audit runs).
"""

from src.audit_engine.audit_runs.schemas import (
    AuditInstanceCreate,
    AuditInstanceListQuery,
    AuditInstanceListResponse,
    AuditInstanceResponse,
    AuditInstanceUpdate,
    AuditItemGenerationResponse,
    AuditItemListResponse,
    AuditItemResponse,
    AuditItemUpdate,
)
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
from src.audit_engine.questionnaires.schemas import (
    QuestionnaireDefinitionCreate,
    QuestionnaireDefinitionResponse,
    QuestionnaireListQuery,
    QuestionnaireListResponse,
)
from src.audit_engine.standards.schemas import (
    CriterionCreate,
    CriterionListQuery,
    CriterionListResponse,
    CriterionResponse,
    RuleCreate,
    RuleListResponse,
    RuleResponse,
    RuleUpdate,
)

__all__ = [
    # brands
    "BrandCreate",
    "BrandUpdate",
    "BrandResponse",
    "BrandListQuery",
    "BrandListResponse",
    "ProductCreate",
    "ProductResponse",
    "SupplyChainNodeCreate",
    "SupplyChainNodeResponse",
    # standards
    "CriterionCreate",
    "CriterionResponse",
    "CriterionListQuery",
    "CriterionListResponse",
    "RuleCreate",
    "RuleUpdate",
    "RuleResponse",
    "RuleListResponse",
    # questionnaires
    "QuestionnaireDefinitionCreate",
    "QuestionnaireDefinitionResponse",
    "QuestionnaireListQuery",
    "QuestionnaireListResponse",
    # audit runs
    "AuditInstanceCreate",
    "AuditInstanceUpdate",
    "AuditInstanceResponse",
    "AuditInstanceListQuery",
    "AuditInstanceListResponse",
    "AuditItemResponse",
    "AuditItemUpdate",
    "AuditItemListResponse",
    "AuditItemGenerationResponse",
]
