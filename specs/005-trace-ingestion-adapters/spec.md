# Feature Specification: Trace Ingestion Adapters

**Feature ID:** 005
**Phase:** 2.1
**Priority:** HIGH
**Status:** Not Started

---

## Problem Statement

Currently, AgentEval only evaluates its own synthetic trace format. Real agent teams use LangChain, CrewAI, AutoGen, custom frameworks, or raw OpenAI API calls. Without ingestion adapters, adoption requires manual trace conversion — a dealbreaker for most users.

## Goal

Make AgentEval useful with real agent traces from real frameworks. Enable teams to evaluate agent runs within minutes of installation, without writing any conversion code.

## Clarifications

### Session 2026-03-24

- Q: Maximum trace size to support? → A: 10MB soft limit - warn above 10MB, fail above 50MB
- Q: Validation error handling strategy? → A: Fail-fast on schema errors, collect warnings
- Q: Bulk ingestion error handling? → A: Continue on errors, report summary at end
- Q: Progress reporting for long operations? → A: Progress bar for bulk operations, quiet for single files

---

## Capabilities

### 1. OpenTelemetry Ingestion

- Accept OTLP trace exports (JSON or protobuf)
- Map OTel span attributes to AgentEval trace schema fields
- Handle nested spans → flat step sequence conversion
- Preserve parent-child relationships via `parent_event_id`

### 2. LangChain / LangSmith Adapter

- Ingest LangChain callback handler output (JSON)
- Map LangChain run types (`llm`, `tool`, `chain`, `retriever`) to AgentEval step types
- Extract tool inputs/outputs from LangChain serialization format
- Handle streaming token events by collapsing them into single steps

### 3. CrewAI Adapter

- Ingest CrewAI task execution logs
- Map agent/task/tool hierarchy to AgentEval actor model
- Handle multi-agent traces with `actor_id` mapping

### 4. Raw API Call Adapter

- Accept OpenAI Chat Completions API response format
- Extract tool_use blocks from assistant messages
- Reconstruct trace steps from conversation turns
- Handle function calling and parallel tool use

### 5. Generic JSON Adapter

- Accept a user-defined mapping configuration (YAML/JSON)
- Map arbitrary JSON trace formats to AgentEval schema
- Validate mapping completeness at import time
- Provide clear error messages for unmappable fields

---

## Architecture

```
src/agenteval/ingestion/
  __init__.py
  base.py          — TraceAdapter Protocol
  otel.py          — OpenTelemetry adapter
  langchain.py     — LangChain adapter
  crewai.py        — CrewAI adapter
  openai_raw.py    — Raw API response adapter
  generic.py       — User-defined mapping adapter
```

### TraceAdapter Protocol

Each adapter implements:

```python
class TraceAdapter(Protocol):
    def can_handle(self, raw: dict) -> bool: ...
    def convert(self, raw: dict) -> Trace: ...
    def validate_mapping(self, raw: dict) -> list[str]: ...  # warnings
```

---

## CLI Interface

```bash
# Auto-detect format and convert
agenteval-ingest trace_export.json --output data/cases/case_new/trace.json

# Specify adapter explicitly
agenteval-ingest trace.json --adapter langchain --output data/cases/case_new/trace.json

# Bulk ingest a directory of traces (continues on errors, reports summary)
agenteval-ingest ./exports/ --adapter otel --output-dir data/cases/
# Output: "✓ Converted 8/10 traces successfully. 2 failed (see errors above)"

# Validate a custom mapping without converting
agenteval-ingest trace.json --adapter generic --mapping my_mapping.yaml --dry-run
```

---

## Constraints

### Performance & Scale

- **Trace Size Limits**:
  - Soft limit: 10MB - emit warning, continue processing
  - Hard limit: 50MB - fail with clear error message
  - Rationale: Balances real-world traces (most <1MB, complex multi-agent up to 10MB) with memory safety

### Validation Behavior

- **Error Handling Strategy**:
  - Schema validation errors: Fail-fast (abort immediately, invalid trace cannot be used)
  - Mapping warnings: Collect all warnings (show comprehensive feedback for user to fix multiple issues)
  - Rationale: Hard errors block progress, but warnings can be batched for better UX

- **Bulk Ingestion**:
  - Continue processing on individual file errors
  - Report summary at end: "✓ Converted N/M traces successfully. X failed"
  - Rationale: Maximize batch throughput, allow users to triage failures

### User Experience

- **Progress Reporting**:
  - Single file: Quiet mode (fast operation, <1s typically)
  - Bulk operations: Progress bar showing "Processing file N/M..."
  - Verbose flag available for detailed conversion logs
  - Rationale: Contextual feedback without clutter

---

## Success Criteria

1. ✅ Teams can ingest LangChain traces without manual conversion
2. ✅ Teams can ingest OpenTelemetry traces without manual conversion
3. ✅ Teams can ingest raw OpenAI API responses without manual conversion
4. ✅ Teams can define custom mappings for proprietary trace formats
5. ✅ All ingested traces pass `agenteval-validate-dataset`
6. ✅ Clear error messages guide users when mappings fail

---

## Dependencies

- Existing trace schema (`schemas/trace_schema.json`)
- Dataset validator (`src/agenteval/dataset/validator.py`)

---

## Testing Requirements

- Unit tests for each adapter with sample input fixtures
- Integration test: ingest → validate → evaluate pipeline
- Error handling tests for malformed inputs
- Mapping validation tests for generic adapter

---

## Documentation Requirements

- Usage guide for each adapter
- Example mapping configurations for generic adapter
- Migration guide for teams with existing custom trace formats
