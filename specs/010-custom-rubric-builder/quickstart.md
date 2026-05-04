# Quickstart: Custom Rubric Builder (Feature 010)

## Scenario 1: Create a rubric from a template (library)

```python
from pathlib import Path
from agenteval.core.rubric_builder import (
    list_templates, load_template, validate_rubric, save_rubric
)
from agenteval.dataset.validator import _get_repo_root

repo_root = _get_repo_root()

# See available templates
templates = list_templates(repo_root)
print(templates)  # ["code_generation", "customer_support", "general_agent", "rag_pipeline"]

# Load the RAG template as a starting point
rubric = load_template("rag_pipeline", repo_root)

# Modify a dimension weight
rubric["dimensions"][0]["weight"] = 2.0

# Add the required version field before saving
# (save_rubric sets this automatically, but validate_rubric needs it)
rubric["version"] = "draft"
is_valid, errors = validate_rubric(rubric)
assert is_valid, errors

# Save — auto-assigns version v1_rag_pipeline
saved_path = save_rubric("rag_pipeline", rubric, repo_root)
print(saved_path)  # rubrics/v1_rag_pipeline.json
```

---

## Scenario 2: Save a second version (auto-increment)

```python
# After editing rubric further...
rubric["dimensions"].append({
    "name": "latency_quality",
    "title": "Latency Quality",
    "scale": "0-2",
    "weight": 0.5,
    "description": "Response time within acceptable bounds.",
    "evidence_required": False,
    "scoring_guide": {
        "0": "Response exceeds 10s with no justification.",
        "1": "Response between 3-10s.",
        "2": "Response under 3s or latency is justified."
    }
})

# v1_rag_pipeline.json already exists → saves as v2_rag_pipeline.json
saved_path = save_rubric("rag_pipeline", rubric, repo_root)
print(saved_path)  # rubrics/v2_rag_pipeline.json
```

---

## Scenario 3: UI workflow

1. Open the **Rubric Builder** page in the Streamlit UI
2. Select a template from the **Start from template** dropdown (or "Blank")
3. Enter a rubric name, e.g. `customer_rag_v1`
4. Edit dimensions:
   - Click **▼ accuracy** to expand a dimension and edit its fields
   - Use **↑** / **↓** buttons to reorder dimensions
   - Click **Remove** to delete a dimension
   - Click **+ Add Dimension** to add a new blank dimension
5. Click **Preview** to see the JSON and YAML representations
6. Click **Validate** to check against `rubric_schema.json`
7. Click **Save Rubric** — file is written to `rubrics/v1_customer_rag_v1.json`
8. A success message shows the saved path and the rubric is immediately available in the Evaluate page

---

## Scenario 4: Validate a hand-crafted rubric dict

```python
from agenteval.core.rubric_builder import validate_rubric

rubric = {
    "version": "v1_custom",
    "dimensions": [
        {
            "name": "accuracy",
            "scale": "0-2",
            "description": "Correctness of claims.",
            "scoring_guide": {"0": "Wrong", "1": "Partial", "2": "Correct"}
        }
    ]
}

is_valid, errors = validate_rubric(rubric)
print(is_valid)  # True
print(errors)    # []

# Missing scoring guide key
bad_rubric = {
    "version": "v1_bad",
    "dimensions": [
        {
            "name": "accuracy",
            "scale": "0-2",
            "description": "Correctness.",
            "scoring_guide": {"0": "Wrong", "2": "Correct"}  # missing "1"
        }
    ]
}
is_valid, errors = validate_rubric(bad_rubric)
print(is_valid)  # False
print(errors)    # ["dimension 'accuracy': scoring_guide missing key '1' for scale '0-2'"]
```

---

## Scenario 5: List saved rubrics

```python
from agenteval.core.rubric_builder import list_rubrics
from agenteval.dataset.validator import _get_repo_root

rubrics = list_rubrics(_get_repo_root())
print(rubrics)
# ["v1_agent_general", "v1_rag_pipeline", "v2_rag_pipeline"]
```
