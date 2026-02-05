"""ToolResult entity for tool execution outcomes."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel as PydanticBaseModel, Field, field_validator

from src.models.base import BaseModel


class ChangeDetail(PydanticBaseModel):
    """Details of a single parameter change."""

    parameter: str = Field(..., description="Parameter name")
    old_value: str | int | None = Field(
        ..., description="Previous value (null if new parameter)"
    )
    new_value: str | int = Field(..., description="New value after change")
    validated: bool = Field(..., description="Whether change was validated before application")


class ToolResult(BaseModel):
    """Outcome of a single tool execution.

    Validates against contracts/tool_response_schema.json.
    """

    tool_name: Literal[
        "iris_config", "os_config", "iris_restart", "message_publisher", "command_consumer"
    ] = Field(..., description="Name of tool executed")

    command_id: UUID = Field(
        ...,
        description="UUID linking to originating RemediationCommand",
    )

    status: Literal["success", "failure", "partial"] = Field(
        ...,
        description="Execution outcome: success=all completed, failure=failed, partial=mixed",
    )

    execution_time_ms: int = Field(
        ...,
        description="Duration in milliseconds",
        ge=0,
        le=60000,
    )

    changes_applied: dict[str, ChangeDetail] = Field(
        default_factory=dict,
        description="Map of parameter name to change details",
    )

    error_message: str | None = Field(
        default=None,
        description="Error details if status=failure (required for failure, null otherwise)",
        max_length=500,
    )

    requires_user_action: bool = Field(
        default=False,
        description="True if manual intervention needed",
    )

    rollback_available: bool = Field(
        default=False,
        description="True if changes can be reverted",
    )

    @field_validator("error_message")
    @classmethod
    def validate_error_message(cls, v: str | None, info: Any) -> str | None:
        """Validate error_message is required when status=failure."""
        status = info.data.get("status")
        if status == "failure" and not v:
            raise ValueError("error_message is required when status=failure")
        if status != "failure" and v:
            raise ValueError("error_message must be null when status is not failure")
        return v


from typing import Any  # noqa: E402 (import at end to avoid circular dependency in validator)
