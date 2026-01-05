"""Brands domain exceptions."""

from src.exceptions import NotFoundError, ValidationError


class BrandNotFoundError(NotFoundError):
    """Brand not found exception."""

    def __init__(self, brand_id: str):
        super().__init__(f"Brand with id {brand_id} not found")


class ReferentialIntegrityError(ValidationError):
    """Referential integrity violation exception."""

    def __init__(self, entity_type: str, entity_id: str, referenced_by: str):
        super().__init__(
            f"Cannot delete {entity_type} with id {entity_id} because it is referenced by {referenced_by}"
        )


