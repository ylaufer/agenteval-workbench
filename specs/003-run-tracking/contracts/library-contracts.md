# Library Contracts: Run Tracking

**Module**: `src/agenteval/core/runs.py`

## Public API

### `generate_run_id() -> str`

Generate a unique run identifier in `YYYYMMDDTHHMMSS_xxxx` format.

- Uses `datetime.utcnow()` for timestamp portion
- Uses `secrets.token_hex(2)` for 4-char hex suffix
- Returns: string matching `^\d{8}T\d{6}_[0-9a-f]{4}$`

### `create_run(dataset_dir: Path, rubric_path: Path) -> RunRecord`

Create a new run record and its directory.

- Generates a unique run_id via `generate_run_id()`
- Creates `runs/<run_id>/` directory
- Writes initial `run.json` with status `running`
- Validates paths via `_safe_resolve_within()`
- Returns: `RunRecord` with status `running`
- Raises: `ValueError` if paths are outside repo root

### `complete_run(run_id: str, num_cases: int) -> RunRecord`

Mark a run as completed.

- Reads existing `run.json`, updates status to `completed`
- Sets `completed_at` to current UTC timestamp
- Sets `num_cases` to provided count
- Writes updated `run.json`
- Returns: Updated `RunRecord`
- Raises: `FileNotFoundError` if run doesn't exist

### `fail_run(run_id: str, error: str, num_cases: int = 0) -> RunRecord`

Mark a run as failed.

- Reads existing `run.json`, updates status to `failed`
- Sets `error` message and `num_cases` (partial count)
- Writes updated `run.json`
- Returns: Updated `RunRecord`
- Raises: `FileNotFoundError` if run doesn't exist

### `list_runs() -> list[RunRecord]`

List all runs in reverse chronological order.

- Scans `runs/` directory for subdirectories
- Reads `run.json` from each valid subdirectory
- Skips directories with missing or invalid `run.json` (logs warning)
- Returns: List of `RunRecord` sorted by `started_at` descending
- Returns empty list if `runs/` directory doesn't exist

### `get_run(run_id: str) -> RunRecord | None`

Retrieve a specific run by ID.

- Reads `runs/<run_id>/run.json`
- Returns: `RunRecord` or `None` if not found

### `get_run_dir(run_id: str) -> Path`

Get the filesystem path for a run's directory.

- Returns: `<repo_root>/runs/<run_id>/`
- Does not verify existence

### `get_run_results(run_id: str) -> list[dict[str, Any]]`

Load all per-case evaluation templates from a run.

- Reads all `*.evaluation.json` files from `runs/<run_id>/` (excluding `summary.evaluation.json`)
- Returns: List of evaluation template dicts sorted by case_id
- Returns empty list if run directory doesn't exist

### `get_run_summary(run_id: str) -> dict[str, Any] | None`

Load the summary report from a run.

- Reads `runs/<run_id>/summary.evaluation.json`
- Returns: Summary dict or `None` if not found

## Service Layer Extensions

### `service.run_evaluation()` — Modified

When run tracking is active (default), `run_evaluation()`:

1. Calls `runs.create_run(dataset_dir, rubric_path)` to create a run record
2. Passes `runs.get_run_dir(run_id)` as `output_dir` to `runner.main()`
3. On success: calls `runs.complete_run(run_id, num_cases)`
4. On failure: calls `runs.fail_run(run_id, error_msg, partial_count)`
5. Returns evaluation results as before (backward-compatible return type)

### `service.list_runs() -> list[dict[str, Any]]` — New

Delegates to `runs.list_runs()`, converts to list of dicts.

### `service.get_run(run_id: str) -> dict[str, Any] | None` — New

Delegates to `runs.get_run()`, converts to dict.

### `service.get_run_results(run_id: str) -> list[dict[str, Any]]` — New

Delegates to `runs.get_run_results()`.

### `service.get_run_summary(run_id: str) -> dict[str, Any] | None` — New

Delegates to `runs.get_run_summary()`.
