# Run Comparison

The **Run Comparison** feature lets you diff two AgentEval evaluation runs to
identify which cases improved or regressed, measure per-dimension trends, and
get a single net-quality-change verdict.

## CLI Usage

```bash
agenteval-compare --run-a <RUN_ID_A> --run-b <RUN_ID_B>
```

Aliases for readability:

```bash
agenteval-compare --baseline <RUN_ID_A> --current <RUN_ID_B>
```

Save the structured result to a JSON file:

```bash
agenteval-compare --run-a <RUN_ID_A> --run-b <RUN_ID_B> --output-json comparison.json
```

Run IDs are the short identifiers shown by `agenteval-list-runs`
(e.g. `20260325T184347_ee91`).

## Output

The command prints a human-readable summary to stdout and exits 0 on success,
1 on error.

The optional `--output-json` file contains a `ComparisonResult` object
validated against `schemas/comparison_schema.json`:

| Field | Description |
|---|---|
| `comparison_id` | Unique ID for this comparison (`comp_<timestamp>_<hex>`) |
| `run_a` / `run_b` | The two run IDs being compared |
| `timestamp` | ISO 8601 timestamp of when the comparison ran |
| `summary` | Aggregate metrics (see below) |
| `dimension_deltas` | Per-dimension stats across all compared cases |
| `case_deltas` | Per-case status and score delta |

### Summary Fields

| Field | Description |
|---|---|
| `total_cases_compared` | Cases present in both runs |
| `cases_improved` | Cases where score increased |
| `cases_regressed` | Cases where score decreased |
| `cases_unchanged` | Cases with no score change |
| `cases_new` | Cases only in run B |
| `cases_removed` | Cases only in run A |
| `overall_score_delta` | Mean normalized score B − mean normalized score A (null if no scores) |
| `net_quality_change` | `"improved"`, `"regressed"`, `"unchanged"`, or `"insufficient_data"` |
| `new_failure_types` | Failure types that appeared in run B but not run A |
| `resolved_failure_types` | Failure types from run A not present in run B |

### Case Status Values

| Status | Meaning |
|---|---|
| `improved` | Overall normalized score increased |
| `regressed` | Overall normalized score decreased |
| `unchanged` | Score identical (or both null) |
| `new` | Case only exists in run B |
| `removed` | Case only exists in run A |

## Score Normalization

Each case's overall score is a weighted average of its dimension scores,
normalized to [0, 1]:

```
normalized = raw_score / scale_max
overall = sum(normalized_i * weight_i) / sum(weight_i)
```

Dimensions with `null` scores are excluded from the weighted average.
If all dimensions are null, the overall score is null.

## Streamlit UI

Navigate to the **Compare** page in the sidebar. Select a baseline run (A) and
a current run (B) from the dropdowns, then click **Compare**.

The page displays:

- **Summary metrics** — net quality change badge, overall score delta, case counts
- **Dimension deltas** — per-dimension mean scores and improvement/regression counts
- **Case-level deltas** — sortable table with per-case status and score delta

## Python Library

```python
from agenteval.core.comparison import compare_runs
from dataclasses import asdict

result = compare_runs("20260325T184347_ee91", "20260325T184409_b550")
print(result.summary.net_quality_change)
print(result.summary.cases_improved, "improved")
print(result.summary.cases_regressed, "regressed")

# Serialize
import json
print(json.dumps(asdict(result), indent=2))
```

The `compare_runs()` function raises `FileNotFoundError` if either run ID is
not found.
