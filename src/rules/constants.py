"""Constants and enums for the rules domain."""

from enum import StrEnum


class RuleState(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    DISABLED = "DISABLED"


class EvidenceClaimCategory(StrEnum):
    ENVIRONMENTAL = "ENVIRONMENTAL"
    SOCIAL = "SOCIAL"
    CIRCULARITY = "CIRCULARITY"
    TRANSPARENCY = "TRANSPARENCY"


class EvidenceClaimType(StrEnum):
    CERTIFICATE = "CERTIFICATE"
    DOCUMENT = "DOCUMENT"
    INVOICE = "INVOICE"
    RECEIPT = "RECEIPT"
    QUESTIONNAIRE = "QUESTIONNAIRE"
    REPORT = "REPORT"
