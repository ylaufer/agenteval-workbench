# Trace Ingestion Troubleshooting Guide

This guide covers common issues and solutions when using `agenteval-ingest`.

## Common Errors

### 1. "No adapter can handle input file"

**Error:**
```
ERROR: No adapter can handle input file: input.json
```

**Cause:** The input file format is not recognized by any registered adapter.

**Solutions:**

1. **Check file format**: Verify the JSON structure matches one of the supported formats:
   - OpenTelemetry: Must have `resourceSpans` array
   - LangChain: Must have `run_type` and `id` fields
   - CrewAI: Must have `tasks` array
   - OpenAI: Must have `messages` array

2. **Use Generic adapter** for custom formats:
   ```bash
   agenteval-ingest input.json --output output.json \\
     --adapter generic \\
     --mapping my_mapping.yaml
   ```

3. **Specify adapter explicitly** if auto-detection fails:
   ```bash
   agenteval-ingest input.json --output output.json --adapter otel
   ```

### 2. "Schema validation failed"

**Error:**
```
ERROR: Schema validation failed: Additional properties are not allowed ('field_name' was unexpected)
```

**Cause:** The converted trace does not match the AgentEval trace schema.

**Solutions:**

1. **Check step field names**: Ensure steps use correct fields:
   - Use `step_id`, not `id` or `event_id` (for primary identifier)
   - Use `type`, not `step_type` or `event_type`
   - Use `timestamp`, not `created_at` or `time`

2. **Verify required fields** are present:
   - Top-level: `task_id`, `user_prompt`, `model_version`, `steps`, `metadata`
   - Metadata: `timestamp`, `environment`
   - Steps: `step_id`, `type`, `content`, `timestamp`

3. **Check step types** are valid:
   - Valid types: `thought`, `tool_call`, `observation`, `final_answer`
   - Invalid types: `action`, `response`, `input`, `output`

### 3. "File size exceeds hard limit"

**Error:**
```
ERROR: File size 55.2 MB exceeds hard limit of 50 MB
```

**Cause:** Input file is larger than 50MB hard limit.

**Solutions:**

1. **Split large traces** into smaller chunks before ingestion

2. **Filter unnecessary events** from the source trace (e.g., streaming tokens, debug events)

3. **Contact maintainers** if legitimate use case requires larger files

### 4. "Missing required field"

**Error:**
```
ERROR: Conversion failed: Span missing required field 'spanId'
```

**Cause:** Input trace is malformed or missing required fields for the detected format.

**Solutions:**

1. **Validate input JSON** against source framework schema:
   - OpenTelemetry: Validate against OTLP spec
   - LangChain: Check run tree structure
   - CrewAI: Verify task and action fields

2. **Use --dry-run** to check mapping before conversion:
   ```bash
   agenteval-ingest input.json --output output.json --dry-run --verbose
   ```

3. **Use Generic adapter** with explicit mapping to handle missing fields gracefully

### 5. "Input file not found"

**Error:**
```
ERROR: Input file not found: input.json
```

**Cause:** File path is incorrect or file doesn't exist.

**Solutions:**

1. **Check file path**: Use absolute paths or verify relative paths from current directory
   ```bash
   # Absolute path
   agenteval-ingest /full/path/to/input.json --output output.json

   # Relative path from current directory
   agenteval-ingest ./traces/input.json --output ./converted/output.json
   ```

2. **Verify file exists**:
   ```bash
   ls -l input.json
   ```

### 6. "Invalid mapping config"

**Error:**
```
ERROR: Invalid mapping config: Missing required mapping field: steps_path
```

**Cause:** Generic adapter mapping configuration is missing required fields.

**Solutions:**

1. **Check required fields** in mapping config:
   - `task_id`
   - `user_prompt`
   - `model_version`
   - `steps_path`
   - `step_mappings` with `step_id`, `type`, `content`, `timestamp`

2. **See mapping reference**: [Generic Mapping Reference](generic_mapping.md)

3. **Example minimal mapping**:
   ```yaml
   task_id: "id"
   user_prompt: "query"
   model_version: "model"
   steps_path: "events"
   step_mappings:
     step_id: "id"
     type: "type"
     content: "text"
     timestamp: "time"
   ```

## Warnings

### 1. "File size exceeds soft limit"

**Warning:**
```
[WARN] Warning: File size 12.5 MB exceeds soft limit of 10 MB
```

**Meaning:** File is larger than recommended 10MB but will still be processed (< 50MB hard limit).

**Action:** No action required, but consider filtering unnecessary events for better performance.

### 2. "No 'service.name' attribute found"

**Warning (OpenTelemetry):**
```
[WARN] Warning: No 'service.name' attribute found (actor_id will be empty)
```

**Meaning:** OTel trace lacks service name, so `actor_id` field will be empty in steps.

**Action:** Add service name to OTel resource attributes:
```json
{
  "resource": {
    "attributes": [
      {
        "key": "service.name",
        "value": {
          "stringValue": "my-agent"
        }
      }
    ]
  }
}
```

### 3. "Streaming token events detected"

**Warning (LangChain):**
```
[WARN] Warning: Streaming token events detected (will be collapsed into final outputs)
```

**Meaning:** LangChain trace contains streaming token events, which will be ignored.

**Action:** No action required. Final outputs are used instead of streaming tokens.

### 4. "OpenAI messages lack timestamps"

**Warning (OpenAI):**
```
[WARN] Warning: OpenAI messages lack timestamps - using current time for all steps
```

**Meaning:** OpenAI API responses don't include timestamps, so current time is used.

**Action:** No action required. This is a limitation of the OpenAI API format.

## Bulk Ingestion Issues

### Some traces fail in bulk mode

**Scenario:**
```
Summary: [OK] 8/10 traces converted successfully. 2 failed.
```

**Solutions:**

1. **Use --verbose** to see which files failed:
   ```bash
   agenteval-ingest traces/ --output-dir converted/ --verbose
   ```

2. **Ingest failed files individually** for detailed error messages:
   ```bash
   agenteval-ingest traces/failed_file.json --output trace.json --verbose
   ```

3. **Check error messages** in stderr output

### Mixed format directory

**Scenario:** Directory contains traces from multiple frameworks.

**Solution:** Use auto-detection (default):
```bash
agenteval-ingest traces/ --output-dir converted/
```

Each file will be processed with the appropriate adapter automatically.

## Performance Issues

### Slow conversion for large traces

**Solutions:**

1. **Filter unnecessary events** before ingestion:
   - Remove debug/logging events
   - Collapse streaming token events
   - Exclude tool result metadata

2. **Process in parallel** (manual parallelization):
   ```bash
   # Split traces into batches and process in parallel
   agenteval-ingest batch1/ --output-dir out1/ &
   agenteval-ingest batch2/ --output-dir out2/ &
   wait
   ```

3. **Check file size limits** - files >10MB may be slow

## Validation Issues

### Trace validates but evaluation fails

**Cause:** Trace is schema-valid but missing semantic information.

**Solutions:**

1. **Check step content**: Ensure `content` fields have meaningful text, not just IDs

2. **Verify timestamps**: Steps should have realistic timestamps in chronological order

3. **Include tool names**: For `tool_call` steps, include `tool_name` field

4. **Add actor_id**: For multi-agent traces, include `actor_id` to distinguish agents

## Getting Help

If you encounter an issue not covered here:

1. **Run with --verbose** to get detailed logs

2. **Check schema files**:
   - `schemas/trace_schema.json` - AgentEval trace schema
   - `docs/dataset_trace_schema.md` - Schema documentation

3. **Report issues** at: [GitHub Issues](https://github.com/anthropics/agenteval-workbench/issues)

Include:
- Input file format (anonymize sensitive data)
- Full error message
- CLI command used
- Version of agenteval (`pip show agenteval`)
