"""Waitlist domain exceptions."""

from src.exceptions import BaseAPIException


class WaitlistEntryExistsError(BaseAPIException):
    """Raised when a waitlist entry with the email already exists."""

    def __init__(self, email: str):
        """Initialize exception with email."""
        message = f"Email {email} is already on the waitlist"
        super().__init__(message=message, status_code=409)
