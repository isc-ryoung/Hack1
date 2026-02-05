"""WorkflowTrace entity for orchestration audit trails."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from src.models.base import BaseModel
from src.models.remediation_command import RemediationCommand
from src.models.tool_result import ToolResult


class WorkflowTrace(BaseModel):
    """End-to-end audit trail for multi-step remediation workflows.

    Tracks complete execution history for orchestrated operations (US7).
    """

    initiated_at: datetime = Field(
        default_factory=lambda: datetime.now(datetime.now().astimezone().tzinfo),
        description="ISO 8601 timestamp when workflow started",
    )

    command_received: RemediationCommand = Field(
        ...,
        description="Original remediation command that triggered workflow",
    )

    steps_executed: list[ToolResult] = Field(
        default_factory=list,
        description="Array of tool results in execution order",
    )

    overall_status: Literal["success", "failure", "partial"] = Field(
        ...,
        description="Aggregate workflow status",
    )

    completion_time_ms: int = Field(
        ...,
        description="Total workflow duration in milliseconds",
        ge=0,
    )

    def add_step(self, result: ToolResult) -> None:
        """Add a tool execution result to the workflow trace.

        Args:
            result: ToolResult from completed tool execution
        """
        self.steps_executed.append(result)

    def calculate_overall_status(self) -> Literal["success", "failure", "partial"]:
        """Calculate aggregate status from all step results.

        Returns:
            success: All tools succeeded
            failure: Any tool failed
            partial: Mixed success/failure results
        """
        if not self.steps_executed:
            return "failure"

        statuses = {step.status for step in self.steps_executed}

        if statuses == {"success"}:
            return "success"
        elif "failure" in statuses:
            return "failure"
        else:
            return "partial"
