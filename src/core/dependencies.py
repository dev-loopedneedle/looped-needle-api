"""Shared dependencies for FastAPI routes."""

from fastapi import Request


def get_request_id(request: Request) -> str | None:
    """
    Dependency to extract request ID from request state.

    Args:
        request: FastAPI Request object

    Returns:
        Request ID string or None if not available
    """
    return getattr(request.state, "request_id", None)

