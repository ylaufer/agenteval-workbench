# Library Contract: Annotation Module (Feature 009)

## Module: `src/agenteval/core/annotations.py`

---

### `add_annotation(case_id, step_id, reviewer_id, content, severity, repo_root) -> Annotation`

Add a reviewer annotation to a trace step. Appends to the case's annotation file, creating it if absent.

**Parameters**:
- `case_id: str` — case identifier (must be non-empty)
- `step_id: str` — trace step identifier (must be non-empty)
- `reviewer_id: str` — reviewer identifier (must be non-empty)
- `content: str` — note text (must be non-empty)
- `severity: Literal["none", "low", "medium", "high"]` — issue severity
- `repo_root: Path` — repository root for path resolution

**Returns**: `Annotation` — the newly created annotation

**Raises**:
- `ValueError` if `content`, `case_id`, `step_id`, or `reviewer_id` is empty
- `ValueError` if `severity` is not a valid value

**Side effects**: Writes to `reports/{case_id}.annotations.json` (creates or appends)

---

### `get_annotations(case_id, repo_root) -> list[Annotation]`

Load all annotations for a case. Returns empty list if no file exists.

**Parameters**:
- `case_id: str`
- `repo_root: Path`

**Returns**: `list[Annotation]` — sorted by timestamp ascending

---

### `delete_annotation(case_id, annotation_id, repo_root) -> bool`

Remove an annotation by ID. Returns `True` if deleted, `False` if not found.

**Parameters**:
- `case_id: str`
- `annotation_id: str`
- `repo_root: Path`

**Returns**: `bool`

---

### `build_auto_eval_overlay(auto_eval: dict) -> AutoEvalOverlay`

Derive an overlay from an auto_evaluation dict. Pure function — no I/O.

**Parameters**:
- `auto_eval: dict` — a loaded `*.auto_evaluation.json` dict

**Returns**: `AutoEvalOverlay` with:
- `step_evidence`: dict mapping step_id → list of `DimEvidence` that cite it
- `case_flags`: list of `DimEvidence` for dimensions with scores but no step evidence

---

### `get_auto_eval_for_case(case_id, repo_root) -> dict | None`

Load the best available auto_evaluation for a case. Checks `reports/` first, then scans run directories for the most recent.

**Parameters**:
- `case_id: str`
- `repo_root: Path`

**Returns**: `dict | None` — loaded auto_evaluation dict, or None if none exists

---

## Service layer additions: `src/agenteval/core/service.py`

### `get_annotations(case_id) -> list[dict]`

Thin wrapper — delegates to `annotations.get_annotations()`. Returns list of annotation dicts.

### `add_annotation(case_id, step_id, reviewer_id, content, severity) -> dict`

Thin wrapper — delegates to `annotations.add_annotation()`. Returns annotation as dict.

### `delete_annotation(case_id, annotation_id) -> bool`

Thin wrapper — delegates to `annotations.delete_annotation()`.

### `get_auto_eval_for_case(case_id) -> dict | None`

Thin wrapper — delegates to `annotations.get_auto_eval_for_case()`.
