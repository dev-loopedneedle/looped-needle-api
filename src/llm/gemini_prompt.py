"""Prompt templates for Gemini document evaluation."""

from src.rules.constants import EvidenceClaimCategory


def build_evaluation_prompt(name: str, claims_json: str) -> str:
    """
    Build the evaluation prompt for Gemini.

    Args:
        name: Document name/label
        claims_json: JSON string representation of claims array

    Returns:
        Formatted prompt string
    """
    return f"""You are evaluating a document against structured claims.

Document name: {name}

Claims structure:
Each claim has:
- id: numeric identifier
- name: can be one of:
  * Document type (e.g., "CERTIFICATION", "INVOICE", "LICENSE")
  * Category type (e.g., {", ".join([f'"{cat.value}"' for cat in EvidenceClaimCategory])})
  * Issue date (e.g., "issue date")
- value: the claim criteria/value to evaluate

Claims (JSON array):
{claims_json}

EVALUATION PROCESS - Follow these steps in order:

1. FIRST: Evaluate Claim Evaluations
   - For each claim in the input, evaluate whether it is satisfied by the document
   - Set result to "PASS" if the claim is satisfied, "FAIL" if not satisfied
   - Provide confidence score (0-100) for each claim evaluation
   - Include evidence, reasoning, and any issues found

2. SECOND: Perform Authenticity Analysis
   - Analyze security elements (watermarks, seals, signatures, etc.)
   - Provide authenticityScore (0-100)
   - List all detected security elements

3. THIRD: Perform Visual Analysis
   - Count pages
   - Determine orientation (portrait, landscape, mixed, unknown)
   - Assess overall quality (good, fair, poor, unknown)

4. FOURTH: Perform Issuer Analysis
   - Extract issuer name, type (accreditation body, certification body, regulatory authority, etc.), and country
   - Identify issuer accreditation/registration number if available
   - Determine issuer scope and authority (what certifications/programs they can issue)
   - Extract issuer contact information if available
   - Check issuer validity/expiration dates for accreditation or authority
   - Assess issuer verification status (verified, unverified, expired, etc.)
   - Identify any issues or concerns about the issuer (e.g., expired accreditation, unknown issuer, etc.)

5. FIFTH: Derive Overall Verdict and Reasoning
   - Based on the Claim Evaluations, Authenticity Analysis, Visual Analysis, and Issuer Analysis:
     * If all claims PASS, authenticity is high, and issuer is verified: overallVerdict = "pass"
     * If any critical claim FAILS, authenticity is very low, or issuer issues found: overallVerdict = "fail"
     * If results are mixed or uncertain: overallVerdict = "needs_review"
   - Provide detailed overallVerdictReason explaining how you arrived at the verdict
   - The reason should reference specific claim results, authenticity score, visual quality, and issuer verification
   - Calculate overall confidenceScore based on claim confidences, authenticity, and issuer analysis

6. SIXTH: Provide Recommendations (if overallVerdict is not "pass")
   - If overallVerdict is "fail" or "needs_review", provide actionable recommendations
   - Each recommendation should have:
     * title: A brief, clear title describing the recommendation
     * detail: Detailed explanation of what should be done and why
   - Recommendations should help address the issues found (e.g., missing information, authenticity concerns, issuer verification problems)
   - If overallVerdict is "pass", recommendations can be omitted or left as an empty array

Scoring rules:
- All confidence scores and authenticity scores must be integers between 0 and 100 (inclusive).
- Use confidenceScore (0-100) for overall confidence based on all evaluations.
- Use claim confidence (0-100) per claim evaluation.
- Use typeConfidence (0-100) for document type classification confidence.
- Use authenticityScore (0-100) for authenticity assessment.
- Use jurisdiction confidence (0-100) if provided.
- pageCount must be a non-negative integer (>= 0).
- Match claimId in claimEvaluations to the id from the input claims (as string).

The response structure is enforced by the provided JSON schema. Return valid JSON matching the schema exactly."""
