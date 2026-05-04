# Data Model: Run Comparison (008)

## Entities

### `CaseDelta`
Per-case comparison result. One entry per case found in either run.

| Field | Type | Notes |
|-------|------|-------|
| `case_id` | `str` | Case identifier |
| `status` | `Literal["improved","regressed","unchanged","new","removed"]` | Change classification |
| `overall_score_a` | `float \| None` | Normalized overall score from Run A (None if not in A) |
| `overall_score_b` | `float \| None` | Normalized overall score from Run B (None if not in B) |
| `overall_delta` | `float \| None` | `overall_score_b - overall_score_a` (None if either absent) |
| `dimension_deltas` | `dict[str, float \| None]` | Per-dimension normalized delta |
| `primary_failure_a` | `str \| None` | Primary failure type from Run A |
| `primary_failure_b` | `str \| None` | Primary failure type from Run B |

### `DimensionDelta`
Aggregate stats for one rubric dimension across all comparable cases.

| Field | Type | Notes |
|-------|------|-------|
| `dimension` | `str` | Dimension name (e.g. `"accuracy"`) |
| `mean_score_a` | `float \| None` | Mean normalized score in Run A |
| `mean_score_b` | `float \| None` | Mean normalized score in Run B |
| `mean_delta` | `float \| None` | `mean_score_b - mean_score_a` |
| `std_delta` | `float \| None` | Change in std dev (None if <2 scored cases) |
| `cases_improved` | `int` | Cases where this dimension score went up |
| `cases_regressed` | `int` | Cases where this dimension score went down |
| `cases_unchanged` | `int` | Cases where this dimension score was equal |

### `ComparisonSummary`
Aggregate across all cases.

| Field | Type | Notes |
|-------|------|-------|
| `total_cases_compared` | `int` | Cases present in both runs |
| `cases_improved` | `int` | Cases with positive overall delta |
| `cases_regressed` | `int` | Cases with negative overall delta |
| `cases_unchanged` | `int` | Cases with zero delta or both unscored |
| `cases_new` | `int` | Cases only in Run B |
| `cases_removed` | `int` | Cases only in Run A |
| `overall_score_delta` | `float \| None` | Mean overall_delta across comparable scored cases |
| `net_quality_change` | `Literal["improved","regressed","unchanged","insufficient_data"]` | Based on overall_score_delta sign |
| `new_failure_types` | `list[str]` | Failure types in B not in A |
| `resolved_failure_types` | `list[str]` | Failure types in A not in B |

### `ComparisonResult`
Top-level output of `compare_runs()`. Validated against `comparison_schema.json`.

| Field | Type | Notes |
|-------|------|-------|
| `comparison_id` | `str` | `comp_<timestamp>_<hex4>` |
| `run_a` | `str` | Run A identifier |
| `run_b` | `str` | Run B identifier |
| `timestamp` | `str` | ISO 8601 UTC timestamp of comparison |
| `summary` | `ComparisonSummary` | Aggregate metrics |
| `dimension_deltas` | `list[DimensionDelta]` | Per-dimension aggregate stats |
| `case_deltas` | `list[CaseDelta]` | Per-case deltas, sorted by `abs(overall_delta)` desc |

---

## Source Data

The comparison engine reads from existing run artifacts only:

```
runs/<run_id>/
├── run.json                        # RunRecord metadata
├── <case_id>.evaluation.json       # Per-case scores (read via get_run_results())
└── summary.evaluation.json         # Not used by comparison engine
```

No new persistent state is created unless `--output-json` is passed to CLI.

---

## Score Normalization

Raw scores (0–2 int) are normalized to [0.0, 1.0]:

```python
scale_max = float(scale_str.split("-")[1])   # "0-2" → 2.0
norm = raw_score / scale_max
```

Overall score = weighted average of normalized per-dimension scores (excluding unscored dimensions):

```python
overall = sum(norm_d * weight_d for d if score_d is not None) /
          sum(weight_d for d if score_d is not None)
```

Returns `None` if all dimensions are unscored.
