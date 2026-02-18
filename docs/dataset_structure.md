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
│           └── validator.py
│
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

### Metadata Requirements

Must include:

- timestamp (ISO 8601)
- latency_ms
- tokens (input/output/total)
- environment
- labels (list)

---

## 4.3 expected_outcome.md

Must begin with a metadata header:

```
---
Case ID: XXX
Primary Failure: <Failure Category>
Secondary Failures: <Optional>
Severity: <Low | Moderate | High | Critical>
---
```

Followed by structured evaluation reasoning.

Primary Failure must match a category defined in:

```
docs/failure_taxonomy.md
```

---

# 5. Validation Rules

All cases must pass:

```
python -m agenteval.dataset.validator --repo-root .
```

Validation includes:

- Required file presence
- JSON schema compliance
- Required fields validation
- Safe path enforcement
- No exposed secrets
- No absolute local paths

---

# 6. Governance Constraints

- Primary Failure must exist in failure taxonomy.
- Each case must map to at least one failure category.
- Coverage matrix must be updated when new primary categories are introduced.
- No duplicate case IDs.
- No manual override of validator.

---

# 7. Extensibility Guidelines

Future cases must:

- Respect naming conventions
- Maintain deterministic failure classification
- Avoid ambiguous failure categorization
- Include clear rubric scoring

---

# 8. Versioning Policy

If schema changes:

- Update validator
- Update documentation
- Bump version in pyproject.toml
- Revalidate all cases

---

# 9. Design Principles

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
