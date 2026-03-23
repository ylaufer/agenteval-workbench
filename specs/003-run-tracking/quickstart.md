# Quickstart: Run Tracking

**Feature**: 003-run-tracking

## Scenario 1: Run an Evaluation with Tracking (via Service Layer)

```python
from agenteval.core import service

# Run evaluation — automatically creates a tracked run
results = service.run_evaluation()
# Results are persisted under runs/<run_id>/
```

## Scenario 2: List Past Runs

```python
from agenteval.core import service

runs = service.list_runs()
for run in runs:
    print(f"{run['run_id']} — {run['status']} — {run['num_cases']} cases")
```

CLI equivalent:
```bash
agenteval-list-runs
```

## Scenario 3: Inspect a Specific Run

```python
from agenteval.core import service

run = service.get_run("20260322T143015_a1b2")
print(run)  # Full metadata

results = service.get_run_results("20260322T143015_a1b2")
print(f"{len(results)} case evaluations")

summary = service.get_run_summary("20260322T143015_a1b2")
print(summary)  # Aggregated summary
```

CLI equivalent:
```bash
agenteval-inspect-run 20260322T143015_a1b2
```

## Scenario 4: Backward-Compatible Direct Runner Usage

```bash
# This still works exactly as before — no run tracking
agenteval-eval-runner --dataset-dir data/cases --output-dir reports
```

## Scenario 5: Streamlit UI

1. Launch: `streamlit run app/app.py`
2. Navigate to **Evaluate** page
3. Click "Run Evaluation" — creates a tracked run
4. View run history below the evaluation action
5. Navigate to **Inspect** page — select a run to see full details

## Test Scenarios

### T1: Create and complete a run
```python
from agenteval.core.runs import create_run, complete_run, get_run
from pathlib import Path

run = create_run(dataset_dir=Path("data/cases"), rubric_path=Path("rubrics/v1_agent_general.json"))
assert run.status == "running"
assert run.run_id matches r"^\d{8}T\d{6}_[0-9a-f]{4}$"

completed = complete_run(run.run_id, num_cases=12)
assert completed.status == "completed"
assert completed.completed_at is not None

fetched = get_run(run.run_id)
assert fetched == completed
```

### T2: List runs in reverse chronological order
```python
from agenteval.core.runs import create_run, list_runs

run1 = create_run(...)
run2 = create_run(...)
runs = list_runs()
assert runs[0].run_id == run2.run_id  # Most recent first
assert runs[1].run_id == run1.run_id
```

### T3: Handle missing run gracefully
```python
from agenteval.core.runs import get_run

result = get_run("nonexistent_id")
assert result is None
```

### T4: Fail a run with error
```python
from agenteval.core.runs import create_run, fail_run

run = create_run(...)
failed = fail_run(run.run_id, error="Trace validation failed", num_cases=3)
assert failed.status == "failed"
assert failed.error == "Trace validation failed"
assert failed.num_cases == 3
```
