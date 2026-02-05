"""Exception hierarchy for Instance IRIS emulation system."""


class InstanceError(Exception):
    """Base exception for all Instance-related errors."""

    def __init__(self, message: str, trace_id: str | None = None) -> None:
        """Initialize exception with message and optional trace ID.

        Args:
            message: Human-readable error description
            trace_id: OpenTelemetry trace ID for correlation
        """
        super().__init__(message)
        self.message = message
        self.trace_id = trace_id

    def __str__(self) -> str:
        """Return string representation with trace ID if available."""
        if self.trace_id:
            return f"{self.message} (trace_id={self.trace_id})"
        return self.message


class ValidationError(InstanceError):
    """Raised when data validation fails."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        trace_id: str | None = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Human-readable error description
            field: Name of field that failed validation
            trace_id: OpenTelemetry trace ID for correlation
        """
        super().__init__(message, trace_id)
        self.field = field


class ToolExecutionError(InstanceError):
    """Raised when tool execution fails."""

    def __init__(
        self,
        message: str,
        tool_name: str,
        command_id: str | None = None,
        trace_id: str | None = None,
    ) -> None:
        """Initialize tool execution error.

        Args:
            message: Human-readable error description
            tool_name: Name of tool that failed
            command_id: UUID of command being executed
            trace_id: OpenTelemetry trace ID for correlation
        """
        super().__init__(message, trace_id)
        self.tool_name = tool_name
        self.command_id = command_id


class ExternalIntegrationError(InstanceError):
    """Raised when external communication fails."""

    def __init__(
        self,
        message: str,
        endpoint: str | None = None,
        status_code: int | None = None,
        trace_id: str | None = None,
    ) -> None:
        """Initialize external integration error.

        Args:
            message: Human-readable error description
            endpoint: URL or identifier of external system
            status_code: HTTP status code if applicable
            trace_id: OpenTelemetry trace ID for correlation
        """
        super().__init__(message, trace_id)
        self.endpoint = endpoint
        self.status_code = status_code
