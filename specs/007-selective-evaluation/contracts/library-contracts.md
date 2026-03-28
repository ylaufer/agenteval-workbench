# Library Contracts: Selective Evaluation (007)

---

## `src/agenteval/core/filtering.py` — New Module

### `filter_cases()`

```python
def filter_cases(
    case_dirs: list[Path],
    case_ids: list[str] | None = None,
    failure_type: str | None = None,
    severity: list[str] | None = None,
    tags: list[str] | None = None,
    pattern: str | None = None,
) -> list[Path]:
```

**Behavior**:
- If `case_ids` is non-empty, returns dirs whose `case_dir.name` is in `case_ids`; all other filters ignored.
- Otherwise applies all non-None criteria as AND (intersection).
- `failure_type`: case-insensitive match against `primary_failure` in `expected_outcome.md` front matter. Missing/unreadable front matter → case excluded when filter is active.
- `severity`: case-insensitive match against `severity` in `expected_outcome.md`. Case must match any value in the list.
- `tags`: calls `tag_trace()` + `derive_structural_tags()` live on `trace.json`; case must have ALL listed tags.
- `pattern`: `fnmatch.fnmatch(case_dir.name, pattern)`.
- Cases where `trace.json` is missing or unreadable are skipped silently.
- Returns empty list (not an error) when no cases match.

**Raises**: Nothing — errors per case are skipped silently.

---

### `derive_structural_tags()`

```python
def derive_structural_tags(trace: Trace) -> tuple[str, ...]:
```

**Behavior**:
- `has_tool_calls`: any step with `type == "tool_call"` present.
- `multi_step`: `len(steps) > 3`.
- `has_final_answer`: any step with `type == "final_answer"` present.
- Returns a tuple of applicable tag strings (empty tuple if none apply).

**Raises**: Nothing.

---

### `get_dataset_tags()`

```python
def get_dataset_tags(case_dirs: list[Path]) -> set[str]:
```

**Behavior**:
- Loads `trace.json` for each case dir.
- Calls `tag_trace()` and `derive_structural_tags()` on each trace.
- Returns union of all tags across all cases.
- Unreadable cases are skipped.

**Raises**: Nothing.

---

## `src/agenteval/core/tagger.py` — Modified

### `tag_trace()` (extended)

```python
def tag_trace(trace: Trace) -> tuple[str, ...]:
```

**Change**: Returns existing failure tags PLUS structural tags from `derive_structural_tags()`. Backward compatible — callers receiving more tags is safe.

---

## `src/agenteval/core/service.py` — Modified

### `run_selective_evaluation()` — New Function

```python
def run_selective_evaluation(
    case_ids: list[str],
    dataset_dir: Path | None = None,
    output_dir: Path | None = None,
) -> dict[str, Any]:
```

**Behavior**:
- Resolves `case_dirs` from `case_ids` within `dataset_dir`.
- Skips nonexistent case IDs with a logged warning (continue-on-failure).
- Creates a tracked run (same pattern as `run_auto_scoring()`).
- Calls `score_dataset()` on the resolved subset.
- Records `filter_criteria = {"case_ids": case_ids}` in run metadata.
- Returns `{"results": [...], "errors": {...}, "run_id": "..."}`.

**Raises**: `RuntimeError` if all cases fail or the scoring engine raises.

---

### `get_dataset_tags()` — New Function (service wrapper)

```python
def get_dataset_tags(dataset_dir: Path | None = None) -> set[str]:
```

Delegates to `filtering.get_dataset_tags()`. Used by UI to populate tag filter dropdown.

---

## `src/agenteval/core/scorer.py` — Modified

### `score_dataset()` (signature extended)

```python
def score_dataset(
    dataset_dir: Path,
    output_dir: Path,
    rubric_path: Path | None = None,
    registry: EvaluatorRegistry | None = None,
    case_filter: list[Path] | None = None,   # ← NEW optional param
) -> list[dict[str, Any]]:
```

**Change**: When `case_filter` is provided, only those case dirs are scored. When `None`, behavior is unchanged (all cases in `dataset_dir`). Backward compatible.

### `main()` (CLI args extended)

New args added to `agenteval-auto-score`:

| Arg | Type | Description |
|---|---|---|
| `--cases` | `str` | Comma-separated case IDs (e.g., `case_001,case_003`) |
| `--filter-failure` | `str` | Match `primary_failure` (case-insensitive) |
| `--filter-severity` | `str` | Comma-separated severities (e.g., `Critical,High`) |
| `--filter-tag` | `str` | Comma-separated tags; case must have ALL |
| `--filter-pattern` | `str` | Glob pattern for case IDs (e.g., `case_0*`) |

**Backward compatibility**: When none of the new args are specified, behavior is identical to current.

**Zero-match behavior**: CLI prints a message and exits 0 (not an error) when filter matches no cases.

**Nonexistent case IDs** (via `--cases`): prints warning per skipped ID, continues with valid IDs.
