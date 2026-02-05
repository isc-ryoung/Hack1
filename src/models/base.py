"""Base Pydantic model with trace ID support."""

from pydantic import BaseModel as PydanticBaseModel, Field, field_validator

from src.models.tracing import generate_trace_id


class BaseModel(PydanticBaseModel):
    """Base model for all Instance entities with automatic trace ID.

    All models inherit from this to ensure trace ID propagation
    across operations for observability (FR-021).
    """

    trace_id: str = Field(
        default_factory=generate_trace_id,
        description="OpenTelemetry format trace ID (128-bit hex)",
        min_length=32,
        max_length=32,
    )

    @field_validator("trace_id")
    @classmethod
    def validate_trace_id(cls, v: str) -> str:
        """Validate trace ID is 32-character hex string.

        Args:
            v: Trace ID value to validate

        Returns:
            Validated trace ID

        Raises:
            ValueError: If trace_id format is invalid
        """
        if len(v) != 32:
            raise ValueError(f"trace_id must be 32 characters, got {len(v)}")
        if not all(c in "0123456789abcdef" for c in v):
            raise ValueError("trace_id must contain only hexadecimal characters")
        return v

    model_config = {"extra": "forbid", "validate_assignment": True, "str_strip_whitespace": True}
