"""Inference engine domain constants."""

from enum import Enum


class CompanySize(str, Enum):
    """Company size enumeration."""

    MICRO = "Micro"
    SME = "SME"
    LARGE = "Large"


class SustainabilityDomain(str, Enum):
    """Sustainability criterion domain enumeration."""

    SOCIAL = "Social"
    ENVIRONMENTAL = "Environmental"
    GOVERNANCE = "Governance"


class AuditInstanceStatus(str, Enum):
    """Audit instance status enumeration."""

    IN_PROGRESS = "IN_PROGRESS"
    REVIEWING = "REVIEWING"
    CERTIFIED = "CERTIFIED"


class AuditItemStatus(str, Enum):
    """Audit item status enumeration."""

    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    EVIDENCE_PROVIDED = "EVIDENCE_PROVIDED"
    UNDER_REVIEW = "UNDER_REVIEW"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class EvidenceLinkStatus(str, Enum):
    """Evidence link status enumeration."""

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


# Pagination defaults
DEFAULT_PAGE_LIMIT = 20
MAX_PAGE_LIMIT = 50
