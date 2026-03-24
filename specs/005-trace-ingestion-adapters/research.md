# Research: Trace Ingestion Adapters

**Date**: 2026-03-24
**Status**: In Progress

## Research Questions

### 1. OpenTelemetry OTLP Format Support

**Question**: Do we need the protobuf library to support OpenTelemetry OTLP, or can we support JSON-only?

**Decision**: Support OTLP JSON format only (no protobuf dependency)

**Rationale**:
- OpenTelemetry supports both protobuf and JSON encodings for OTLP
- JSON format is human-readable and easier to debug
- Avoids adding `protobuf` as a runtime dependency (aligns with Minimal Dependencies principle)
- Most OTel SDKs can export JSON format via `OTEL_EXPORTER_OTLP_PROTOCOL=http/json`
- If protobuf support is needed later, it can be added as an optional extra

**Alternatives considered**:
- Support both JSON and protobuf → rejected due to dependency bloat
- Protobuf-only → rejected due to poor debuggability

**Implementation notes**:
- Accept JSON files with OTLP trace structure
- Document how to export OTel traces as JSON in usage guide
- Use `jsonschema` for OTLP structure validation (already a dependency)

---

### 2. LangChain Trace Format

**Question**: What is the structure of LangChain callback handler output?

**Decision**: Support LangSmith run tree JSON format

**Rationale**:
- LangSmith run trees are the canonical trace format for LangChain
- Accessible via `langchain.callbacks.tracers.LangChainTracer`
- Well-documented JSON structure with run types: `llm`, `tool`, `chain`, `retriever`
- Includes inputs, outputs, start/end times, token counts, errors

**Key mappings**:
- `llm` run → `thought` step (contains LLM reasoning)
- `tool` run → `tool_call` + `observation` steps
- `chain` run → ignored (container, not a step)
- `retriever` run → `tool_call` (retrieval is a tool)
- Run hierarchy → `parent_event_id` relationships

**Alternatives considered**:
- Raw callback events → rejected due to verbosity and complexity
- LangServe API logs → rejected (not a trace format)

**Implementation notes**:
- Parse run tree recursively
- Flatten into step sequence while preserving parent-child via `parent_event_id`
- Handle streaming by collapsing token events into final output

---

### 3. CrewAI Trace Format

**Question**: What is the structure of CrewAI task execution logs?

**Decision**: Support CrewAI execution result JSON

**Rationale**:
- CrewAI provides structured execution results via `crew.kickoff()`
- Includes agent actions, task results, tool usage, and timing
- Multi-agent traces naturally map to AgentEval's `actor_id` field

**Key mappings**:
- Agent → `actor_id`
- Task → sequence of steps
- Tool usage → `tool_call` + `observation`
- Agent thought → `thought` step

**Alternatives considered**:
- CrewAI logs (text) → rejected (unstructured)
- Custom instrumentation → rejected (too complex for users)

**Implementation notes**:
- Parse execution result JSON
- Map agent hierarchy to `actor_id`
- Preserve task boundaries in step metadata

---

### 4. OpenAI API Response Structure

**Question**: How do we extract trace steps from OpenAI Chat Completions API responses?

**Decision**: Parse assistant messages with tool calls from conversation array

**Rationale**:
- OpenAI API responses include `messages` array with `role`, `content`, `tool_calls`
- Function calling and parallel tool use are first-class in the API
- Can reconstruct agent flow from conversation turns

**Key mappings**:
- User message → not a step (it's the prompt)
- Assistant message without tools → `thought` or `final_answer` (heuristic based on position)
- Assistant message with `tool_calls` → one `tool_call` step per tool
- Tool message (function result) → `observation` step

**Alternatives considered**:
- Use OpenAI evals format → rejected (different use case)
- Require streaming API → rejected (not all users stream)

**Implementation notes**:
- Accept full conversation JSON (messages array)
- Reconstruct step sequence from turns
- Handle parallel tool calls by creating multiple tool_call steps with same timestamp
- Detect final answer heuristically (last assistant message without tool_calls)

---

### 5. Generic JSON Mapping Strategy

**Question**: How should users define custom mappings for proprietary trace formats?

**Decision**: YAML/JSON configuration with JSONPath-like selectors

**Rationale**:
- JSONPath is familiar to developers
- Declarative mapping is easier to maintain than code
- Can validate mapping completeness before conversion

**Mapping structure**:
```yaml
version: "1.0"
mappings:
  steps:
    source_path: "$.events[*]"  # Array of events
    fields:
      step_type:
        from: "event_type"
        transform: "map"
        map:
          "llm_call": "thought"
          "tool_use": "tool_call"
      content:
        from: "payload.text"
      timestamp:
        from: "created_at"
        transform: "iso8601"
```

**Alternatives considered**:
- Python code → rejected (requires users to write Python)
- Jinja templates → rejected (too complex for simple mappings)
- GraphQL-like schema → rejected (overkill)

**Implementation notes**:
- Use simple dot notation or JSONPath expressions
- Support basic transforms: `map`, `iso8601`, `concat`
- Validate mapping at load time
- Provide clear error messages for unmappable fields

---

### 6. Adapter Pattern Best Practices

**Question**: What's the best pattern for pluggable adapters in Python?

**Decision**: Protocol-based with registry pattern

**Rationale**:
- `typing.Protocol` provides duck typing without inheritance overhead
- Registry pattern enables auto-detection ("which adapter can handle this?")
- Each adapter is independent and testable

**Pattern**:
```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class TraceAdapter(Protocol):
    def can_handle(self, raw: dict) -> bool:
        """Return True if this adapter can convert the raw input."""
        ...

    def convert(self, raw: dict) -> Trace:
        """Convert raw input to AgentEval trace."""
        ...

    def validate_mapping(self, raw: dict) -> list[str]:
        """Return warnings about unmappable fields."""
        ...
```

**Alternatives considered**:
- Abstract base class → rejected (forces inheritance)
- Strategy pattern with factory → rejected (more complex than needed)

**Implementation notes**:
- Each adapter implements the Protocol
- Auto-detection loop: try `can_handle()` on each adapter
- Explicit adapter selection via `--adapter` flag
- Registry in `__init__.py` for easy extensibility

---

## Summary of Decisions

| Question | Decision | Impact on Dependencies |
|----------|----------|----------------------|
| OTel format | JSON-only | No new dependencies |
| LangChain | LangSmith run tree JSON | No new dependencies |
| CrewAI | Execution result JSON | No new dependencies |
| OpenAI | Chat Completions messages array | No new dependencies |
| Generic mapping | YAML config with JSONPath | No new dependencies (use stdlib) |
| Adapter pattern | Protocol + registry | No new dependencies |

**Net new dependencies**: **ZERO** ✅

All adapters can be implemented using:
- `json` (stdlib)
- `jsonschema` (existing dependency)
- `typing.Protocol` (stdlib)
- `pathlib` (stdlib)

This aligns perfectly with the Minimal Dependencies principle.
