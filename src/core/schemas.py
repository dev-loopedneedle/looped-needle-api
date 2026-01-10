"""Core shared Pydantic schemas."""

from uuid import UUID

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standardized error response schema for all API errors."""

    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    status_code: int = Field(
        ..., alias="statusCode", serialization_alias="statusCode", description="HTTP status code"
    )
    request_id: UUID | str | None = Field(
        None,
        alias="requestId",
        serialization_alias="requestId",
        description="Request identifier for tracing",
    )
    detail: str | None = Field(None, description="Additional context about the error")

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "error": "WaitlistEntryExists",
                "message": "Email example@email.com is already on the waitlist",
                "statusCode": 409,
                "requestId": "c95988cc-b8b7-4047-8842-1c1d7c16cefb",
            }
        },
    }
