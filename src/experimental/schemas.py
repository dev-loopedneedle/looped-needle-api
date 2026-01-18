"""Experimental endpoints Pydantic schemas."""

from enum import StrEnum

from pydantic import BaseModel, Field

from src.rules.constants import EvidenceClaimCategory


class GeminiDocumentType(StrEnum):
    """Supported document types for Gemini evaluation."""

    CERTIFICATION = "CERTIFICATION"
    INVOICE = "INVOICE"
    LICENSE = "LICENSE"


class OverallVerdict(StrEnum):
    """Overall assessment verdict for the document."""

    PASS = "pass"
    FAIL = "fail"
    NEEDS_REVIEW = "needs_review"


class RiskLevel(StrEnum):
    """Overall risk level assessment."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ClaimVerdict(StrEnum):
    """Verdict for individual claim evaluation."""

    SUPPORTED = "supported"
    NOT_SUPPORTED = "not_supported"
    PARTIAL = "partial"
    INCONCLUSIVE = "inconclusive"


class ClaimResult(StrEnum):
    """Result for individual claim evaluation."""

    PASS = "PASS"
    FAIL = "FAIL"


class DocumentOrientation(StrEnum):
    """Document orientation classification."""

    PORTRAIT = "portrait"
    LANDSCAPE = "landscape"
    MIXED = "mixed"
    UNKNOWN = "unknown"


class DocumentQuality(StrEnum):
    """Overall document quality assessment."""

    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNKNOWN = "unknown"


class GeminiClaimInput(BaseModel):
    """Claim input for Gemini evaluation.

    The 'name' field can be one of:
    - Document type (e.g., "CERTIFICATION", "INVOICE", "LICENSE")
    - Category type (e.g., "ENVIRONMENT", "SUSTAINABILITY", "SOCIAL", "GOVERNANCE", "TRACEABILITY", "OTHER")
    - Issue date (e.g., "issue date")
    """

    id: int
    name: str  # Can be document type | category type | issue date
    value: str

    model_config = {"populate_by_name": True}


class DocumentClassification(BaseModel):
    """Document classification results."""

    detected_type: "DetectedDocumentType" = Field(
        ..., alias="detectedType", serialization_alias="detectedType"
    )
    type_confidence: int = Field(
        ...,
        ge=0,
        le=100,
        alias="typeConfidence",
        serialization_alias="typeConfidence",
    )
    detected_language: str | None = Field(
        None, alias="detectedLanguage", serialization_alias="detectedLanguage"
    )
    detected_country: str | None = Field(
        None, alias="detectedCountry", serialization_alias="detectedCountry"
    )
    detected_issuer: str | None = Field(
        None, alias="detectedIssuer", serialization_alias="detectedIssuer"
    )
    document_category: EvidenceClaimCategory | None = Field(
        None, alias="documentCategory", serialization_alias="documentCategory"
    )

    model_config = {"populate_by_name": True}


class DetectedDocumentType(StrEnum):
    """Detected document type from classification."""

    CERTIFICATION = "CERTIFICATION"
    INVOICE = "INVOICE"
    LICENSE = "LICENSE"
    UNKNOWN = "UNKNOWN"


class ClaimEvaluation(BaseModel):
    """Evaluation result for a single claim."""

    claim_id: str = Field(..., alias="claimId", serialization_alias="claimId")
    claim_name: str = Field(..., alias="claimName", serialization_alias="claimName")
    result: ClaimResult = Field(..., description="PASS or FAIL for the claim")
    confidence: int = Field(..., ge=0, le=100)
    evidence: list[str] = Field(default_factory=list)
    reasoning: str
    issues: list[str] = Field(default_factory=list)

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Convert claim_id to string if it's an integer (from JSON number)."""
        if isinstance(obj, dict) and "claimId" in obj:
            if isinstance(obj["claimId"], int):
                obj["claimId"] = str(obj["claimId"])
        return super().model_validate(obj, **kwargs)

    model_config = {"populate_by_name": True}


class AuthenticityAnalysis(BaseModel):
    """Authenticity analysis results."""

    authenticity_score: int = Field(
        ...,
        ge=0,
        le=100,
        alias="authenticityScore",
        serialization_alias="authenticityScore",
    )
    security_elements: list[str] = Field(
        default_factory=list,
        alias="securityElements",
        serialization_alias="securityElements",
    )

    model_config = {"populate_by_name": True}


class ExtractedContent(BaseModel):
    """Key content extracted from the document."""

    document_title: str | None = Field(
        None, alias="documentTitle", serialization_alias="documentTitle"
    )
    document_number: str | None = Field(
        None, alias="documentNumber", serialization_alias="documentNumber"
    )
    issue_date: str | None = Field(None, alias="issueDate", serialization_alias="issueDate")
    expiration_date: str | None = Field(
        None, alias="expirationDate", serialization_alias="expirationDate"
    )
    issuing_organization: str | None = Field(
        None, alias="issuingOrganization", serialization_alias="issuingOrganization"
    )
    certified_products: list[str] = Field(
        default_factory=list,
        alias="certifiedProducts",
        serialization_alias="certifiedProducts",
    )
    materials: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class VisualAnalysis(BaseModel):
    """Visual analysis of the document."""

    page_count: int = Field(..., alias="pageCount", serialization_alias="pageCount")
    orientation: DocumentOrientation
    overall_quality: DocumentQuality = Field(
        ..., alias="overallQuality", serialization_alias="overallQuality"
    )

    model_config = {"populate_by_name": True}


class IssuerAnalysis(BaseModel):
    """Issuer analysis for certification context."""

    issuer_name: str | None = Field(
        None,
        alias="issuerName",
        serialization_alias="issuerName",
        description="Name of the issuing organization",
    )
    issuer_type: str | None = Field(
        None,
        alias="issuerType",
        serialization_alias="issuerType",
        description="Type of issuer (e.g., accreditation body, certification body, regulatory authority)",
    )
    issuer_country: str | None = Field(
        None,
        alias="issuerCountry",
        serialization_alias="issuerCountry",
        description="Country/jurisdiction of the issuer",
    )
    issuer_accreditation_number: str | None = Field(
        None,
        alias="issuerAccreditationNumber",
        serialization_alias="issuerAccreditationNumber",
        description="Accreditation or registration number of the issuer",
    )
    issuer_scope: str | None = Field(
        None,
        alias="issuerScope",
        serialization_alias="issuerScope",
        description="Scope of authority or certification programs offered by the issuer",
    )
    issuer_contact: str | None = Field(
        None,
        alias="issuerContact",
        serialization_alias="issuerContact",
        description="Contact information for the issuer",
    )
    issuer_validity: str | None = Field(
        None,
        alias="issuerValidity",
        serialization_alias="issuerValidity",
        description="Validity period or expiration of issuer's accreditation/authority",
    )
    issuer_verification_status: str | None = Field(
        None,
        alias="issuerVerificationStatus",
        serialization_alias="issuerVerificationStatus",
        description="Status of issuer verification (e.g., verified, unverified, expired)",
    )
    issues: list[str] = Field(
        default_factory=list, description="Any issues or concerns identified about the issuer"
    )

    model_config = {"populate_by_name": True}


class JurisdictionAnalysis(BaseModel):
    """Jurisdiction analysis of the document."""

    jurisdiction: str | None = None
    confidence: int | None = Field(None, ge=0, le=100)
    issues: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    """Recommendation returned from Gemini evaluation."""

    title: str
    detail: str


class GeminiEvaluationRequest(BaseModel):
    """Request for Gemini document evaluation."""

    name: str = Field(..., description="Document name or label")
    claims: list[GeminiClaimInput] = Field(
        ..., description="Claims to evaluate the document against"
    )

    model_config = {"populate_by_name": True}


class GeminiEvaluationResponse(BaseModel):
    """Response from Gemini document evaluation."""

    overall_verdict: OverallVerdict = Field(
        ..., alias="overallVerdict", serialization_alias="overallVerdict"
    )
    overall_verdict_reason: str = Field(
        ...,
        alias="overallVerdictReason",
        serialization_alias="overallVerdictReason",
        description="Detailed reasoning for the overall verdict based on claim evaluations, authenticity, and visual analysis",
    )
    confidence_score: int = Field(
        ...,
        ge=0,
        le=100,
        alias="confidenceScore",
        serialization_alias="confidenceScore",
        description="Confidence score (0-100) for the overall verdict",
    )
    risk_level: RiskLevel = Field(..., alias="riskLevel", serialization_alias="riskLevel")
    classification: DocumentClassification
    claim_evaluations: list[ClaimEvaluation] = Field(
        ..., alias="claimEvaluations", serialization_alias="claimEvaluations"
    )
    authenticity_analysis: AuthenticityAnalysis = Field(
        ..., alias="authenticityAnalysis", serialization_alias="authenticityAnalysis"
    )
    extracted_content: ExtractedContent = Field(
        ..., alias="extractedContent", serialization_alias="extractedContent"
    )
    visual_analysis: VisualAnalysis = Field(
        ..., alias="visualAnalysis", serialization_alias="visualAnalysis"
    )
    issuer_analysis: IssuerAnalysis = Field(
        ..., alias="issuerAnalysis", serialization_alias="issuerAnalysis"
    )
    jurisdiction_analysis: JurisdictionAnalysis = Field(
        ..., alias="jurisdictionAnalysis", serialization_alias="jurisdictionAnalysis"
    )
    recommendations: list[Recommendation]

    model_config = {"populate_by_name": True}

