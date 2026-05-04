# Library Contract: Rubric Builder Module (Feature 010)

## Module: `src/agenteval/core/rubric_builder.py`

---

### `list_templates(repo_root) -> list[str]`

Return the available template IDs by scanning `rubrics/templates/`.

**Parameters**:
- `repo_root: Path`

**Returns**: Sorted list of template IDs (filename stems without `.json`), e.g. `["code_generation", "customer_support", "general_agent", "rag_pipeline"]`

---

### `load_template(template_id, repo_root) -> dict`

Load a starter template from `rubrics/templates/{template_id}.json`.

**Parameters**:
- `template_id: str` — template identifier
- `repo_root: Path`

**Returns**: Dict with `name`, optional `description`, and `dimensions` list

**Raises**:
- `FileNotFoundError` if template does not exist

---

### `validate_rubric(rubric: dict) -> tuple[bool, list[str]]`

Validate a rubric dict against `schemas/rubric_schema.json` and apply additional semantic checks.

**Parameters**:
- `rubric: dict` — rubric dict with `version`, `dimensions`, etc.

**Returns**: `(is_valid: bool, errors: list[str])` — errors is empty when valid

**Semantic checks beyond schema**:
- Each dimension `name` matches `^[a-z0-9_]+$`
- Each dimension `scoring_guide` contains all keys for its scale
- At least one dimension present

---

### `save_rubric(name, rubric, repo_root) -> Path`

Save a rubric dict to `rubrics/` with an auto-versioned filename.

**Parameters**:
- `name: str` — rubric base name (e.g. `rag_pipeline`). Must match `^[a-z0-9_]+$`
- `rubric: dict` — rubric dict (must pass `validate_rubric` first)
- `repo_root: Path`

**Returns**: `Path` to the saved file (e.g. `rubrics/v1_rag_pipeline.json`)

**Raises**:
- `ValueError` if `name` is empty or contains invalid characters
- `ValueError` if rubric fails validation

**Side effects**: Writes `rubrics/v{N}_{name}.json`. Sets `rubric["version"]` to `"v{N}_{name}"` before writing.

---

### `list_rubrics(repo_root) -> list[str]`

List all rubric files available in `rubrics/` (excludes `templates/` subdirectory).

**Parameters**:
- `repo_root: Path`

**Returns**: Sorted list of filenames (stems), e.g. `["v1_agent_general", "v1_rag_pipeline", "v2_rag_pipeline"]`

---

### `next_version(name, repo_root) -> str`

Determine the next version prefix for a given rubric name.

**Parameters**:
- `name: str` — rubric base name
- `repo_root: Path`

**Returns**: Version string, e.g. `"v1"` if none exist, `"v2"` if `v1_{name}.json` exists

---

## Service layer additions: `src/agenteval/core/service.py`

### `list_rubric_templates() -> list[str]`

Thin wrapper — delegates to `rubric_builder.list_templates()`.

### `load_rubric_template(template_id) -> dict`

Thin wrapper — delegates to `rubric_builder.load_template()`.

### `validate_rubric(rubric) -> tuple[bool, list[str]]`

Thin wrapper — delegates to `rubric_builder.validate_rubric()`.

### `save_rubric(name, rubric) -> str`

Thin wrapper — delegates to `rubric_builder.save_rubric()`. Returns the saved path as a string.

### `list_rubrics() -> list[str]`

Thin wrapper — delegates to `rubric_builder.list_rubrics()`.
