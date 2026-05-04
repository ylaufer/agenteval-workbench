# Library Contract: `agenteval.core.comparison`

## Public API

```python
from agenteval.core.comparison import compare_runs, classify_change, ComparisonResult
```

---

### `compare_runs(run_a_id, run_b_id, repo_root?) -> ComparisonResult`

Compare two evaluation runs and return a structured diff.

```python
def compare_runs(
    run_a_id: str,
    run_b_id: str,
    repo_root: Path | None = None,
) -> ComparisonResult:
    ...
```

**Parameters**:
- `run_a_id` — ID of the baseline run (must exist under `runs/`)
- `run_b_id` — ID of the current run (must exist under `runs/`)
- `repo_root` — override repo root (defaults to `_get_repo_root()`)

**Returns**: `ComparisonResult` dataclass  
**Raises**: `FileNotFoundError` if either run directory is missing  
**Raises**: `ValueError` if run data is malformed

---

### `classify_change(score_a, score_b) -> str`

Classify the type of change between two normalized overall scores.

```python
def classify_change(
    score_a: float | None,
    score_b: float | None,
) -> Literal["improved", "regressed", "unchanged"]:
    ...
```

**Notes**: Returns `"unchanged"` if both are None. Does not handle "new"/"removed" — those are determined at the case-set level in `compare_runs()`.

---

### `ComparisonResult` (dataclass)

See `data-model.md` for field definitions. Key attributes:

```python
result.comparison_id       # str
result.run_a               # str
result.run_b               # str
result.summary             # ComparisonSummary
result.dimension_deltas    # list[DimensionDelta]
result.case_deltas         # list[CaseDelta]
```

**Serialization**:
```python
import dataclasses, json
json.dumps(dataclasses.asdict(result), indent=2)
```

---

## Service Layer

`service.py` exposes `compare_runs()` as a thin wrapper for the Streamlit UI:

```python
from agenteval.core.service import compare_runs

result = compare_runs(run_a_id="20260320T...", run_b_id="20260324T...")
```

Returns the same `ComparisonResult`. Any `FileNotFoundError` or `ValueError` should be caught by the UI and displayed to the user.
