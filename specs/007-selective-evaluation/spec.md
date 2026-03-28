# Feature Specification: Selective Evaluation

**Feature ID:** 007
**Phase:** 2.3
**Priority:** MEDIUM
**Status:** Not Started

---

## Clarifications

### Session 2026-03-28

- Q: Where do auto-detected tags come from — live derivation, pre-computed sidecar, or deferred? → A: Derive tags live from `trace.json` at filter time (no tag store, no pre-indexing).
- Q: During batch evaluation, if one case fails, what happens to the rest? → A: Continue on failure — process all cases, collect per-case errors, surface a summary at the end.
- Q: When "Evaluate This Case" / "Evaluate Selected" is triggered in the UI, which pipeline runs? → A: Auto-score only (`agenteval-auto-score`). Filter params added to `agenteval-eval-runner` is out of scope. UI should make clear that auto-scoring is being targeted; contextual explanation deferred to guided onboarding (feature 006 follow-up).
- Q: When multiple filter criteria are applied simultaneously, should cases match all or any? → A: AND logic — case must satisfy all specified criteria (intersection).
- Q: Should case_id pattern filtering use glob or regex syntax? → A: Glob only (e.g., `case_0*`, `case_01?`). No regex support.

---

## Problem Statement

Evaluating the entire dataset on every run is wasteful during iterative development. Teams need to focus on specific cases — by failure type, severity, tag, or manual selection.

## Goal

Transform evaluation from a blunt instrument into a surgical tool. Enable fast, focused iteration during agent development.

---

## Capabilities

### 1. Single Case Evaluation

- Click "Evaluate this case" from the inspect page
- Runs evaluation only for the selected case
- Immediately displays results

### 2. Multi-Select Batch Evaluation

- Checkbox selection on case list
- "Evaluate Selected" button
- Progress indicator for batch operations

### 3. Filter-Based Evaluation

- Filter cases before evaluation:
  - by failure type (primary or secondary)
  - by severity level (Critical, High, Medium, Low)
  - by auto-detected tags (e.g., `has_tool_calls`, `multi_step`) — derived live by inspecting `trace.json` at filter time; no sidecar or pre-indexing
  - by case_id pattern (glob syntax only, e.g., `case_0*`, `case_01?`)
- Apply filter → "Evaluate Filtered Cases" button

### 4. CLI Support

```bash
# Specific cases
agenteval-auto-score --cases case_001,case_003,case_007

# By failure type
agenteval-auto-score --filter-failure "Tool Hallucination"

# By severity
agenteval-auto-score --filter-severity Critical,High

# By tag
agenteval-auto-score --filter-tag "has_tool_calls"

# Case ID glob pattern
agenteval-auto-score --filter-pattern "case_0*"  # glob syntax only
```

### 5. Run Metadata

- Run tracking records the filter criteria used
- Runs are reproducible from metadata
- Report indicates which subset was evaluated

---

## UI Design

### Case List with Selection

```
[ ] case_001  Tool Hallucination     Critical  ⚙️
[✓] case_002  Constraint Violation   High      ⚙️
[✓] case_003  Instruction Drift      Medium    ⚙️

Filter by: [Failure Type ▾] [Severity ▾] [Tags ▾] [Pattern: _____]

[Evaluate Selected (2)]  [Evaluate All Filtered]
```

### Single Case Action

```
case_001 — Tool Hallucination
[View Trace] [Evaluate This Case] [View Report]
```

---

## Architecture

### Filtering Logic

```python
# src/agenteval/core/filtering.py

def filter_cases(
    cases: list[str],
    failure_type: str | None = None,
    severity: list[str] | None = None,
    tags: list[str] | None = None,
    pattern: str | None = None,
) -> list[str]:
    """Filter case list by multiple criteria.

    All criteria are combined with AND logic — a case must satisfy every
    specified criterion to be included (intersection, not union).
    Tags are derived live from trace.json at call time (no pre-indexing).
    Supported tag derivation: has_tool_calls (any tool_call step present),
    multi_step (step count > threshold), has_final_answer, etc.
    """
    ...
```

### CLI Updates

- Add filtering parameters to `agenteval-auto-score` only
- `agenteval-eval-runner` filtering is out of scope for this feature
- Store filter metadata in run configuration
- UI evaluate actions ("Evaluate This Case", "Evaluate Selected", "Evaluate Filtered") all target the auto-scoring pipeline; label wording must make this clear to the user

### Service Layer Updates

```python
# src/agenteval/core/service.py

def run_selective_evaluation(
    case_ids: list[str],
    rubric_path: str,
    output_dir: str,
) -> dict:
    """Run evaluation on a specific subset of cases."""
    ...
```

---

## Success Criteria

1. ✅ Users can evaluate a single case from the UI
2. ✅ Users can select multiple cases and evaluate them as a batch
3. ✅ Users can filter by failure type, severity, tag, and pattern
4. ✅ CLI supports all filtering options
5. ✅ Run metadata records filter criteria
6. ✅ Reports indicate which subset was evaluated
7. ✅ Performance: evaluating 5 cases is ~5x faster than evaluating 50

---

## Dependencies

- Existing case metadata (failure type, severity from `expected_outcome.md`)
- Run tracking system (003-run-tracking)
- Service layer (`src/agenteval/core/service.py`)

---

## Edge Cases & Error Handling

- **Zero-match filter**: If filter criteria match no cases, display a clear empty-state message ("No cases match the current filter") and disable the evaluate button. CLI exits with a non-zero code and a descriptive message.
- **Nonexistent case_ids** (CLI `--cases`): Skip unrecognized IDs, log a warning per skipped ID, continue with valid IDs.
- **Mid-batch failure**: Continue processing remaining cases. Collect per-case errors. Surface a summary at completion: "N evaluated, M failed" with per-case error details. Consistent with existing `EvaluatorRegistry` per-dimension error isolation.
- **All cases fail**: Return an error summary; do not write a partial report as if it were complete.

---

## Testing Requirements

- Unit tests for filtering logic
- Integration tests for selective evaluation
- CLI argument parsing tests
- Run metadata persistence tests

---

## Documentation Requirements

- Usage guide for filtering options
- Examples of common filtering workflows
- CLI reference for new parameters
