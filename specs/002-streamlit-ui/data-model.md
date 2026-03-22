# Data Model: Streamlit UI for AgentEval Workbench

## Overview

The Streamlit UI introduces no new persistent data entities. It operates on the existing data model defined by the AgentEval library. A new service layer (`src/agenteval/core/service.py`) provides orchestration functions that compose existing library APIs. Runner.py and report.py remain untouched.

## Existing Entities (read/write via service layer)

### Benchmark Case (directory)

- **Location**: `data/cases/{case_id}/`
- **Files**: `prompt.txt`, `trace.json`, `expected_outcome.md`
- **Created by**: `service.generate_case()` → delegates to `dataset.generator.generate_case()`
- **Validated by**: `service.validate_dataset()` → delegates to `dataset.validator.validate_dataset()`
- **UI operations**: Create (Generate page), Read (Inspect page)

### ValidationResult (in-memory)

- **Source**: `service.validate_dataset()` return value
- **Fields**: `ok: bool`, `issues: tuple[ValidationIssue, ...]`
- **ValidationIssue fields**: `case_id: str`, `file_path: str`, `message: str`, `severity: str`
- **UI operations**: Display with severity grouping and case-ID partitioning (Generate page)

### CaseEvaluationTemplate (file-based)

- **Source**: `service.run_evaluation()` calls `runner.main()` which writes files, then reads generated JSON
- **Persisted to**: `reports/{case_id}.evaluation.json`, `reports/{case_id}.evaluation.md`
- **Key fields**: `case_id`, `primary_failure`, `severity`, `dimensions`, `trace_summary`, `auto_tags`, `case_version`
- **UI operations**: Generate (Evaluate page), Display via `service.load_evaluation_template()` (Inspect page)

### Summary Report (file-based)

- **Source**: `service.generate_summary_report()` calls `report.main()` which writes files, then reads generated JSON
- **Persisted to**: `reports/summary.evaluation.json`, `reports/summary.evaluation.md`
- **Key fields**: `summary` (case counts), `dimensions` (per-dimension stats), `failure_summary` (frequency counts), `recommendations`
- **UI operations**: Generate and display (Report page)

### Rubric (read-only)

- **Source**: `core.loader.load_rubric()`
- **Location**: `rubrics/v1_agent_general.json`
- **UI operations**: Loaded by runner during evaluation; not directly exposed in UI v1

## Service Layer Functions

All UI-facing orchestration lives in `src/agenteval/core/service.py`:

| Function | Delegates To | Returns |
|----------|-------------|---------|
| `generate_case()` | `dataset.generator.generate_case()` | `Path` |
| `validate_dataset()` | `dataset.validator.validate_dataset()` | `ValidationResult` |
| `run_evaluation()` | `runner.main(argv)` + read JSON | `list[dict]` |
| `generate_summary_report()` | `report.main(argv)` + read JSON | `dict` |
| `list_cases()` | directory listing | `list[str]` |
| `load_case_metadata()` | parse YAML header | `dict[str, str]` |
| `load_trace()` | `core.loader.load_trace()` | `dict` |
| `load_evaluation_template()` | read JSON file | `dict | None` |

## Data Flow

```
User Input (case_id, failure_type)
    → service.generate_case() → Case directory on disk
    → service.validate_dataset() → ValidationResult (in-memory)
    → service.run_evaluation() → runner writes files → service reads JSON → list[dict]
    → service.generate_summary_report() → report writes files → service reads JSON → dict
```

No new database, state management, or session persistence is needed. All state is on the filesystem. Runner.py and report.py are never modified.
