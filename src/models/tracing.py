"""Trace ID generation and propagation for OpenTelemetry compatibility."""

import secrets
from contextvars import ContextVar

# Context variable for trace ID propagation across async calls
_trace_id_context: ContextVar[str | None] = ContextVar("trace_id", default=None)


def generate_trace_id() -> str:
    """Generate a new OpenTelemetry-compatible trace ID.

    Returns:
        32-character hexadecimal string (128 bits)

    Example:
        >>> trace_id = generate_trace_id()
        >>> len(trace_id)
        32
        >>> all(c in '0123456789abcdef' for c in trace_id)
        True
    """
    return secrets.token_hex(16)  # 16 bytes = 128 bits = 32 hex chars


def get_current_trace_id() -> str:
    """Get the current trace ID from context or generate a new one.

    Returns:
        Current trace ID from context, or newly generated ID if none exists
    """
    trace_id = _trace_id_context.get()
    if trace_id is None:
        trace_id = generate_trace_id()
        _trace_id_context.set(trace_id)
    return trace_id


def set_trace_id(trace_id: str) -> None:
    """Set the trace ID in the current context.

    Args:
        trace_id: 32-character hexadecimal trace ID

    Raises:
        ValueError: If trace_id is not a valid 128-bit hex string
    """
    if not isinstance(trace_id, str) or len(trace_id) != 32:
        raise ValueError(f"Invalid trace_id: must be 32-character hex string, got {trace_id}")
    if not all(c in "0123456789abcdef" for c in trace_id):
        raise ValueError(f"Invalid trace_id: must contain only hex characters, got {trace_id}")
    _trace_id_context.set(trace_id)


def clear_trace_id() -> None:
    """Clear the trace ID from the current context."""
    _trace_id_context.set(None)
