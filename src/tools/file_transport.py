"""File-based transport implementation for testing and local development."""

import json
from collections.abc import AsyncIterator
from pathlib import Path

import aiofiles

from src.models.exceptions import ExternalIntegrationError
from src.models.iris_message import IRISMessage
from src.models.logging import get_logger
from src.models.remediation_command import RemediationCommand
from src.models.tracing import get_current_trace_id

logger = get_logger(__name__)


class FileTransport:
    """File-based transport for message publishing and command consumption.

    Useful for testing without external dependencies.
    """

    def __init__(self, output_dir: str = "./output", input_dir: str = "./input") -> None:
        """Initialize file transport.

        Args:
            output_dir: Directory for published messages (default: ./output)
            input_dir: Directory for consuming commands (default: ./input)
        """
        self.output_dir = Path(output_dir)
        self.input_dir = Path(input_dir)

        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.input_dir.mkdir(parents=True, exist_ok=True)

    async def publish(self, message: IRISMessage) -> bool:
        """Write IRIS message to JSON file.

        Args:
            message: IRISMessage to publish

        Returns:
            True if write succeeded

        Raises:
            ExternalIntegrationError: If file write fails
        """
        trace_id = get_current_trace_id()

        # Use trace_id as filename for uniqueness
        filename = f"message_{message.trace_id}.json"
        filepath = self.output_dir / filename

        try:
            payload = {
                "timestamp": message.timestamp,
                "process_id": message.process_id,
                "severity": message.severity,
                "category": message.category,
                "message_text": message.message_text,
                "generated_at": message.generated_at.isoformat(),
                "trace_id": message.trace_id,
            }

            async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
                await f.write(json.dumps(payload, indent=2))

            logger.info(
                "Published message to file",
                filepath=str(filepath),
                severity=message.severity,
                category=message.category,
            )
            return True

        except Exception as e:
            raise ExternalIntegrationError(
                f"Failed to write message to file: {e}",
                endpoint=str(filepath),
                trace_id=trace_id,
            ) from e

    async def consume(self) -> AsyncIterator[RemediationCommand]:
        """Read remediation commands from JSON files in input directory.

        Yields:
            RemediationCommand objects from files

        Raises:
            ExternalIntegrationError: If file read fails
        """
        trace_id = get_current_trace_id()

        try:
            # Find all JSON files in input directory
            json_files = list(self.input_dir.glob("*.json"))

            for filepath in json_files:
                try:
                    async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
                        content = await f.read()
                        data = json.loads(content)

                    command = RemediationCommand(**data)
                    logger.info(
                        "Consumed command from file",
                        filepath=str(filepath),
                        command_id=str(command.command_id),
                        error_type=command.error_type,
                    )

                    yield command

                    # Optionally: Move processed file to archive
                    # archive_dir = self.input_dir / "processed"
                    # archive_dir.mkdir(exist_ok=True)
                    # filepath.rename(archive_dir / filepath.name)

                except Exception as e:
                    logger.error(
                        "Failed to parse command file",
                        filepath=str(filepath),
                        error=str(e),
                    )
                    continue

        except Exception as e:
            raise ExternalIntegrationError(
                f"Failed to read commands from directory: {e}",
                endpoint=str(self.input_dir),
                trace_id=trace_id,
            ) from e
