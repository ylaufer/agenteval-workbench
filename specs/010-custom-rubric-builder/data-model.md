# Data Model: Custom Rubric Builder (Feature 010)

## Entities

### RubricDimension (in-memory / session state)

A single scoring dimension being edited in the UI. Maps 1:1 to the `dimensions[]` array items in the rubric JSON schema.

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | `str` | Yes | Snake_case machine identifier, e.g. `tool_use`. Pattern: `^[a-z0-9_]+$` |
| `title` | `str` | No | Human-readable name, e.g. "Tool Use Quality" |
| `scale` | `str` | Yes | One of `"0-2"`, `"1-5"`, `"0-4"` |
| `weight` | `float` | No | Weighting factor ≥ 0. Default 1.0 |
| `description` | `str` | Yes | What this dimension measures (non-empty) |
| `scoring_guide` | `dict[str, str]` | Yes | Score value → criteria text. Keys match scale |
| `evidence_required` | `bool` | No | Default `True` |

**Validation rules**:
- `name` must match `^[a-z0-9_]+$`
- `scale` must be one of the three schema-allowed values
- `description` must be non-empty
- `scoring_guide` must contain all keys for the chosen scale (e.g. `"0-2"` → `"0"`, `"1"`, `"2"`)
- `weight` must be ≥ 0

---

### RubricDraft (session state)

The full rubric being assembled in the UI, held in `st.session_state`.

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Rubric identifier, used for the filename (e.g. `rag_pipeline`) |
| `description` | `str` | Optional human-readable description |
| `dimensions` | `list[RubricDimension]` | Ordered list of dimensions (at least 1) |
| `template_source` | `str \| None` | Name of template this was started from, or None |

---

### Rubric (on-disk)

JSON file at `rubrics/{name}.json`. Schema governed by `schemas/rubric_schema.json`.

```json
{
  "version": "v1_rag_pipeline",
  "name": "RAG Pipeline Evaluation",
  "dimensions": [
    {
      "name": "accuracy",
      "title": "Accuracy",
      "scale": "0-2",
      "weight": 1.0,
      "description": "Factual correctness of claims in the response.",
      "evidence_required": true,
      "scoring_guide": {
        "0": "Major incorrect claims.",
        "1": "Partially correct with gaps.",
        "2": "All claims correct and supported."
      }
    }
  ]
}
```

**Naming convention**: `v{N}_{name}.json` — N is the next unused version prefix for that name.

---

### RubricTemplate (on-disk)

Starter template stored as JSON at `rubrics/templates/{template_id}.json`. Same structure as a saved Rubric, minus the `version` field (that is assigned on save).

| Template ID | Description |
|---|---|
| `general_agent` | Current v1 general-purpose agent dimensions |
| `rag_pipeline` | RAG-focused: accuracy, retrieval quality, source attribution, hallucination |
| `customer_support` | Support-focused: tone, resolution, escalation, policy compliance |
| `code_generation` | Code-focused: correctness, test coverage, security, code style |

---

## Python Representations

```python
# src/agenteval/core/rubric_builder.py

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

VALID_SCALES = ("0-2", "1-5", "0-4")

SCALE_KEYS: dict[str, list[str]] = {
    "0-2": ["0", "1", "2"],
    "1-5": ["1", "2", "3", "4", "5"],
    "0-4": ["0", "1", "2", "3", "4"],
}


@dataclass
class RubricDimension:
    name: str
    scale: Literal["0-2", "1-5", "0-4"]
    description: str
    scoring_guide: dict[str, str]
    title: str = ""
    weight: float = 1.0
    evidence_required: bool = True

    def to_dict(self) -> dict[str, object]: ...


@dataclass
class RubricDraft:
    name: str
    dimensions: list[RubricDimension] = field(default_factory=list)
    description: str = ""
    template_source: str | None = None

    def to_rubric_dict(self, version: str) -> dict[str, object]: ...
```

---

## Module Layout

```
src/agenteval/core/rubric_builder.py   — RubricDimension, RubricDraft, CRUD + validation
rubrics/templates/                     — 4 starter template JSON files
  general_agent.json
  rag_pipeline.json
  customer_support.json
  code_generation.json
app/page_rubric.py                     — Streamlit rubric builder page
tests/test_rubric_builder.py           — Unit tests
```

---

## Relationships

```
rubric_schema.json
    ← validates
rubrics/v1_agent_general.json          (existing, immutable)
rubrics/v{N}_{name}.json              (created by rubric_builder.save_rubric())
    ↑ referenced by
runs/{run_id}/run.json  rubric_path
    ↑ compared by
comparison.py                          (mismatch warning added)
```
