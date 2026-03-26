# Service Layer API Contract: Ingestion Functions

**Feature**: Ingestion UI (012)
**Module**: `src/agenteval/core/service.py`
**Date**: 2026-03-25

## Overview

This contract defines the three new functions added to the service layer to support trace ingestion workflows. All functions follow the library-first architecture: they delegate to `src/agenteval/ingestion/` and provide orchestration for the UI.

---

## Function: `get_next_case_id()`

**Purpose**: Return the next available case ID by scanning existing cases.

**Signature**:
```python
def get_next_case_id() -> str
```

**Behavior**:
1. Scan `data/cases/` directory for existing case subdirectories
2. Extract numeric suffixes from `case_NNN` pattern
3. Find the maximum N
4. Return `f"case_{max_n + 1:03d}"` (zero-padded to 3 digits)
5. If no cases exist, return `"case_001"`

**Returns**:
- `str` — Next case ID (e.g., `"case_042"`)

**Errors**:
- **Never raises** (safe default behavior)

**Example**:
```python
next_id = get_next_case_id()  # "case_015" if case_001 through case_014 exist
```

**Test Scenarios**:
- Empty `data/cases/` → returns `"case_001"`
- Cases exist up to `case_010` → returns `"case_011"`
- Non-sequential cases (case_001, case_003, case_010) → returns `"case_011"`

---

## Function: `ingest_trace()`

**Purpose**: Convert a single trace file using specified adapter and create a complete case directory.

**Signature**:
```python
def ingest_trace(
    raw_content: dict,
    adapter_name: str = "auto",
    mapping_config: dict | None = None,
    output_case_id: str | None = None,
    original_filename: str = "trace.json"
) -> dict
```

**Parameters**:
- `raw_content` — Parsed JSON content from uploaded file
- `adapter_name` — Adapter to use: `"auto"` (default), `"otel"`, `"langchain"`, `"crewai"`, `"openai"`, `"generic"`
- `mapping_config` — Mapping config dict for Generic adapter (required if `adapter_name == "generic"`)
- `output_case_id` — Target case ID (e.g., `"case_042"`). If `None`, calls `get_next_case_id()`
- `original_filename` — Original uploaded filename (for placeholder metadata)

**Behavior**:
1. If `adapter_name == "auto"`:
   - Call `ingestion.auto_detect_adapter(raw_content)`
   - If no match → raise `ValueError("Format not recognized")`
2. Else:
   - Get adapter by name via `ingestion.get_adapter_by_name(adapter_name)`
3. Convert trace: `trace = adapter.convert(raw_content)`
4. Validate trace against `schemas/trace_schema.json`
5. If validation fails → raise `ValueError(f"Schema validation failed: {errors}")`
6. Create case directory: `data/cases/{output_case_id}/`
7. Write 3 files:
   - `trace.json` — Converted trace
   - `prompt.txt` — Placeholder with metadata
   - `expected_outcome.md` — Placeholder with YAML front matter
8. Return summary dict (see below)

**Returns**:
```python
{
    "case_id": "case_042",
    "trace_path": "data/cases/case_042/trace.json",
    "adapter_name": "OTelAdapter",
    "step_count": 12,
    "step_types": {"thought": 3, "tool_call": 5, "observation": 5, "final_answer": 1},
    "warnings": ["Missing tool output for step 3"],
    "validation_errors": []  # Empty if valid
}
```

**Errors**:
- `ValueError` — Format not recognized (auto-detect failed)
- `ValueError` — Schema validation failed
- `ValueError` — Generic adapter selected but no mapping config provided
- `FileExistsError` — Case directory already exists (caller should check first)
- `PermissionError` — Cannot write to case directory

**Example**:
```python
with open("otel_trace.json") as f:
    raw = json.load(f)

result = ingest_trace(
    raw_content=raw,
    adapter_name="auto",
    output_case_id="case_042"
)

print(f"Created {result['case_id']} with {result['step_count']} steps")
```

**Test Scenarios**:
- Valid OTel trace → auto-detection succeeds, case created
- Invalid JSON structure → auto-detection fails, ValueError raised
- Valid trace but fails schema → ValueError with validation errors
- Case directory exists → FileExistsError raised
- Generic adapter without mapping config → ValueError raised

---

## Function: `ingest_bulk()`

**Purpose**: Process a ZIP file containing multiple trace files and return per-file results.

**Signature**:
```python
def ingest_bulk(
    zip_bytes: bytes,
    adapter_name: str = "auto",
    mapping_config: dict | None = None,
    start_case_id: int | None = None
) -> list[dict]
```

**Parameters**:
- `zip_bytes` — ZIP file content as bytes
- `adapter_name` — Adapter to use for all files (default: `"auto"` per-file detection)
- `mapping_config` — Mapping config for Generic adapter (applies to all files)
- `start_case_id` — Starting case number (e.g., `42` → first file gets `case_042`). If `None`, uses `get_next_case_id()`

**Behavior**:
1. Parse ZIP using `zipfile.ZipFile(BytesIO(zip_bytes))`
2. Extract entries ending in `.json`
3. For each JSON file:
   - Try to parse JSON
   - If parse fails → status `"failed"`, error message
   - If parse succeeds → call `ingest_trace()` with auto-incremented case ID
   - If conversion succeeds → status `"converted"`
   - If conversion fails → status `"failed"`, error message
4. For each non-JSON file:
   - Status `"skipped"`, reason `"not JSON"`
5. Return list of per-file results

**Returns**:
```python
[
    {
        "filename": "trace1.json",
        "status": "converted",
        "case_id": "case_042",
        "adapter_name": "LangChainAdapter",
        "step_count": 8,
        "error": None
    },
    {
        "filename": "trace2.json",
        "status": "failed",
        "case_id": None,
        "adapter_name": None,
        "step_count": None,
        "error": "Schema validation failed: steps.0.type is required"
    },
    {
        "filename": "readme.txt",
        "status": "skipped",
        "case_id": None,
        "adapter_name": None,
        "step_count": None,
        "error": None,
        "skip_reason": "not JSON"
    }
]
```

**Errors**:
- `ValueError` — Invalid ZIP file
- **Note**: Per-file errors are captured in result dicts, not raised

**Example**:
```python
with open("batch_traces.zip", "rb") as f:
    zip_bytes = f.read()

results = ingest_bulk(
    zip_bytes=zip_bytes,
    adapter_name="auto",
    start_case_id=50
)

converted = [r for r in results if r["status"] == "converted"]
print(f"Converted {len(converted)} / {len(results)} files")
```

**Test Scenarios**:
- ZIP with 3 valid JSON files → 3 converted, case_050, case_051, case_052
- ZIP with 1 valid + 1 invalid JSON → 1 converted, 1 failed
- ZIP with JSON + non-JSON files → JSON processed, non-JSON skipped
- ZIP with zero JSON files → returns empty list (or all skipped)
- Corrupted ZIP file → ValueError raised immediately

---

## Error Handling Strategy

**Single File (`ingest_trace`)**:
- Raise exceptions immediately for all errors
- Caller (UI) catches and displays error message

**Bulk (`ingest_bulk`)**:
- Capture per-file errors in result dicts
- Continue processing remaining files (partial success allowed)
- Only raise for ZIP-level errors (invalid ZIP format)

---

## Integration with Existing Code

**Uses**:
- `ingestion.auto_detect_adapter()` — Auto-detection
- `ingestion.get_adapter_by_name()` — Manual adapter selection
- `loader.load_trace()` — Schema validation
- `_get_repo_root()`, `_safe_resolve_within()` — Safe filesystem operations

**Modifies**:
- None (purely additive)

**Dependencies**:
- `src/agenteval/ingestion/` (Feature 005)
- `src/agenteval/core/loader.py` (existing)
- `schemas/trace_schema.json` (existing)

---

## Acceptance Criteria

1. **AC-001**: `get_next_case_id()` returns correct next ID when cases exist
2. **AC-002**: `get_next_case_id()` returns `"case_001"` when no cases exist
3. **AC-003**: `ingest_trace()` with valid OTel trace creates 3 files in case directory
4. **AC-004**: `ingest_trace()` with invalid trace raises `ValueError` with schema errors
5. **AC-005**: `ingest_trace()` with `adapter_name="generic"` but no mapping raises `ValueError`
6. **AC-006**: `ingest_bulk()` processes all files and returns correct per-file status
7. **AC-007**: `ingest_bulk()` with 1 failure doesn't block other conversions
8. **AC-008**: `ingest_bulk()` skips non-JSON files with `"skipped"` status

---

## Test Fixtures

Reuse existing fixtures from `tests/ingestion/fixtures/`:
- `otel_trace.json`
- `langchain_trace.json`
- `crewai_trace.json`
- `openai_trace.json`

Add new fixtures:
- `bulk_traces.zip` — ZIP with 3 valid + 1 invalid JSON
- `empty.zip` — ZIP with no JSON files
- `non_json.zip` — ZIP with only .txt files
