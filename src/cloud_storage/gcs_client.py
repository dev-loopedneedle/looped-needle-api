"""
Google Cloud Storage client utilities.

This module provides a wrapper around the Google Cloud Storage client for managing
file operations including uploads, downloads, deletions, and signed URL generation.
It handles credential setup, file path generation, and validation for evidence files
organized by brand, audit, and workflow.
"""

import asyncio
import json
import logging
import os
import re
import tempfile
from datetime import UTC, datetime, timedelta
from uuid import UUID

from google.api_core.exceptions import NotFound
from google.cloud import storage

from src.config import settings

logger = logging.getLogger(__name__)


class GCSClient:
    """Google Cloud Storage client wrapper."""

    def __init__(self) -> None:
        """Initialize GCS client."""
        self._temp_creds_file: str | None = None
        self._setup_credentials()
        self._client: storage.Client | None = None
        self._bucket_name = settings.gcs_bucket_name

    def _setup_credentials(self) -> None:
        """Set up Google Cloud credentials from GOOGLE_APPLICATION_CREDENTIALS_JSON or GOOGLE_APPLICATION_CREDENTIALS."""
        json_creds = (
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
            or settings.google_application_credentials_json
        )

        if json_creds:
            try:
                json.loads(json_creds)
                with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
                    f.write(json_creds)
                    temp_path = f.name
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path
                self._temp_creds_file = temp_path
                logger.info(
                    "Google Cloud credentials loaded from GOOGLE_APPLICATION_CREDENTIALS_JSON"
                )
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in GOOGLE_APPLICATION_CREDENTIALS_JSON: {e}")
                raise ValueError(f"Invalid JSON credentials: {e}") from e
        else:
            # Check for GOOGLE_APPLICATION_CREDENTIALS file path
            creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if creds_path:
                # Verify file exists and is readable
                if not os.path.exists(creds_path):
                    logger.error(f"Google Cloud credentials file not found: {creds_path}")
                    raise FileNotFoundError(
                        f"Google Cloud credentials file not found: {creds_path}"
                    )
                if not os.path.isfile(creds_path):
                    logger.error(f"Google Cloud credentials path is not a file: {creds_path}")
                    raise ValueError(f"Google Cloud credentials path is not a file: {creds_path}")
                # Ensure it's set in environment (in case it wasn't already)
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path
                logger.info(f"Google Cloud credentials loaded from file: {creds_path}")
            else:
                logger.warning(
                    "No Google Cloud credentials found. Will attempt to use default credentials."
                )

    def _cleanup_credentials(self) -> None:
        """Clean up temporary credentials file if created."""
        if self._temp_creds_file and os.path.exists(self._temp_creds_file):
            try:
                os.unlink(self._temp_creds_file)
            except Exception as e:
                logger.warning(
                    f"Failed to clean up temporary credentials file {self._temp_creds_file}: {e}",
                    exc_info=False,
                )

    def _get_client(self) -> storage.Client:
        """Get or create GCS client."""
        if self._client is None:
            self._client = storage.Client()
        return self._client

    def _get_bucket(self) -> storage.Bucket:
        """Get GCS bucket."""
        client = self._get_client()
        return client.bucket(self._bucket_name)

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename by removing path separators and dangerous characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename safe for GCS paths
        """
        # Remove path separators and dangerous characters
        sanitized = re.sub(r"[^\w\s.-]", "", filename)
        # Replace spaces with underscores
        sanitized = sanitized.replace(" ", "_")
        # Remove multiple consecutive dots/underscores
        sanitized = re.sub(r"[._]{2,}", "_", sanitized)
        # Remove leading/trailing dots and underscores
        sanitized = sanitized.strip("._")
        return sanitized

    @staticmethod
    def generate_gcs_path(brand_id: UUID, audit_id: UUID, workflow_id: UUID, filename: str) -> str:
        """
        Generate GCS path for evidence file.

        Format: evidence/{brandId}/{auditId}/{workflowId}/{timestamp}-{sanitizedFileName}

        Args:
            brand_id: Brand UUID
            audit_id: Audit UUID
            workflow_id: Workflow UUID
            filename: Original filename

        Returns:
            GCS path string
        """
        timestamp = int(datetime.now(UTC).timestamp() * 1000)  # milliseconds
        sanitized_filename = GCSClient.sanitize_filename(filename)
        return f"evidence/{brand_id}/{audit_id}/{workflow_id}/{timestamp}-{sanitized_filename}"

    async def generate_upload_signed_url(
        self, file_path: str, content_type: str, expiration_minutes: int | None = None
    ) -> tuple[str, datetime]:
        """
        Generate a signed URL for uploading a file to GCS (PUT method).

        Args:
            file_path: GCS path where file will be stored
            content_type: MIME type of the file
            expiration_minutes: URL expiration time in minutes (default: from settings)

        Returns:
            Tuple of (signed_url, expires_at)
        """
        expiration_minutes = expiration_minutes or settings.gcs_signed_url_expiration_minutes
        expires_at = datetime.now(UTC) + timedelta(minutes=expiration_minutes)

        def _generate_url() -> str:
            bucket = self._get_bucket()
            logger.info(
                f"Generating signed URL for bucket: {self._bucket_name}, "
                f"file_path: {file_path}, method: PUT, content_type: {content_type}"
            )

            # Get the service account email being used for signing
            from google.auth import default as get_default_credentials

            creds, _ = get_default_credentials()
            service_account_email = None
            if hasattr(creds, "service_account_email"):
                service_account_email = creds.service_account_email
            elif hasattr(creds, "_service_account_email"):
                service_account_email = creds._service_account_email

            logger.info(
                f"Using credentials for signed URL generation: "
                f"service_account={service_account_email or 'default'}, "
                f"bucket={self._bucket_name}"
            )

            blob = bucket.blob(file_path)
            try:
                # Generate signed URL - bucket.reload() is not needed and requires storage.buckets.get permission
                url = blob.generate_signed_url(
                    version="v4",
                    method="PUT",
                    expiration=timedelta(minutes=expiration_minutes),
                    content_type=content_type,
                )
                logger.info(
                    f"Successfully generated signed URL for {file_path}, "
                    f"bucket: {self._bucket_name}, expires at {expires_at}, "
                    f"URL length: {len(url)} chars"
                )
                return url
            except Exception as e:
                logger.error(
                    f"Failed to generate signed URL for {file_path}, "
                    f"bucket: {self._bucket_name}, error: {e}",
                    exc_info=True,
                )
                raise

        signed_url = await asyncio.to_thread(_generate_url)
        return signed_url, expires_at

    async def generate_download_signed_url(
        self, file_path: str, expiration_minutes: int | None = None
    ) -> str:
        """
        Generate a signed URL for downloading a file from GCS (GET method).

        Args:
            file_path: GCS path to the file
            expiration_minutes: URL expiration time in minutes (default: from settings)

        Returns:
            Signed URL string for downloading the file
        """
        expiration_minutes = expiration_minutes or settings.gcs_signed_url_expiration_minutes

        def _generate_url() -> str:
            bucket = self._get_bucket()
            blob = bucket.blob(file_path)
            url = blob.generate_signed_url(
                version="v4",
                method="GET",
                expiration=timedelta(minutes=expiration_minutes),
            )
            logger.info(
                f"Generated download signed URL for {file_path}, "
                f"expires in {expiration_minutes} minutes"
            )
            return url

        return await asyncio.to_thread(_generate_url)

    async def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in GCS.

        Args:
            file_path: GCS path to check

        Returns:
            True if file exists, False if file doesn't exist

        Raises:
            Exception: For network errors, permission issues, or other GCS API errors
                      (distinguishes between "file doesn't exist" and "error occurred")
                      Note: blob.exists() returns False for non-existent files and only
                      raises exceptions for real errors, so we re-raise to surface issues.
        """

        def _check_exists() -> bool:
            bucket = self._get_bucket()
            blob = bucket.blob(file_path)
            return blob.exists()

        try:
            exists = await asyncio.to_thread(_check_exists)
            return exists
        except Exception as e:
            # Real error occurred (network, permissions, etc.) - log and re-raise
            # blob.exists() returns False for non-existent files, so any exception
            # here indicates a real problem that should be surfaced
            logger.error(
                f"Error checking file existence for {file_path}: {e}",
                exc_info=True,
            )
            raise

    async def download_file(self, file_path: str) -> bytes | None:
        """
        Download a file from GCS.

        Args:
            file_path: GCS path to the file

        Returns:
            File content as bytes, or None if file doesn't exist
        """

        def _download() -> bytes | None:
            bucket = self._get_bucket()
            blob = bucket.blob(file_path)
            if not blob.exists():
                return None
            return blob.download_as_bytes()

        try:
            content = await asyncio.to_thread(_download)
            logger.debug(
                f"Downloaded file from GCS: {file_path}, size: {len(content) if content else 0} bytes"
            )
            return content
        except NotFound:
            logger.warning(f"File not found in GCS: {file_path}")
            return None
        except Exception as e:
            logger.error(f"Error downloading file {file_path}: {e}")
            raise

    async def delete_file(self, file_path: str) -> None:
        """
        Delete a file from GCS.

        Args:
            file_path: GCS path to delete

        Raises:
            NotFound: If file doesn't exist
        """

        def _delete() -> None:
            bucket = self._get_bucket()
            blob = bucket.blob(file_path)
            blob.delete()

        try:
            await asyncio.to_thread(_delete)
            logger.info(f"Deleted file from GCS: {file_path}")
        except NotFound:
            logger.warning(f"File not found in GCS: {file_path}")
            raise
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            raise

    def validate_path_belongs_to_workflow(
        self, file_path: str, brand_id: UUID, audit_id: UUID, workflow_id: UUID
    ) -> bool:
        """
        Validate that a file path belongs to the specified brand/audit/workflow.

        Args:
            file_path: GCS path to validate
            brand_id: Expected brand ID
            audit_id: Expected audit ID
            workflow_id: Expected workflow ID

        Returns:
            True if path belongs to workflow, False otherwise
        """
        expected_prefix = f"evidence/{brand_id}/{audit_id}/{workflow_id}/"
        return file_path.startswith(expected_prefix)

    def __del__(self) -> None:
        """Ensure temporary credentials file is cleaned up on object deletion."""
        self._cleanup_credentials()


# Global client instance
_gcs_client: GCSClient | None = None


def get_gcs_client() -> GCSClient:
    """Get global GCS client instance."""
    global _gcs_client
    if _gcs_client is None:
        _gcs_client = GCSClient()
    return _gcs_client
