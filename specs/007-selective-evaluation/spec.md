# Feature Specification: Selective Evaluation

**Feature ID:** 007
**Phase:** 2.3
**Priority:** MEDIUM
**Status:** Not Started

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
  - by auto-detected tags (e.g., `has_tool_calls`, `multi_step`)
  - by case_id pattern (glob or regex)
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

# Case ID pattern
agenteval-auto-score --filter-pattern "case_0*"
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
    """Filter case list by multiple criteria."""
    ...
```

### CLI Updates

- Add filtering parameters to `agenteval-auto-score`
- Add filtering parameters to `agenteval-eval-runner`
- Store filter metadata in run configuration

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
