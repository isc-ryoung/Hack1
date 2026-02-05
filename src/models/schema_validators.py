"""JSON schema validators for external contracts."""

import json
from pathlib import Path
from typing import Any

from src.models.exceptions import ValidationError
from src.models.logging import get_logger

logger = get_logger(__name__)

# Load JSON schemas from contracts/ directory
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "specs" / "001-iris-emulation" / "contracts"


def load_schema(schema_name: str) -> dict[str, Any]:
    """Load JSON schema from contracts directory.

    Args:
        schema_name: Name of schema file (e.g., "iris_message_schema.json")

    Returns:
        Loaded JSON schema dictionary

    Raises:
        FileNotFoundError: If schema file doesn't exist
    """
    schema_path = CONTRACTS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Load schemas at module import time
try:
    IRIS_MESSAGE_SCHEMA = load_schema("iris_message_schema.json")
    REMEDIATION_COMMAND_SCHEMA = load_schema("remediation_command_schema.json")
    TOOL_RESPONSE_SCHEMA = load_schema("tool_response_schema.json")
except FileNotFoundError as e:
    logger.warning(f"Could not load schema: {e}")
    # Schemas will be None if files don't exist yet
    IRIS_MESSAGE_SCHEMA = None
    REMEDIATION_COMMAND_SCHEMA = None
    TOOL_RESPONSE_SCHEMA = None


def validate_iris_message(data: dict[str, Any], trace_id: str | None = None) -> None:
    """Validate data against iris_message_schema.json.

    Args:
        data: Dictionary to validate
        trace_id: Optional trace ID for error context

    Raises:
        ValidationError: If validation fails
    """
    if IRIS_MESSAGE_SCHEMA is None:
        logger.warning("IRIS message schema not loaded, skipping validation")
        return

    try:
        # Basic validation - full JSON Schema validation would use jsonschema library
        required_fields = IRIS_MESSAGE_SCHEMA.get("required", [])
        for field in required_fields:
            if field not in data:
                raise ValidationError(
                    f"Missing required field: {field}",
                    field=field,
                    trace_id=trace_id,
                )
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(
            f"Schema validation error: {e}",
            trace_id=trace_id,
        ) from e


def validate_remediation_command(data: dict[str, Any], trace_id: str | None = None) -> None:
    """Validate data against remediation_command_schema.json.

    Args:
        data: Dictionary to validate
        trace_id: Optional trace ID for error context

    Raises:
        ValidationError: If validation fails
    """
    if REMEDIATION_COMMAND_SCHEMA is None:
        logger.warning("Remediation command schema not loaded, skipping validation")
        return

    try:
        required_fields = REMEDIATION_COMMAND_SCHEMA.get("required", [])
        for field in required_fields:
            if field not in data:
                raise ValidationError(
                    f"Missing required field: {field}",
                    field=field,
                    trace_id=trace_id,
                )

        # Validate error_type enum
        error_type = data.get("error_type")
        valid_error_types = {"config", "license", "resource"}
        if error_type not in valid_error_types:
            raise ValidationError(
                f"Invalid error_type: {error_type}. Must be one of {valid_error_types}",
                field="error_type",
                trace_id=trace_id,
            )

    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(
            f"Schema validation error: {e}",
            trace_id=trace_id,
        ) from e


def validate_tool_response(data: dict[str, Any], trace_id: str | None = None) -> None:
    """Validate data against tool_response_schema.json.

    Args:
        data: Dictionary to validate
        trace_id: Optional trace ID for error context

    Raises:
        ValidationError: If validation fails
    """
    if TOOL_RESPONSE_SCHEMA is None:
        logger.warning("Tool response schema not loaded, skipping validation")
        return

    try:
        required_fields = TOOL_RESPONSE_SCHEMA.get("required", [])
        for field in required_fields:
            if field not in data:
                raise ValidationError(
                    f"Missing required field: {field}",
                    field=field,
                    trace_id=trace_id,
                )

        # Validate status + error_message consistency
        status = data.get("status")
        error_message = data.get("error_message")

        if status == "failure" and not error_message:
            raise ValidationError(
                "error_message is required when status=failure",
                field="error_message",
                trace_id=trace_id,
            )

    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(
            f"Schema validation error: {e}",
            trace_id=trace_id,
        ) from e
