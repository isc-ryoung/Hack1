# Quickstart: Instance - IRIS Database Emulation & Remediation

**Purpose**: Get Instance running locally for development and testing  
**Time**: ~15 minutes  
**Prerequisites**: Python 3.11+, Git, Linux/WSL (for OS tool testing)

## Quick Setup

### 1. Clone and Setup Environment

```bash
# Clone repository
git clone https://github.com/isc-ryoung/Hack1.git
cd Hack1

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-dev.txt
```

### 2. Configure API Keys

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
echo "INSTANCE_OPENAI_API_KEY=sk-your-key-here" >> .env
echo "INSTANCE_LLM_TEMPERATURE=0.7" >> .env
echo "INSTANCE_MESSAGE_TRANSPORT=file" >> .env
echo "INSTANCE_LOG_LEVEL=INFO" >> .env
```

### 3. Verify Installation

```bash
# Run type checking
mypy src/

# Run test suite
pytest tests/ -v --cov=src --cov-report=term-missing

# Should see: >=85% coverage, all tests pass
```

---

## Usage Examples

### Generate IRIS Error Messages

```bash
# Generate a single configuration error
python -m src.cli.generate --category config --count 1

# Output:
# 02/05/26-14:23:45:123 (12345) 2 [Config.Error] Global buffer size 128MB below recommended minimum 256MB

# Generate batch of resource errors with JSON output
python -m src.cli.generate --category resource --count 5 --format json > messages.json

# View generated messages
cat messages.json
```

### Dry-Run Remediation

```bash
# Create a remediation command (JSON file)
cat > command.json <<EOF
{
  "command_id": "$(uuidgen)",
  "error_type": "config",
  "severity": 2,
  "recommended_action": "Increase global buffers to 512MB",
  "parameters": {
    "cpf_section": "config",
    "parameter": "globals",
    "new_value": "512"
  },
  "requires_restart": true,
  "execution_order": ["iris_config"],
  "dry_run": true,
  "timeout_seconds": 60
}
EOF

# Execute dry-run (validates without applying)
python -m src.cli.remediate --command command.json

# Output shows validation results and what would change
```

### Validate Message Format

```bash
# Validate generated message against reference samples
python -m src.cli.validate --message "02/05/26-14:23:45:123 (12345) 2 [Config.Error] Test message"

# Output: ✓ Valid IRIS format
# - Timestamp: ✓ Valid
# - Process ID: ✓ Valid (12345)
# - Severity: ✓ Valid (2)
# - Category: ✓ Known (Config.Error)
```

---

## Development Workflow

### Running Tests

```bash
# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests (requires Docker for some tests)
pytest tests/integration/ -v

# Contract tests (validates schemas)
pytest tests/contract/ -v

# Run with coverage
pytest --cov=src --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Type Checking

```bash
# Check all source files
mypy src/ --strict

# Check specific module
mypy src/agents/message_generator.py

# Generate type stub files
stubgen -p src.models -o stubs/
```

### Code Formatting

```bash
# Format code (ruff replaces black + isort)
ruff format src/ tests/

# Lint and auto-fix
ruff check --fix src/ tests/

# Check for issues without fixing
ruff check src/ tests/
```

---

## Project Structure Reference

```
src/
├── agents/                 # LLM-powered agents
│   ├── message_generator.py
│   ├── remediation_orchestrator.py
│   └── tool_agents.py
├── tools/                  # Deterministic remediation tools
│   ├── iris_config.py
│   ├── os_config.py
│   ├── iris_restart.py
│   ├── message_publisher.py
│   └── command_consumer.py
├── models/                 # Pydantic schemas
│   ├── iris_message.py
│   ├── remediation_command.py
│   └── tool_response.py
├── prompts/                # Version-controlled LLM prompts
│   ├── message_generation.txt
│   └── remediation_planner.txt
├── utils/                  # Shared utilities
│   ├── iris_parser.py
│   ├── trace.py
│   └── config.py
└── cli/                    # Command-line interface
    ├── generate.py
    ├── remediate.py
    └── validate.py

tests/
├── unit/                   # Fast, isolated tests
├── integration/            # Multi-component tests
└── contract/               # Schema validation tests

log_samples/                # Reference IRIS logs
└── messages.log            # 50K lines of real IRIS output
```

---

## Configuration Options

### Environment Variables

All settings can be configured via environment variables with `INSTANCE_` prefix:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `INSTANCE_OPENAI_API_KEY` | Yes | - | OpenAI API key |
| `INSTANCE_LLM_TEMPERATURE` | No | 0.7 | LLM temperature (0.0-1.0) |
| `INSTANCE_MESSAGE_TRANSPORT` | No | file | Transport type: `file`, `http` |
| `INSTANCE_EXTERNAL_ENDPOINT` | No | None | HTTP endpoint for message publishing |
| `INSTANCE_LOG_LEVEL` | No | INFO | Logging level: DEBUG, INFO, WARNING, ERROR |
| `INSTANCE_DRY_RUN_DEFAULT` | No | true | Default dry-run mode |
| `INSTANCE_TRACE_ENABLED` | No | true | Enable distributed tracing |

### Config File (config.yaml)

```yaml
llm:
  provider: openai
  model: gpt-4
  temperature: 0.7
  fallback_provider: anthropic

message_transport:
  type: http
  endpoint: https://external-system.example.com/messages
  retry_max_attempts: 3
  retry_backoff_base: 2

tools:
  iris_config:
    cpf_path: /usr/local/IRIS/iris.cpf
    backup_enabled: true
  os_config:
    require_sudo: true
    validate_min_values: true
  iris_restart:
    check_active_users: true
    startup_timeout_seconds: 120

logging:
  level: INFO
  format: json
  output: stdout
```

---

## Troubleshooting

### "Module not found: openai"
```bash
# Ensure you're in the virtual environment
source .venv/bin/activate
pip install -r requirements.txt
```

### "OpenAI API key not configured"
```bash
# Check .env file exists and has INSTANCE_OPENAI_API_KEY
cat .env | grep OPENAI
```

### "Permission denied" for OS config tool
```bash
# OS config tool requires sudo for kernel parameter changes
# Run with dry-run mode for testing without privileges
python -m src.cli.remediate --command command.json --dry-run
```

### Tests failing with "log_samples/messages.log not found"
```bash
# Ensure log_samples directory exists
ls -la log_samples/messages.log

# If missing, sample file should be in repository
git pull origin main
```

### Type checking errors with mypy
```bash
# Ensure using Python 3.11+
python --version

# Install type stubs
pip install types-aiofiles types-redis
```

---

## Next Steps

1. **Read the spec**: [spec.md](spec.md) - Full feature specification
2. **Review data models**: [data-model.md](data-model.md) - Pydantic schemas
3. **Check contracts**: [contracts/](contracts/) - JSON schemas for external integration
4. **Review plan**: [plan.md](plan.md) - Implementation strategy
5. **Start with P1**: Generate message functionality (see tasks.md when available)

---

## Development Tools

### Recommended VS Code Extensions
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Ruff (charliermarsh.ruff)
- YAML (redhat.vscode-yaml)

### Useful Commands

```bash
# Watch tests (requires pytest-watch)
ptw tests/unit/ -- -v

# Profile test performance
pytest --profile

# Generate API docs (using mkdocs)
mkdocs serve

# Run linter in watch mode
ruff check --watch src/
```

---

**Need Help?** Check [docs/](../../docs/) or file an issue on GitHub.
