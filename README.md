# AgentEval Workbench

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

The validator enforces:

- JSON schema validation
- Required file structure
- Secret detection (API keys, Bearer tokens, etc.)
- URL blocking
- Absolute path blocking
- Path traversal blocking

If any violation is found, the command exits with a non-zero status.

---

## Running the Evaluation Runner (Core Engine)

The core evaluation engine generates **structured evaluation templates** for each benchmark case,
grounded in the rubric defined under `rubrics/`.

From the repo root:

```bash
agenteval-eval-runner \
  --dataset-dir data/cases \
  --output-dir reports
```

This will:

- Load the rubric from `rubrics/v1_agent_general.json`
- Validate each `trace.json` against `schemas/trace_schema.json`
- Parse the metadata header from each `expected_outcome.md`
- Emit, per case:
  - `reports/case_XXX.evaluation.json`
  - `reports/case_XXX.evaluation.md`

### What the runner produces

- **JSON template** (`case_XXX.evaluation.json`):
  - Case and task identifiers
  - Rubric version and name
  - Parsed primary/secondary failures and severity
  - Trace summary (total steps, counts per step `type`, run timestamp/latency when present)
  - One entry per rubric dimension, with:
    - `score` (initially `null`)
    - `weight` and `scale`
    - `evidence_step_ids` (initially empty)
    - `notes` (initially empty)
  - Convenience `labels` (e.g., `primary:Tool Hallucination`, `severity:Critical`)

- **Markdown template** (`case_XXX.evaluation.md`):
  - Human-friendly summary (IDs, failures, severity, labels)
  - Trace overview (step counts by `type`, timing)
  - Table listing all rubric dimensions with columns for score, evidence step_ids, and notes
  - Freeform “Evaluation notes” section

### How reviewers use the templates

- Open the markdown file for a case, inspect:
  - The **Summary** and **Trace overview** sections
  - The underlying `prompt.txt`, `trace.json`, and `expected_outcome.md` as needed
- For each rubric dimension:
  - Assign a score within the defined scale (e.g., `0–2`)
  - Populate `Evidence step_ids` with the relevant `step_id` / `event_id` values from the trace
  - Add short notes explaining the judgment, referencing failure taxonomy terms when useful
- Optionally mirror the same judgments into the JSON template for downstream processing.

### Automation hooks

The JSON templates are designed for:

- Programmatic aggregation of scores across cases
- Inter-rater agreement analysis
- Export to dashboards or reporting systems

The `agenteval-eval-report` CLI ingests the filled `*.evaluation.json` files (see below),
computes weighted scores per dimension and per case, and produces aggregate benchmark
summaries in both JSON and Markdown formats.

---

## Generating Structured Evaluation Reports

Once evaluators (or automated agents) have filled in scores in the JSON templates, you can
generate **summary reports**:

```bash
agenteval-eval-report \
  --input-dir reports \
  --output-json reports/summary.evaluation.json \
  --output-md reports/summary.evaluation.md
```

This will:

- Load the rubric (`rubrics/v1_agent_general.json`) to interpret scales and weights
- Read all `reports/case_XXX.evaluation.json` files
- Compute:
  - Per-dimension stats (mean score, distribution, scored/unscored counts)
  - Normalized overall scores per case (0–1) when scores are present
  - Primary failure and severity distributions across the benchmark
- Write:
  - `reports/summary.evaluation.json` — structured, machine-readable summary
  - `reports/summary.evaluation.md` — stakeholder-readable report

The Markdown report is intended for stakeholders and reviewers; the JSON report is designed
for downstream analytics, dashboards, and governance workflows.

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


