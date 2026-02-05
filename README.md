# Instance - IRIS Database Emulation & Remediation System

An agentic AI system that generates realistic InterSystems IRIS messages.log entries and automates remediation through intelligent agent orchestration.

## Features

- **P1 - Message Generation**: Generate authentic IRIS error messages (config, license, resource constraints)
- **P2 - External Publishing**: Send messages to external consumers via JSON API
- **P3 - Command Consumption**: Receive and validate remediation commands from external systems
- **P4 - IRIS Configuration**: Automated CPF configuration changes with validation
- **P5 - OS Configuration**: Kernel parameter adjustments for IRIS optimization
- **P6 - IRIS Restarts**: Graceful instance restarts with safety checks
- **P7 - Workflow Orchestration**: Multi-step remediation coordination

## Requirements

- Python 3.11+
- OpenAI API key
- InterSystems IRIS installation (for production use)

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Setup pre-commit hooks
pre-commit install

# Copy environment template
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Generate IRIS Messages

```bash
# Generate a single configuration error message
instance generate --category config --count 1 --severity 2

# Generate 10 license-related warnings
instance generate --category license --count 10 --severity 1-2

# Generate messages and save as JSON
instance generate --category resource --count 5 --output json
```

### 3. Publish Messages to External System

```bash
# Generate and publish messages
instance generate --category config --count 5 --publish

# Configure external endpoint in .env:
# EXTERNAL_ENDPOINT_URL=http://your-system.com/api/messages
```

### 4. Consume Remediation Commands

```bash
# Poll for commands from external system
instance consume --source http://your-system.com/api/commands --interval 5s

# Process commands from file
instance consume --source file://./commands/ --interval 10s
```

### 5. Execute Remediation (Dry-Run)

```bash
# Validate IRIS config change without applying
instance orchestrate --command-file examples/config_change.json --dry-run

# Validate OS configuration change
instance orchestrate --command-file examples/os_change.json --dry-run
```

### 6. Multi-Step Workflow (with restart)

```bash
# Execute config change + restart workflow
instance orchestrate --command-file examples/config_with_restart.json

# Note: Requires appropriate permissions for IRIS operations
```

## Development

### Run Tests

```bash
# Run all tests with coverage
pytest

# Run specific test module
pytest tests/unit/test_iris_message_parser.py

# Run integration tests only
pytest tests/integration/

# Run with verbose output
pytest -v
```

### Type Checking

```bash
# Run mypy strict type checking
mypy src/
```

### Code Formatting

```bash
# Format code with black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Run all pre-commit hooks
pre-commit run --all-files
```

## Configuration

All configuration is managed through environment variables (see `.env.example`) or YAML configuration file:

```yaml
# config.yaml
openai:
  api_key: ${OPENAI_API_KEY}
  temperature: 0.7
  model: gpt-4

iris:
  home_dir: /usr/irissys
  cpf_path: /usr/irissys/iris.cpf
  process_name: iris

logging:
  level: INFO
  format: json
```

## Architecture

```
src/
├── agents/          # AI agents (message generator, orchestrator)
├── tools/           # Remediation tools (IRIS config, OS config, restart)
├── models/          # Pydantic data models and validation
├── prompts/         # LLM prompt templates
└── cli/             # Command-line interface

tests/
├── unit/            # Unit tests
├── integration/     # Integration tests
└── contract/        # Contract tests for LLM interactions
```

## Documentation

- [Feature Specification](specs/001-iris-emulation/spec.md)
- [Implementation Plan](specs/001-iris-emulation/plan.md)
- [Data Model](specs/001-iris-emulation/data-model.md)
- [API Contracts](specs/001-iris-emulation/contracts/)
- [Task Breakdown](specs/001-iris-emulation/tasks.md)

## Safety & Compliance

- **Type Safety**: 100% mypy strict mode compliance
- **Test Coverage**: >=85% code coverage requirement
- **TDD**: Tests written before implementation
- **Observability**: OpenTelemetry trace IDs on all operations
- **PII Redaction**: Sensitive data automatically redacted from logs
- **Dry-Run Mode**: All tools support validation without applying changes

## License

MIT
