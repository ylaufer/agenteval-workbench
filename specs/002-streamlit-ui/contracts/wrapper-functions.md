# Interface Contract: Service Layer

**Module**: `src/agenteval/core/service.py`
**Purpose**: UI-facing orchestration layer that composes existing library APIs. Runner.py and report.py remain untouched.

---

## generate_case()

**Delegates to**: `agenteval.dataset.generator.generate_case()`

### Signature

```python
def generate_case(
    case_id: str | None = None,
    failure_type: str | None = None,
    output_dir: Path | None = None,
    overwrite: bool = False,
) -> Path:
```

### Return Value

`Path` — path to the created case directory.

### Error Behavior

- Raises `ValueError` if case exists and `overwrite=False`
- Raises `ValueError` if `failure_type` is not a valid taxonomy entry
- Raises `ValueError` if `output_dir` is outside repo root

---

## validate_dataset()

**Delegates to**: `agenteval.dataset.validator.validate_dataset()`

### Signature

```python
def validate_dataset(
    dataset_dir: Path | None = None,
    schema_path: Path | None = None,
) -> ValidationResult:
```

### Return Value

`ValidationResult` — contains `ok: bool` and `issues: tuple[ValidationIssue, ...]`.

---

## run_evaluation()

**Orchestration**: Calls `runner.main()` with constructed argv, then reads generated JSON files from disk.

### Signature

```python
def run_evaluation(
    dataset_dir: Path | None = None,
    output_dir: Path | None = None,
) -> list[dict[str, Any]]:
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| dataset_dir | Path \| None | `data/cases/` | Directory containing case subdirectories |
| output_dir | Path \| None | `reports/` | Directory for output files |

### Return Value

`list[dict[str, Any]]` — list of evaluation template dicts, one per case. Each dict is the parsed content of a `{case_id}.evaluation.json` file.

### Side Effects

- Creates `output_dir` if it does not exist
- Writes `{case_id}.evaluation.json` per case (via runner.main)
- Writes `{case_id}.evaluation.md` per case (via runner.main)

### Error Behavior

- Raises `RuntimeError` if runner.main() returns non-zero exit code
- Individual case errors (invalid trace, missing files) are skipped by runner; those cases won't appear in return list

### Backward Compatibility

runner.py is never modified. Service layer calls `runner.main()` as a function with argv.

---

## generate_summary_report()

**Orchestration**: Calls `report.main()` with constructed argv, then reads generated summary JSON.

### Signature

```python
def generate_summary_report(
    input_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| input_dir | Path \| None | `reports/` | Directory containing `.evaluation.json` files |
| output_dir | Path \| None | `reports/` | Directory for summary output files |

### Return Value

`dict[str, Any]` with structure matching `summary.evaluation.json`.

### Side Effects

- Writes `summary.evaluation.json` (via report.main)
- Writes `summary.evaluation.md` (via report.main)

### Error Behavior

- Raises `RuntimeError` if report.main() returns non-zero exit code

---

## list_cases()

### Signature

```python
def list_cases(
    dataset_dir: Path | None = None,
) -> list[str]:
```

### Return Value

`list[str]` — sorted list of case IDs (directory names) found in dataset_dir.

---

## load_case_metadata()

### Signature

```python
def load_case_metadata(
    case_dir: Path,
) -> dict[str, str]:
```

### Return Value

`dict[str, str]` — parsed YAML header fields from `expected_outcome.md` (Case ID, Primary Failure, Secondary Failures, Severity, case_version).

---

## load_trace()

**Delegates to**: `agenteval.core.loader.load_trace()`

### Signature

```python
def load_trace(
    case_dir: Path,
) -> dict[str, Any]:
```

### Return Value

`dict[str, Any]` — the trace JSON object with `steps`, `run_id`, `task_id`, etc.

---

## load_evaluation_template()

### Signature

```python
def load_evaluation_template(
    case_id: str,
    reports_dir: Path | None = None,
) -> dict[str, Any] | None:
```

### Return Value

`dict[str, Any] | None` — parsed evaluation template JSON, or `None` if the file does not exist.
