# CLI Contract: agenteval-ingest

**Command**: `agenteval-ingest`
**Version**: 1.0.0
**Entry Point**: `agenteval.ingestion.cli:main`

## Purpose

Convert traces from external agent frameworks to AgentEval format.

## Command Signature

```bash
agenteval-ingest <input> [options]
```

## Arguments

### Positional

| Argument | Type | Description |
|----------|------|-------------|
| `input` | path | Path to input trace file or directory |

### Options

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--output` | path | - | Output file path (required for single file) |
| `--output-dir` | path | - | Output directory (required for bulk ingest) |
| `--adapter` | string | auto | Adapter to use: `auto`, `otel`, `langchain`, `crewai`, `openai`, `generic` |
| `--mapping` | path | - | Mapping config file (required for `generic` adapter) |
| `--dry-run` | flag | false | Validate mapping without converting |
| `--repo-root` | path | auto | Repository root (auto-detected from git) |
| `--verbose` | flag | false | Show detailed conversion logs |
| `--help` | flag | - | Show help message |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Invalid arguments |
| 2 | Input file not found |
| 3 | No adapter can handle input format |
| 4 | Conversion failed |
| 5 | Schema validation failed |
| 6 | Security scan failed |
| 7 | Output path invalid (traversal attempt) |
| 8 | File size exceeds hard limit (50MB) |

## Examples

### Auto-detect format and convert

```bash
agenteval-ingest trace_export.json --output data/cases/case_new/trace.json
```

**Expected output**:
```
✓ Detected format: OpenTelemetry OTLP
✓ Converted 12 spans to 12 steps
✓ Validated against trace schema
✓ Security scan passed
✓ Wrote trace to data/cases/case_new/trace.json
```

### Specify adapter explicitly

```bash
agenteval-ingest langchain_run.json --adapter langchain --output data/cases/case_001/trace.json
```

**Expected output**:
```
✓ Using adapter: LangChain
✓ Converted 8 runs to 15 steps (tool calls expanded)
✓ Validated against trace schema
✓ Security scan passed
✓ Wrote trace to data/cases/case_001/trace.json
```

### Bulk ingest directory

```bash
agenteval-ingest ./exports/ --adapter otel --output-dir data/cases/
```

**Expected output**:
```
Processing traces: [████████░░] 4/5 files
✓ Converted exports/trace_1.json → data/cases/case_012/trace.json
✓ Converted exports/trace_2.json → data/cases/case_013/trace.json (8.2 MB - warning: large file)
✓ Converted exports/trace_3.json → data/cases/case_014/trace.json
✗ Failed exports/trace_4.json: missing required field 'spanId'
✓ Converted exports/trace_5.json → data/cases/case_015/trace.json

Summary: ✓ 4/5 traces converted successfully. 1 failed.
```

### Large file handling

```bash
agenteval-ingest large_trace.json --output data/cases/case_016/trace.json
```

**Expected output (>10MB <50MB)**:
```
⚠ Warning: Input file is 15.2 MB (exceeds 10 MB soft limit)
✓ Converted 450 spans to 450 steps
✓ Validated against trace schema
✓ Security scan passed
✓ Wrote trace to data/cases/case_016/trace.json
```

**Expected output (>50MB)**:
```
ERROR: File size exceeds hard limit

File: large_trace.json
Size: 52.1 MB
Limit: 50 MB

Fix: Split the trace into smaller segments or filter unnecessary data before ingestion.
Exit code: 8
```

### Validate custom mapping (dry-run)

```bash
agenteval-ingest trace.json --adapter generic --mapping my_mapping.yaml --dry-run
```

**Expected output**:
```
✓ Loaded mapping: my_mapping.yaml
✓ Mapping validation passed
⚠ Warning: field 'context_refs' has no mapping (will be empty)
✓ Dry-run conversion succeeded
```

## Error Messages

### No adapter can handle input

```
ERROR: No adapter can handle input file: trace.json

Tried adapters: OTel, LangChain, CrewAI, OpenAI, Generic
Hints:
  - For OpenTelemetry: check for 'resourceSpans' field
  - For LangChain: check for 'runs' field
  - For CrewAI: check for 'tasks' field
  - For OpenAI: check for 'messages' array
  - For custom formats: use --adapter generic --mapping <config>

Use --verbose for detailed format detection logs.
```

### Conversion failed

```
ERROR: Conversion failed for trace.json

Adapter: LangChain
Reason: Missing required field 'run_type' in run ID 'abc123'
Location: runs[3]

Fix: Ensure all runs have 'run_type' field.
```

### Schema validation failed

```
ERROR: Converted trace failed schema validation

File: trace.json
Schema: schemas/trace_schema.json
Error: 'step_type' is a required property
Location: steps[5]

Fix: Ensure adapter maps all required trace fields.
```

### Security scan failed

```
ERROR: Security scan failed for converted trace

File: trace.json
Violation: Absolute filesystem path detected
Location: steps[2].content
Pattern: /Users/alice/secret_data/

Fix: Remove absolute paths before ingestion or update adapter mapping.
```

### Output path traversal

```
ERROR: Output path invalid

Path: ../../etc/passwd
Reason: Path traversal attempt detected

Fix: Output path must be within repository root.
```

## Programmatic Usage

```python
from agenteval.ingestion import auto_detect_adapter, convert_trace
from agenteval.dataset.validator import validate_dataset
from pathlib import Path

# Load input
raw = json.loads(Path("trace.json").read_text())

# Auto-detect adapter
adapter = auto_detect_adapter(raw)
if not adapter:
    raise ValueError("No adapter can handle this format")

# Convert
trace = adapter.convert(raw)

# Validate
from agenteval.core.loader import validate_trace
validate_trace(trace)

# Write
output_path = Path("data/cases/case_new/trace.json")
output_path.write_text(json.dumps(trace, indent=2))
```

## Backward Compatibility

This is a new command. No backward compatibility constraints.

## Future Extensions

- `--format-version`: Specify framework version for better compatibility
- `--strict`: Fail on warnings (currently warnings are non-fatal)
- `--batch-size N`: Process N files at a time in bulk mode
- `--output-format`: Support YAML output in addition to JSON
