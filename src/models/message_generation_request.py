"""MessageGenerationRequest entity for message generation parameters."""

from typing import Literal

from pydantic import Field, field_validator

from src.models.base import BaseModel


class MessageGenerationRequest(BaseModel):
    """Request to generate IRIS error messages.

    Used by MessageGeneratorAgent to specify generation parameters.
    """

    error_category: Literal["config", "license", "resource"] = Field(
        ...,
        description="Category of error messages to generate",
    )

    count: int = Field(
        default=1,
        description="Number of messages to generate",
        ge=1,
        le=100,
    )

    severity_range: tuple[int, int] = Field(
        default=(0, 3),
        description="Minimum and maximum severity levels (inclusive)",
    )

    include_timestamps: bool = Field(
        default=True,
        description="Whether to generate sequential timestamps",
    )

    output_format: Literal["raw", "json"] = Field(
        default="raw",
        description="Output format: raw IRIS log format or JSON",
    )

    @field_validator("severity_range")
    @classmethod
    def validate_severity_range(cls, v: tuple[int, int]) -> tuple[int, int]:
        """Validate severity range is valid and ordered."""
        min_sev, max_sev = v

        if not (0 <= min_sev <= 3):
            raise ValueError(f"Minimum severity must be 0-3, got {min_sev}")
        if not (0 <= max_sev <= 3):
            raise ValueError(f"Maximum severity must be 0-3, got {max_sev}")
        if min_sev > max_sev:
            raise ValueError(
                f"Minimum severity ({min_sev}) cannot be greater than maximum ({max_sev})"
            )

        return v
