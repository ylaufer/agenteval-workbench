# Data Model: Trace Ingestion Adapters

**Date**: 2026-03-24

## Entities

### 1. TraceAdapter (Protocol)

**Purpose**: Abstract interface for all trace format converters

**Fields**:
```python
@runtime_checkable
class TraceAdapter(Protocol):
    """Protocol for trace format adapters."""

    def can_handle(self, raw: dict) -> bool:
        """
        Determine if this adapter can convert the raw input.

        Args:
            raw: Parsed JSON object from input file

        Returns:
            True if this adapter recognizes the format
        """
        ...

    def convert(self, raw: dict) -> Trace:
        """
        Convert raw input to AgentEval Trace.

        Args:
            raw: Parsed JSON object from input file

        Returns:
            Validated Trace object

        Raises:
            ValueError: If conversion fails
        """
        ...

    def validate_mapping(self, raw: dict) -> list[str]:
        """
        Check for unmappable fields and return warnings.

        Args:
            raw: Parsed JSON object from input file

        Returns:
            List of warning messages (empty if all fields mappable)
        """
        ...
```

**Validation Rules**:
- `convert()` output MUST validate against `schemas/trace_schema.json`
- `can_handle()` MUST NOT raise exceptions (return False on error)
- `validate_mapping()` is advisory only (warnings, not errors)

**State Transitions**: N/A (stateless protocol)

---

### 2. OTelAdapter

**Purpose**: Convert OpenTelemetry OTLP JSON traces to AgentEval format

**Key Mappings**:
```python
OTEL_SPAN_KIND_TO_STEP_TYPE = {
    "SPAN_KIND_INTERNAL": "thought",      # Internal processing
    "SPAN_KIND_CLIENT": "tool_call",      # Outbound call
    "SPAN_KIND_SERVER": "observation",    # Inbound response (rare)
}

OTEL_ATTRIBUTES_TO_METADATA = {
    "service.name": "actor_id",
    "span.kind": "step_type_hint",
    "error.message": "error.message",
}
```

**Validation Rules**:
- Must have `resourceSpans[*].scopeSpans[*].spans` structure
- Each span must have `spanId`, `traceId`, `startTimeUnixNano`, `endTimeUnixNano`
- Nested spans flattened via `parentSpanId` → `parent_event_id`
- Span attributes extracted to step metadata

**Conversion Logic**:
1. Traverse nested span hierarchy
2. Sort spans by start time (deterministic ordering)
3. Map span attributes to step fields
4. Calculate latency from nano timestamps
5. Preserve parent-child via `parentSpanId`

---

### 3. LangChainAdapter

**Purpose**: Convert LangSmith run tree JSON to AgentEval format

**Key Mappings**:
```python
LANGCHAIN_RUN_TYPE_TO_STEP_TYPE = {
    "llm": "thought",           # LLM reasoning
    "tool": "tool_call",        # Tool invocation (followed by observation)
    "retriever": "tool_call",   # Retrieval is a tool
    "chain": None,              # Skip (container only)
}
```

**Validation Rules**:
- Must have `runs` array or single run object
- Each run must have `id`, `run_type`, `start_time`, `end_time`
- Tool runs create two steps: `tool_call` + `observation`
- Chain runs are skipped (not steps, just hierarchy)

**Conversion Logic**:
1. Flatten run tree recursively
2. Map each run type to step type
3. For `tool` runs, create two steps:
   - `tool_call` with inputs
   - `observation` with outputs
4. Collapse streaming tokens into final output
5. Preserve run hierarchy via `parent_run_id` → `parent_event_id`

---

### 4. CrewAIAdapter

**Purpose**: Convert CrewAI execution result JSON to AgentEval format

**Key Mappings**:
```python
CREWAI_ACTION_TO_STEP_TYPE = {
    "thought": "thought",
    "tool": "tool_call",
    "observation": "observation",
    "final_answer": "final_answer",
}
```

**Validation Rules**:
- Must have `tasks` array with agent actions
- Each task must have `agent`, `actions`, `result`
- Agent name maps to `actor_id`

**Conversion Logic**:
1. Iterate through tasks in execution order
2. For each task, extract agent actions
3. Map agent name to `actor_id`
4. Create steps from action sequence
5. Preserve task boundaries in metadata

---

### 5. OpenAIRawAdapter

**Purpose**: Convert OpenAI Chat Completions API responses to AgentEval format

**Validation Rules**:
- Must have `messages` array
- Each message must have `role`, `content` (or `tool_calls`)
- Function results must have matching `tool_call_id`

**Conversion Logic**:
1. Skip user messages (they're the prompt, not steps)
2. For each assistant message:
   - If `tool_calls` present → create `tool_call` steps
   - If no `tool_calls` → create `thought` or `final_answer` (heuristic)
3. For each tool message → create `observation` step
4. Link observations to tool_calls via `tool_call_id`
5. Reconstruct timestamps (not in API response) using sequential ordering

**Heuristic for final_answer**:
- Last assistant message in sequence
- No `tool_calls` present
- Content is non-empty

---

### 6. GenericAdapter

**Purpose**: Convert arbitrary JSON via user-defined mapping configuration

**Configuration Schema**:
```yaml
version: "1.0"
metadata:
  format_name: "Custom Agent Trace"
  description: "Internal agent trace format"

mappings:
  steps:
    source_path: "$.events[*]"  # JSONPath to step array
    fields:
      step_type:
        from: "type"              # Source field name
        transform: "map"          # Transform type
        map:                      # Map values
          "llm_call": "thought"
          "tool_call": "tool_call"
          "tool_result": "observation"
      content:
        from: "payload.message"
      timestamp:
        from: "created_at"
        transform: "iso8601"      # Parse ISO8601 string
      metadata:
        from: "attrs"             # Copy entire object
```

**Supported Transforms**:
- `map`: Value mapping (dict lookup)
- `iso8601`: Parse ISO8601 datetime string
- `concat`: Concatenate multiple fields
- `template`: String template substitution

**Validation Rules**:
- Mapping file must validate against mapping schema
- All required trace fields must have mapping
- Unmapped optional fields generate warnings
- Invalid JSONPath expressions fail validation

**Conversion Logic**:
1. Load and validate mapping configuration
2. Apply `source_path` to extract step array
3. For each step, apply field mappings
4. Run transforms on mapped values
5. Construct Trace object
6. Validate against trace schema

---

## Relationships

```
Input JSON → Adapter.can_handle() → Adapter.convert() → Trace → Validation
                 ↓                                               ↓
            Auto-detect                                   trace_schema.json
            or explicit
```

## Data Flow

1. **Input**: Raw JSON file from external framework
2. **Size Check**: Verify file size (warn if >10MB, fail if >50MB)
3. **Detection**: Loop through adapters calling `can_handle()`
4. **Selection**: Use first matching adapter (or explicit `--adapter` flag)
5. **Conversion**: Adapter.convert() produces Trace object
6. **Validation**: Trace validated against `schemas/trace_schema.json` (fail-fast on errors)
7. **Warning Collection**: Accumulate mapping warnings (display all at end)
8. **Security Check**: Trace validated for secrets/URLs/paths
9. **Output**: Write trace.json to output path

## Error Handling

| Error Condition | Response | Behavior |
|----------------|----------|----------|
| File size > 50MB | Clear error message with size limit | Fail immediately |
| File size > 10MB | Warning message | Continue processing |
| No adapter can handle input | Clear error message with format hints | Fail immediately |
| Conversion fails | ValueError with specific unmappable field | Fail immediately (single) or continue (bulk) |
| Schema validation fails | jsonschema error with field path | Fail immediately (hard error) |
| Mapping warnings | List of unmappable fields | Collect all, display at end |
| Security scan fails | ValidationError with detected pattern | Fail immediately |
| Output path outside repo | Path traversal error | Fail immediately |
| Bulk mode individual failure | Error logged, continue to next file | Continue, report summary at end |

## Extension Points

New adapters can be added by:
1. Implementing `TraceAdapter` protocol
2. Registering in `src/agenteval/ingestion/__init__.py`
3. Adding tests in `tests/ingestion/test_<adapter>.py`
4. Adding fixture in `tests/ingestion/fixtures/<adapter>_trace.json`

No changes to CLI or core logic required.
