"""Google Gemini API client for document analysis."""

import asyncio
import json
import logging
import os
import re
from typing import Any

from google import genai
from google.genai import types
from google.genai.types import (
    HarmBlockThreshold,
    HarmCategory,
    Part,
    SafetySetting,
)

from src.config import settings
from src.llm.gemini_prompt import build_evaluation_prompt
from src.llm.gemini_schema import get_evaluation_response_schema

logger = logging.getLogger(__name__)

SAFETY_SETTINGS = [
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=HarmBlockThreshold.BLOCK_NONE,
    ),
]

GENERATION_TEMPERATURE = 0.3
GENERATION_TOP_P = 0.85
GENERATION_TOP_K = 30


class GeminiClient:
    """Async wrapper for Google Gemini API client."""

    def __init__(self) -> None:
        """Initialize Google Gemini API client."""
        self._model_name = getattr(settings, "gemini_model_name", "gemini-3-pro-preview")
        self._client: genai.Client | None = None  # Client for content generation (API Key)

    def _get_generation_client(self) -> genai.Client:
        """Get or create client for content generation (API Key)."""
        if self._client is None:
            api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "gemini_api_key", None)
            self._client = genai.Client(api_key=api_key)
        return self._client

    def _extract_response_text(self, response: Any) -> str | None:
        """Extract text content from Gemini API response."""
        try:
            if hasattr(response, "text") and response.text:
                return response.text
        except (AttributeError, ValueError):
            pass

        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and candidate.content:
                if hasattr(candidate.content, "parts"):
                    parts_text = []
                    for part in candidate.content.parts:
                        if hasattr(part, "text") and part.text:
                            parts_text.append(part.text)
                    if parts_text:
                        return " ".join(parts_text)

        return None

    def _handle_empty_response(self, response: Any) -> ValueError:
        """Handle case when Gemini API returns no text content."""
        block_reason = None
        if hasattr(response, "prompt_feedback"):
            feedback = response.prompt_feedback
            if hasattr(feedback, "block_reason") and feedback.block_reason:
                block_reason = str(feedback.block_reason)

        error_detail = "No text content in Gemini API response"
        if block_reason:
            error_detail += f". Content was blocked: {block_reason}"

        logger.error(
            f"Gemini API returned no text content. Block reason: {block_reason}",
            exc_info=False,
        )
        return ValueError(error_detail)

    def _handle_response_parsing_error(
        self, error: Exception, response_text: str | None
    ) -> ValueError:
        """Handle errors when parsing Gemini API response JSON."""
        if isinstance(error, json.JSONDecodeError):
            logger.error(
                f"Failed to parse Gemini response JSON. Error: {error}",
                extra={
                    "response_preview": response_text[:500] if response_text else None,
                    "response_length": len(response_text) if response_text else 0,
                    "error_position": getattr(error, "pos", None),
                },
            )
            return ValueError(f"Gemini API returned invalid JSON: {error}")
        else:
            logger.error(
                f"Gemini response validation error: {error}",
                extra={"response_preview": response_text[:500] if response_text else None},
            )
            return ValueError(str(error))

    def _handle_api_error(self, error: Exception) -> Exception:
        """Handle general Gemini API errors."""
        error_msg = str(error)
        error_type = type(error).__name__

        logger.error(
            f"Gemini API error - Type: {error_type}, Message: {error_msg}",
            exc_info=True,
        )
        return Exception(f"Gemini API error: {error_msg}")

    async def analyze_document(
        self,
        file_content: bytes | None = None,
        gemini_file_uri: str | None = None,
        mime_type: str = "application/pdf",
        name: str = "",
        claims: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze a document using Gemini API with visual understanding.

        Args:
            file_content: File content as bytes. Either file_content or gemini_file_uri must be provided.
            gemini_file_uri: Gemini File API URI (https://generativelanguage.googleapis.com/...).
                          Either file_content or gemini_file_uri must be provided.
            mime_type: MIME type of the file (e.g., 'application/pdf', 'image/jpeg')
            name: Document name/label provided by the request
            claims: List of claims/criteria to evaluate against (document type should be in claims)

        Returns:
            Dictionary containing structured response JSON matching the evaluation schema

        Raises:
            ValueError: If neither file_content nor gemini_file_uri is provided, or if both are provided
            Exception: For various API errors
        """
        if claims is None:
            claims = []

        if not file_content and not gemini_file_uri:
            raise ValueError("Either file_content or gemini_file_uri must be provided")

        if file_content and gemini_file_uri:
            raise ValueError(
                "Cannot provide both file_content and gemini_file_uri. Provide only one."
            )

        try:
            claims_json = json.dumps(claims, ensure_ascii=True, indent=2)
            response_schema = get_evaluation_response_schema()
            prompt = build_evaluation_prompt(name, claims_json)

            def generate_content() -> Any:
                generation_config = types.GenerateContentConfig(
                    temperature=GENERATION_TEMPERATURE,
                    top_p=GENERATION_TOP_P,
                    top_k=GENERATION_TOP_K,
                    response_mime_type="application/json",
                    response_json_schema=response_schema,
                    safety_settings=SAFETY_SETTINGS,
                    tools=[],
                )

                # Build parts based on whether we have file content or URI
                parts = [Part.from_text(text=prompt)]
                if file_content:
                    # Send file content directly using Part.from_bytes
                    parts.append(Part.from_bytes(data=file_content, mime_type=mime_type))
                elif gemini_file_uri:
                    # Use existing Gemini File API URI
                    parts.append(Part.from_uri(file_uri=gemini_file_uri, mime_type=mime_type))

                client = self._get_generation_client()
                response = client.models.generate_content(
                    model=self._model_name,
                    contents=parts,
                    config=generation_config,
                )
                return response

            response = await asyncio.to_thread(generate_content)

            response_text = self._extract_response_text(response)

            if not response_text:
                raise self._handle_empty_response(response)

            try:
                json_text = response_text.strip()

                if json_text.startswith("```"):
                    json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", json_text, re.DOTALL)
                    if json_match:
                        json_text = json_match.group(1).strip()

                result = json.loads(json_text)

                if not isinstance(result, dict):
                    raise ValueError(
                        f"Gemini API returned invalid structure: expected object, got {type(result).__name__}"
                    )

            except (json.JSONDecodeError, ValueError) as e:
                raise self._handle_response_parsing_error(e, response_text) from e

            return result

        except (ValueError, Exception) as e:
            raise self._handle_api_error(e) from e

    async def generate_text(
        self,
        prompt: str,
        response_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Generate text content using Gemini API without file registration.
        Useful for testing text-only requests.

        Args:
            prompt: Text prompt to send to Gemini
            response_schema: Optional JSON schema for structured output.
                          If None, returns raw text response.

        Returns:
            Dictionary containing the response. If response_schema is provided,
            returns parsed JSON. Otherwise, returns {"text": response_text}.

        Raises:
            Exception: For various API errors
        """
        try:

            def generate_content() -> Any:
                config_params: dict[str, Any] = {
                    "temperature": GENERATION_TEMPERATURE,
                    "top_p": GENERATION_TOP_P,
                    "top_k": GENERATION_TOP_K,
                    "safety_settings": SAFETY_SETTINGS,
                    "tools": [],  # Disable function calling
                }

                if response_schema:
                    config_params["response_mime_type"] = "application/json"
                    config_params["response_json_schema"] = response_schema

                generation_config = types.GenerateContentConfig(**config_params)
                parts = [Part.from_text(text=prompt)]

                client = self._get_generation_client()
                response = client.models.generate_content(
                    model=self._model_name,
                    contents=parts,
                    config=generation_config,
                )
                return response

            response = await asyncio.to_thread(generate_content)

            response_text = self._extract_response_text(response)

            if not response_text:
                raise self._handle_empty_response(response)

            if response_schema:
                # Parse JSON response
                try:
                    json_text = response_text.strip()

                    if json_text.startswith("```"):
                        json_match = re.search(r"```(?:json)?\s*\n(.*?)\n```", json_text, re.DOTALL)
                        if json_match:
                            json_text = json_match.group(1).strip()

                    result = json.loads(json_text)

                    if not isinstance(result, dict):
                        raise ValueError(
                            f"Gemini API returned invalid structure: expected object, got {type(result).__name__}"
                        )

                    return result
                except (json.JSONDecodeError, ValueError) as e:
                    raise self._handle_response_parsing_error(e, response_text) from e
            else:
                # Return raw text
                return {"text": response_text}

        except (ValueError, Exception) as e:
            raise self._handle_api_error(e) from e


# Global client instance
_gemini_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    """Get global Gemini client instance."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
