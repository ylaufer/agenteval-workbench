# Dataset Structure & Conventions

This document defines the formal structure, naming conventions, and validation rules for the AgentEval benchmark dataset.

The goal is to ensure:

- Consistency across cases
- Deterministic validation
- Governance-ready benchmark construction
- Scalability for future case expansion

---

# 1. Repository Structure

```
agenteval-workbench/
│
├── data/
│   └── cases/
│       ├── case_001/
│       │   ├── prompt.txt
│       │   ├── trace.json
│       │   └── expected_outcome.md
│       ├── case_002/
│       └── ...
│
├── docs/
│   ├── failure_taxonomy.md
│   ├── failure_coverage_matrix.md
│   └── dataset_structure.md
│
├── src/
│   └── agenteval/
│       └── dataset/
│           ├── validator.py
│           └── generator.py
│
├── .pre-commit-config.yaml
├── pyproject.toml
└── .github/workflows/
```

---

# 2. Case Directory Naming Convention

Each case must follow:

```
case_XXX
```

Where:

- `XXX` is a zero-padded three-digit identifier
- Examples:
  - `case_001`
  - `case_010`
  - `case_023`

Rules:

- Lowercase only
- Underscore separator
- No additional suffixes

---

# 3. Required Files Per Case

Each case directory must contain exactly:

```
prompt.txt
trace.json
expected_outcome.md
```

All three files are mandatory.

---

# 4. File Specifications

## 4.1 prompt.txt

Plain text file containing:

- The exact user prompt
- No additional metadata
- No comments

Must match the `user_prompt` field inside `trace.json`.

---

## 4.2 trace.json

Must conform to the dataset trace schema.

Traces are modeled as an **append-only, deterministically ordered event log**. The `steps` array
captures every plan, reasoning span, tool invocation, observation, and final answer as a
structured event.

### Required Top-Level Fields

- task_id
- user_prompt
- model_version
- run_id
- steps
- metadata

### Required Step Fields

Each step must contain:

- step_id
- type
- content

Optional:

- tool_name
- tool_input
- tool_output
- event_id
- parent_event_id
- actor_id
- span_id
- context_refs

### Metadata Requirements

Must include:

- timestamp (ISO 8601)
- latency_ms
- tokens (input/output/total)
- environment
- labels (list)

---

## 4.3 expected_outcome.md

Must begin with a YAML front matter header containing all 5 required fields:

```
---
Case ID: XXX
Primary Failure: <Failure Category>
Secondary Failures: <Optional, comma-separated>
Severity: <Low | Moderate | High | Critical>
case_version: <MAJOR.MINOR, e.g., 1.0>
---
```

Followed by structured evaluation reasoning.

Primary Failure must match a category defined in `docs/failure_taxonomy.md`.

The `case_version` field tracks changes to the case over time. It must be incremented when `trace.json` or `expected_outcome.md` content changes. The validator will warn (but not block) if changes are detected without a version bump.

---

# 5. Validation Rules

All cases must pass:

```bash
agenteval-validate-dataset --repo-root .
```

Validation includes:

- Required file presence (`prompt.txt`, `trace.json`, `expected_outcome.md`)
- JSON schema compliance (`trace.json` against `schemas/trace_schema.json`)
- YAML header completeness (5 required fields including `case_version`)
- Version-bump detection (advisory warning when content changes without `case_version` increment)
- Safe path enforcement
- No exposed secrets
- No absolute local paths
- No external URLs

Issues are categorized by severity:

- **Errors** — block commits and cause non-zero exit code
- **Warnings** — reported but do not block (e.g., version-bump detection)

A pre-commit hook (`.pre-commit-config.yaml`) runs validation automatically before every commit.

---

# 6. Governance Constraints

- Primary Failure must exist in failure taxonomy.
- Each case must map to at least one failure category.
- Coverage matrix must be updated when new primary categories are introduced.
- No duplicate case IDs.
- No manual override of validator.

---

# 7. Case Generation

New cases can be generated using the case generator CLI or library function:

```bash
# Generate a generic case
agenteval-generate-case --case-id case_013

# Generate a case with a specific failure type
agenteval-generate-case --case-id case_013 --failure-type tool_hallucination

# Overwrite an existing case
agenteval-generate-case --case-id demo_case --overwrite
```

Or via the library:

```python
from agenteval.dataset import generate_case

case_dir = generate_case(case_id="case_013", failure_type="tool_hallucination")
```

Generated cases include all 3 required files with valid headers (including `case_version: 1.0`) and pass validation immediately.

---

# 8. Extensibility Guidelines

Future cases must:

- Respect naming conventions
- Maintain deterministic failure classification
- Avoid ambiguous failure categorization
- Include clear rubric scoring

---

# 9. Versioning Policy

### Case Versioning

Each case tracks its own version via the `case_version` field in the `expected_outcome.md` header:

- New cases start at `case_version: 1.0`
- Increment `case_version` when modifying `trace.json` or `expected_outcome.md` content
- Changes to `prompt.txt` only (e.g., typo fixes) do not require a version bump
- The validator warns when content changes are detected without a version bump

### Schema Versioning

If the trace or rubric schema changes:

- Update validator
- Update documentation
- Bump version in pyproject.toml
- Revalidate all cases

---

# 10. Design Principles

This dataset follows:

- Security-first validation
- Deterministic failure mapping
- Reproducible evaluation conditions
- Separation of prompt, trace, and evaluation judgment

The benchmark is designed for use in:

- LLM evaluation
- Agent system benchmarking
- Failure pattern mining
- QA calibration exercises

---

End of specification.
