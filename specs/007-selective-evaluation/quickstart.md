# Quickstart: Selective Evaluation (007)

---

## CLI Usage

### Score specific cases by ID

```bash
agenteval-auto-score --cases case_001,case_003
```

### Score by failure type

```bash
agenteval-auto-score --filter-failure "Tool Hallucination"
```

### Score by severity

```bash
agenteval-auto-score --filter-severity Critical,High
```

### Score cases with specific tags

```bash
agenteval-auto-score --filter-tag "has_tool_calls"
```

### Combine filters (AND logic)

```bash
# Critical Tool Hallucination cases only
agenteval-auto-score --filter-failure "Tool Hallucination" --filter-severity Critical
```

### Glob pattern on case IDs

```bash
agenteval-auto-score --filter-pattern "case_0*"
```

---

## Library Usage

```python
from pathlib import Path
from agenteval.core.filtering import filter_cases

dataset_dir = Path("data/cases")
case_dirs = [d for d in dataset_dir.iterdir() if d.is_dir()]

# Filter to Critical Tool Hallucination cases
selected = filter_cases(
    case_dirs,
    failure_type="Tool Hallucination",
    severity=["Critical"],
)

print(f"Selected {len(selected)} cases")
```

### Via service layer

```python
from agenteval.core.service import run_selective_evaluation

result = run_selective_evaluation(
    case_ids=["case_001", "case_003", "case_007"],
)
print(f"Run ID: {result['run_id']}")
print(f"Scored: {len(result['results'])} cases")
if result['errors']:
    print(f"Errors: {result['errors']}")
```

---

## UI Usage

1. Open the **Evaluate** page
2. Use the filter controls to narrow the case list:
   - **Failure Type** dropdown
   - **Severity** dropdown
   - **Tags** dropdown
   - **Pattern** text input (glob, e.g. `case_0*`)
3. Check individual cases or use **Evaluate All Filtered**
4. Click **Run Auto-Scoring on Selected (N)** — the button label makes clear this runs auto-scoring

For a single case, open the **Inspect** page → navigate to a case → click **Evaluate This Case**.

---

## Available Tags

| Tag | Meaning |
|---|---|
| `has_tool_calls` | Trace has at least one `tool_call` step |
| `multi_step` | Trace has more than 3 steps |
| `has_final_answer` | Trace has at least one `final_answer` step |
| `incomplete_execution` | Tool call without a following observation |
| `hallucination_tool_output` | Final answer contradicts tool output |
| `ui_mismatch` | Screenshot/UI state discrepancy detected |
| `format_violation` | Format constraint not followed in final answer |
