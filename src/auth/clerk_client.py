"""Clerk SDK wrapper for request/token verification.

We use the official Clerk Python SDK repo (`clerk/clerk-sdk-python`), which is published as the
`clerk-backend-api` package and imported as `clerk_backend_api`.
"""

import logging
from typing import Any

import httpx
from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions

from src.auth.exceptions import AuthenticationError, ServiceUnavailableError
from src.config import settings

logger = logging.getLogger(__name__)


class ClerkClient:
    """Wrapper for Clerk SDK client."""

    def __init__(self):
        """Initialize Clerk client with secret key."""
        if not settings.clerk_secret_key:
            raise ValueError("CLERK_SECRET_KEY must be set in environment variables")
        # The official SDK uses `bearer_auth` for authenticating Clerk Backend API requests.
        # For request authentication / session verification, this is still required.
        self.client = Clerk(bearer_auth=settings.clerk_secret_key)

    def verify_token(self, token: str) -> dict[str, Any]:
        """
        Verify an incoming Clerk token and return decoded session claims.

        Args:
            token: JWT token string

        Returns:
            Decoded token claims including user ID and public_metadata

        Raises:
            AuthenticationError: If token is invalid or expired
            ServiceUnavailableError: If Clerk service is unavailable
        """
        try:
            # The SDK's request authenticator operates on an httpx.Request. We build a minimal
            # request that carries the bearer token (this matches our API auth flow).
            req = httpx.Request(
                method="GET",
                url="http://looped-needle.local/auth",
                headers={"Authorization": f"Bearer {token}"},
            )

            opts = AuthenticateRequestOptions(
                authorized_parties=settings.clerk_authorized_parties or None
            )
            request_state = self.client.authenticate_request(req, opts)

            if not getattr(request_state, "is_signed_in", False):
                raise AuthenticationError("Invalid or expired token")

            # Extract user ID and claims from the request state
            user_id = getattr(request_state, "user_id", None)

            # The SDK returns session claims in various possible fields
            claims_obj = (
                getattr(request_state, "session_claims", None)
                or getattr(request_state, "claims", None)
                or getattr(request_state, "payload", None)
            )

            claims: dict[str, Any] = {}
            if isinstance(claims_obj, dict):
                claims = claims_obj
            elif claims_obj is not None:
                if hasattr(claims_obj, "model_dump"):
                    claims = claims_obj.model_dump()
                elif hasattr(claims_obj, "dict"):
                    claims = claims_obj.dict()
                else:
                    claims = dict(claims_obj)

            # Ensure user ID is present in the returned dict as 'sub' for consistency
            if user_id and not claims.get("sub"):
                claims["sub"] = user_id

            return claims
        except Exception as e:
            # If we already classified it as an auth error, preserve that.
            if isinstance(e, AuthenticationError):
                logger.warning(f"Clerk token verification failed: {e.message}")
                raise

            logger.error(f"Clerk service error: {e}")
            raise ServiceUnavailableError("Authentication service unavailable") from e
