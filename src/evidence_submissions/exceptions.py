"""Evidence submissions domain exceptions."""


class SubmissionError(Exception):
    """Base exception for evidence submission errors."""

    pass


class SubmissionNotFoundError(SubmissionError):
    """Raised when submission is not found."""

    pass


class InvalidFileError(SubmissionError):
    """Raised when file is invalid (size, type, etc.)."""

    pass


class ProcessingError(SubmissionError):
    """Raised when submission processing fails."""

    pass


class FileNotFoundError(SubmissionError):
    """Raised when file path does not exist in storage."""

    pass



