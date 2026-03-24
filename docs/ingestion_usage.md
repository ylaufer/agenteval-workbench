# Trace Ingestion Usage Guide

This guide shows how to use the `agenteval-ingest` CLI to convert traces from various agent frameworks to AgentEval format.

## Quick Start

```bash
# Install agenteval (if not already installed)
pip install -e .

# Ingest a single trace file (auto-detect format)
agenteval-ingest input.json --output output.json

# Ingest multiple trace files from a directory
agenteval-ingest traces/ --output-dir converted/
```

## Supported Formats

### OpenTelemetry (OTLP JSON)

Converts OpenTelemetry OTLP JSON traces to AgentEval format.

**Example:**
```bash
agenteval-ingest otel_trace.json --output trace.json --adapter otel --verbose
```

**Input format:**
- Must contain `resourceSpans` array
- Spans include `spanId`, `startTimeUnixNano`, `kind`, `attributes`
- Service name extracted from `resource.attributes` → `actor_id`

**Mappings:**
- `SPAN_KIND_INTERNAL` → `thought`
- `SPAN_KIND_CLIENT` → `tool_call`
- `SPAN_KIND_SERVER` → `observation`
- Timestamps converted from nanoseconds to ISO8601

### LangChain / LangSmith

Converts LangChain run tree JSON to AgentEval format.

**Example:**
```bash
agenteval-ingest langchain_run.json --output trace.json --adapter langchain --verbose
```

**Input format:**
- Must contain `run_type`, `id`, `start_time` fields
- Nested `child_runs` array with run hierarchy
- Tool runs automatically expanded to tool_call + observation pairs

**Mappings:**
- `llm` → `thought`
- `chain` → `thought`
- `tool` → `tool_call` + `observation` (expanded)
- `retriever` → `tool_call`

### CrewAI

Converts CrewAI task execution logs to AgentEval format.

**Example:**
```bash
agenteval-ingest crewai_log.json --output trace.json --adapter crewai --verbose
```

**Input format:**
- Must contain `tasks` array
- Each task has `actions` array with agent events
- Agent name extracted from `action.agent` → `actor_id`

**Mappings:**
- `thought` → `thought`
- `tool_use` → `tool_call` + `observation` (expanded)
- `observation` → `observation`
- `final_answer` → `final_answer`

### OpenAI Raw API

Converts OpenAI Chat Completions API responses to AgentEval format.

**Example:**
```bash
agenteval-ingest openai_response.json --output trace.json --adapter openai --verbose
```

**Input format:**
- Must contain `messages` array
- Supports `tool_calls` in assistant messages
- Tool messages with `tool_call_id` for observations

**Mappings:**
- User messages → skipped (not agent actions)
- Assistant messages → `thought` or `final_answer` (last message)
- Tool calls → `tool_call` steps
- Tool messages → `observation` steps

### Generic (Custom Formats)

Converts custom JSON formats using user-defined mapping configurations.

**Example:**
```bash
agenteval-ingest custom.json --output trace.json \\
  --adapter generic \\
  --mapping custom_mapping.yaml \\
  --verbose
```

**Mapping configuration** (YAML or JSON):
```yaml
# Required field mappings (dot-notation paths)
task_id: "execution.run_id"
user_prompt: "execution.input_query"
model_version: "execution.model_name"

# Steps array path
steps_path: "execution.events"

# Step field mappings
step_mappings:
  step_id: "event_id"
  type:
    path: "event_type"
    transform: "map"
    mapping:
      "think": "thought"
      "call_tool": "tool_call"
      "tool_result": "observation"
  content: "event_data.text"
  timestamp:
    path: "created_at"
    transform: "iso8601"
  tool_name: "event_data.tool_id"
  actor_id: "event_data.agent_name"

# Optional metadata
metadata_timestamp: "execution.started_at"
metadata_source: "custom"
```

See [Generic Mapping Reference](generic_mapping.md) for details on transforms and advanced usage.

## CLI Options

### Single File Ingestion

```bash
agenteval-ingest INPUT --output OUTPUT [OPTIONS]
```

**Required:**
- `INPUT`: Path to input trace file
- `--output`: Output file path

**Optional:**
- `--adapter`: Adapter to use (`auto`, `otel`, `langchain`, `crewai`, `openai`, `generic`)
- `--mapping`: Mapping config file (required for `generic` adapter)
- `--dry-run`: Validate mapping without converting
- `--verbose`: Show detailed conversion logs

### Bulk Ingestion

```bash
agenteval-ingest INPUT_DIR --output-dir OUTPUT_DIR [OPTIONS]
```

**Required:**
- `INPUT_DIR`: Directory containing trace files (*.json)
- `--output-dir`: Output directory for converted traces

**Optional:**
- `--adapter`: Adapter to use (defaults to `auto`)
- `--mapping`: Mapping config file (for `generic` adapter)
- `--verbose`: Show detailed logs

**Output structure:**
```
output_dir/
  case_001/
    trace.json
  case_002/
    trace.json
  ...
```

## Validation & Size Limits

All ingested traces are automatically validated against the AgentEval trace schema.

**Size limits:**
- **Soft limit**: 10MB (warning but continues)
- **Hard limit**: 50MB (fails with error)

**Example:**
```bash
agenteval-ingest large_trace.json --output trace.json --verbose
# [WARN] Warning: File size 12.5 MB exceeds soft limit of 10 MB
# [OK] Loaded input file: large_trace.json
# ...
```

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: Input file/directory not found
- `3`: No adapter can handle input
- `4`: Conversion failed
- `5`: Schema validation failed
- `8`: File size exceeds hard limit

## Examples

### Auto-detect and Convert Single File

```bash
agenteval-ingest otel_trace.json --output trace.json --verbose
```

Output:
```
[OK] Loaded input file: otel_trace.json
[OK] Detected format: OTelAdapter
[OK] Converted to 5 steps
[OK] Validated against trace schema
[OK] Wrote trace to trace.json
```

### Bulk Conversion with Mixed Sources

```bash
agenteval-ingest traces/ --output-dir converted/ --verbose
```

Output:
```
Found 10 trace files in traces/

[1/10] Processing otel_001.json...
[OK] Converted otel_001.json → converted/case_001/trace.json

[2/10] Processing langchain_002.json...
[OK] Converted langchain_002.json → converted/case_002/trace.json

...

Summary: [OK] 9/10 traces converted successfully. 1 failed.
```

### Dry-run Validation

```bash
agenteval-ingest custom.json \\
  --adapter generic \\
  --mapping custom_mapping.yaml \\
  --dry-run
```

Output:
```
[WARN] Warning: Field 'user_prompt' (path: 'input.query') not found in input
[OK] Dry-run validation succeeded
```

## Troubleshooting

See [Ingestion Troubleshooting Guide](ingestion_troubleshooting.md) for common issues and solutions.
