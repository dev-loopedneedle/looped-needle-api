"""Inference engine domain exceptions."""

from src.exceptions import NotFoundError, ValidationError


class BrandNotFoundError(NotFoundError):
    """Brand not found exception."""

    def __init__(self, brand_id: str):
        super().__init__(f"Brand with id {brand_id} not found")


class ProductNotFoundError(NotFoundError):
    """Product not found exception."""

    def __init__(self, product_id: str):
        super().__init__(f"Product with id {product_id} not found")


class SupplyChainNodeNotFoundError(NotFoundError):
    """Supply chain node not found exception."""

    def __init__(self, node_id: str):
        super().__init__(f"Supply chain node with id {node_id} not found")


class CriterionNotFoundError(NotFoundError):
    """Sustainability criterion not found exception."""

    def __init__(self, criterion_id: str):
        super().__init__(f"Sustainability criterion with id {criterion_id} not found")


class RuleNotFoundError(NotFoundError):
    """Criteria rule not found exception."""

    def __init__(self, rule_id: str):
        super().__init__(f"Criteria rule with id {rule_id} not found")


class QuestionnaireNotFoundError(NotFoundError):
    """Questionnaire definition not found exception."""

    def __init__(self, questionnaire_id: str):
        super().__init__(f"Questionnaire definition with id {questionnaire_id} not found")


class AuditInstanceNotFoundError(NotFoundError):
    """Audit instance not found exception."""

    def __init__(self, audit_instance_id: str):
        super().__init__(f"Audit instance with id {audit_instance_id} not found")


class AuditItemNotFoundError(NotFoundError):
    """Audit item not found exception."""

    def __init__(self, audit_item_id: str):
        super().__init__(f"Audit item with id {audit_item_id} not found")


class EvidenceFileNotFoundError(NotFoundError):
    """Evidence file not found exception."""

    def __init__(self, evidence_file_id: str):
        super().__init__(f"Evidence file with id {evidence_file_id} not found")


class InvalidStatusTransitionError(ValidationError):
    """Invalid status transition exception."""

    def __init__(self, from_status: str, to_status: str, entity_type: str = "entity"):
        super().__init__(
            f"Invalid {entity_type} status transition from {from_status} to {to_status}"
        )


class ReferentialIntegrityError(ValidationError):
    """Referential integrity violation exception."""

    def __init__(self, entity_type: str, entity_id: str, referenced_by: str):
        super().__init__(
            f"Cannot delete {entity_type} with id {entity_id} because it is referenced by {referenced_by}"
        )


class InferenceValidationError(ValidationError):
    """Audit engine validation error exception."""

    def __init__(self, message: str = "Invalid audit engine data"):
        super().__init__(message)


class InferenceConflictError(ValidationError):
    """Audit engine conflict error exception."""

    def __init__(self, message: str = "Audit engine conflict error"):
        super().__init__(message)
