"""Configuration management using Pydantic Settings."""

import os
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Application configuration from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key for LLM access")
    message_generator_temperature: float = Field(
        default=0.7, description="Temperature for message generation (0.0-1.0)"
    )
    message_generator_model: str = Field(default="gpt-4", description="Model for generation")
    message_classifier_model: str = Field(
        default="gpt-3.5-turbo", description="Model for classification"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Log level (DEBUG, INFO, WARNING, ERROR)")

    # IRIS Configuration
    iris_home_dir: str = Field(
        default="/usr/irissys", description="IRIS installation directory"
    )
    iris_cpf_path: str = Field(
        default="/usr/irissys/iris.cpf", description="Path to IRIS CPF file"
    )
    iris_process_name: str = Field(default="iris", description="IRIS process name")

    # External Integration
    external_endpoint_url: str = Field(
        default="http://localhost:8000/api", description="External system endpoint URL"
    )
    external_endpoint_timeout: int = Field(
        default=30, description="HTTP request timeout in seconds"
    )
    publish_retry_max_attempts: int = Field(default=3, description="Max retry attempts")
    publish_retry_backoff_factor: int = Field(
        default=2, description="Exponential backoff multiplier"
    )

    # Tool Configuration
    tool_execution_timeout: int = Field(
        default=60, ge=10, le=300, description="Tool execution timeout in seconds"
    )
    tool_dry_run_default: bool = Field(
        default=False, description="Default dry-run mode for tools"
    )

    # Transport Configuration
    transport_type: Literal["http", "file"] = Field(
        default="http", description="Transport type for message publishing"
    )
    file_transport_output_dir: str = Field(
        default="./output", description="Output directory for file transport"
    )
    file_transport_input_dir: str = Field(
        default="./input", description="Input directory for file transport"
    )

    # IRIS Restart Configuration
    iris_restart_user_wait_timeout: int = Field(
        default=60, description="Timeout waiting for active users (seconds)"
    )
    iris_restart_shutdown_timeout: int = Field(
        default=120, description="Timeout for graceful shutdown (seconds)"
    )
    iris_restart_startup_timeout: int = Field(
        default=60, description="Timeout for startup completion (seconds)"
    )


# Singleton instance
_config: Config | None = None


def get_config() -> Config:
    """Get configuration singleton instance.

    Returns:
        Config instance loaded from environment
    """
    global _config
    if _config is None:
        _config = Config()  # type: ignore
    return _config
