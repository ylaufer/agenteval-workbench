# Data Model: Trace Annotation & Review UI (Feature 009)

## Entities

### Annotation

A reviewer note attached to a specific trace step.

| Field | Type | Required | Description |
|---|---|---|---|
| `annotation_id` | `str` | Yes | Unique identifier (`ann_<8-hex>`) |
| `case_id` | `str` | Yes | The case this annotation belongs to |
| `step_id` | `str` | Yes | The trace step this note references |
| `reviewer_id` | `str` | Yes | Reviewer identifier (free text) |
| `timestamp` | `str` | Yes | ISO 8601 UTC timestamp |
| `content` | `str` | Yes | Note text (non-empty) |
| `severity` | `str` | Yes | One of: `none`, `low`, `medium`, `high` |

**Storage**: `reports/{case_id}.annotations.json`

**File format**:
```json
{
  "case_id": "case_001",
  "annotations": [
    {
      "annotation_id": "ann_3f7a1b2c",
      "case_id": "case_001",
      "step_id": "step_2",
      "reviewer_id": "alice",
      "timestamp": "2026-05-04T10:30:00+00:00",
      "content": "Tool call uses incorrect parameter format",
      "severity": "high"
    }
  ]
}
```

---

### AnnotationFile (container)

The top-level file written to disk.

| Field | Type | Required | Description |
|---|---|---|---|
| `case_id` | `str` | Yes | Matches the case this file belongs to |
| `annotations` | `list[Annotation]` | Yes | Ordered list (append-only) |

---

### AutoEvalOverlay (derived, not persisted)

A mapping derived at runtime from an `auto_evaluation.json` file.

| Field | Type | Description |
|---|---|---|
| `step_evidence` | `dict[str, list[DimEvidence]]` | step_id → list of dimensions that cite this step |
| `case_flags` | `list[DimEvidence]` | Dimensions with scores but no step-level evidence |

### DimEvidence (derived)

| Field | Type | Description |
|---|---|---|
| `dimension` | `str` | Rubric dimension name |
| `score` | `int \| None` | Dimension score |
| `notes` | `str` | Evaluator notes |
| `evaluator_type` | `str` | `rule` or `llm` |

---

## Python Representations

```python
# src/agenteval/core/annotations.py

@dataclass(frozen=True)
class Annotation:
    annotation_id: str
    case_id: str
    step_id: str
    reviewer_id: str
    timestamp: str
    content: str
    severity: Literal["none", "low", "medium", "high"]

@dataclass(frozen=True)
class DimEvidence:
    dimension: str
    score: int | None
    notes: str
    evaluator_type: str

@dataclass(frozen=True)
class AutoEvalOverlay:
    step_evidence: dict[str, list[DimEvidence]]   # step_id → dims citing this step
    case_flags: list[DimEvidence]                  # dims scored but no step evidence
```

---

## Module Layout

```
src/agenteval/core/annotations.py    — Annotation dataclass, persistence, overlay builder
schemas/annotation_schema.json       — JSON Schema for annotation files
app/components/annotation.py         — Streamlit annotation widget (add/display notes)
app/page_inspect.py                  — Enhanced: overlay + annotations + evidence linking
tests/test_annotations.py            — Unit tests for annotations module
```

---

## Relationships

```
case_001/trace.json
    └── steps[]: step_id = "step_1", "step_2", ...
             ↑ referenced by
reports/case_001.auto_evaluation.json
    └── dimensions[tool_use].evidence_step_ids = ["step_2"]
             ↑ same step_ids
reports/case_001.annotations.json
    └── annotations[].step_id = "step_2"
```
