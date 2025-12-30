"""Global exception classes."""


class BaseAPIException(Exception):
    """Base exception for API errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(BaseAPIException):
    """Resource not found exception."""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationError(BaseAPIException):
    """Validation error exception."""

    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=400)


class DatabaseError(BaseAPIException):
    """Database error exception."""

    def __init__(self, message: str = "Database error"):
        super().__init__(message, status_code=500)

