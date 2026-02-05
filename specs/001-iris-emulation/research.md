# Research: Instance - IRIS Database Emulation & Remediation

**Phase**: 0 (Outline & Research)  
**Date**: 2026-02-05  
**Purpose**: Resolve all NEEDS CLARIFICATION items from Technical Context and document technology choices

## Research Tasks Completed

### 1. IRIS Message Format Analysis

**Decision**: Use regex-based parsing with Pydantic validation for IRIS messages.log format

**Rationale**:
- IRIS format is well-defined: `MM/DD/YY-HH:MM:SS:mmm (PID) SEVERITY [CATEGORY] Message`
- Sample `log_samples/messages.log` contains 50K lines of real patterns
- No need for complex NLP - deterministic parsing sufficient

**Alternatives Considered**:
- **LLM-based parsing**: Rejected - adds latency, non-determinism, cost for a solved problem
- **Hand-rolled parsing**: Rejected - regex with named groups provides clarity and maintainability
- **Generic log parsers (e.g., Logstash)**: Rejected - overkill for single format, adds dependency

**Implementation Approach**:
```python
# Pattern for IRIS message format
IRIS_MESSAGE_PATTERN = re.compile(
    r'(?P<timestamp>\d{2}/\d{2}/\d{2}-\d{2}:\d{2}:\d{2}:\d{3})\s+'
    r'\((?P<pid>\d+)\)\s+'
    r'(?P<severity>\d)\s+'
    r'\[(?P<category>[\w.]+)\]\s+'
    r'(?P<message>.*)'
)
```

### 2. LLM Integration for Message Generation

**Decision**: Use OpenAI GPT-4 with temperature=0.7 for message generation, GPT-3.5-turbo for classification

**Rationale**:
- GPT-4 better at generating realistic technical content matching IRIS style
- Temperature 0.7 balances creativity (varied errors) with consistency (format adherence)
- GPT-3.5-turbo sufficient for error type classification (cheaper, faster)
- Few-shot prompting with real examples from `log_samples/` ensures format compliance

**Alternatives Considered**:
- **Claude (Anthropic)**: Rejected initially - GPT-4 has more training data on system logs, but keep as backup
- **Temperature 0.0**: Rejected - produces repetitive messages, defeats emulation purpose
- **Temperature 1.0**: Rejected - too creative, risks format violations
- **Fine-tuned model**: Rejected - premature optimization, few-shot sufficient for MVP

**Cost Analysis**:
- GPT-4 message generation: ~500 tokens/call = $0.015/message
- Target: <100 messages/minute = ~$90/hour worst case
- Acceptable for testing workloads, can optimize later with caching

### 3. External Integration Transport

**Decision**: Use pluggable transport abstraction with initial implementations for HTTP REST API and file export

**Rationale**:
- Spec says "cannot rely on specific message queue technology"
- Interface-based design allows swapping transports without agent changes
- HTTP REST most common for external systems
- File export enables testing without external dependencies

**Alternatives Considered**:
- **Kafka**: Rejected - heavy dependency, over-engineered for initial deployment
- **Redis Pub/Sub**: Rejected - requires Redis installation, adds ops complexity
- **RabbitMQ**: Rejected - same issues as Kafka
- **WebSockets**: Rejected - requires persistent connections, complicated retry logic

**Interface Design**:
```python
class MessageTransport(Protocol):
    async def publish(self, message: IRISMessage) -> bool:
        """Publish message to external consumer. Returns success."""
        ...
    
    async def consume(self) -> AsyncIterator[RemediationCommand]:
        """Consume remediation commands from external source."""
        ...
```

### 4. Async I/O Framework

**Decision**: Use `asyncio` with `aiohttp` for HTTP and `aiofiles` for file I/O

**Rationale**:
- FR-006 mandates async non-blocking message publishing
- `asyncio` is Python stdlib, no additional framework needed
- `aiohttp` is mature, well-maintained, supports retry logic
- Enables 50 concurrent operations (SC-010) without thread overhead

**Alternatives Considered**:
- **Trio**: Rejected - less ecosystem support, learning curve
- **Twisted**: Rejected - legacy, complex API
- **Threading**: Rejected - heavier than async, doesn't scale to 50 concurrent ops efficiently

### 5. Configuration Management

**Decision**: Use Pydantic Settings with environment variable overrides and YAML config files

**Rationale**:
- Type-safe configuration aligns with constitution
- Environment variables enable Docker/cloud deployment
- YAML human-readable for local development
- Pydantic validates config at startup (fail fast)

**Alternatives Considered**:
- **Python ConfigParser**: Rejected - no type safety, manual validation
- **JSON config**: Rejected - no comments, harder to document
- **TOML**: Rejected - less familiar to ops teams than YAML

**Example**:
```python
class InstanceSettings(BaseSettings):
    openai_api_key: str
    llm_temperature: float = 0.7
    message_transport: Literal["http", "file"] = "file"
    external_endpoint: HttpUrl | None = None
    log_level: str = "INFO"
    
    class Config:
        env_prefix = "INSTANCE_"
        env_file = ".env"
```

### 6. IRIS Configuration Tool Implementation

**Decision**: Use `configparser` to read/write CPF files with manual validation against known parameters

**Rationale**:
- IRIS CPF files are INI format (key=value sections)
- Python `configparser` is stdlib, proven for INI files
- Manual validation necessary - no public IRIS CPF schema available
- Constitution mandates validation before apply (FR-009)

**Alternatives Considered**:
- **Direct file editing**: Rejected - risky, no syntax validation
- **IRIS API calls**: Rejected - requires running IRIS instance, breaks emulation model
- **XML-based config**: Rejected - CPF is INI format not XML

**Known CPF Parameters to Validate**:
```
[config]
globals = 256 (MB, must be power of 2, 8-65536)
routines = 64 (MB, must be power of 2, 8-8192)
locksiz = 16777216 (bytes, range validation)
```

### 7. OS Configuration Tool Safety

**Decision**: Use `subprocess` with dry-run mode reading `/proc/sys` and `/sys` before writes

**Rationale**:
- OS parameters (shmmax, shmall) accessible via `/proc/sys/kernel/shm*`
- Dry-run can read current values without requiring privileges
- Write requires `sudo`, tool detects and fails gracefully
- Constitution mandates checking current values (FR-011)

**Alternatives Considered**:
- **Direct system calls**: Rejected - requires C extensions, adds complexity
- **Ansible playbooks**: Rejected - external dependency, overkill for 3-4 parameters
- **Salt/Chef**: Rejected - too heavy for simple parameter changes

**Implementation**:
```python
# Dry-run: read current value
with open('/proc/sys/kernel/shmmax', 'r') as f:
    current_shmmax = int(f.read().strip())

# Actual: write new value (requires sudo)
subprocess.run(['sudo', 'sysctl', '-w', f'kernel.shmmax={new_value}'], check=True)
```

### 8. IRIS Restart Tool Strategy

**Decision**: Use `psutil` to detect IRIS processes and check for active connections before shutdown

**Rationale**:
- `psutil` cross-platform, reliable process management
- Can query process tree, detect child processes
- Check TCP connections to IRIS port (default 1972) for active users
- Constitution mandates 100% accuracy in detecting active users (SC-007)

**Alternatives Considered**:
- **IRIS ^%SYS.Process API**: Rejected - requires running IRIS, can't detect from outside
- **Lsof/netstat parsing**: Rejected - platform-specific, fragile
- **Kill -0 signal**: Rejected - only checks if process exists, not if safe to shutdown

**Active User Detection**:
```python
import psutil

def has_active_iris_connections(pid: int, port: int = 1972) -> bool:
    proc = psutil.Process(pid)
    connections = proc.connections()
    return any(conn.laddr.port == port and conn.status == 'ESTABLISHED' 
               for conn in connections)
```

### 9. Tracing and Observability

**Decision**: Use `structlog` with JSON output and OpenTelemetry trace ID format (128-bit hex)

**Rationale**:
- `structlog` designed for structured logging, better than stdlib `logging`
- JSON output machine-parseable (FR-022)
- OpenTelemetry IDs compatible with distributed tracing tools
- Constitution mandates trace IDs for all operations (FR-021)

**Alternatives Considered**:
- **Stdlib logging**: Rejected - unstructured, harder to parse
- **Python-json-logger**: Rejected - less flexible than structlog
- **UUID4 for trace IDs**: Rejected - OpenTelemetry format industry standard

**Trace Context Propagation**:
```python
import structlog
from contextvars import ContextVar

trace_id_var: ContextVar[str] = ContextVar('trace_id', default='')

log = structlog.get_logger()
log.info("message_generated", trace_id=trace_id_var.get(), message_id=msg.id)
```

### 10. Testing Strategy for LLM Components

**Decision**: Use `responses` library to mock OpenAI API, record/replay pattern for integration tests

**Rationale**:
- Constitution mandates TDD with mocked LLM responses (Principle III)
- `responses` intercepts `aiohttp` requests deterministically
- Record/replay enables using real LLM output in tests without API calls
- Contract tests validate schema, not content creativity

**Alternatives Considered**:
- **Real LLM calls in tests**: Rejected - slow, expensive, non-deterministic
- **VCR.py**: Rejected - designed for HTTP not async aiohttp
- **pytest-httpx**: Rejected - less mature than responses

**Example**:
```python
import responses

@responses.activate
def test_message_generation():
    responses.post(
        "https://api.openai.com/v1/chat/completions",
        json={"choices": [{"message": {"content": "11/14/25-09:45:55:657 (50745) 2 [Config.Error] Invalid buffer size"}}]},
        status=200
    )
    result = await generate_message(error_type="config")
    assert result.severity == 2
```

## Best Practices Applied

### OpenAI SDK Usage
- Use `openai.AsyncOpenAI()` for async support
- Set timeouts (30s default per FR-018 60s tool timeout budget)
- Implement exponential backoff in SDK (built-in retry support)
- Cache model responses using `functools.lru_cache` for repeated prompts

### Pydantic V2 Patterns
- Use `Field()` with descriptions for LLM schema generation
- Leverage `model_validator` for cross-field validation
- Export JSON Schema for external API documentation
- Use `ConfigDict` for immutability where appropriate

### Async Patterns
- Use `asyncio.gather()` for concurrent message generation
- Apply `asyncio.Semaphore` to limit concurrent LLM calls (avoid rate limits)
- Use `asyncio.Queue` for tool orchestration pipeline
- Handle `asyncio.CancelledError` for graceful shutdown

### Error Handling
- Define custom exceptions hierarchy: `InstanceError` → `ValidationError`, `ToolError`, `LLMError`
- Use Result type pattern for tool outcomes (success/failure/partial)
- Log all exceptions with trace context
- Never catch broad `Exception` - be specific

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| LLM generates invalid IRIS format | High - breaks downstream consumers | Validate with regex after generation, retry up to 3 times |
| IRIS process detection false negatives | Critical - unsafe shutdown | Use `psutil` +  port connection check, add configurable safety timeout |
| External endpoint unavailable | Medium - message loss | Implement persistent queue (optional Redis), exponential backoff |
| Configuration rollback fails | High - system unstable | Create backup files before changes, validate backup integrity |
| OS permission denied | Medium - tool failure | Detect early with dry-run, provide clear sudo instructions |
| Tool timeout doesn't fire | Low - hanging processes | Use `asyncio.wait_for()` with timeout, test edge cases |

## Dependencies

**Core**:
- `openai>=1.0.0` - LLM integration
- `pydantic>=2.0` - Schema validation
- `aiohttp>=3.9` - Async HTTP
- `structlog>=23.0` - Structured logging
- `psutil>=5.9` - Process management

**Testing**:
- `pytest>=7.4` - Test framework
- `pytest-asyncio>=0.21` - Async test support
- `pytest-cov>=4.1` - Coverage reporting
- `responses>=0.24` - HTTP mocking
- `mypy>=1.7` - Type checking

**Optional**:
- `redis>=5.0` - Message queue (if configured)
- `prometheus-client>=0.19` - Metrics export (future)

## Open Questions

1. **LLM Provider Fallback**: Should we auto-fallback to Claude if OpenAI rate limits hit?
   - **Answer**: Yes, implement provider abstraction with fallback chain
   
2. **Message Queue Persistence**: How long to retain failed messages?
   - **Answer**: 24 hours default, configurable via settings

3. **IRIS Version Detection**: Should tool detect IRIS version and adjust format?
   - **Answer**: Not for MVP - assume IRIS 2025.x, document in constraints

4. **Multi-Instance Support**: Can one Instance system manage multiple IRIS instances?
   - **Answer**: Not for MVP - single instance focus, scale later if needed

## Next Steps (Phase 1)

1. Define Pydantic models in `data-model.md`
2. Create JSON schemas in `contracts/`
3. Write `quickstart.md` for local development setup
4. Update agent context with technology choices
