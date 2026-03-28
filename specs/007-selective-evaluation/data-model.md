# Data Model: Selective Evaluation (007)

---

## New Entities

### FilterCriteria

Represents a set of filter conditions applied to select a case subset. All non-None fields are combined with AND logic.

| Field | Type | Required | Description |
|---|---|---|---|
| `case_ids` | `list[str] \| None` | No | Explicit case IDs; overrides all other filters when set |
| `failure_type` | `str \| None` | No | Match `primary_failure` field in `expected_outcome.md` front matter |
| `severity` | `list[str] \| None` | No | Match `severity` field; values: `Critical`, `High`, `Medium`, `Low` |
| `tags` | `list[str] \| None` | No | Match tags derived live from `trace.json`; case must have ALL listed tags |
| `pattern` | `str \| None` | No | Glob pattern matched against `case_id` (e.g., `case_0*`); uses `fnmatch` |

**Validation rules**:
- If `case_ids` is non-empty, `failure_type`, `severity`, `tags`, and `pattern` are ignored
- All string comparisons are case-insensitive for `failure_type` and `severity`
- `pattern` uses `fnmatch.fnmatch()` — no regex

---

## Modified Entities

### AutoEvaluation (existing — `src/agenteval/core/types.py`)

No schema changes. `auto_tags` field already present and populated by `tag_trace()`.

The `auto_tags` tuple will now include structural tags in addition to failure-pattern tags:

| Tag | Source | Meaning |
|---|---|---|
| `incomplete_execution` | existing `tagger.py` | Tool call without following observation |
| `hallucination_tool_output` | existing `tagger.py` | Final answer contradicts tool output |
| `ui_mismatch` | existing `tagger.py` | Screenshot/UI state discrepancy |
| `format_violation` | existing `tagger.py` | Format constraint not followed |
| `has_tool_calls` | **new** | Trace contains at least one `tool_call` step |
| `multi_step` | **new** | Trace contains more than 3 steps |
| `has_final_answer` | **new** | Trace contains at least one `final_answer` step |

---

### RunRecord (existing — `src/agenteval/core/types.py`)

No structural change. `filter_criteria` will be stored in the existing `config` or `metadata` field within `run.json` to preserve reproducibility.

```json
{
  "run_id": "...",
  "filter_criteria": {
    "failure_type": "Tool Hallucination",
    "severity": ["Critical", "High"],
    "tags": null,
    "pattern": null
  }
}
```

---

## New Modules

### `src/agenteval/core/filtering.py`

Pure library module — no external dependencies.

**Functions**:

```python
def filter_cases(
    case_dirs: list[Path],
    case_ids: list[str] | None = None,
    failure_type: str | None = None,
    severity: list[str] | None = None,
    tags: list[str] | None = None,
    pattern: str | None = None,
) -> list[Path]:
    """Return case_dirs matching all non-None criteria (AND logic).

    All criteria combined as intersection. Unknown/unreadable cases are skipped.
    Returns empty list if no cases match (not an error).
    """
```

```python
def derive_structural_tags(trace: Trace) -> tuple[str, ...]:
    """Derive structural tags from trace steps.

    Returns tags: has_tool_calls, multi_step, has_final_answer.
    Called live from filter_cases() when tag filter is active.
    """
```

```python
def get_dataset_tags(case_dirs: list[Path]) -> set[str]:
    """Return union of all tags across all cases in dataset.

    Used by UI to populate tag filter dropdown.
    Loads trace.json for each case and calls tag_trace() + derive_structural_tags().
    """
```

---

## Source of Truth for Case Metadata

| Filter Dimension | Source File | Field |
|---|---|---|
| Failure type | `expected_outcome.md` | `primary_failure` (YAML front matter) |
| Severity | `expected_outcome.md` | `severity` (YAML front matter) |
| Tags | `trace.json` | Derived live via `tag_trace()` + `derive_structural_tags()` |
| Case ID pattern | directory name | `case_dir.name` matched with `fnmatch` |

---

## File Layout (no new files beyond source)

```
src/agenteval/core/
├── filtering.py          ← NEW: filter_cases(), derive_structural_tags(), get_dataset_tags()
├── tagger.py             ← MODIFIED: add has_tool_calls, multi_step, has_final_answer tags
├── scorer.py             ← MODIFIED: add --cases/--filter-* CLI args
└── service.py            ← MODIFIED: add run_selective_evaluation(), get_dataset_tags()

app/
├── page_evaluate.py      ← MODIFIED: add case selection UI + filter controls
└── page_inspect.py       ← MODIFIED: add "Evaluate This Case" button

tests/
└── test_filtering.py     ← NEW: unit tests for filtering.py
```
