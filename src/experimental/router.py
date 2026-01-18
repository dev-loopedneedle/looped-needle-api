"""Experimental endpoints router."""

import json
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import ValidationError

from src.auth.dependencies import UserContext, get_current_user
from src.evidence_submissions.constants import MAX_FILE_SIZE_BYTES, SUPPORTED_MIME_TYPES
from src.experimental.schemas import GeminiEvaluationRequest, GeminiEvaluationResponse
from src.llm.gemini_client import get_gemini_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/experiments", tags=["experimental"])


@router.post(
    "/evaluate-gemini",
    response_model=GeminiEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Evaluate document with Gemini API",
    description="Upload a document and evaluate it against specified claims using Gemini API with visual analysis. "
    "This is an experimental endpoint that provides comprehensive document analysis including visual elements "
    "(stamps, seals, structure) and confidence scoring. No audit or workflow association required.",
)
async def evaluate_document_with_gemini(
    file: UploadFile = File(..., description="Document file to evaluate"),
    name: str = Form(..., description="Document name or label"),
    claims: str = Form(..., description="Claims array as JSON string"),
    current_user: UserContext = Depends(get_current_user),
) -> GeminiEvaluationResponse:
    """
    Evaluate document using Gemini API with visual analysis.

    This is a standalone experimental endpoint that doesn't require audit or workflow association.
    Perfect for quick document evaluation and testing.
    """
    # Log incoming request
    logger.info(
        f"POST /api/v1/experiments/evaluate-gemini - "
        f"User: {current_user.profile.id}, "
        f"File: {file.filename}, "
        f"Content-Type: {file.content_type}, "
        f"Name: {name}, "
        f"Claims length: {len(claims) if claims else 0} chars"
    )

    # Validate file type
    if file.content_type not in SUPPORTED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(SUPPORTED_MIME_TYPES)}",
        )

    # Read file content
    try:
        file_content = await file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}") from e

    # Validate file size
    file_size = len(file_content)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES} bytes (50MB)",
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Validate claims
    if not claims or not claims.strip():
        raise HTTPException(status_code=400, detail="Claims cannot be empty")

    try:
        claims_payload = json.loads(claims)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400,
            detail="Claims must be a valid JSON array of claim objects",
        ) from e

    if not isinstance(claims_payload, list) or not claims_payload:
        raise HTTPException(
            status_code=400,
            detail="Claims must be a non-empty JSON array of claim objects",
        )

    try:
        request_payload = GeminiEvaluationRequest.model_validate(
            {
                "name": name,
                "claims": claims_payload,
            }
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request payload: {e}",
        ) from e

    # Log request payload details
    logger.info(
        f"Gemini evaluation request - "
        f"File: {file.filename}, "
        f"Size: {file_size} bytes, "
        f"MIME type: {file.content_type}, "
        f"Claims count: {len(request_payload.claims)}"
    )

    # Get Gemini client and analyze document
    try:
        gemini_client = get_gemini_client()
        logger.info(f"Calling Gemini API for document evaluation - File: {file.filename}")
        result = await gemini_client.analyze_document(
            file_content=file_content,
            mime_type=file.content_type or "application/pdf",
            name=request_payload.name,
            claims=[claim.model_dump(by_alias=True) for claim in request_payload.claims],
        )
        logger.info(
            f"Gemini API call completed successfully - "
            f"File: {file.filename}, "
            f"Confidence score: {result.get('confidence_score', 'N/A') if result else 'N/A'}"
        )

        # Ensure result is not None
        if result is None:
            logger.error(
                "Gemini API returned None result. This should not happen - "
                "analyze_document should always return a dict or raise an exception."
            )
            raise HTTPException(
                status_code=500,
                detail="Gemini API returned no result",
            )

        try:
            # Validate response structure using Pydantic
            validated_response = GeminiEvaluationResponse.model_validate(result)

            # Additional validation: ensure all required fields are present and properly structured
            if not validated_response.overall_verdict:
                raise ValueError("Response missing required field: overallVerdict")
            if not validated_response.overall_verdict_reason:
                raise ValueError("Response missing required field: overallVerdictReason")
            if not validated_response.claim_evaluations:
                raise ValueError(
                    "Response missing required field: claimEvaluations (must be non-empty array)"
                )
            if len(validated_response.claim_evaluations) == 0:
                raise ValueError(
                    "Response claimEvaluations array is empty (must contain at least one evaluation)"
                )

            return validated_response
        except ValidationError as e:
            logger.error(
                "Gemini API returned invalid schema response",
                extra={"error": str(e), "response": result},
            )
            raise ValueError(
                f"Gemini API returned response that does not match expected schema: {e}"
            ) from e
        except ValueError as e:
            # Re-raise ValueError as-is (from our validation or from gemini_client)
            logger.error(
                f"Gemini response validation error: {e}",
                extra={"response": result if "result" in locals() else None},
            )
            raise HTTPException(
                status_code=502,
                detail=f"Gemini API returned invalid response structure: {str(e)}",
            ) from e

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        logger.error(
            f"Failed to evaluate document with Gemini API. "
            f"Error Type: {error_type}, Error Message: {error_msg}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to evaluate document with Gemini API: {error_msg}",
        ) from e
