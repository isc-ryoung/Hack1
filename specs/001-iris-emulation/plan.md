# Implementation Plan: Instance - IRIS Database Emulation & Remediation System

**Branch**: `001-iris-emulation` | **Date**: 2026-02-05 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-iris-emulation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Instance is an agentic AI system that generates realistic InterSystems IRIS messages.log entries and automates remediation through intelligent agent orchestration. The system emulates IRIS database platform errors (configuration, license, resource constraints) and executes corrective actions via modular tools (IRIS config, OS config, instance restart). External integration enables bidirectional message publishing and command consumption for testing automation workflows.

## Technical Context

**Language/Version**: Python 3.11+ (required for improved error messages, performance, and type system features)  
**Primary Dependencies**: OpenAI SDK (LLM interface), Pydantic v2 (schema validation), aiohttp (async I/O), structlog (structured logging), pytest (testing)  
**Storage**: File-based (log_samples/ for reference patterns, local message queue optional), No database required  
**Testing**: pytest with coverage >=85%, mypy strict mode, contract tests for LLM I/O, integration tests for multi-agent workflows  
**Target Platform**: Linux server (Red Hat Enterprise Linux 9 to match IRIS 2025.x deployment environment)  
**Project Type**: single (command-line tools with agent orchestration, no web/mobile UI)  
**Performance Goals**: 500ms single message generation, 2s for batches of 10, p95 <5s for agent decision-making, 50 concurrent operations without degradation  
**Constraints**: <200ms p95 for tool validation (dry-run mode), 60s timeout for tool execution, 99% message delivery success rate with retry logic, zero false positives in config validation  
**Scale/Scope**: <100 messages/minute initial deployment, 7 user stories (P1-P7), 24 functional requirements, 3 tool types, 5 key entities

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Agent-First Architecture ✅ PASS
- **Requirement**: Agents are self-contained with explicit goals, tools, termination conditions
- **Assessment**: Design includes 3 agent types (Message Generator, Remediation Orchestrator, Tool Agents) with clear boundaries and explicit handoffs per FR-021 (trace IDs)
- **Status**: COMPLIANT

### II. Type Safety & Validation (NON-NEGOTIABLE) ✅ PASS
- **Requirement**: Pydantic models for all validation, mypy strict mode, runtime validation at boundaries
- **Assessment**: 5 key entities defined with Pydantic schemas (IRISMessage, RemediationCommand, ToolResult, WorkflowTrace, MessageGenerationRequest), FR-003 mandates validation against reference samples
- **Status**: COMPLIANT

### III. Test-First Development (NON-NEGOTIABLE) ✅ PASS
- **Requirement**: TDD mandatory, tests before implementation, contract tests for agents
- **Assessment**: Constitution mandates pytest with >=85% coverage, mypy strict mode, contract tests for LLM I/O, integration tests for orchestration (per constitution section "Development Workflow")
- **Status**: COMPLIANT - Must be enforced during implementation

### IV. Observability & Traceability ✅ PASS
- **Requirement**: Structured logging, unique trace IDs, prompt/response logging
- **Assessment**: FR-021 (trace IDs for all operations), FR-022 (structured JSON logging), FR-024 (PII redaction), Constitution requires logging: command → decisions → tool executions → results
- **Status**: COMPLIANT

### V. Deterministic Behavior Where Possible ✅ PASS
- **Requirement**: Explicit LLM temperature, bounded retries, deterministic fallbacks
- **Assessment**: FR-023 (exponential backoff max 3 attempts), FR-018 (60s timeout), Constitution mandates temperature 0.0 for production, configurable random seeds
- **Status**: COMPLIANT

### VI. Tool Modularity & Composability ✅ PASS
- **Requirement**: Tools are standalone, framework-agnostic, with clear I/O types
- **Assessment**: 6 tools defined (IRIS config, OS config, restart, message gen, publisher, command parser), FR-017 (dry-run mode for all), FR-016 (rollback capability), Constitution mandates <100 word descriptions
- **Status**: COMPLIANT

### VII. Simplicity & YAGNI ✅ PASS
- **Requirement**: Start simple, prefer single-agent solutions, justify complexity
- **Assessment**: Progressive complexity P1→P7, single-agent for message generation (P1), multi-agent only for orchestration (P7) after individual tools proven, no premature frameworks
- **Status**: COMPLIANT

### IRIS-Specific Constraints ✅ PASS
- **Message Format**: FR-001 mandates exact IRIS format `MM/DD/YY-HH:MM:SS:mmm (PID) SEVERITY [CATEGORY] Message`, validated against log_samples/
- **Tool Safety**: FR-009/011 (validate before apply), FR-013 (check active users), FR-016 (rollback on failure), FR-017 (dry-run mode)
- **External Integration**: FR-006 (async non-blocking), FR-023 (retry with backoff), FR-008 (schema validation)
- **Status**: COMPLIANT

### Overall Gate Status: ✅ PASS - Proceed to Phase 0 Research

No constitutional violations detected. All 7 core principles and IRIS-specific constraints are addressed in requirements.

## Project Structure

### Documentation (this feature)

```text
specs/001-iris-emulation/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── iris_message_schema.json
│   ├── remediation_command_schema.json
│   └── tool_response_schema.json
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── agents/
│   ├── message_generator.py      # P1: Generate IRIS log entries (LLM-based)
│   ├── remediation_orchestrator.py  # P7: Multi-step workflow coordination
│   └── tool_agents.py             # P4-P6: Tool execution agents
├── tools/
│   ├── iris_config.py             # P4: CPF configuration modifications
│   ├── os_config.py               # P5: Kernel parameter adjustments
│   ├── iris_restart.py            # P6: Graceful shutdown/startup
│   ├── message_publisher.py       # P2: External message output
│   └── command_consumer.py        # P3: JSON command input
├── models/
│   ├── iris_message.py            # Pydantic schema for messages.log entries
│   ├── remediation_command.py     # Pydantic schema for external commands
│   ├── tool_response.py           # Standardized tool output format
│   ├── workflow_trace.py          # End-to-end audit trail
│   └── message_request.py         # Message generation request schema
├── prompts/
│   ├── message_generation.txt     # System prompt for error message creation
│   ├── remediation_planner.txt    # System prompt for command interpretation
│   └── error_templates/           # Few-shot examples by category
│       ├── config_errors.txt
│       ├── license_errors.txt
│       └── resource_errors.txt
├── utils/
│   ├── iris_parser.py             # Parse messages.log format
│   ├── trace.py                   # Distributed tracing helpers
│   ├── validation.py              # Shared validation logic
│   └── config.py                  # Configuration management
└── cli/
    ├── generate.py                # CLI for message generation
    ├── remediate.py               # CLI for remediation workflows
    └── validate.py                # CLI for dry-run mode

tests/
├── unit/
│   ├── test_message_generator.py
│   ├── test_iris_parser.py
│   ├── test_tools.py
│   ├── test_schemas.py
│   └── test_validation.py
├── integration/
│   ├── test_remediation_flow.py   # End-to-end workflows
│   ├── test_message_pipeline.py   # Generate → publish flow
│   └── test_orchestration.py      # Multi-tool coordination
└── contract/
    ├── test_iris_message_format.py  # Validate against log_samples/
    ├── test_external_api.py          # External integration contracts
    └── test_llm_responses.py         # Mock LLM I/O contracts

log_samples/
└── messages.log                   # Reference IRIS log samples (50K lines)

.specify/
├── memory/
│   └── constitution.md            # Project governance (v1.1.0)
├── templates/
└── scripts/
```

**Structure Decision**: Single project structure selected (Option 1). This is a command-line tool with agent orchestration - no web frontend or mobile app required. All code lives under `src/` with clear separation: agents (LLM-powered logic), tools (deterministic actions), models (Pydantic schemas), prompts (version-controlled templates), utils (shared helpers), and cli (user interface).

The structure follows the constitution's mandated layout with explicit directories for agent implementations, tools, models, and prompts. Testing mirrors source structure with unit/integration/contract separation.

## Complexity Tracking

**No constitutional violations detected - all complexity justified**

This section is intentionally empty. The design passes all constitutional gates without requiring complexity justification. The system follows YAGNI principles with:
- Single-agent solutions for P1-P6 (no premature orchestration)
- Multi-agent orchestration only in P7 after individual components proven
- No unnecessary frameworks (stdlib + targeted libraries)
- Progressive complexity matching priority order (P1→P7)

## Post-Design Constitution Re-Check

*GATE: Final validation after Phase 1 design complete*

### Re-Evaluation Summary: ✅ ALL GATES PASS

**Phase 1 Artifacts Reviewed**:
- `research.md`: Technology choices documented with rationale
- `data-model.md`: 5 Pydantic models with validation rules
- `contracts/`: 3 JSON schemas for external integration
- `quickstart.md`: Local development setup guide

**Design Changes from Phase 0**: None - technical context was complete

**New Compliance Checks**:
1. **Type Safety**: All 5 entities use Pydantic v2 with strict validation ✅
2. **Tool Modularity**: 6 tools designed as standalone functions with Protocol interfaces ✅
3. **Observability**: OpenTelemetry trace IDs propagated through all entities ✅
4. **Deterministic Behavior**: LLM temperature configurable (default 0.7), exponential backoff implemented ✅
5. **Simplicity**: No frameworks beyond targeted libraries (OpenAI SDK, aiohttp, structlog) ✅

**Constitutional Compliance**: 100% - Ready for Phase 2 (tasks generation)

---

## Phase 2 Next Steps

**Command**: Run `/speckit.tasks` to generate implementation task list

**Prerequisites Complete**:
- ✅ Specification validated ([spec.md](spec.md))
- ✅ Technical research complete ([research.md](research.md))
- ✅ Data models designed ([data-model.md](data-model.md))
- ✅ API contracts defined ([contracts/](contracts/))
- ✅ Local development guide created ([quickstart.md](quickstart.md))
- ✅ Agent context updated ([.github/agents/copilot-instructions.md](../../.github/agents/copilot-instructions.md))

**Ready for Implementation**: Task breakdown will organize work by user story (P1-P7) enabling incremental delivery.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
