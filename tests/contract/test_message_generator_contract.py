"""
Contract tests for MessageGeneratorAgent.

These tests verify the contract between the MessageGeneratorAgent and the OpenAI LLM:
- Prompt structure and content
- Temperature settings
- Response parsing
- Few-shot examples from log_samples/

Tests should pass even when LLM responses vary, focusing on the contract, not specific outputs.
"""

import json
import re
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.message_generator import MessageGeneratorAgent
from src.models.iris_message import IRISMessage
from src.models.message_generation_request import MessageGenerationRequest


class TestMessageGeneratorContract:
    """Contract tests for MessageGeneratorAgent LLM integration."""

    @pytest.fixture
    def sample_log_entries(self) -> list[str]:
        """Load sample IRIS log entries from log_samples/messages.log."""
        log_file = Path("log_samples/messages.log")
        if not log_file.exists():
            pytest.skip("log_samples/messages.log not found")
        
        with open(log_file, "r") as f:
            # Read first 100 lines as reference samples
            return [line.strip() for line in f.readlines()[:100] if line.strip()]

    @pytest.fixture
    def mock_openai_response(self) -> dict[str, Any]:
        """Mock OpenAI API response matching their response format."""
        return {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "created": 1677858242,
            "model": "gpt-4",
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "11/14/25-09:45:58:123 (50900) 2 [Config.InvalidParameter] "
                        "Parameter 'globals' value '128' is below minimum requirement of 256MB",
                    },
                    "finish_reason": "stop",
                    "index": 0,
                }
            ],
        }

    @pytest.fixture
    async def agent(self) -> MessageGeneratorAgent:
        """Create MessageGeneratorAgent instance for testing."""
        # Agent should be configurable with API key
        return MessageGeneratorAgent(api_key="test-key-123")

    @pytest.mark.asyncio
    async def test_prompt_structure_includes_system_message(
        self, agent: MessageGeneratorAgent, sample_log_entries: list[str]
    ) -> None:
        """Verify that prompts include a system message with IRIS format rules."""
        request = MessageGenerationRequest(
            category="config",
            count=1,
            severity_range=(2, 3),
            trace_id="a" * 32,
        )

        with patch.object(agent, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "11/14/25-09:45:58:123 (50900) 2 [Config.InvalidParameter] Test message"
            
            await agent.generate_messages(request)
            
            # Verify _call_openai was called
            assert mock_call.called
            call_args = mock_call.call_args
            
            # Extract messages argument
            messages = call_args[1].get("messages") if call_args[1] else call_args[0][0]
            
            # Verify system message exists
            system_messages = [m for m in messages if m["role"] == "system"]
            assert len(system_messages) > 0, "System message must be present in prompt"
            
            system_content = system_messages[0]["content"]
            
            # Verify system message contains format specification
            assert "MM/DD/YY-HH:MM:SS:mmm" in system_content, "Timestamp format must be specified"
            assert "PID" in system_content or "process" in system_content.lower(), "Process ID must be mentioned"
            assert "severity" in system_content.lower(), "Severity must be explained"

    @pytest.mark.asyncio
    async def test_prompt_includes_few_shot_examples(
        self, agent: MessageGeneratorAgent, sample_log_entries: list[str]
    ) -> None:
        """Verify that prompts include few-shot examples from log_samples/."""
        request = MessageGenerationRequest(
            category="config",
            count=1,
            severity_range=(2, 3),
            trace_id="a" * 32,
        )

        with patch.object(agent, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "11/14/25-09:45:58:123 (50900) 2 [Config.InvalidParameter] Test message"
            
            await agent.generate_messages(request)
            
            call_args = mock_call.call_args
            messages = call_args[1].get("messages") if call_args[1] else call_args[0][0]
            
            # Verify examples are included in user message or system message
            all_content = " ".join([m["content"] for m in messages])
            
            # Should contain examples of actual IRIS log formats
            # Look for the characteristic IRIS timestamp pattern
            iris_pattern = r"\d{2}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}:\d{3}"
            matches = re.findall(iris_pattern, all_content)
            
            assert len(matches) >= 2, "Prompt must include at least 2 few-shot examples from log_samples"

    @pytest.mark.asyncio
    async def test_temperature_is_point_seven(
        self, agent: MessageGeneratorAgent
    ) -> None:
        """Verify that LLM calls use temperature=0.7 for balanced creativity."""
        request = MessageGenerationRequest(
            category="config",
            count=1,
            severity_range=(2, 3),
            trace_id="a" * 32,
        )

        with patch.object(agent, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "11/14/25-09:45:58:123 (50900) 2 [Config.InvalidParameter] Test message"
            
            await agent.generate_messages(request)
            
            call_args = mock_call.call_args
            
            # Check if temperature is passed in kwargs
            temperature = call_args[1].get("temperature") if call_args[1] else None
            
            assert temperature is not None, "Temperature must be explicitly set"
            assert temperature == 0.7, f"Temperature must be 0.7, got {temperature}"

    @pytest.mark.asyncio
    async def test_response_parsing_extracts_iris_format(
        self, agent: MessageGeneratorAgent, mock_openai_response: dict[str, Any]
    ) -> None:
        """Verify that agent can parse LLM responses into IRISMessage objects."""
        request = MessageGenerationRequest(
            category="config",
            count=1,
            severity_range=(2, 3),
            trace_id="a" * 32,
        )

        # Mock the OpenAI client to return our mock response
        with patch("openai.AsyncOpenAI") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            
            # Setup mock response
            mock_completion = MagicMock()
            mock_completion.choices = [MagicMock()]
            mock_completion.choices[0].message.content = mock_openai_response["choices"][0]["message"]["content"]
            mock_instance.chat.completions.create = AsyncMock(return_value=mock_completion)
            
            # Create new agent with mocked client
            agent = MessageGeneratorAgent(api_key="test-key")
            messages = await agent.generate_messages(request)
            
            # Verify parsing succeeded
            assert len(messages) == 1, "Should parse one message from response"
            assert isinstance(messages[0], IRISMessage), "Should return IRISMessage object"
            
            # Verify parsed fields are correct
            msg = messages[0]
            assert msg.timestamp == "11/14/25-09:45:58:123"
            assert msg.process_id == 50900
            assert msg.severity == 2
            assert msg.category == "Config.InvalidParameter"
            assert "globals" in msg.message_text

    @pytest.mark.asyncio
    async def test_response_parsing_handles_malformed_output(
        self, agent: MessageGeneratorAgent
    ) -> None:
        """Verify that agent handles malformed LLM output gracefully."""
        request = MessageGenerationRequest(
            category="config",
            count=1,
            severity_range=(2, 3),
            trace_id="a" * 32,
        )

        # Mock the OpenAI client to return malformed response
        with patch("openai.AsyncOpenAI") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            
            # Setup mock response with invalid format
            mock_completion = MagicMock()
            mock_completion.choices = [MagicMock()]
            mock_completion.choices[0].message.content = "This is not a valid IRIS log message"
            mock_instance.chat.completions.create = AsyncMock(return_value=mock_completion)
            
            # Create new agent with mocked client
            agent = MessageGeneratorAgent(api_key="test-key")
            
            # Should raise validation error or return empty list
            with pytest.raises((ValueError, ValidationError)) or []:
                messages = await agent.generate_messages(request)
                assert len(messages) == 0, "Should return empty list for invalid format"

    @pytest.mark.asyncio
    async def test_trace_id_propagation(
        self, agent: MessageGeneratorAgent, mock_openai_response: dict[str, Any]
    ) -> None:
        """Verify that trace_id from request is propagated to generated messages."""
        trace_id = "b" * 32
        request = MessageGenerationRequest(
            category="config",
            count=1,
            severity_range=(2, 3),
            trace_id=trace_id,
        )

        with patch("openai.AsyncOpenAI") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            
            mock_completion = MagicMock()
            mock_completion.choices = [MagicMock()]
            mock_completion.choices[0].message.content = mock_openai_response["choices"][0]["message"]["content"]
            mock_instance.chat.completions.create = AsyncMock(return_value=mock_completion)
            
            agent = MessageGeneratorAgent(api_key="test-key")
            messages = await agent.generate_messages(request)
            
            assert len(messages) == 1
            assert messages[0].trace_id == trace_id, "Trace ID must be propagated from request"

    @pytest.mark.asyncio
    async def test_category_specific_prompting(
        self, agent: MessageGeneratorAgent
    ) -> None:
        """Verify that prompts are customized based on error category."""
        categories = ["config", "license", "resource"]
        
        for category in categories:
            request = MessageGenerationRequest(
                category=category,
                count=1,
                severity_range=(2, 3),
                trace_id="c" * 32,
            )

            with patch.object(agent, "_call_openai", new_callable=AsyncMock) as mock_call:
                mock_call.return_value = f"11/14/25-09:45:58:123 (50900) 2 [{category.title()}.Error] Test"
                
                await agent.generate_messages(request)
                
                call_args = mock_call.call_args
                messages = call_args[1].get("messages") if call_args[1] else call_args[0][0]
                
                # Verify category is mentioned in the prompt
                all_content = " ".join([m["content"] for m in messages]).lower()
                assert category.lower() in all_content, f"Category '{category}' must be mentioned in prompt"

    @pytest.mark.asyncio
    async def test_severity_range_enforcement(
        self, agent: MessageGeneratorAgent
    ) -> None:
        """Verify that generated messages respect requested severity range."""
        request = MessageGenerationRequest(
            category="config",
            count=1,
            severity_range=(2, 3),
            trace_id="d" * 32,
        )

        with patch("openai.AsyncOpenAI") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            
            # Generate message with severity=2 (within range)
            mock_completion = MagicMock()
            mock_completion.choices = [MagicMock()]
            mock_completion.choices[0].message.content = "11/14/25-09:45:58:123 (50900) 2 [Config.Error] Test"
            mock_instance.chat.completions.create = AsyncMock(return_value=mock_completion)
            
            agent = MessageGeneratorAgent(api_key="test-key")
            messages = await agent.generate_messages(request)
            
            assert len(messages) == 1
            assert 2 <= messages[0].severity <= 3, "Severity must be within requested range"

    @pytest.mark.asyncio
    async def test_batch_generation_count(
        self, agent: MessageGeneratorAgent
    ) -> None:
        """Verify that agent generates the requested number of messages."""
        request = MessageGenerationRequest(
            category="config",
            count=5,
            severity_range=(1, 3),
            trace_id="e" * 32,
        )

        with patch("openai.AsyncOpenAI") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            
            # Mock response for batch generation
            mock_completion = MagicMock()
            mock_completion.choices = [MagicMock()]
            mock_completion.choices[0].message.content = "\n".join([
                f"11/14/25-09:45:58:{i:03d} (50900) {i%3+1} [Config.Error] Test message {i}"
                for i in range(5)
            ])
            mock_instance.chat.completions.create = AsyncMock(return_value=mock_completion)
            
            agent = MessageGeneratorAgent(api_key="test-key")
            messages = await agent.generate_messages(request)
            
            assert len(messages) == 5, f"Should generate {request.count} messages"

    @pytest.mark.asyncio
    async def test_format_validation_against_regex(
        self, agent: MessageGeneratorAgent, mock_openai_response: dict[str, Any]
    ) -> None:
        """Verify that generated messages match IRIS format regex."""
        request = MessageGenerationRequest(
            category="config",
            count=1,
            severity_range=(2, 3),
            trace_id="f" * 32,
        )

        with patch("openai.AsyncOpenAI") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value = mock_instance
            
            mock_completion = MagicMock()
            mock_completion.choices = [MagicMock()]
            mock_completion.choices[0].message.content = mock_openai_response["choices"][0]["message"]["content"]
            mock_instance.chat.completions.create = AsyncMock(return_value=mock_completion)
            
            agent = MessageGeneratorAgent(api_key="test-key")
            messages = await agent.generate_messages(request)
            
            # IRIS format regex from data-model.md
            iris_pattern = r"^(\d{2}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}:\d{3})\s+\((\d+)\)\s+(\d)\s+\[([A-Za-z]+(?:\.[A-Za-z]+)*)\]\s+(.+)$"
            
            for msg in messages:
                # Reconstruct the original format
                formatted = f"{msg.timestamp} ({msg.process_id}) {msg.severity} [{msg.category}] {msg.message_text}"
                
                assert re.match(iris_pattern, formatted), f"Message must match IRIS format: {formatted}"


# Import ValidationError for test
try:
    from pydantic import ValidationError
except ImportError:
    ValidationError = ValueError  # Fallback for test compatibility
