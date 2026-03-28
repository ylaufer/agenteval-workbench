# Selective Evaluation

Selective evaluation lets you run auto-scoring on a targeted subset of benchmark cases instead of the entire dataset.

## CLI

### Score specific cases by ID

```bash
agenteval-auto-score --cases case_001,case_003,case_007
```

Unknown case IDs produce a per-ID warning and are skipped; valid IDs are still scored.

### Filter by failure type

```bash
agenteval-auto-score --filter-failure "Tool Hallucination"
```

Case-insensitive match against `primary_failure` in `expected_outcome.md`.

### Filter by severity

```bash
agenteval-auto-score --filter-severity Critical,High
```

Comma-separated. Case must match any listed value.

### Filter by tag

```bash
agenteval-auto-score --filter-tag "has_tool_calls"
```

Case must have **all** listed tags. Multiple tags: `--filter-tag "has_tool_calls,multi_step"`.

Available tags:

| Tag | Meaning |
|---|---|
| `has_tool_calls` | Trace has at least one `tool_call` step |
| `multi_step` | Trace has more than 3 steps |
| `has_final_answer` | Trace has at least one `final_answer` step |
| `incomplete_execution` | Tool call without following observation |
| `hallucination_tool_output` | Final answer contradicts tool output |
| `ui_mismatch` | Screenshot/UI state discrepancy |
| `format_violation` | Format constraint not followed |

### Filter by case ID glob pattern

```bash
agenteval-auto-score --filter-pattern "case_0*"
```

Uses `fnmatch` glob syntax (not regex). Matches against the case directory name.

### Combine filters (AND logic)

All filter criteria are combined as intersection — a case must match every specified criterion.

```bash
# Only Critical Tool Hallucination cases
agenteval-auto-score --filter-failure "Tool Hallucination" --filter-severity Critical

# Tool-call cases matching a pattern
agenteval-auto-score --filter-pattern "case_0*" --filter-tag "has_tool_calls"
```

### Zero-match behaviour

When the filter matches no cases, the CLI prints `"No cases matched the specified filter."` and exits with code 0 (not an error).

### Backward compatibility

When no filter arguments are supplied, behaviour is identical to before — all cases in `--dataset-dir` are scored.

## Python library

```python
from pathlib import Path
from agenteval.core.filtering import filter_cases

dataset_dir = Path("data/cases")
case_dirs = [d for d in dataset_dir.iterdir() if d.is_dir()]

selected = filter_cases(
    case_dirs,
    failure_type="Tool Hallucination",
    severity=["Critical"],
)
print(f"Selected {len(selected)} cases")
```

### Via service layer

```python
from agenteval.core.service import run_selective_evaluation

result = run_selective_evaluation(
    case_ids=["case_001", "case_003"],
)
print(f"Run ID: {result['run_id']}")
print(f"Scored: {len(result['results'])} cases")
if result["skipped"]:
    print(f"Skipped (not found): {result['skipped']}")
```

## Streamlit UI

### Single case

Open the **Inspect** page → select a case → click **Run Auto-Scoring on this case**. Results appear inline below the trace.

### Multi-select / filter-based

Open the **Evaluate** page → use the filter controls (Failure Type, Severity, Tags, Case ID Pattern) → check individual cases or click **Evaluate All Filtered**. The button label clarifies this runs auto-scoring only.

Filter criteria used in each run are recorded in `runs/<run_id>/run.json` under `filter_criteria` and shown in the Run History table.
