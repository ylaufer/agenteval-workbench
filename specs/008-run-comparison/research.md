# Research: Run Comparison (008)

## Run Data Format

**Decision**: Read `runs/<run_id>/*.evaluation.json` directly (not via summary).  
**Rationale**: Per-case evaluation JSONs contain the per-dimension score data needed for case-level deltas. The summary only has aggregate stats. `get_run_results()` in `runs.py` already provides a sorted list of these dicts.  
**Alternatives considered**: Reading `summary.evaluation.json` — rejected because it only has mean scores per dimension, not per-case scores.

### Per-case evaluation JSON shape
```json
{
  "case_id": "case_001",
  "primary_failure": "Tool Hallucination",
  "severity": "Critical",
  "dimensions": {
    "accuracy": { "score": null, "weight": 1.0, "scale": "0-2", ... },
    "security_safety": { "score": 1, "weight": 1.5, "scale": "0-2", ... }
  }
}
```

---

## Score Normalization

**Decision**: Normalize raw scores to [0, 1] by dividing by `scale_max` (parsed from `"0-2"` → 2.0). Weight-average across scored dimensions for overall score.  
**Formula**:
```
norm_score_d = raw_score_d / scale_max_d
overall = sum(norm_score_d * weight_d) / sum(weight_d)   # only over scored dimensions
```
**Null score handling**: A dimension with `score: null` is excluded from the weighted average. If all dimensions are null, `overall_score` is `None`.  
**Alternatives considered**: Using raw 0-2 scores for deltas — rejected because weights differ (security_safety = 1.5x) so raw averaging would be misleading.

---

## Change Classification

**Decision**: Four-value classification at case level:
- `"improved"` — normalized overall score increased
- `"regressed"` — normalized overall score decreased
- `"unchanged"` — score equal or both None
- `"new"` — case exists only in Run B
- `"removed"` — case exists only in Run A

**Threshold**: any delta != 0 counts as improved/regressed (no dead-band). Floating-point comparison uses `round(delta, 6) != 0`.  
**Alternatives considered**: Adding a minimum delta threshold (e.g., 0.01) — deferred; can be added later if noise is a problem.

---

## Comparison ID

**Decision**: `comp_<timestamp>_<hex4>` format, generated at comparison time.  
**Rationale**: Consistent with existing `run_id` pattern (`20260323T010455_745a`). Prefix `comp_` makes the purpose unambiguous.

---

## Output / Persistence

**Decision**: `compare_runs()` returns a `ComparisonResult` dataclass in memory. CLI prints a summary to stdout and optionally writes JSON to `--output-json <path>`. No automatic persistence under `runs/`.  
**Rationale**: Comparisons are derived artifacts — they can be regenerated any time. Storing them adds directory clutter without benefit for MVP.  
**Alternatives considered**: Auto-saving to `runs/<comp_id>/comparison.json` — deferred to a later milestone if users want comparison history.

---

## Failure Type Deltas

**Decision**: Compute from per-case `primary_failure` fields. Report new failure types (appeared in B but not A) and resolved failure types (in A but not in B).  
**Rationale**: This directly answers "did we introduce new failure modes?" which is the core question.

---

## Dimension-Level Aggregate Stats

**Decision**: For each dimension, report: `mean_score_a`, `mean_score_b`, `mean_delta`, `cases_improved`, `cases_regressed`, `cases_unchanged` (only over cases present in both runs with at least one score).  
**Std dev change**: Included in `ComparisonResult` as `std_delta` per dimension — computed only if ≥2 scored cases exist.

---

## Rubric Weights Source

**Decision**: Read weights directly from the per-case evaluation JSON (`dimensions[d]["weight"]`), not from the rubric YAML. This avoids loading a second file and stays consistent with what was actually used at scoring time.

---

## UI Integration

**Decision**: New `page_compare.py` page added to sidebar as "Compare Runs". Run selectors use `list_runs()` from `runs.py`. Comparison triggered by button click; result cached in `st.session_state`.  
**Sparkline trend**: Deferred — requires ≥3 runs. Noted in UI as "coming soon" when only 2 runs exist.
