"""Constants and enums for the rules domain."""

from enum import StrEnum


class RuleState(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DISABLED = "DISABLED"


class EvidenceClaimCategory(StrEnum):
    ENVIRONMENT = "ENVIRONMENT"
    SUSTAINABILITY = "SUSTAINABILITY"
    SOCIAL = "SOCIAL"
    GOVERNANCE = "GOVERNANCE"
    TRACEABILITY = "TRACEABILITY"
    OTHER = "OTHER"


class EvidenceClaimType(StrEnum):
    CERTIFICATE = "CERTIFICATE"
    INVOICE = "INVOICE"
    QUESTIONNAIRE = "QUESTIONNAIRE"
    REPORT = "REPORT"
    OTHER = "OTHER"
