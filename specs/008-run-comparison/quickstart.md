# Quickstart: Run Comparison (Feature 008)

## CLI

```bash
# Compare two runs — prints summary table
agenteval-compare --run-a 20260320T120000_aa11 --run-b 20260324T150000_bb22

# Save full comparison JSON for further analysis
agenteval-compare --run-a 20260320T120000_aa11 --run-b 20260324T150000_bb22 \
  --output-json reports/comparison.json

# Using baseline/current aliases
agenteval-compare --baseline 20260320T120000_aa11 --current 20260324T150000_bb22
```

## Python API

```python
from agenteval.core.comparison import compare_runs

result = compare_runs("20260320T120000_aa11", "20260324T150000_bb22")

print(result.summary.net_quality_change)      # "improved"
print(result.summary.overall_score_delta)     # 0.15
print(result.summary.cases_regressed)         # 2

# Per-case deltas sorted by magnitude
for case in result.case_deltas:
    print(f"{case.case_id}: {case.status} ({case.overall_delta:+.2f})")

# Dimension breakdown
for dim in result.dimension_deltas:
    print(f"{dim.dimension}: {dim.mean_delta:+.3f}")
```

## Streamlit UI

Navigate to the **Compare Runs** page from the sidebar. Select two runs from the dropdowns and click **Compare**. The page shows:

- Summary metrics (overall score delta, improvement/regression counts)
- Dimension delta table with color-coded indicators
- Case-level table sortable by delta magnitude
- Click any row to expand per-dimension breakdown

## Interpreting Results

| Indicator | Meaning |
|-----------|---------|
| ▲ improved | Normalized overall score increased |
| ▼ regressed | Normalized overall score decreased |
| – unchanged | Score equal or both unscored |
| new | Case only in Run B (added) |
| removed | Case only in Run A (removed) |

**Overall score delta** is a weighted average across all cases where both runs have at least one scored dimension. Dimensions with `null` scores are excluded from the average.

**Security & Safety** has 1.5× weight in the rubric — a small regression there has larger impact on the overall delta than the same regression in other dimensions.
