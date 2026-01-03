"""Schemas for questionnaires (definitions and listing)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from src.audit_engine.constants import MAX_PAGE_LIMIT


class QuestionnaireDefinitionCreate(BaseModel):
    """Schema for creating a questionnaire definition."""

    name: str = Field(..., description="Questionnaire name")
    form_schema: dict[str, Any] = Field(..., description="Form structure (JSON schema)")
    is_active: bool = Field(default=True, description="Active status")

    @field_validator("form_schema")
    @classmethod
    def validate_form_schema(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate form schema structure."""
        if not isinstance(v, dict):
            raise ValueError("form_schema must be a dictionary")
        if "questions" not in v and not isinstance(v, list):
            if not isinstance(v, list):
                raise ValueError(
                    "form_schema must be a dictionary with 'questions' key or a list of questions"
                )
        return v


class QuestionnaireDefinitionResponse(BaseModel):
    """Schema for questionnaire definition response."""

    id: UUID
    name: str
    form_schema: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class QuestionnaireListQuery(BaseModel):
    """Schema for questionnaire list query parameters."""

    is_active: bool | None = Field(None, description="Filter by active status")
    limit: int = Field(
        default=20, ge=1, le=MAX_PAGE_LIMIT, description="Maximum number of records to return"
    )
    offset: int = Field(default=0, ge=0, description="Number of records to skip")


class QuestionnaireListResponse(BaseModel):
    """Schema for paginated questionnaire list response."""

    items: list[QuestionnaireDefinitionResponse]
    total: int
    limit: int
    offset: int


__all__ = [
    "QuestionnaireDefinitionCreate",
    "QuestionnaireDefinitionResponse",
    "QuestionnaireListQuery",
    "QuestionnaireListResponse",
]
