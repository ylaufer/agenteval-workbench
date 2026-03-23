# Research: Run Tracking

**Feature**: 003-run-tracking
**Date**: 2026-03-22

## Research Topics

### 1. Run ID Generation Strategy

**Decision**: Timestamp-prefixed with 4-character hex random suffix (`YYYYMMDDTHHMMSS_xxxx`)

**Rationale**: Human-readable, naturally sortable by filesystem and string comparison, unique under concurrent runs. The 4-hex-char suffix provides 65,536 possible values per second — more than sufficient for a single-user local tool.

**Alternatives considered**:
- UUID v4: Globally unique but not human-friendly, not naturally sortable
- Sequential integers: Simple but fragile with concurrent runs, requires mutex or lock file
- Timestamp-only: Not unique if two runs start in the same second

**Implementation**: `datetime.utcnow().strftime("%Y%m%dT%H%M%S") + "_" + secrets.token_hex(2)`

### 2. Run Storage Layout

**Decision**: Each run gets a directory under `runs/<run_id>/` containing `run.json` (metadata) and all evaluation output files.

**Rationale**: Directory-per-run isolates each run's artifacts completely. Using the run_id as directory name enables natural filesystem listing in chronological order. `run.json` stores metadata separately from evaluation outputs, keeping concerns clean.

**Alternatives considered**:
- Single JSON file for all runs (index-only): Doesn't solve output persistence; still need per-run directories for evaluation files
- SQLite database: Adds complexity and a new dependency; overkill for v1 local filesystem storage
- Nested date-based directories (`runs/2026/03/22/<id>`): Extra nesting without benefit; run IDs already contain dates

### 3. Run Index Approach

**Decision**: No separate index file. Derive the run list by scanning `runs/` directory entries and reading each `run.json`.

**Rationale**: Eliminates index-vs-reality synchronization bugs. Directory scanning is fast for local filesystems (hundreds of runs). The run.json files are small (< 1KB each). This approach handles manual deletion gracefully — deleted runs simply disappear from the list.

**Alternatives considered**:
- Central `runs/index.json`: Faster lookup but requires synchronization, breaks if manually edited, adds corruption risk
- Hybrid (index + fallback scan): Extra complexity without clear benefit at v1 scale

### 4. Backward Compatibility Strategy

**Decision**: Existing CLI commands (`agenteval-eval-runner`, `agenteval-eval-report`) continue to work unchanged. The runner's `--output-dir` argument still controls where files are written. The service layer's `run_evaluation()` function changes to create a run directory and pass it as `--output-dir` to the runner.

**Rationale**: The runner itself doesn't need to know about runs. Run tracking is an orchestration concern handled by `runs.py` and `service.py`. Users who call the runner directly get the same behavior as before. Users who go through the service layer (UI, new CLI) get run tracking automatically.

**Alternatives considered**:
- Modifying runner.py to accept `--run-id`: Violates backward compatibility, mixes concerns
- Wrapping runner in a subprocess: Unnecessary overhead; runner.main(argv) already works as a function call

### 5. Run Status Lifecycle

**Decision**: Three statuses: `running`, `completed`, `failed`. Status recorded in `run.json` and updated atomically via file write.

**Rationale**: Simple state machine. `running` is set at creation. On success, updated to `completed` with end timestamp. On failure, updated to `failed` with error info. If the process crashes mid-run, `run.json` retains `running` status, which the list/inspect commands can display as "incomplete" (a `running` run with no active process is effectively incomplete).

**Alternatives considered**:
- Adding `incomplete` as a fourth status: Requires detecting stale processes; `running` without an active process serves the same purpose
- Lock files for crash detection: Over-engineered for v1; filesystem locks are platform-dependent

### 6. UI Integration Pattern

**Decision**: Extend existing Streamlit pages rather than adding new pages. The Evaluate page gains a run history section. The Inspect page gains a run selector.

**Rationale**: Keeps the page count manageable (4 pages). Run tracking is an enhancement to existing workflows, not a separate workflow. Users evaluate → see run in history → inspect run details. This matches the natural flow.

**Alternatives considered**:
- New "Runs" page: Adds navigation complexity; separates run listing from evaluation context
- Replacing Evaluate page entirely: Too disruptive; existing page works well for the evaluation action itself
