# CLI Contracts: Run Tracking

## New CLI Entry Points

### `agenteval-list-runs`

**Module**: `agenteval.core.runs:main_list`

**Arguments**:

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| (none) | — | — | Lists all runs; no arguments required |

**Output** (stdout):

```
Run ID                    Status      Cases  Started
────────────────────────  ──────────  ─────  ───────────────────
20260322T150030_c3d4      completed       12  2026-03-22 15:00:30
20260322T143015_a1b2      failed           8  2026-03-22 14:30:15
```

**Exit codes**:
- `0`: Success (including empty list)

**Empty state output**:
```
No evaluation runs found. Run an evaluation first:
  agenteval-eval-runner --dataset-dir data/cases --output-dir runs/<run_id>
```

### `agenteval-inspect-run`

**Module**: `agenteval.core.runs:main_inspect`

**Arguments**:

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `run_id` | positional `str` | (required) | The run identifier to inspect |

**Output** (stdout):

```
Run: 20260322T143015_a1b2
Status: completed
Started: 2026-03-22 14:30:15 UTC
Completed: 2026-03-22 14:31:02 UTC
Dataset: data/cases
Rubric: rubrics/v1_agent_general.json
Cases evaluated: 12

Per-case results:
  Case ID            Primary Failure              Severity
  ─────────────────  ───────────────────────────  ────────
  case_001           Incomplete Execution         High
  case_002           Tool Hallucination           Critical
  ...
```

**Exit codes**:
- `0`: Success
- `1`: Run not found

**Error output** (run not found):
```
Error: Run '20260322T999999_0000' not found.
```

## Existing CLI Entry Points (Unchanged)

### `agenteval-eval-runner`

No changes. Accepts `--output-dir` as before. When called directly, writes to the specified directory (no run tracking). Run tracking is orchestrated by the service layer, not the runner.

### `agenteval-eval-report`

No changes. Accepts `--input-dir` as before. Can be pointed at a run directory to generate summary for a specific run.

## pyproject.toml Additions

```toml
[project.scripts]
# ... existing entries ...
agenteval-list-runs = "agenteval.core.runs:main_list"
agenteval-inspect-run = "agenteval.core.runs:main_inspect"
```
