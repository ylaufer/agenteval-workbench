# Quickstart: Trace Annotation & Review UI (Feature 009)

## Scenario 1: Add an annotation to a trace step

```python
from pathlib import Path
from agenteval.core.annotations import add_annotation, get_annotations
from agenteval.dataset.validator import _get_repo_root

repo_root = _get_repo_root()

# Add a note to step_2 of case_001
ann = add_annotation(
    case_id="case_001",
    step_id="step_2",
    reviewer_id="alice",
    content="Tool call uses incorrect parameter format",
    severity="high",
    repo_root=repo_root,
)
print(ann.annotation_id)  # ann_3f7a1b2c

# Reload all annotations for the case
annotations = get_annotations("case_001", repo_root)
print(len(annotations))  # 1
```

---

## Scenario 2: Build an auto-score overlay

```python
import json
from agenteval.core.annotations import get_auto_eval_for_case, build_auto_eval_overlay
from agenteval.dataset.validator import _get_repo_root

repo_root = _get_repo_root()

auto_eval = get_auto_eval_for_case("case_001", repo_root)
if auto_eval:
    overlay = build_auto_eval_overlay(auto_eval)

    # Steps with evidence links
    for step_id, dims in overlay.step_evidence.items():
        print(f"{step_id}: flagged by {[d.dimension for d in dims]}")

    # Dimensions scored without step-level evidence
    for flag in overlay.case_flags:
        print(f"{flag.dimension}: score={flag.score} ({flag.notes[:40]})")
```

---

## Scenario 3: UI workflow

1. Open the **Inspect** page
2. Select a case from the dropdown
3. Trace steps are displayed with color-coded badges:
   - 🔴 Step flagged by an evaluator
   - 🟢 Step clean / no flags
   - ⚪ No auto-evaluation available
4. Click **Add Note** on any step to open the annotation form:
   - Enter your reviewer name (pre-filled from session)
   - Write your note
   - Select severity (none / low / medium / high)
   - Click **Save Note**
5. Notes appear inline below the step on all subsequent loads
6. The **Evaluation** section shows which steps each dimension cited as evidence; clicking **→ Step** highlights that step in the trace viewer

---

## Scenario 4: Delete an annotation

```python
from agenteval.core.annotations import delete_annotation
from agenteval.dataset.validator import _get_repo_root

deleted = delete_annotation("case_001", "ann_3f7a1b2c", _get_repo_root())
print(deleted)  # True
```
