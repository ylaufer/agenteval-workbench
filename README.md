# AgentEval Workbench

![Validate Dataset](https://github.com/ylaufer/agenteval-workbench/actions/workflows/validate_dataset.yml/badge.svg)

Security-first evaluation framework for LLM outputs and autonomous agent workflows.

---

## Overview

AgentEval Workbench is a structured evaluation framework designed to assess:

- Large Language Model (LLM) outputs
- Multi-step autonomous agent workflows
- Tool invocation correctness
- Screenshot-grounded UI interactions
- Failure pattern recurrence
- Evaluation consistency across reviewers

This project reflects real-world AI Model Evaluator responsibilities, including rubric-based scoring, trace analysis, and benchmark governance.

---

## Why This Exists

Evaluating LLM and agent systems requires more than checking the final answer.

Modern AI systems involve:

- Tool calls
- Planning steps
- Observations
- Multi-step reasoning traces
- UI actions
- Error handling
- Security constraints

This framework enforces:

- Structured schema validation
- Rubric-driven evaluation
- Failure taxonomy alignment
- Security scanning
- CI-enforced dataset integrity

---

## Core Principles

### Security First

- No tokens allowed in benchmark data
- No external URLs
- No absolute paths
- No path traversal
- All filesystem access constrained to repo root
- Offline validation only

### Schema-Driven

All traces validate against a formal JSON schema (`trace_schema.json`).

### Benchmark-Based

Canonical failure cases define evaluation standards.

### CI-Enforced Governance

Every push and pull request automatically validates:

- Dataset structure
- Schema compliance
- Security constraints

---

## Project Structure

```text
agenteval-workbench/
├── src/agenteval/
│   ├── dataset/
│   │   └── validator.py
│   ├── core/
│   └── ...
├── data/cases/
├── rubrics/
├── schemas/
├── docs/
├── reports/
├── pyproject.toml
└── .github/workflows/
```

---

## Installation

Create a virtual environment:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install the project in editable mode:

```bash
pip install -e .
```

Optional (development tools):

```bash
pip install -e ".[dev]"
```

---

## Running the Dataset Validator

Run the validator:

```bash
agenteval-validate-dataset --repo-root .
```

Or:

```bash
AGENTEVAL_REPO_ROOT=. python -m agenteval.dataset.validator
```

The validator enforces:

- JSON schema validation
- Required file structure
- Secret detection (API keys, Bearer tokens, etc.)
- URL blocking
- Absolute path blocking
- Path traversal blocking

If any violation is found, the command exits with a non-zero status.

---

## Continuous Integration

This repository includes a GitHub Actions workflow that automatically runs the dataset validator on:

- Every push
- Every pull request

The CI pipeline prevents:

- Unsafe benchmark cases
- Schema-breaking traces
- Secret leaks
- Malformed dataset structures

---

## Benchmark Coverage

The benchmark dataset includes canonical agent failure scenarios such as:

- Tool hallucination
- Unnecessary tool invocation
- Instruction drift
- Partial completion
- Tool schema misuse
- UI grounding mismatch
- Unsafe output
- Format violation
- Latency mismanagement
- Reasoning inconsistency

Each case is mapped to a structured failure taxonomy and aligned with evaluation rubrics.

---

## Evaluation Philosophy

This project reflects production-grade AI evaluation practices:

- Final answer correctness is not enough.
- Tool grounding must be verified.
- Failures must be classified.
- Rubrics must be explicit and versioned.
- Evaluator consistency must be measurable.
- Security must be enforced at the dataset level.

---

## Intended Audience

- AI Model Evaluators
- QA Engineers working with LLM systems
- Agent system developers
- Research teams building autonomous workflows
- Organizations implementing structured AI evaluation

---


