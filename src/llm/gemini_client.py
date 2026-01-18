"""Google Gemini API client for document analysis."""

import asyncio
import json
import logging
import os
import re
import tempfile
from typing import Any

from google import genai
from google.auth import default as get_default_credentials
from google.auth.transport.requests import Request
from google.genai import types
from google.genai.types import (
    HarmBlockThreshold,
    HarmCategory,
    Part,
    RegisterFilesConfig,
    SafetySetting,
)
from google.oauth2 import service_account

from src.config import settings
from src.llm.gemini_prompt import build_evaluation_prompt
from src.llm.gemini_schema import get_evaluation_response_schema

logger = logging.getLogger(__name__)

# Configuration constants
REQUIRED_GCS_SCOPES = [
    "https://www.googleapis.com/auth/devstorage.read_only",
    "https://www.googleapis.com/auth/cloud-platform",
]

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
        self._temp_creds_file: str | None = None
        self._setup_credentials()
        self._model_name = getattr(settings, "gemini_model_name", "gemini-3-pro-preview")
        self._client = self._configure_client()

    def _setup_credentials(self) -> None:
        """Set up Google Cloud credentials from GOOGLE_APPLICATION_CREDENTIALS_JSON or API key."""
        credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON") or getattr(
            settings, "google_application_credentials_json", ""
        )

        if credentials_json:
            try:
                json.loads(credentials_json)
                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                    f.write(credentials_json)
                    temp_path = f.name
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path
                self._temp_creds_file = temp_path
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")
                raise ValueError(f"Invalid JSON credentials: {e}") from e
        else:
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if credentials_path:
                if not os.path.exists(credentials_path):
                    logger.error(f"Google Cloud credentials file not found: {credentials_path}")
                    raise FileNotFoundError(
                        f"Google Cloud credentials file not found: {credentials_path}"
                    )
                if not os.path.isfile(credentials_path):
                    logger.error(f"Google Cloud credentials path is not a file: {credentials_path}")
                    raise ValueError(
                        f"Google Cloud credentials path is not a file: {credentials_path}"
                    )
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "gemini_api_key", "")
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key

    def _configure_client(self) -> genai.Client:
        """Configure and return the Gemini client."""
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            return genai.Client(api_key=api_key)

        return genai.Client()

    def _cleanup_credentials(self) -> None:
        """Clean up temporary credentials file if created."""
        if self._temp_creds_file and os.path.exists(self._temp_creds_file):
            try:
                os.unlink(self._temp_creds_file)
            except OSError:
                pass

    def _handle_registration_error(self, error: Exception, gcs_uri: str) -> ValueError:
        """Handle GCS file registration errors."""
        error_msg = str(error)

        is_scope_error = (
            "insufficient authentication scopes" in error_msg.lower()
            or "permission_denied" in error_msg.lower()
            or "access_token_scope_insufficient" in error_msg.lower()
            or (hasattr(error, "status_code") and error.status_code == 403)
        )

        if is_scope_error:
            gemini_error = error_msg
            if hasattr(error, "__cause__") and error.__cause__:
                cause_msg = str(error.__cause__)
                if "generativelanguage" in cause_msg.lower():
                    gemini_error = cause_msg

            logger.error(
                f"OAuth scope error during GCS file registration: {gemini_error}. "
                f"GCS URI: {gcs_uri}. Required scopes: {REQUIRED_GCS_SCOPES}.",
                exc_info=True,
            )
            return ValueError(f"Insufficient OAuth scopes for Gemini API: {gemini_error}")
        else:
            logger.error(
                f"Gemini API registration failed: {error_msg}. GCS URI: {gcs_uri}",
                exc_info=True,
            )
            return ValueError(f"Gemini API registration failed: {error_msg}")

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

    def _get_credentials_with_scopes(self) -> Any:
        """Get credentials with required GCS scopes."""
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON") or getattr(
            settings, "google_application_credentials_json", ""
        )

        if credentials_json:
            try:
                creds_dict = json.loads(credentials_json)
                credentials = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=REQUIRED_GCS_SCOPES,
                )
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse service account JSON: {e}")
                raise ValueError(f"Invalid service account credentials: {e}") from e
        elif credentials_path and os.path.exists(credentials_path):
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=REQUIRED_GCS_SCOPES,
            )
        else:
            credentials, project = get_default_credentials(scopes=REQUIRED_GCS_SCOPES)
            if hasattr(credentials, "with_scopes"):
                credentials = credentials.with_scopes(REQUIRED_GCS_SCOPES)

        if not credentials:
            raise ValueError("Failed to obtain credentials")

        if hasattr(credentials, "scopes"):
            actual_scopes = credentials.scopes or []
            missing_scopes = set(REQUIRED_GCS_SCOPES) - set(actual_scopes)
            if missing_scopes:
                if isinstance(credentials, service_account.Credentials):
                    credentials = credentials.with_scopes(REQUIRED_GCS_SCOPES)

        try:
            credentials.refresh(Request())
        except Exception as refresh_error:
            logger.error(
                f"Failed to refresh credentials with required scopes: {refresh_error}",
                exc_info=True,
            )
            raise ValueError(
                f"Failed to refresh credentials with required scopes: {refresh_error}"
            ) from refresh_error

        if not (hasattr(credentials, "token") and credentials.token):
            raise ValueError("Failed to obtain access token from credentials")

        return credentials

    async def _register_gcs_file(self, gcs_uri: str) -> str:
        """Register a GCS file with Gemini API and return the Gemini file URI."""

        def register_file() -> Any:
            credentials = self._get_credentials_with_scopes()
            registration_client = genai.Client(credentials=credentials)

            response = registration_client.files.register_files(
                auth=credentials,
                uris=[gcs_uri],
                config=RegisterFilesConfig(),
            )
            return response

        registration_response = await asyncio.to_thread(register_file)

        if registration_response.files and len(registration_response.files) > 0:
            registered_file = registration_response.files[0]
            return registered_file.uri
        else:
            raise ValueError(f"Registration response has no files: {registration_response}")

    async def analyze_document(
        self,
        input_file_uri: str,
        mime_type: str = "application/pdf",
        name: str = "",
        claims: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Analyze a document using Gemini API with visual understanding.

        Args:
            input_file_uri: GCS URI (gs://bucket/path) or Gemini File API URI.
                      For GCS URIs (gs://...), service account credentials are REQUIRED.
                      Files are registered directly from GCS - no download/upload to backend.
            mime_type: MIME type of the file (e.g., 'application/pdf', 'image/jpeg')
            name: Document name/label provided by the request
            claims: List of claims/criteria to evaluate against (document type should be in claims)

        Returns:
            Dictionary containing structured response JSON matching the evaluation schema

        Raises:
            ValueError: If GCS URI provided without service account credentials, or unsupported URI format
            Exception: For various API errors
        """
        if claims is None:
            claims = []

        gemini_file_uri: str | None = None

        try:
            if input_file_uri:
                if input_file_uri.startswith("https://generativelanguage.googleapis.com"):
                    gemini_file_uri = input_file_uri
                elif input_file_uri.startswith("gs://"):
                    has_service_account = (
                        os.getenv("GOOGLE_APPLICATION_CREDENTIALS") is not None
                        or os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON") is not None
                    )

                    if not has_service_account:
                        error_msg = (
                            f"Service account credentials are REQUIRED for GCS file registration. "
                            f"GCS URI: {input_file_uri}. "
                            f"Please configure GOOGLE_APPLICATION_CREDENTIALS or GOOGLE_APPLICATION_CREDENTIALS_JSON. "
                            f"Downloading files to backend is not supported - files must be registered directly from GCS."
                        )
                        logger.error(f"GCS file registration failed: {error_msg}")
                        raise ValueError(error_msg)

                    try:
                        gemini_file_uri = await self._register_gcs_file(input_file_uri)
                    except Exception as registration_error:
                        raise self._handle_registration_error(
                            registration_error, input_file_uri
                        ) from registration_error
                else:
                    raise ValueError(f"Unsupported file URI format: {input_file_uri}")

            if not gemini_file_uri:
                raise ValueError(
                    f"Failed to process file URI: {input_file_uri}. "
                    f"Expected GCS URI (gs://...) or Gemini File API URI (https://generativelanguage.googleapis.com/...)"
                )

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
                )
                parts = [
                    Part.from_text(text=prompt),
                    Part.from_uri(file_uri=gemini_file_uri, mime_type=mime_type),
                ]
                response = self._client.models.generate_content(
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

    def __del__(self) -> None:
        """Ensure temporary credentials file is cleaned up on object deletion."""
        self._cleanup_credentials()


# Global client instance
_gemini_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    """Get global Gemini client instance."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
