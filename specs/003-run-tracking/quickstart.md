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
