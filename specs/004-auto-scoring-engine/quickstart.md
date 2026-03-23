# Quickstart: Auto-Scoring Engine

**Feature**: 004-auto-scoring-engine
**Date**: 2026-03-22

## Scenario 1: Run rule-based auto-scoring via CLI

```bash
# Score all cases with rule-based evaluators (default)
agenteval-auto-score --dataset-dir data/cases --output-dir reports

# Output:
# Auto-scored 12 case(s):
#   case_001: 2/6 dimensions scored (tool_use=2, security_safety=2)
#   ...
# Results written to reports/
```

Produces `reports/case_XXX.auto_evaluation.json` for each case.

## Scenario 2: Run auto-scoring as a library call

```python
from agenteval.core.scorer import score_dataset, default_registry
from agenteval.core.loader import load_rubric
from pathlib import Path

rubric = load_rubric(Path("rubrics/v1_agent_general.json"))
results = score_dataset(
    dataset_dir=Path("data/cases"),
    output_dir=Path("reports"),
    rubric_path=Path("rubrics/v1_agent_general.json"),
)

for result in results:
    print(f"{result['case_id']}: {len(result['dimensions'])} dimensions")
```

## Scenario 3: Score a single case

```python
from agenteval.core.scorer import score_case
from agenteval.core.loader import load_rubric
from pathlib import Path

rubric = load_rubric(Path("rubrics/v1_agent_general.json"))
result = score_case(Path("data/cases/case_001"), rubric)

for dim_name, dim_result in result["dimensions"].items():
    score = dim_result["score"]
    notes = dim_result["notes"]
    print(f"  {dim_name}: {score} — {notes}")
```

## Scenario 4: Run auto-scoring with run tracking (via service layer)

```python
from agenteval.core.service import run_auto_scoring

results = run_auto_scoring()
# Creates a tracked run under runs/<run_id>/
# Writes auto_evaluation files to the run directory
```

## Scenario 5: Include auto-scores in summary reports

```bash
# First, run auto-scoring
agenteval-auto-score --dataset-dir data/cases --output-dir reports

# Then, generate report (automatically picks up auto_evaluation files)
agenteval-eval-report --input-dir reports \
  --output-json reports/summary.evaluation.json \
  --output-md reports/summary.evaluation.md

# The summary now includes both manual and auto scores with source attribution
```
