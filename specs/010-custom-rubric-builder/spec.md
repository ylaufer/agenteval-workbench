# Feature Specification: Custom Rubric Builder

**Feature ID:** 010
**Phase:** 2.6
**Priority:** MEDIUM
**Status:** Not Started

---

## Problem Statement

The current rubric is defined in YAML and requires manual editing. Teams with different evaluation priorities (e.g., a customer support bot team doesn't care about UI grounding) can't easily create their own rubrics.

## Goal

Enable teams to define evaluation criteria that match their actual use case without editing raw YAML. Make rubric creation accessible via a UI-based editor with templates and validation.

---

## Capabilities

### 1. UI-Based Rubric Editor

- Create new rubrics from the Streamlit UI
- Add/remove/reorder dimensions
- Set per-dimension configuration:
  - `name` (machine identifier)
  - `title` (human-readable name)
  - `description` (what this dimension measures)
  - `scale` (min/max score values)
  - `weight` (relative importance)
  - `scoring_guide` (how to assign scores)
  - `evidence_required` (boolean)
- Preview the rubric in both YAML and JSON formats
- Validate against `rubric_schema.json` before saving

### 2. Rubric Templates

Provide starter templates for common use cases:

#### General Agent (current v1)
- Accuracy
- Tool Use
- Instruction Following
- UI Grounding
- Efficiency
- Security & Safety

#### RAG Pipeline
- Accuracy
- Retrieval Quality
- Source Attribution
- Hallucination Detection

#### Customer Support
- Tone & Empathy
- Resolution Quality
- Escalation Appropriateness
- Policy Compliance

#### Code Generation
- Correctness
- Test Coverage
- Security
- Code Style

Templates are starting points, fully editable.

### 3. Rubric Versioning

- Every rubric save creates a new version file (e.g., `v2_rag_pipeline.json`)
- Existing evaluation data is never orphaned — reports always reference their rubric version
- Comparison across rubric versions is explicit
- Warn if comparing runs that used different rubrics

---

## Data Flow

```
Template Selection → Dimension Editor → Preview → Validation → Save
     ↓                     ↓                ↓          ↓          ↓
Choose starter    Add/edit dims     See YAML/JSON  Schema check  v2_custom.json
```

---

## UI Design

### Rubric Builder Page

```
┌──────────────────────────────────────────────────────────────┐
│  Custom Rubric Builder                                       │
│                                                              │
│  Start from template: [General Agent ▾]                     │
│  Rubric Name: [custom_rag_v1____________]                   │
│  Description: [RAG pipeline evaluation rubric_________]     │
│                                                              │
│  Dimensions (6)                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ 1. Accuracy                              [Edit] [Remove]│ │
│  │    Weight: 1.0  Scale: 0-2  Evidence Required: Yes     │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ 2. Retrieval Quality                     [Edit] [Remove]│ │
│  │    Weight: 1.5  Scale: 0-2  Evidence Required: Yes     │ │
│  ├────────────────────────────────────────────────────────┤ │
│  │ ...                                                     │ │
│  └────────────────────────────────────────────────────────┘ │
│  [+ Add Dimension]                                           │
│                                                              │
│  Preview: [YAML] [JSON]                                      │
│  [Validate] [Save Rubric]                                    │
└──────────────────────────────────────────────────────────────┘
```

### Dimension Editor Modal

```
┌──────────────────────────────────────────────────────────────┐
│  Edit Dimension                                              │
│                                                              │
│  Name:        [accuracy_______________]                      │
│  Title:       [Accuracy________________]                     │
│  Description: [Measures factual correctness of responses__] │
│  Scale Min:   [0_]  Scale Max: [2_]                         │
│  Weight:      [1.0_]                                         │
│  Evidence Required: [✓]                                      │
│                                                              │
│  Scoring Guide:                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 0: Completely incorrect or no answer                 │  │
│  │ 1: Partially correct with significant gaps           │  │
│  │ 2: Fully correct and complete                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  [Cancel] [Save]                                             │
└──────────────────────────────────────────────────────────────┘
```

---

## Architecture

```
app/page_rubric.py               — Streamlit rubric builder page
app/components/dimension_editor.py — dimension editor modal
rubrics/templates/               — starter template directory
  ├─ general_agent.yaml
  ├─ rag_pipeline.yaml
  ├─ customer_support.yaml
  └─ code_generation.yaml
src/agenteval/core/rubric_builder.py — rubric creation/validation logic
```

### Core Functions

```python
# src/agenteval/core/rubric_builder.py

def create_rubric_from_template(template_name: str) -> dict:
    """Load a starter template."""
    ...

def validate_rubric(rubric: dict) -> tuple[bool, list[str]]:
    """Validate rubric against schema. Returns (is_valid, errors)."""
    ...

def save_rubric(rubric: dict, name: str, repo_root: Path) -> Path:
    """Save rubric with version suffix. Returns saved path."""
    ...

def list_rubrics(repo_root: Path) -> list[str]:
    """List all available rubrics."""
    ...
```

---

## Rubric Versioning Strategy

- Rubric filenames include version: `v1_general_agent.json`, `v2_rag_pipeline.json`
- Evaluation runs store rubric version in metadata
- Reports display rubric version used
- Comparison tool checks rubric version and warns if different

---

## Success Criteria

1. ✅ Users can create a new rubric from a template via the UI
2. ✅ Users can add, edit, remove, and reorder dimensions
3. ✅ Rubrics are validated against `rubric_schema.json` before saving
4. ✅ Preview shows YAML and JSON representations
5. ✅ Templates cover common use cases (general, RAG, support, code gen)
6. ✅ Rubric versioning prevents orphaned evaluation data
7. ✅ Comparison tool warns when comparing runs with different rubrics

---

## Dependencies

- Rubric schema (`schemas/rubric_schema.json`)
- Existing rubric loader (`src/agenteval/core/loader.py`)
- Service layer (`src/agenteval/core/service.py`)

---

## Testing Requirements

- Unit tests for rubric validation logic
- Unit tests for version suffix generation
- Integration tests: create → validate → save → load pipeline
- Template loading tests
- Schema validation tests

---

## Documentation Requirements

- Rubric builder usage guide
- Template selection guide
- Dimension configuration reference
- Versioning best practices
