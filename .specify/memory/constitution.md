<!--
SYNC IMPACT REPORT - Constitution Update
Version: 0.0.0 → 1.0.0 → 1.1.0
Date: 2026-02-05

CHANGES:
- Initial constitution creation for Python Agentic AI project (v1.0.0)
- Updated for Instance project: IRIS database emulation system (v1.1.0)
- Added domain-specific context for IRIS message.log emulation
- Added IRIS-specific tools and constraints (config, OS, restart)
- Added external message consumption/production requirements
- Added multi-agent orchestration patterns for remediation workflows

TEMPLATES REQUIRING UPDATES:
✅ plan-template.md - "Constitution Check" gate already generic
✅ spec-template.md - Requirement structure aligns with principles
✅ tasks-template.md - Task categorization supports agent development patterns

FOLLOW-UP ITEMS:
- Define IRIS message.log format schemas in src/models/
- Create sample JSON remediation command schemas
- Document agent orchestration patterns for multi-tool workflows
-->

# Instance: IRIS Database Emulation & Remediation Constitution

## Project Overview

**Instance** is an agentic AI system that emulates InterSystems IRIS database platform behavior for testing and remediation automation. The system consists of:

1. **Message Generation Agents**: Generate realistic IRIS messages.log entries simulating system errors (configuration issues, license problems, resource constraints)
2. **Message Consumption Agents**: Parse external JSON remediation commands and orchestrate corrective actions
3. **Remediation Tools**: Modular tools for IRIS configuration changes, OS reconfiguration, and instance restarts
4. **External Interfaces**: Message publishing to external consumers and command consumption from external systems

**Domain Context**: InterSystems IRIS is an enterprise database platform. The messages.log file contains timestamped system events, errors, and warnings. Sample log format:
```
11/14/25-09:45:55:657 (50745) 0 [Generic.Event] Allocated 504MB shared memory
11/14/25-09:45:57:762 (50803) 2 [Generic.Event] Kerberos authentication unavailable
```

## Core Principles

### I. Agent-First Architecture

Every feature MUST be designed as an autonomous agent capability with clear boundaries:

- Agents are self-contained units with defined input/output contracts
- Each agent MUST have explicit goals, tools, and termination conditions
- Agent state MUST be traceable and reproducible
- Agents MUST fail gracefully with actionable error messages
- No implicit dependencies between agents without explicit orchestration

**Instance-Specific Requirements**:
- **Message Generator Agent**: Produces IRIS-format log entries based on error categories (config/license/resource)
- **Remediation Orchestrator Agent**: Parses JSON commands and delegates to appropriate tools
- **Tool Agents**: Each remediation tool (IRIS config, OS config, restart) operates independently
- Agent handoffs MUST be explicit with validation at boundaries

**Rationale**: IRIS remediation workflows require coordinated multi-agent responses. Clear boundaries prevent cascading failures when one remediation step fails.

### II. Type Safety & Validation (NON-NEGOTIABLE)

Static typing MUST be enforced throughout the codebase:

- All functions, methods, and classes MUST have complete type annotations
- Pydantic models MUST be used for all data validation and LLM I/O
- mypy strict mode MUST pass with zero errors
- Runtime validation MUST occur at agent boundaries
- Schema definitions MUST be version-controlled and documented

**Instance-Specific Requirements**:
- IRIS message.log entries MUST have validated schemas (timestamp, process ID, severity, category, message)
- External JSON commands MUST be validated before agent execution
- Tool outputs MUST conform to structured response schemas
- Reference sample: `log_samples/messages.log` for schema validation

**Rationale**: IRIS systems are mission-critical. Malformed commands or messages could cause data loss or system instability. Strict validation is mandatory.

### III. Test-First Development (NON-NEGOTIABLE)

TDD is mandatory for all agent capabilities:

- Unit tests written → User approved → Tests fail → Then implement
- Each agent MUST have contract tests defining expected behavior
- Mock LLM responses for deterministic unit testing
- Integration tests MUST cover agent orchestration paths
- Red-Green-Refactor cycle strictly enforced

**Rationale**: Agentic AI behavior is non-deterministic by nature. Comprehensive testing creates guardrails that prevent regression and ensure agents operate within acceptable boundaries.

### IV. Observability & Traceability

All agent actions MUST be observable and debuggable:

- Structured logging (JSON) required for all agent decisions and tool calls
- Each agent execution MUST have a unique trace ID
- Prompts, LLM responses, and tool outputs MUST be logged
- Token usage and latency MUST be tracked per agent interaction
- Logging MUST support filtering by agent, trace, user, and timestamp

**Instance-Specific Requirements**:
- Generated IRIS messages MUST be logged with generation context (agent, parameters, timestamp)
- Remediation workflows MUST log: incoming JSON command → agent decisions → tool executions → results
- Tool failures MUST include IRIS error context for debugging
- External message publish/consume events MUST be traceable to source agents

**Rationale**: Debugging IRIS remediation requires correlating generated errors, external commands, and tool executions. Full traceability prevents lost context in multi-agent workflows.

### V. Deterministic Behavior Where Possible

Minimize non-determinism through architectural choices:

- LLM temperature MUST be explicitly configured (prefer 0.0 for production)
- Random seeds MUST be configurable for reproducible testing
- Agent retry logic MUST have bounded attempts with exponential backoff
- Fallback strategies MUST be deterministic (no cascading LLM calls)
- Configuration MUST be explicit (no environment-dependent defaults)

**Rationale**: While LLMs are inherently stochastic, system-level determinism makes debugging tractable and builds user trust.

### VI. Tool Modularity & Composability

Agent tools MUST be reusable, testable components:

- Each tool MUST be a standalone function with clear input/output types
- Tools MUST be framework-agnostic (no tight coupling to LangChain/LlamaIndex)
- Tool descriptions MUST be concise and optimized for LLM consumption (<100 words)
- Tools MUST validate inputs and return structured errors
- Tool composition MUST be explicit (no hidden dependencies)

**Instance-Specific Tools**:
1. **IRIS Configuration Tool**: Modify CPF settings, validate syntax, report success/failure
2. **OS Configuration Tool**: Adjust memory limits, CPU affinity, kernel parameters
3. **IRIS Restart Tool**: Graceful shutdown, startup validation, health checks
4. **Message Generation Tool**: Create realistic IRIS log entries from error templates
5. **Message Publisher Tool**: Send generated messages to external consumers
6. **Command Parser Tool**: Validate and parse incoming JSON remediation commands

**Tool Safety Requirements**:
- Configuration changes MUST validate before applying (no blind writes)
- Restart tool MUST check for active transactions before shutdown
- All tools MUST support dry-run mode for testing

**Rationale**: IRIS remediation tools interact with production-like systems. Isolated, testable tools prevent cascading failures and enable safe testing.

### VII. Simplicity & YAGNI

Start with the simplest solution that works:

- Prefer single-agent solutions over multi-agent orchestration
- Use structured output over function calling when sufficient
- Avoid premature abstraction (no frameworks for <3 use cases)
- Question every dependency: does this solve a real problem today?
- Complexity MUST be justified in writing before implementation

**Rationale**: Agentic AI introduces inherent complexity. Every additional abstraction multiplies debugging difficulty. Fight complexity at every layer.

## Python Standards

**Language**: Python 3.11+ (for improved error messages and performance)

**Core Dependencies**:
- OpenAI Python SDK (primary LLM interface)
- Pydantic v2 (data validation and schema generation)
- Anthropic SDK (if using Claude models)
- pytest (testing framework)
- structlog (structured logging)
- aiohttp (async external message I/O)
- redis / kafka-python (optional: message queue for external integration)

**Code Quality**:
- Formatting: ruff (replaces black + isort + flake8)
- Type checking: mypy with strict mode
- Testing: pytest with coverage >= 85%
- Docstrings: Google style for all public APIs

**Instance Project Structure**:
```
src/
├── agents/
│   ├── message_generator.py    # IRIS log message generation
│   ├── remediation_orchestrator.py  # Command parsing & delegation
│   └── tool_agents.py          # Individual tool execution agents
├── tools/
│   ├── iris_config.py          # IRIS configuration modifications
│   ├── os_config.py            # OS-level changes
│   ├── iris_restart.py         # Instance restart logic
│   ├── message_publisher.py    # External message output
│   └── command_consumer.py     # External JSON command input
├── models/
│   ├── iris_message.py         # messages.log entry schema
│   ├── remediation_command.py  # External command schema
│   └── tool_response.py        # Standardized tool output
├── prompts/
│   ├── message_generation.txt  # Error message generation prompts
│   └── remediation_planner.txt # Command interpretation prompts
└── utils/
    ├── iris_parser.py          # messages.log parsing utilities
    └── trace.py                # Distributed tracing helpers

tests/
├── unit/
│   ├── test_message_generator.py
│   ├── test_tools.py
│   └── test_schemas.py
├── integration/
│   ├── test_remediation_flow.py
│   └── test_message_pipeline.py
└── contract/
    ├── test_iris_message_format.py
    └── test_external_api.py

log_samples/
└── messages.log               # Reference IRIS log samples
```

## AI-Specific Constraints

**Prompt Engineering**:
- All prompts MUST be version-controlled in `src/prompts/`
- System prompts MUST NOT exceed 2000 tokens
- Few-shot examples MUST be validated against real `log_samples/messages.log` entries
- Prompt changes MUST be tested with representative IRIS error scenarios

**Safety & Security**:
- Input validation MUST sanitize user content before LLM consumption
- Agent outputs MUST be validated before execution (no blind eval)
- Rate limiting MUST be enforced (per-user and per-agent)
- PII MUST be redacted from logs and LLM calls
- Prompt injection defenses MUST be documented per agent
- **CRITICAL**: External JSON commands MUST be validated before tool execution (prevent malicious config changes)

**Cost & Performance**:
- Token budgets MUST be defined per agent (enforce limits)
- Caching MUST be used for repeated LLM calls (semantic caching)
- Model selection MUST be justified (GPT-4 vs GPT-3.5 tradeoffs)
- Latency targets: p95 < 5s for user-facing agents

## IRIS-Specific Constraints

**Message Generation**:
- Generated messages MUST conform to IRIS format: `MM/DD/YY-HH:MM:SS:mmm (PID) SEVERITY [CATEGORY] Message`
- Severity levels: 0 (Info), 1 (Warning), 2 (Error), 3 (Severe)
- Common categories: Generic.Event, Database.*, WriteDaemon.*, Crypto.*, Utility.Event
- Error templates MUST be derived from real `log_samples/messages.log` patterns
- Timestamps MUST follow IRIS conventions (no ISO 8601)

**Remediation Commands**:
- External JSON MUST include: `error_type`, `severity`, `recommended_action`, `parameters`
- Commands MUST specify restart requirement: `requires_restart: bool`
- Multi-step remediations MUST define execution order
- Tool selection MUST be deterministic based on error category

**Tool Execution Safety**:
- IRIS configuration changes MUST validate CPF syntax before applying
- OS changes MUST check current values and log diffs
- Restart tool MUST verify no active users before shutdown
- All tools MUST support rollback on failure
- Tool execution MUST timeout after 60s (prevent hanging)

**External Integration**:
- Message publishing MUST use async I/O (non-blocking)
- External consumers MUST receive JSON with schema version
- Command consumption MUST handle malformed JSON gracefully
- Network failures MUST trigger exponential backoff (max 3 retries)

## Development Workflow

**Feature Development**:
1. Specification MUST define agent goals, tools, and success criteria
2. Contract tests MUST be written and approved before implementation
3. Prompts MUST be prototyped in playground before coding
4. IRIS message schemas MUST be validated against `log_samples/messages.log`
5. Tool implementations MUST include dry-run mode for testing
6. Implementation MUST pass mypy strict + 85% coverage
7. Integration tests MUST validate full remediation workflows (message → command → tool → result)

**Code Review Requirements**:
- All PRs MUST include test coverage for new agent capabilities
- Prompt changes MUST include before/after examples with real IRIS log patterns
- New tools MUST include usage documentation + safety considerations
- Tool changes MUST include dry-run test results
- Message generation changes MUST validate against `log_samples/` reference
- External integration changes MUST include schema migration plan
- Performance impact MUST be measured for agent changes

**Quality Gates**:
- `ruff check` and `mypy --strict` MUST pass
- All tests MUST pass with mocked LLM responses
- Integration tests MUST pass with real LLM (run on CI)
- Documentation MUST be updated for user-facing changes

## Governance

This constitution supersedes all other development practices. When conflicts arise, constitution principles take precedence.

**Amendment Process**:
1. Proposed changes MUST be documented with rationale
2. Changes MUST include migration plan for existing code
3. Team approval required before adoption
4. Version bump according to semantic versioning:
   - MAJOR: Backward incompatible principle changes
   - MINOR: New principles or sections added
   - PATCH: Clarifications and refinements

**Compliance**:
- All pull requests MUST verify constitution alignment
- Complexity introductions MUST be justified in writing
- Regular audits ensure ongoing compliance

**Version**: 1.1.0 | **Ratified**: 2026-02-05 | **Last Amended**: 2026-02-05
