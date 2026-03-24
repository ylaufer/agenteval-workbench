# Feature Specification: Trace Annotation & Review UI

**Feature ID:** 009
**Phase:** 2.5
**Priority:** MEDIUM
**Status:** Not Started

---

## Problem Statement

The current inspect page renders trace steps linearly with no interactivity. Reviewers can't annotate specific steps, mark issues, or see where auto-scoring flagged problems. This makes the review process disconnected from the evaluation output.

## Goal

Transform review into a connected workflow where evaluation results and trace data are interleaved, not siloed. Enable collaborative review with persistent annotations.

---

## Capabilities

### 1. Inline Annotations

- Click any trace step to add a reviewer note
- Notes are persisted alongside the evaluation template
- Notes include:
  - `reviewer_id` (user identifier)
  - `timestamp` (when note was added)
  - `content` (note text)
  - `step_id` (which trace step this references)

### 2. Auto-Score Overlay

- When an auto-evaluation exists for a case, overlay it on the trace viewer
- Highlight steps that were flagged as evidence by rule-based or LLM evaluators
- Color-code steps by issue severity:
  - 🔴 Red: flagged by evaluator
  - 🟡 Yellow: warning
  - 🟢 Green: clean

### 3. Step-Level Diff View

- For cases that appear in two runs, show a step-by-step diff
- Highlight steps that changed between trace versions
- Useful when comparing traces from different model versions or prompt variants

### 4. Evidence Linking

- From the evaluation template, click an `evidence_step_id` to jump to that step in the trace viewer
- From a trace step, see which rubric dimensions reference it as evidence
- Bidirectional navigation between evaluation and trace

---

## Data Model

### Annotation Schema

```json
{
  "annotations": [
    {
      "annotation_id": "ann_001",
      "step_id": "step_3",
      "reviewer_id": "reviewer_alice",
      "timestamp": "2026-03-24T10:30:00Z",
      "content": "This tool call uses an incorrect parameter format",
      "severity": "high"
    }
  ]
}
```

Stored in: `reports/{case_id}.annotations.json`

### Auto-Evaluation Overlay

- Read from existing `{case_id}.auto_evaluation.json`
- Extract `evidence` fields from each dimension score
- Match `evidence.step_id` to trace steps

---

## UI Design

### Trace Viewer with Annotations

```
┌──────────────────────────────────────────────────────────────┐
│  Trace for case_001                                          │
│                                                              │
│  Step 1: thought 🟢                                          │
│  "I need to check the weather for Seattle"                  │
│                                                              │
│  Step 2: tool_call 🔴                                        │
│  get_weather(city: "Seattle", units: "celsius")             │
│  [!] Flagged by SecurityEvaluator: exposes PII              │
│  📝 Annotation (reviewer_alice, 2026-03-24):                │
│     "Tool call parameters should be sanitized"              │
│  [Add Note]                                                  │
│                                                              │
│  Step 3: observation 🟢                                      │
│  {"temperature": 15, "conditions": "cloudy"}                │
└──────────────────────────────────────────────────────────────┘
```

### Evidence Linking

```
Evaluation Template — Accuracy Dimension
Score: 1 / 2
Evidence:
  - step_3 [→ Jump to trace]
  - step_5 [→ Jump to trace]
Reasoning: "Agent provided correct weather but failed to..."
```

### Step-Level Diff

```
┌──────────────────────────────────────────────────────────────┐
│  Trace Diff: run_a vs. run_b                                │
│                                                              │
│  Step 1: thought (unchanged)                                │
│  "I need to check the weather for Seattle"                  │
│                                                              │
│  Step 2: tool_call (CHANGED)                                │
│  - run_a: get_weather(city: "Seattle")                      │
│  + run_b: get_weather(city: "Seattle", units: "celsius")    │
│                                                              │
│  Step 3: observation (unchanged)                            │
│  {"temperature": 15, "conditions": "cloudy"}                │
└──────────────────────────────────────────────────────────────┘
```

---

## Architecture

```
app/page_inspect.py               — enhanced trace viewer
app/components/annotation.py      — annotation UI components
app/components/evidence_link.py   — evidence linking UI
src/agenteval/core/annotations.py — annotation persistence logic
schemas/annotation_schema.json    — annotation data schema
```

### Core Functions

```python
# src/agenteval/core/annotations.py

def add_annotation(
    case_id: str,
    step_id: str,
    reviewer_id: str,
    content: str,
    severity: Literal["low", "medium", "high"],
    repo_root: Path,
) -> None:
    """Add a reviewer annotation to a trace step."""
    ...

def get_annotations(case_id: str, repo_root: Path) -> list[Annotation]:
    """Load all annotations for a case."""
    ...

def overlay_auto_scores(
    trace: dict,
    auto_eval: dict,
) -> dict:
    """Overlay auto-evaluation evidence onto trace steps."""
    ...
```

---

## Success Criteria

1. ✅ Reviewers can add notes to specific trace steps
2. ✅ Annotations persist and are visible on subsequent loads
3. ✅ Auto-evaluation evidence is overlaid on the trace viewer
4. ✅ Steps are color-coded by flagged status
5. ✅ Evidence linking works bidirectionally (eval ↔ trace)
6. ✅ Step-level diff view shows changes between runs

---

## Dependencies

- Auto-scoring engine (004-auto-scoring-engine)
- Trace schema (`schemas/trace_schema.json`)
- Auto-evaluation schema (`schemas/auto_evaluation_schema.json`)
- Streamlit UI (`app/page_inspect.py`)

---

## Testing Requirements

- Unit tests for annotation persistence
- Integration tests for auto-score overlay logic
- UI tests for evidence linking navigation
- Diff computation tests for trace comparison

---

## Documentation Requirements

- Annotation workflow guide
- Evidence linking usage examples
- Reviewer collaboration best practices
