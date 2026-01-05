"""Logging configuration and setup."""

import json
import logging
from datetime import datetime

from src.config import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Add request ID if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def setup_logging() -> None:
    """Configure application logging."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(message)s"
        if settings.log_format == "json"
        else "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    if settings.log_format == "json":
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logging.getLogger().handlers = [handler]

