# Interface Contract: Wrapper Functions

## run_evaluation()

**Module**: `src/agenteval/core/runner.py`
**Purpose**: Programmatic API for generating evaluation templates. Extracted from `main()` logic.

### Signature

```python
def run_evaluation(
    dataset_dir: Path | None = None,
    rubric_path: Path | None = None,
    output_dir: Path | None = None,
    trace_schema_path: Path | None = None,
) -> list[CaseEvaluationTemplate]:
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| dataset_dir | Path \| None | `data/cases/` | Directory containing case subdirectories |
| rubric_path | Path \| None | `rubrics/v1_agent_general.json` | Path to rubric JSON |
| output_dir | Path \| None | `reports/` | Directory for output files |
| trace_schema_path | Path \| None | `schemas/trace_schema.json` | Path to trace JSON schema |

### Return Value

`list[CaseEvaluationTemplate]` — one template per successfully processed case. Cases that fail schema validation are skipped (logged but not in return list).

### Side Effects

- Creates `output_dir` if it does not exist
- Writes `{case_id}.evaluation.json` per case
- Writes `{case_id}.evaluation.md` per case

### Error Behavior

- Raises `RuntimeError` if rubric file is missing or invalid
- Raises `RuntimeError` if dataset directory does not exist
- Individual case errors (invalid trace, missing files) are skipped; processing continues

### Backward Compatibility

`main()` is refactored to call `run_evaluation()` internally. CLI behavior is unchanged.

---

## generate_summary_report()

**Module**: `src/agenteval/core/report.py`
**Purpose**: Programmatic API for aggregating evaluation templates into a summary report. Extracted from `main()` logic.

### Signature

```python
def generate_summary_report(
    input_dir: Path | None = None,
    rubric_path: Path | None = None,
    output_dir: Path | None = None,
    scores_dir: Path | None = None,
) -> dict[str, Any]:
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| input_dir | Path \| None | `reports/` | Directory containing `.evaluation.json` files |
| rubric_path | Path \| None | `rubrics/v1_agent_general.json` | Path to rubric JSON |
| output_dir | Path \| None | `reports/` | Directory for summary output files |
| scores_dir | Path \| None | `scores/` | Optional directory with reviewer score files |

### Return Value

`dict[str, Any]` with structure:

```json
{
  "summary": {
    "num_cases": 12,
    "num_scored_cases": 5,
    "rubric_version": "v1_agent_general"
  },
  "dimensions": {
    "dimension_name": {
      "scale_min": 0, "scale_max": 2,
      "weight": 1.0,
      "num_scored": 5, "num_unscored": 7,
      "mean_score": 1.4,
      "distribution": {"0": 1, "1": 1, "2": 3}
    }
  },
  "failure_summary": {
    "primary_failure_counts": {"Tool Hallucination": 3},
    "severity_counts": {"Critical": 2, "High": 5},
    "auto_tag_counts": {"incomplete_execution": 4}
  },
  "failed_cases": ["case_001", "case_003"],
  "recommendations": ["Focus on..."]
}
```

### Side Effects

- Creates `output_dir` if it does not exist
- Writes `summary.evaluation.json`
- Writes `summary.evaluation.md`

### Error Behavior

- Raises `RuntimeError` if no evaluation templates found in input_dir
- Raises `RuntimeError` if rubric file is missing or invalid

### Backward Compatibility

`main()` is refactored to call `generate_summary_report()` internally. CLI behavior is unchanged.
