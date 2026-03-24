# Feature Specification: Run Comparison

**Feature ID:** 008
**Phase:** 2.4
**Priority:** HIGH
**Status:** Not Started

---

## Problem Statement

Without comparison, evaluation runs exist in isolation. Teams can't answer "did our prompt change actually help?" or "did we regress on security?"

## Goal

Make every evaluation run part of a measurable improvement story. Enable teams to track progress, detect regressions, and validate that changes actually improved agent performance.

---

## Capabilities

### 1. Core Comparison Engine

- Compare any two runs by run_id
- Compute per-dimension score deltas
- Compute per-case score deltas
- Classify changes:
  - **Improved**: score increased
  - **Regressed**: score decreased
  - **Unchanged**: same score
  - **New**: case exists only in Run B
  - **Removed**: case exists only in Run A

### 2. Comparison Metrics

#### Dimension-Level Metrics
- Mean score change
- Standard deviation change
- Min/max shifts
- Number of improved vs. regressed cases per dimension

#### Failure-Level Metrics
- Failure type distribution change
- New failure types introduced
- Failure types resolved

#### Aggregate Metrics
- Overall score change (weighted by rubric)
- Total number of regressions
- Total number of improvements
- Net quality delta

### 3. CLI Interface

```bash
# Basic comparison
agenteval-compare --run-a <run_id_a> --run-b <run_id_b>

# Save comparison as JSON
agenteval-compare --run-a <run_id_a> --run-b <run_id_b> --output-json comparison.json

# Compare with specific baseline
agenteval-compare --baseline <run_id> --current <run_id>
```

### 4. UI: Side-by-Side Comparison Page

- Comparison page accessible from run list
- Side-by-side display of two runs
- Color-coded delta indicators:
  - 🟢 Green for improvements
  - 🔴 Red for regressions
  - ⚪ Gray for unchanged
- Sortable table: sort by largest regression, largest improvement, or by dimension
- Drill-down: click a case to see per-dimension diff
- Sparkline trend if more than 2 runs exist

---

## Data Model

### Comparison Result Schema

```json
{
  "comparison_id": "comp_20260324_001",
  "run_a": "run_20260320_001",
  "run_b": "run_20260324_001",
  "timestamp": "2026-03-24T10:30:00Z",
  "summary": {
    "total_cases_compared": 12,
    "cases_improved": 5,
    "cases_regressed": 2,
    "cases_unchanged": 5,
    "overall_score_delta": 0.15,
    "net_quality_change": "improved"
  },
  "dimension_deltas": [
    {
      "dimension": "accuracy",
      "mean_delta": 0.20,
      "cases_improved": 3,
      "cases_regressed": 1,
      "cases_unchanged": 8
    }
  ],
  "case_deltas": [
    {
      "case_id": "case_001",
      "status": "improved",
      "overall_delta": 0.30,
      "dimension_deltas": {
        "accuracy": 0.5,
        "tool_use": 0.0,
        "security_safety": 0.0
      }
    }
  ]
}
```

Schema location: `schemas/comparison_schema.json`

---

## Architecture

```
src/agenteval/core/comparison.py   — comparison engine
app/page_compare.py                — Streamlit comparison page
schemas/comparison_schema.json     — comparison result schema
```

### Core Functions

```python
# src/agenteval/core/comparison.py

def compare_runs(
    run_a_id: str,
    run_b_id: str,
    repo_root: Path,
) -> ComparisonResult:
    """Compare two evaluation runs and return structured diff."""
    ...

def classify_change(
    score_a: float | None,
    score_b: float | None,
) -> Literal["improved", "regressed", "unchanged", "new", "removed"]:
    """Classify the type of change between two scores."""
    ...
```

---

## UI Design

### Comparison Page Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Compare Runs                                                │
│                                                              │
│  Run A: run_20260320_001  (Baseline)                        │
│  Run B: run_20260324_001  (Current)                         │
│                                                              │
│  Summary                                                     │
│  ├─ Overall Score: 0.65 → 0.80 (+0.15) 🟢                   │
│  ├─ Cases Improved: 5                                       │
│  ├─ Cases Regressed: 2                                      │
│  └─ Cases Unchanged: 5                                      │
│                                                              │
│  Dimension Deltas                                            │
│  ┌────────────────────┬─────────┬─────────┬────────┐        │
│  │ Dimension          │ Run A   │ Run B   │ Delta  │        │
│  ├────────────────────┼─────────┼─────────┼────────┤        │
│  │ Accuracy           │ 0.60    │ 0.80    │ +0.20🟢│        │
│  │ Tool Use           │ 0.70    │ 0.65    │ -0.05🔴│        │
│  │ Security & Safety  │ 0.80    │ 0.80    │  0.00⚪│        │
│  └────────────────────┴─────────┴─────────┴────────┘        │
│                                                              │
│  Case-Level Changes (sort by: [Largest Regression ▾])       │
│  ┌────────────┬─────────┬─────────┬────────┬──────────┐    │
│  │ Case       │ Run A   │ Run B   │ Delta  │ Status   │    │
│  ├────────────┼─────────┼─────────┼────────┼──────────┤    │
│  │ case_002   │ 0.80    │ 0.50    │ -0.30🔴│ Regressed│    │
│  │ case_005   │ 0.60    │ 0.40    │ -0.20🔴│ Regressed│    │
│  │ case_001   │ 0.50    │ 0.80    │ +0.30🟢│ Improved │    │
│  └────────────┴─────────┴─────────┴────────┴──────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## Success Criteria

1. ✅ Users can compare any two runs from the UI
2. ✅ CLI comparison outputs structured JSON
3. ✅ Comparison results are validated against `comparison_schema.json`
4. ✅ UI clearly highlights improvements and regressions
5. ✅ Dimension-level and case-level deltas are computed correctly
6. ✅ Comparison results can be exported for further analysis

---

## Dependencies

- Run tracking system (003-run-tracking)
- Evaluation reports (`reports/*.evaluation.json`)
- Summary reports (`reports/summary.evaluation.json`)

---

## Testing Requirements

- Unit tests for delta computation logic
- Unit tests for change classification
- Integration tests: compare two real runs
- Edge cases: runs with different case sets, missing scores
- Schema validation tests

---

## Documentation Requirements

- Comparison workflow guide
- CLI reference for `agenteval-compare`
- Interpretation guide (how to read delta indicators)
- Examples of common comparison scenarios
