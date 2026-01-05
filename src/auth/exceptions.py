"""Authentication domain exceptions."""


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(self.message)


class ServiceUnavailableError(Exception):
    """Raised when authentication service is unavailable."""

    def __init__(self, message: str = "Authentication service unavailable"):
        self.message = message
        super().__init__(self.message)


class AccessDeniedError(Exception):
    """Raised when user does not have access to a resource."""

    def __init__(self, message: str = "Access denied"):
        self.message = message
        super().__init__(self.message)

