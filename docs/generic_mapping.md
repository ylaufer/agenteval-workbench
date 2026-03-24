# Generic Mapping Reference

This guide explains how to create custom mapping configurations for the Generic JSON adapter.

## Overview

The Generic adapter allows you to convert arbitrary JSON trace formats to AgentEval format by defining a mapping configuration file (YAML or JSON).

## Mapping Configuration Structure

```yaml
# Required top-level field mappings
task_id: <path>
user_prompt: <path>
model_version: <path>

# Steps array location
steps_path: <path>

# Step field mappings
step_mappings:
  step_id: <path | config>
  type: <path | config>
  content: <path | config>
  timestamp: <path | config>
  # Optional fields:
  tool_name: <path | config>
  actor_id: <path | config>
  parent_event_id: <path | config>

# Optional metadata fields
metadata_timestamp: <path>
metadata_source: <string>
```

## Path Syntax

Paths use dot notation to navigate nested objects:

```yaml
# Simple path
task_id: "execution.run_id"

# Nested path
user_prompt: "metadata.request.query"

# Array element (not yet supported)
# first_step: "steps[0].content"
```

**Examples:**

```json
{
  "execution": {
    "run_id": "abc-123",
    "metadata": {
      "request": {
        "query": "What is the weather?"
      }
    }
  }
}
```

Mappings:
- `"execution.run_id"` → `"abc-123"`
- `"metadata.request.query"` → `"What is the weather?"`

## Transform Functions

Transform functions modify extracted values before applying them to the output.

### `map` Transform

Maps input values to output values using a lookup table.

**Configuration:**
```yaml
type:
  path: "event_type"
  transform: "map"
  mapping:
    "think": "thought"
    "call_tool": "tool_call"
    "tool_result": "observation"
    "answer": "final_answer"
```

**Example:**

Input:
```json
{
  "event_type": "think"
}
```

Output:
```json
{
  "type": "thought"
}
```

### `iso8601` Transform

Converts timestamps to ISO8601 format.

**Configuration:**
```yaml
timestamp:
  path: "created_at"
  transform: "iso8601"
```

Supports multiple input formats:
- ISO8601 strings (returned as-is)
- Unix epoch seconds
- Unix epoch milliseconds
- Nanoseconds (>1e15)

**Examples:**

| Input | Output |
|-------|--------|
| `"2024-01-15T10:00:00Z"` | `"2024-01-15T10:00:00Z"` (unchanged) |
| `1705320000` | `"2024-01-15T10:00:00Z"` (seconds) |
| `1705320000000` | `"2024-01-15T10:00:00Z"` (milliseconds) |
| `1705320000000000000` | `"2024-01-15T10:00:00Z"` (nanoseconds) |

### `concat` Transform

Concatenates multiple field values (not yet implemented).

## Required Fields

All mapping configurations must include these required fields:

### Top-level Fields

- `task_id`: Unique identifier for the trace
- `user_prompt`: Initial user query or task description
- `model_version`: Model or agent version identifier
- `steps_path`: Path to array of step/event objects

### Step Fields

- `step_id`: Unique identifier for each step
- `type`: Step type (`thought`, `tool_call`, `observation`, `final_answer`)
- `content`: Step content (text, JSON, etc.)
- `timestamp`: Step timestamp (will be converted to ISO8601)

### Optional Step Fields

- `tool_name`: Tool identifier (for `tool_call` steps)
- `actor_id`: Agent/actor identifier (for multi-agent traces)
- `parent_event_id`: Parent step ID (for hierarchical traces)
- `latency_ms`: Step duration in milliseconds

## Complete Example

### Input JSON

```json
{
  "execution": {
    "run_id": "custom-run-001",
    "input_query": "Analyze sales data",
    "model_name": "analyst-v1",
    "started_at": "2024-02-01T09:00:00Z",
    "events": [
      {
        "event_id": "evt-001",
        "event_type": "think",
        "created_at": "2024-02-01T09:00:01Z",
        "event_data": {
          "text": "I need to load the data first.",
          "agent_name": "analyst"
        }
      },
      {
        "event_id": "evt-002",
        "event_type": "call_tool",
        "created_at": "2024-02-01T09:00:05Z",
        "event_data": {
          "text": "{\"filename\": \"sales.csv\"}",
          "tool_id": "load_file",
          "agent_name": "analyst"
        }
      },
      {
        "event_id": "evt-003",
        "event_type": "tool_result",
        "created_at": "2024-02-01T09:00:10Z",
        "event_data": {
          "text": "{\"rows\": 1523}",
          "agent_name": "analyst"
        }
      }
    ]
  }
}
```

### Mapping Configuration

```yaml
# custom_mapping.yaml
task_id: "execution.run_id"
user_prompt: "execution.input_query"
model_version: "execution.model_name"

steps_path: "execution.events"

step_mappings:
  step_id: "event_id"
  type:
    path: "event_type"
    transform: "map"
    mapping:
      "think": "thought"
      "call_tool": "tool_call"
      "tool_result": "observation"
      "answer": "final_answer"
  content: "event_data.text"
  timestamp:
    path: "created_at"
    transform: "iso8601"
  tool_name: "event_data.tool_id"
  actor_id: "event_data.agent_name"

metadata_timestamp: "execution.started_at"
metadata_source: "custom"
```

### Output Trace

```json
{
  "task_id": "custom-run-001",
  "user_prompt": "Analyze sales data",
  "model_version": "analyst-v1",
  "steps": [
    {
      "step_id": "evt-001",
      "type": "thought",
      "content": "I need to load the data first.",
      "timestamp": "2024-02-01T09:00:01Z",
      "actor_id": "analyst",
      "event_id": "evt-001"
    },
    {
      "step_id": "evt-002",
      "type": "tool_call",
      "content": "{\"filename\": \"sales.csv\"}",
      "timestamp": "2024-02-01T09:00:05Z",
      "tool_name": "load_file",
      "actor_id": "analyst",
      "event_id": "evt-002"
    },
    {
      "step_id": "evt-003",
      "type": "observation",
      "content": "{\"rows\": 1523}",
      "timestamp": "2024-02-01T09:00:10Z",
      "actor_id": "analyst",
      "event_id": "evt-003"
    }
  ],
  "metadata": {
    "timestamp": "2024-02-01T09:00:00Z",
    "environment": {
      "source": "custom"
    }
  }
}
```

## Validation

Use `--dry-run` to validate your mapping configuration without converting:

```bash
agenteval-ingest custom.json \\
  --adapter generic \\
  --mapping custom_mapping.yaml \\
  --dry-run \\
  --verbose
```

This will report warnings if any mapped fields are missing from the input.

## Advanced Patterns

### Multi-Agent Traces

Use `actor_id` to track multiple agents:

```yaml
step_mappings:
  actor_id: "event.agent_name"
```

### Hierarchical Traces

Use `parent_event_id` to preserve trace hierarchy:

```yaml
step_mappings:
  parent_event_id: "event.parent_id"
```

### Conditional Mapping

Not yet supported. All mapped fields are extracted if present, skipped if missing.

## Troubleshooting

### Missing Fields

If a mapped field is not found in the input:
- **Required fields** (`task_id`, `user_prompt`, `model_version`, `steps_path`): Conversion fails
- **Optional step fields** (`tool_name`, `actor_id`): Field is omitted from output

### Transform Errors

If a transform fails (e.g., invalid timestamp format), the original value is used as-is.

### Type Mismatches

If `steps_path` does not resolve to an array, conversion fails with error.

## See Also

- [Ingestion Usage Guide](ingestion_usage.md) - CLI usage and examples
- [Troubleshooting Guide](ingestion_troubleshooting.md) - Common issues and solutions
- [Trace Schema](../schemas/trace_schema.json) - Complete AgentEval trace schema
