# CLI Contracts: Selective Evaluation (007)

---

## `agenteval-auto-score` — Extended

All existing arguments are unchanged. New optional arguments:

### New Arguments

```
--cases CASE_IDS
    Comma-separated list of case IDs to score (e.g., "case_001,case_003,case_007").
    When specified, all --filter-* arguments are ignored.

--filter-failure FAILURE_TYPE
    Filter cases by primary_failure value from expected_outcome.md front matter.
    Case-insensitive match. Example: --filter-failure "Tool Hallucination"

--filter-severity SEVERITIES
    Comma-separated severity levels to include.
    Valid values: Critical, High, Medium, Low (case-insensitive).
    Example: --filter-severity Critical,High

--filter-tag TAGS
    Comma-separated tags; case must have ALL listed tags.
    Tags: incomplete_execution, hallucination_tool_output, ui_mismatch,
          format_violation, has_tool_calls, multi_step, has_final_answer
    Example: --filter-tag "has_tool_calls"

--filter-pattern GLOB
    Glob pattern matched against case directory name.
    Uses fnmatch syntax (not regex). Example: --filter-pattern "case_0*"
```

### Behavior Matrix

| Arguments | Behavior |
|---|---|
| No filter args | Score all cases (current behavior, unchanged) |
| `--cases case_001,case_002` | Score only case_001, case_002; skip unknown IDs with warning |
| `--filter-failure "Tool Hallucination"` | Score cases where primary_failure matches |
| `--filter-severity Critical,High` | Score Critical and High severity cases |
| Multiple `--filter-*` args | AND logic — case must match ALL specified filters |
| Filter matches 0 cases | Print "No cases matched the specified filter." and exit 0 |

### Exit Codes (unchanged + new behaviors)

| Code | Condition |
|---|---|
| 0 | All matched cases scored successfully (or 0 cases matched filter) |
| 1 | One or more cases had scoring errors |
| 2 | Invalid arguments or dataset directory not found |

### Example Invocations

```bash
# Score specific cases
agenteval-auto-score --cases case_001,case_003,case_007

# Score by failure type
agenteval-auto-score --filter-failure "Tool Hallucination"

# Score by severity
agenteval-auto-score --filter-severity Critical,High

# Score by tag
agenteval-auto-score --filter-tag "has_tool_calls"

# Score by glob pattern
agenteval-auto-score --filter-pattern "case_0*"

# Combine filters (AND logic)
agenteval-auto-score --filter-failure "Tool Hallucination" --filter-severity Critical

# Existing behavior unchanged
agenteval-auto-score --dataset-dir data/cases --output-dir reports
```

---

## `agenteval-eval-runner` — Unchanged

Filter arguments are **not** added to `agenteval-eval-runner` in this feature.
