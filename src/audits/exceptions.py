"""Audits domain exceptions."""

from src.exceptions import NotFoundError, ValidationError


class AuditNotFoundError(NotFoundError):
    """Audit record not found exception."""

    def __init__(self, audit_id: str):
        super().__init__(f"Audit record with id {audit_id} not found")


class AuditValidationError(ValidationError):
    """Audit validation error exception."""

    def __init__(self, message: str = "Invalid audit record data"):
        super().__init__(message)
