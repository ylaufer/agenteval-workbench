# Data Model: Run Tracking

**Feature**: 003-run-tracking
**Date**: 2026-03-22

## Entities

### RunStatus (Enum)

Represents the lifecycle state of an evaluation run.

| Value | Description |
|-------|-------------|
| `running` | Run is currently in progress |
| `completed` | Run finished successfully |
| `failed` | Run encountered an error |

**Notes**: A run with `running` status and no active process is effectively "incomplete" (crash recovery). No explicit `incomplete` value is needed.

### RunRecord (Frozen Dataclass)

Represents the metadata for a single evaluation run. Persisted as `runs/<run_id>/run.json`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | `str` | Yes | Unique identifier in `YYYYMMDDTHHMMSS_xxxx` format |
| `status` | `RunStatus` | Yes | Current lifecycle state |
| `started_at` | `str` (ISO 8601) | Yes | UTC timestamp when run began |
| `completed_at` | `str \| None` | No | UTC timestamp when run ended (null if running/failed-before-completion) |
| `dataset_dir` | `str` | Yes | Filesystem path to the dataset directory evaluated |
| `rubric_path` | `str` | Yes | Filesystem path to the rubric used |
| `num_cases` | `int` | Yes | Number of cases evaluated (0 if empty dataset) |
| `error` | `str \| None` | No | Error message if status is `failed` |

**Identity**: `run_id` is globally unique. Generated via `datetime.utcnow().strftime("%Y%m%dT%H%M%S") + "_" + secrets.token_hex(2)`.

**Immutability**: Frozen dataclass. Status transitions create a new instance written to disk.

### RunResult (Conceptual — not a separate type)

The collection of files produced during a run. Not modeled as a Python type; represented by the filesystem contents of `runs/<run_id>/`:

| File Pattern | Description |
|-------------|-------------|
| `run.json` | RunRecord serialized as JSON |
| `<case_id>.evaluation.json` | Per-case evaluation template (produced by runner) |
| `<case_id>.evaluation.md` | Per-case evaluation markdown (produced by runner) |
| `summary.evaluation.json` | Aggregated summary (produced by report) |
| `summary.evaluation.md` | Summary markdown (produced by report) |

### RunIndex (Conceptual — not a persisted entity)

The run index is derived at runtime by scanning the `runs/` directory and reading each `run.json`. No separate index file is maintained.

**Operations**:
- `list_runs()` → Scan `runs/`, read `run.json` from each subdirectory, return sorted by `started_at` descending
- `get_run(run_id)` → Read `runs/<run_id>/run.json`, return RunRecord or None
- `get_run_results(run_id)` → List evaluation files in `runs/<run_id>/`

## State Transitions

```
[create] → running → completed
                   → failed
```

- `running → completed`: Set `completed_at`, `num_cases`, `status = completed`
- `running → failed`: Set `error`, `status = failed`, preserve partial `num_cases`
- No transitions from `completed` or `failed` (terminal states)

## Filesystem Layout

```
<repo_root>/
└── runs/
    ├── 20260322T143015_a1b2/
    │   ├── run.json
    │   ├── case_001.evaluation.json
    │   ├── case_001.evaluation.md
    │   ├── case_002.evaluation.json
    │   ├── case_002.evaluation.md
    │   ├── summary.evaluation.json
    │   └── summary.evaluation.md
    ├── 20260322T150030_c3d4/
    │   ├── run.json
    │   └── ...
    └── ...
```

## Validation Rules

- `run_id` MUST match pattern `^\d{8}T\d{6}_[0-9a-f]{4}$`
- `started_at` MUST be valid ISO 8601 UTC timestamp
- `completed_at` MUST be null when status is `running`
- `completed_at` MUST be non-null when status is `completed`
- `error` MUST be null when status is not `failed`
- `dataset_dir` MUST be a valid filesystem path (validated at creation time via `_safe_resolve_within`)
- `rubric_path` MUST be a valid filesystem path (validated at creation time via `_safe_resolve_within`)
- `num_cases` MUST be >= 0
