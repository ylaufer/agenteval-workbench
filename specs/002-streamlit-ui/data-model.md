# Data Model: Streamlit UI for AgentEval Workbench

## Overview

The Streamlit UI introduces no new persistent data entities. It operates on the existing data model defined by the AgentEval library. This document maps the existing entities to their UI usage patterns.

## Existing Entities (read/write via library functions)

### Benchmark Case (directory)

- **Location**: `data/cases/{case_id}/`
- **Files**: `prompt.txt`, `trace.json`, `expected_outcome.md`
- **Created by**: `generate_case()` in `dataset.generator`
- **Validated by**: `validate_dataset()` in `dataset.validator`
- **UI operations**: Create (Generate page), Read (Inspect page)

### ValidationResult (in-memory)

- **Source**: `validate_dataset()` return value
- **Fields**: `ok: bool`, `issues: tuple[ValidationIssue, ...]`
- **ValidationIssue fields**: `case_id: str`, `file_path: str`, `message: str`, `severity: str`
- **UI operations**: Display with severity grouping and case-ID partitioning (Generate page)

### CaseEvaluationTemplate (in-memory + file)

- **Source**: `run_evaluation()` return value (new wrapper)
- **Persisted to**: `reports/{case_id}.evaluation.json`, `reports/{case_id}.evaluation.md`
- **Key fields**: `case_id`, `primary_failure`, `severity`, `dimensions` (mapping of dimension scores), `trace_summary`, `auto_tags`, `case_version`
- **UI operations**: Generate (Evaluate page), Display (Inspect page)

### Summary Report (in-memory + file)

- **Source**: `generate_summary_report()` return value (new wrapper)
- **Persisted to**: `reports/summary.evaluation.json`, `reports/summary.evaluation.md`
- **Key fields**: `summary` (case counts), `dimensions` (per-dimension stats), `failure_summary` (frequency counts), `recommendations`
- **UI operations**: Generate and display (Report page)

### Rubric (read-only)

- **Source**: `load_rubric()` in `core.loader`
- **Location**: `rubrics/v1_agent_general.json`
- **UI operations**: Read for display in Inspect page (dimension details, scoring guides)

## New Wrapper Function Signatures

These are not new data entities but new library function interfaces that return existing types:

### `run_evaluation()` (added to `core/runner.py`)

```
Input:  dataset_dir: Path, rubric_path: Path, output_dir: Path, trace_schema_path: Path | None
Output: list[CaseEvaluationTemplate]
Side effect: writes .evaluation.json and .evaluation.md per case to output_dir
```

### `generate_summary_report()` (added to `core/report.py`)

```
Input:  input_dir: Path, rubric_path: Path, output_dir: Path, scores_dir: Path | None
Output: dict[str, Any]  (the summary report structure)
Side effect: writes summary.evaluation.json and summary.evaluation.md to output_dir
```

## Data Flow

```
User Input (case_id, failure_type)
    → generate_case() → Case directory on disk
    → validate_dataset() → ValidationResult (in-memory)
    → run_evaluation() → list[CaseEvaluationTemplate] + files on disk
    → generate_summary_report() → dict + files on disk
```

No new database, state management, or session persistence is needed. All state is on the filesystem.
