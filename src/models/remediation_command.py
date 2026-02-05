"""RemediationCommand entity for external command intake."""

from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import Field, field_validator

from src.models.base import BaseModel


class RemediationCommand(BaseModel):
    """External JSON command instructing Instance to perform remediation actions.

    Validates against contracts/remediation_command_schema.json.
    """

    command_id: UUID = Field(
        default_factory=uuid4,
        description="UUID v4 identifier for command tracking",
    )

    error_type: Literal["config", "license", "resource"] = Field(
        ...,
        description="Category of error being remediated",
    )

    severity: int = Field(
        ...,
        description="Error severity from original IRIS message",
        ge=0,
        le=3,
    )

    recommended_action: str = Field(
        ...,
        description="Human-readable description of action to take",
        min_length=1,
        max_length=200,
    )

    parameters: dict[str, Any] = Field(
        ...,
        description="Action-specific parameters (schema depends on error_type)",
    )

    requires_restart: bool = Field(
        default=False,
        description="Whether remediation requires IRIS instance restart",
    )

    execution_order: list[str] = Field(
        default_factory=list,
        description="Ordered list of tool names to execute",
    )

    dry_run: bool = Field(
        default=False,
        description="If true, validate but don't apply changes",
    )

    timeout_seconds: int = Field(
        default=60,
        description="Max execution time",
        ge=10,
        le=300,
    )

    @field_validator("execution_order")
    @classmethod
    def validate_execution_order(cls, v: list[str]) -> list[str]:
        """Validate tool names in execution order."""
        valid_tools = {"iris_config", "os_config", "iris_restart"}
        for tool_name in v:
            if tool_name not in valid_tools:
                raise ValueError(
                    f"Invalid tool name '{tool_name}'. Must be one of: {valid_tools}"
                )
        return v

    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, v: dict[str, Any], info: Any) -> dict[str, Any]:
        """Validate parameters schema based on error_type.

        Note: This is a basic validation. Full schema validation happens in
        schema_validators.py against JSON schemas.
        """
        if not v:
            raise ValueError("parameters cannot be empty")

        # Basic structure validation - full validation in schema_validators.py
        error_type = info.data.get("error_type")

        if error_type == "config":
            required = {"cpf_section", "parameter", "new_value"}
            if not required.issubset(v.keys()):
                raise ValueError(f"Config parameters missing required fields: {required}")

        elif error_type == "resource":
            required = {"kernel_param", "new_value"}
            if not required.issubset(v.keys()):
                raise ValueError(f"Resource parameters missing required fields: {required}")

        elif error_type == "license":
            required = {"action"}
            if not required.issubset(v.keys()):
                raise ValueError(f"License parameters missing required fields: {required}")

        return v
