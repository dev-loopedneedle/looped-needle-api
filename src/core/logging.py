"""Logging configuration and setup."""

import json
import logging
import sys
from datetime import datetime
from typing import Any

from src.config import settings

# ANSI color codes
COLORS = {
    "DEBUG": "\033[36m",  # Cyan
    "INFO": "\033[32m",  # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[35m",  # Magenta
    "RESET": "\033[0m",  # Reset
    "BOLD": "\033[1m",
    "DIM": "\033[2m",
}

# Emojis for log levels
EMOJIS = {
    "DEBUG": "🔍",
    "INFO": "ℹ️",
    "WARNING": "⚠️",
    "ERROR": "❌",
    "CRITICAL": "🚨",
}


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
        # Add extra fields if present
        if hasattr(record, "extra") and record.extra:
            log_data.update(record.extra)
        return json.dumps(log_data)


class PrettyFormatter(logging.Formatter):
    """Pretty formatter with emojis, colors, and readable formatting."""

    def __init__(self, use_colors: bool = True):
        """Initialize pretty formatter."""
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()

    def _get_color(self, level: str) -> str:
        """Get color code for log level."""
        if not self.use_colors:
            return ""
        return COLORS.get(level, "")

    def _get_emoji(self, level: str) -> str:
        """Get emoji for log level."""
        return EMOJIS.get(level, "📝")

    def _format_timestamp(self, record: logging.LogRecord) -> str:
        """Format timestamp in readable format."""
        dt = datetime.fromtimestamp(record.created)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def _format_logger_name(self, name: str) -> str:
        """Format logger name to be more readable."""
        # Shorten long logger names
        if name.startswith("src."):
            name = name[4:]  # Remove 'src.' prefix
        # Keep last 2 parts for readability
        parts = name.split(".")
        if len(parts) > 2:
            name = ".".join(parts[-2:])
        return name

    def _format_extra(self, record: logging.LogRecord) -> str:
        """Format extra fields if present."""
        if not hasattr(record, "__dict__"):
            return ""

        extra_fields = []
        # Skip standard logging fields
        skip_fields = {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "thread",
            "threadName",
            "exc_info",
            "exc_text",
            "stack_info",
        }

        for key, value in record.__dict__.items():
            if key not in skip_fields and not key.startswith("_"):
                if isinstance(value, dict):
                    # Format dict nicely with indentation
                    formatted = json.dumps(value, indent=2)
                    # Indent each line
                    indented = "\n".join(f"    {line}" for line in formatted.split("\n"))
                    extra_fields.append(f"  {key}:\n{indented}")
                elif isinstance(value, (list, tuple)):
                    # Format lists/tuples nicely
                    if len(value) > 3:
                        # Long lists: show first 3 and count
                        preview = ", ".join(str(v) for v in value[:3])
                        extra_fields.append(f"  {key}: [{preview}, ... ({len(value)} total)]")
                    else:
                        extra_fields.append(f"  {key}: {value}")
                elif isinstance(value, str) and len(value) > 100:
                    # Truncate very long strings
                    extra_fields.append(f"  {key}: {value[:100]}... ({len(value)} chars)")
                else:
                    extra_fields.append(f"  {key}: {value}")

        if extra_fields:
            dim = COLORS["DIM"] if self.use_colors else ""
            reset = COLORS["RESET"] if self.use_colors else ""
            return f"\n{dim}└─ Extra:{reset}\n" + "\n".join(extra_fields)
        return ""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record in a pretty, readable way."""
        level = record.levelname
        emoji = self._get_emoji(level)
        color = self._get_color(level)
        reset = COLORS["RESET"] if self.use_colors else ""
        dim = COLORS["DIM"] if self.use_colors else ""

        timestamp = self._format_timestamp(record)
        logger_name = self._format_logger_name(record.name)
        message = record.getMessage()

        # Build the formatted log line
        parts = [
            f"{color}{emoji} {level:<8}{reset}",
            f"{dim}{timestamp}{reset}",
            f"{dim}[{logger_name}]{reset}",
            f"{message}",
        ]

        # Add request ID if available
        if hasattr(record, "request_id"):
            parts.insert(-1, f"{dim}req:{record.request_id}{reset}")

        log_line = " ".join(parts)

        # Add extra fields
        extra = self._format_extra(record)
        if extra:
            log_line += extra

        # Add exception traceback if present
        if record.exc_info:
            exc_text = self.formatException(record.exc_info)
            if exc_text:
                # Format exception with better indentation
                dim = COLORS["DIM"] if self.use_colors else ""
                indented_exc = "\n".join(
                    f"{dim}  {line}{reset}" if i > 0 else f"{color}{line}{reset}"
                    for i, line in enumerate(exc_text.split("\n"))
                )
                log_line += f"\n{dim}└─ Exception:{reset}\n{indented_exc}"

        return log_line


def setup_logging() -> None:
    """Configure application logging."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Remove existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    # Create handler
    handler = logging.StreamHandler()
    handler.setLevel(log_level)

    # Set formatter based on log_format setting
    if settings.log_format == "json":
        handler.setFormatter(JSONFormatter())
    elif settings.log_format == "pretty":
        handler.setFormatter(PrettyFormatter(use_colors=True))
    else:
        # Default pretty format
        handler.setFormatter(PrettyFormatter(use_colors=True))

    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Set level for third-party loggers to WARNING to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
