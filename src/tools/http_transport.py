"""HTTP transport implementation for message publishing and command consumption."""

import asyncio
from collections.abc import AsyncIterator

import aiohttp

from src.models.exceptions import ExternalIntegrationError
from src.models.iris_message import IRISMessage
from src.models.logging import get_logger
from src.models.remediation_command import RemediationCommand
from src.models.tracing import get_current_trace_id

logger = get_logger(__name__)


class HTTPTransport:
    """HTTP REST API transport for external integration."""

    def __init__(
        self,
        endpoint_url: str,
        timeout: int = 30,
        retry_max_attempts: int = 3,
        retry_backoff_factor: int = 2,
    ) -> None:
        """Initialize HTTP transport.

        Args:
            endpoint_url: Base URL for external API
            timeout: Request timeout in seconds (default: 30)
            retry_max_attempts: Maximum retry attempts (default: 3)
            retry_backoff_factor: Exponential backoff multiplier (default: 2)
        """
        self.endpoint_url = endpoint_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.retry_max_attempts = retry_max_attempts
        self.retry_backoff_factor = retry_backoff_factor

    async def publish(self, message: IRISMessage) -> bool:
        """Publish IRIS message to external endpoint with retry logic.

        Args:
            message: IRISMessage to publish

        Returns:
            True if publish succeeded

        Raises:
            ExternalIntegrationError: If all retry attempts fail
        """
        trace_id = get_current_trace_id()
        url = f"{self.endpoint_url}/messages"

        # Convert to JSON matching contracts/iris_message_schema.json
        payload = {
            "timestamp": message.timestamp,
            "process_id": message.process_id,
            "severity": message.severity,
            "category": message.category,
            "message_text": message.message_text,
            "generated_at": message.generated_at.isoformat(),
            "trace_id": message.trace_id,
        }

        for attempt in range(1, self.retry_max_attempts + 1):
            try:
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(
                        url,
                        json=payload,
                        headers={"X-Trace-ID": trace_id},
                    ) as response:
                        if response.status in {200, 201, 202}:
                            logger.info(
                                "Published message successfully",
                                url=url,
                                status=response.status,
                                attempt=attempt,
                                severity=message.severity,
                                category=message.category,
                            )
                            return True

                        logger.warning(
                            "Publish failed with non-success status",
                            url=url,
                            status=response.status,
                            attempt=attempt,
                        )

            except asyncio.TimeoutError:
                logger.warning("Publish timeout", url=url, attempt=attempt, timeout=self.timeout)
            except aiohttp.ClientError as e:
                logger.warning("Publish client error", url=url, attempt=attempt, error=str(e))
            except Exception as e:
                logger.error("Unexpected publish error", url=url, attempt=attempt, error=str(e))

            # Exponential backoff before retry
            if attempt < self.retry_max_attempts:
                delay = self.retry_backoff_factor ** (attempt - 1)
                logger.info("Retrying after delay", delay=delay, attempt=attempt)
                await asyncio.sleep(delay)

        # All attempts failed
        raise ExternalIntegrationError(
            f"Failed to publish message after {self.retry_max_attempts} attempts",
            endpoint=url,
            trace_id=trace_id,
        )

    async def consume(self) -> AsyncIterator[RemediationCommand]:
        """Poll external endpoint for remediation commands.

        Yields:
            RemediationCommand objects from external system

        Raises:
            ExternalIntegrationError: If transport fails
        """
        trace_id = get_current_trace_id()
        url = f"{self.endpoint_url}/commands"

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(
                    url,
                    headers={"X-Trace-ID": trace_id},
                ) as response:
                    if response.status != 200:
                        raise ExternalIntegrationError(
                            f"Failed to consume commands: HTTP {response.status}",
                            endpoint=url,
                            status_code=response.status,
                            trace_id=trace_id,
                        )

                    data = await response.json()

                    # Expect array of commands
                    if not isinstance(data, list):
                        data = [data]

                    for cmd_data in data:
                        try:
                            command = RemediationCommand(**cmd_data)
                            logger.info(
                                "Consumed command",
                                command_id=str(command.command_id),
                                error_type=command.error_type,
                            )
                            yield command
                        except Exception as e:
                            logger.error(
                                "Failed to parse command", error=str(e), data=cmd_data
                            )
                            continue

        except aiohttp.ClientError as e:
            raise ExternalIntegrationError(
                f"HTTP client error while consuming commands: {e}",
                endpoint=url,
                trace_id=trace_id,
            ) from e
