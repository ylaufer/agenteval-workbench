# Data Model: Ingestion UI

**Feature**: Ingestion UI (012)
**Date**: 2026-03-25
**Phase**: 1 (Design)

## Entities

### UploadedFile

Represents a file uploaded by the user (JSON trace or ZIP archive).

**Fields**:
- `name: str` — Original filename (e.g., "otel_trace.json")
- `size_bytes: int` — File size in bytes
- `content: bytes` — Raw file content
- `mime_type: str` — MIME type (e.g., "application/json", "application/zip")

**Validation Rules**:
- Size MUST be <= 50MB (hard limit, reject immediately)
- Size > 10MB triggers warning (soft limit, allow continuation)
- JSON files MUST be valid JSON (parseable)
- ZIP files MUST be valid ZIP archives

**State**: Immutable once uploaded

---

### ConversionPreview

Summary of what an adapter produced, shown before user commits to saving.

**Fields**:
- `adapter_name: str` — Adapter used (e.g., "OTelAdapter", "Auto-detected: LangChain")
- `step_count: int` — Total number of steps in converted trace
- `step_types: dict[str, int]` — Breakdown by step type (e.g., `{"thought": 3, "tool_call": 5, "observation": 5, "final_answer": 1}`)
- `warnings: list[str]` — Mapping warnings from adapter (e.g., ["Missing tool output for step 3"])
- `validation_errors: list[str] | None` — Schema validation errors (if any)

**Validation Rules**:
- If `validation_errors` is not empty → save MUST be blocked
- `step_count` MUST match length of converted trace's `steps` array
- `step_types` keys MUST be valid step types from trace schema

**State**: Regenerated when user changes adapter selection

---

### IngestionResult

Outcome of a single file's conversion (used for bulk uploads).

**Fields**:
- `filename: str` — Original filename from ZIP
- `status: Literal["converted", "failed", "skipped"]`
- `case_id: str | None` — Output case ID if converted (e.g., "case_042")
- `adapter_name: str | None` — Adapter used if converted
- `error: str | None` — Error reason if failed
- `skip_reason: str | None` — Reason if skipped (e.g., "not JSON")

**Validation Rules**:
- If `status == "converted"` → `case_id` and `adapter_name` MUST be set
- If `status == "failed"` → `error` MUST be set
- If `status == "skipped"` → `skip_reason` MUST be set

**State**: Immutable once bulk processing completes

---

### CaseDirectory

Target directory where converted trace and placeholder files are written.

**Fields**:
- `case_id: str` — Case identifier (e.g., "case_042")
- `path: Path` — Absolute path to case directory (e.g., `repo_root/data/cases/case_042`)
- `exists: bool` — Whether directory already exists (triggers overwrite warning)
- `files: dict[str, Path]` — Paths to required files (`{"trace": ..., "prompt": ..., "expected_outcome": ...}`)

**Validation Rules**:
- `case_id` MUST match pattern `case_\d{3}` (enforced by `get_next_case_id()`)
- `path` MUST be within repo root (enforced by `_safe_resolve_within()`)
- If `exists == True` → user MUST confirm overwrite before proceeding

**State Transitions**:
1. **Proposed** → User selects case ID, directory doesn't exist yet
2. **Exists** → Directory found, overwrite warning shown
3. **Created** → Files written, case is complete

---

## Relationships

```
UploadedFile (1) -----> (1) ConversionPreview
    ↓                        ↓
    |                        |
    └──> (adapter) ──────────┘
                ↓
         CaseDirectory (1) <----- (N) IngestionResult
```

**Explanation**:
- One `UploadedFile` produces one `ConversionPreview` via an adapter
- Preview determines the target `CaseDirectory`
- For bulk uploads, multiple `IngestionResult`s target different `CaseDirectory` instances

---

## Adapter Selection State Machine

```
[File Uploaded] --> [Auto-Detect]
                         ↓
                   ┌─────┴─────┐
                   ↓           ↓
            [Match Found]  [No Match]
                   ↓           ↓
            [Show Preview]  [Show Error + Manual Dropdown]
                   ↓           ↓
            [User Overrides?] [User Selects Adapter]
                   ↓           ↓
            [Regenerate Preview]
```

---

## Bulk Upload Processing Flow

```
[ZIP Uploaded] --> [Extract Entries]
                         ↓
                   [Filter JSON Files]
                         ↓
              ┌──────────┼──────────┐
              ↓          ↓          ↓
        [File 1]    [File 2]    [File N]
              ↓          ↓          ↓
        [Auto-Detect] [Auto-Detect] [Auto-Detect]
              ↓          ↓          ↓
        [Convert]    [Convert]    [Convert]
              ↓          ↓          ↓
     [IngestionResult] [IngestionResult] [IngestionResult]
              └──────────┴──────────┘
                         ↓
                  [Status Table]
```

**Error Handling**: Each file processes independently. One failure doesn't block others.

---

## Placeholder File Templates

### prompt.txt

```
[TODO: Add the agent prompt that produced this trace]

This trace was ingested from: {original_filename}
Adapter used: {adapter_name}
Ingested on: {timestamp}
```

### expected_outcome.md

```yaml
---
primary_failure: unknown
severity: unknown
tags: []
notes: ""
---

# Expected Outcome

[TODO: Describe the expected behavior and actual failure observed in this trace]

## Primary Failure Type

[TODO: Select one of the 12 canonical failure types from docs/failure_taxonomy.md]

## Evaluation Guidance

[TODO: Provide guidance for human reviewers on what to look for when evaluating this case]
```

---

## Validation Checkpoints

1. **Upload Validation** (pre-conversion)
   - File size within limits
   - JSON parseable (for single files)
   - ZIP valid (for bulk uploads)

2. **Conversion Validation** (post-adapter)
   - Converted trace validates against `schemas/trace_schema.json`
   - All required fields present
   - Step types valid

3. **Directory Validation** (pre-save)
   - Case ID not already in use (or user confirms overwrite)
   - Path within repo root
   - Permissions sufficient to write files

---

## Session State Schema (Streamlit)

```python
st.session_state = {
    "ingest_uploaded_file": UploadedFile | None,
    "ingest_adapter": str,  # "auto" | "otel" | "langchain" | "crewai" | "openai" | "generic"
    "ingest_mapping_config": dict | None,  # For Generic adapter
    "ingest_preview": ConversionPreview | None,
    "ingest_case_id": str | None,
    "ingest_bulk_results": list[IngestionResult] | None
}
```

---

## Notes

- All entities are data transfer objects (no behavior, pure data)
- Validation logic lives in service layer (`service.py`) and ingestion module
- State transitions managed by Streamlit session state
- Immutability ensures consistent preview display
