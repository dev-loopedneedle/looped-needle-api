"""Evidence submissions domain constants."""


class SubmissionStatus:
    """Evidence submission status constants."""

    PENDING_PROCESSING = "PENDING_PROCESSING"
    PROCESSING = "PROCESSING"
    PROCESSING_COMPLETE = "PROCESSING_COMPLETE"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class MatchDecision:
    """Match decision constants."""

    MATCH = "MATCH"
    NO_MATCH = "NO_MATCH"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ReviewDecision:
    """Review decision constants."""

    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class FileType:
    """Supported file type constants."""

    PDF = "application/pdf"
    JPEG = "image/jpeg"
    PNG = "image/png"
    DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


# Maximum file size: 50 MB
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024

# Supported MIME types
SUPPORTED_MIME_TYPES = [
    FileType.PDF,
    FileType.JPEG,
    FileType.PNG,
    FileType.DOCX,
]

