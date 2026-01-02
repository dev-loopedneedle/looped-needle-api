"""Inference engine utility functions."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.audit_engine.constants import AuditInstanceStatus, AuditItemStatus
from src.audit_engine.exceptions import InferenceValidationError


async def check_brand_references(session: AsyncSession, brand_id: str) -> tuple[bool, str | None]:
    """
    Check if a brand is referenced by audit instances.

    Args:
        session: Database session
        brand_id: Brand ID to check

    Returns:
        Tuple of (is_referenced, reference_type)
    """
    from src.audit_engine.models import AuditInstance

    result = await session.execute(
        select(AuditInstance).where(
            AuditInstance.brand_id == brand_id, AuditInstance.deleted_at.is_(None)
        )
    )
    if result.scalar_one_or_none():
        return True, "audit_instances"
    return False, None


async def check_criterion_references(
    session: AsyncSession, criterion_id: str
) -> tuple[bool, str | None]:
    """
    Check if a criterion is referenced by audit items.

    Args:
        session: Database session
        criterion_id: Criterion ID to check

    Returns:
        Tuple of (is_referenced, reference_type)
    """
    from src.audit_engine.models import AuditItem

    result = await session.execute(
        select(AuditItem).where(
            AuditItem.criteria_id == criterion_id, AuditItem.deleted_at.is_(None)
        )
    )
    if result.scalar_one_or_none():
        return True, "audit_items"
    return False, None


async def check_rule_references(session: AsyncSession, rule_id: str) -> tuple[bool, str | None]:
    """
    Check if a rule is referenced by audit items.

    Args:
        session: Database session
        rule_id: Rule ID to check

    Returns:
        Tuple of (is_referenced, reference_type)
    """
    from src.audit_engine.models import AuditItem

    result = await session.execute(
        select(AuditItem).where(
            AuditItem.triggered_by_rule_id == rule_id, AuditItem.deleted_at.is_(None)
        )
    )
    if result.scalar_one_or_none():
        return True, "audit_items"
    return False, None


def can_transition_audit_instance(
    from_status: AuditInstanceStatus, to_status: AuditInstanceStatus
) -> bool:
    """
    Check if audit instance status transition is allowed.

    Forward-only transitions:
    - IN_PROGRESS -> REVIEWING or CERTIFIED
    - REVIEWING -> CERTIFIED
    - Cannot revert CERTIFIED or REVIEWING

    Args:
        from_status: Current status
        to_status: Target status

    Returns:
        True if transition is allowed, False otherwise
    """
    if from_status == AuditInstanceStatus.IN_PROGRESS:
        return to_status in (
            AuditInstanceStatus.REVIEWING,
            AuditInstanceStatus.CERTIFIED,
        )
    if from_status == AuditInstanceStatus.REVIEWING:
        return to_status == AuditInstanceStatus.CERTIFIED
    # CERTIFIED is terminal, cannot transition from it
    return False


def can_transition_audit_item(from_status: AuditItemStatus, to_status: AuditItemStatus) -> bool:
    """
    Check if audit item status transition is allowed.

    Forward-only transitions:
    - MISSING_EVIDENCE -> EVIDENCE_PROVIDED -> UNDER_REVIEW -> ACCEPTED/REJECTED
    - Cannot revert ACCEPTED or REJECTED

    Args:
        from_status: Current status
        to_status: Target status

    Returns:
        True if transition is allowed, False otherwise
    """
    transitions = {
        AuditItemStatus.MISSING_EVIDENCE: [
            AuditItemStatus.EVIDENCE_PROVIDED,
        ],
        AuditItemStatus.EVIDENCE_PROVIDED: [
            AuditItemStatus.UNDER_REVIEW,
        ],
        AuditItemStatus.UNDER_REVIEW: [
            AuditItemStatus.ACCEPTED,
            AuditItemStatus.REJECTED,
        ],
    }
    # ACCEPTED and REJECTED are terminal
    if from_status in (AuditItemStatus.ACCEPTED, AuditItemStatus.REJECTED):
        return False
    return to_status in transitions.get(from_status, [])


def validate_audit_instance_status_transition(
    current_status: AuditInstanceStatus, new_status: AuditInstanceStatus
) -> None:
    """
    Validate audit instance status transition.

    Args:
        current_status: Current status
        new_status: New status

    Raises:
        InferenceValidationError: If transition is invalid
    """
    if not can_transition_audit_instance(current_status, new_status):
        raise InferenceValidationError(
            f"Invalid status transition from {current_status} to {new_status}. "
            f"Forward-only transitions allowed: IN_PROGRESS -> REVIEWING/CERTIFIED, REVIEWING -> CERTIFIED"
        )


def validate_audit_item_status_transition(
    current_status: AuditItemStatus, new_status: AuditItemStatus
) -> None:
    """
    Validate audit item status transition.

    Args:
        current_status: Current status
        new_status: New status

    Raises:
        InferenceValidationError: If transition is invalid
    """
    if not can_transition_audit_item(current_status, new_status):
        raise InferenceValidationError(
            f"Invalid status transition from {current_status} to {new_status}. "
            f"Forward-only transitions allowed: MISSING_EVIDENCE -> EVIDENCE_PROVIDED -> UNDER_REVIEW -> ACCEPTED/REJECTED"
        )
