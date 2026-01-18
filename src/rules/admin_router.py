"""Admin utility endpoints for rules domain."""

from fastapi import APIRouter, Depends

from src.auth.dependencies import UserContext
from src.rules.constants import EvidenceClaimCategory, EvidenceClaimType
from src.rules.dependencies import get_admin

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get(
    "/evidence-claim-categories",
    response_model=list[EvidenceClaimCategory],
    summary="List evidence claim categories",
    description="Retrieve a list of all predefined categories for evidence claims. Requires admin access.",
)
async def list_evidence_claim_categories(
    _: UserContext = Depends(get_admin),
) -> list[EvidenceClaimCategory]:
    """List all available evidence claim categories."""
    return list(EvidenceClaimCategory)


@router.get(
    "/evidence-claim-types",
    response_model=list[EvidenceClaimType],
    summary="List evidence claim types",
    description="Retrieve a list of all predefined types for evidence claims. Requires admin access.",
)
async def list_evidence_claim_types(
    _: UserContext = Depends(get_admin),
) -> list[EvidenceClaimType]:
    """List all available evidence claim types."""
    return list(EvidenceClaimType)
