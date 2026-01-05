"""Audits domain exceptions."""

from src.exceptions import BaseAPIException


class AuditNotFoundError(BaseAPIException):
    """Raised when an audit is not found."""

    def __init__(self, audit_id: str):
        super().__init__(
            message=f"Audit with ID {audit_id} not found",
            status_code=404,
        )


class BrandNotFoundError(BaseAPIException):
    """Raised when a brand is not found."""

    def __init__(self, brand_id: str):
        super().__init__(
            message=f"Brand with ID {brand_id} not found",
            status_code=404,
        )


class AuditPublishedError(BaseAPIException):
    """Raised when trying to update a published audit."""

    def __init__(self, audit_id: str):
        super().__init__(
            message=f"Audit with ID {audit_id} is published and cannot be updated",
            status_code=400,
        )
