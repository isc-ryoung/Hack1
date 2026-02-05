"""Protocol definitions for transport abstractions."""

from collections.abc import AsyncIterator
from typing import Protocol

from src.models.iris_message import IRISMessage
from src.models.remediation_command import RemediationCommand


class MessageTransport(Protocol):
    """Protocol for message publishing and command consumption transports.

    Implementations: HTTP REST API, file-based, message queue, etc.
    """

    async def publish(self, message: IRISMessage) -> bool:
        """Publish IRIS message to external consumer.

        Args:
            message: IRISMessage to publish

        Returns:
            True if publish succeeded, False otherwise

        Raises:
            ExternalIntegrationError: If transport fails after retries
        """
        ...

    async def consume(self) -> AsyncIterator[RemediationCommand]:
        """Consume remediation commands from external source.

        Yields:
            RemediationCommand objects from external system

        Raises:
            ExternalIntegrationError: If transport fails
        """
        ...
