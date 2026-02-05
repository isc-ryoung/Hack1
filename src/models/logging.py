"""Structured logging configuration with JSON formatter and trace ID support."""

import logging
import os
import sys
from typing import Any

import structlog

from src.models.tracing import get_current_trace_id


def add_trace_id(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add trace ID to log event dictionary.

    Args:
        logger: Logger instance (unused but required by structlog)
        method_name: Log method name (unused but required by structlog)
        event_dict: Event dictionary to modify

    Returns:
        Modified event dictionary with trace_id added
    """
    event_dict["trace_id"] = get_current_trace_id()
    return event_dict


def add_timestamp(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add ISO 8601 timestamp to log event dictionary.

    Args:
        logger: Logger instance (unused but required by structlog)
        method_name: Log method name (unused but required by structlog)
        event_dict: Event dictionary to modify

    Returns:
        Modified event dictionary with timestamp added
    """
    from datetime import datetime, timezone

    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat()
    return event_dict


def redact_sensitive_data(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Redact sensitive information from logs (FR-024).

    Args:
        logger: Logger instance (unused but required by structlog)
        method_name: Log method name (unused but required by structlog)
        event_dict: Event dictionary to modify

    Returns:
        Modified event dictionary with sensitive data redacted
    """
    sensitive_keys = {
        "password",
        "api_key",
        "apikey",
        "token",
        "secret",
        "license_key",
        "auth",
        "authorization",
    }

    for key, value in event_dict.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            if isinstance(value, str):
                event_dict[key] = "***REDACTED***"

    return event_dict


def configure_logging() -> None:
    """Configure structlog with JSON formatting and trace ID propagation.

    Sets up structured logging with:
    - JSON output format
    - Automatic trace ID injection
    - ISO 8601 timestamps
    - PII redaction
    - Configurable log level from environment
    """
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            add_timestamp,
            add_trace_id,
            redact_sensitive_data,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level),
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__ of calling module)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)
