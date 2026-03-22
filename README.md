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
- Type-safe Python bindings for schemas

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
├── app/                        # Streamlit UI (thin presentation layer)
│   ├── app.py                  # Entry point — sidebar navigation, page routing
│   ├── page_generate.py        # Generate & Validate page
│   ├── page_evaluate.py        # Run Evaluation page
│   ├── page_inspect.py         # Inspect Trace & Evaluation page
│   └── page_report.py          # Aggregated Report page
├── src/agenteval/
│   ├── dataset/
│   │   ├── validator.py        # Dataset validation (structure, schema, security, headers)
│   │   └── generator.py        # Case generation with failure-type presets
│   ├── core/
│   │   ├── calibration.py
│   │   ├── execution.py
│   │   ├── loader.py
│   │   ├── report.py
│   │   ├── runner.py
│   │   ├── service.py          # UI-facing orchestration layer (composes existing APIs)
│   │   ├── tagger.py
│   │   └── types.py
│   ├── schemas/
│   │   ├── trace.py
│   │   └── rubric.py
│   └── __init__.py
├── tests/
│   ├── conftest.py
│   ├── test_calibration.py
│   ├── test_generator.py
│   ├── test_loader.py
│   ├── test_report.py
│   ├── test_runner.py
│   ├── test_service.py
│   ├── test_tagger.py
│   ├── test_types.py
│   └── test_validator.py
├── data/cases/
├── rubrics/
├── schemas/
├── docs/
├── reports/
├── .pre-commit-config.yaml
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

Optional (development tools — includes ruff, mypy, pytest, pre-commit):

```bash
pip install -e ".[dev]"
```

Optional (Streamlit UI):

```bash
pip install -e ".[ui]"
```

Activate pre-commit hooks (one-time per clone):

```bash
pre-commit install
```

---

## Key Commands

```bash
# Dataset validation (must pass before every commit)
agenteval-validate-dataset --repo-root .

# Generate a benchmark case
agenteval-generate-case --case-id my_case --failure-type tool_hallucination

# Run evaluation pipeline
agenteval-eval-runner --dataset-dir data/cases --output-dir reports

# Generate aggregated report
agenteval-eval-report --input-dir reports

# Inter-reviewer calibration
agenteval-eval-calibration --scores-dir scores

# Linting
ruff check src/
ruff format --check src/

# Type checking
mypy src/

# Run tests
pytest tests/ -v

# Launch Streamlit UI (requires pip install -e ".[ui]")
streamlit run app/app.py
```

---

## Running the Dataset Validator

Run the validator:

```bash
agenteval-validate-dataset --repo-root .
```

The validator enforces:

- Required file structure (`prompt.txt`, `trace.json`, `expected_outcome.md`)
- JSON schema validation (`trace.json` against `schemas/trace_schema.json`)
- YAML header completeness (5 required fields: `Case ID`, `Primary Failure`, `Secondary Failures`, `Severity`, `case_version`)
- Error/warning severity levels (errors block, warnings are advisory)
- Version-bump detection (warns if `trace.json` or `expected_outcome.md` changed without incrementing `case_version`)
- Secret detection (API keys, Bearer tokens, etc.)
- URL blocking
- Absolute path blocking
- Path traversal blocking

Exit codes:

- `0` — all cases valid (warnings may be present)
- `1` — one or more validation errors found

Example output with issues:

```
[case_003] ERROR: Missing required file: prompt.txt
[case_007] ERROR: expected_outcome.md missing required header field: case_version
[demo_case] WARNING: trace.json modified without case_version bump (1.0 → 1.0)

❌ Dataset validation failed (2 error(s), 1 warning(s)).
```

---

## Generating Benchmark Cases

Generate complete, schema-valid cases using the case generator:

```bash
# Generate a generic case
agenteval-generate-case --case-id my_test_case

# Generate a case with a specific failure type
agenteval-generate-case --case-id halluc_example --failure-type tool_hallucination

# Overwrite an existing case
agenteval-generate-case --case-id demo_case --overwrite
```

Supported failure types (from the 12 canonical categories):

`tool_hallucination`, `unnecessary_tool_invocation`, `instruction_drift`, `partial_completion`,
`tool_schema_misuse`, `ui_grounding_mismatch`, `unsafe_output`, `format_violation`,
`latency_mismanagement`, `reasoning_inconsistency`, `constraint_violation`, `incomplete_execution`

Each generated case includes all 3 required files with valid headers and passes validation immediately.

The generator is also available as a library function:

```python
from agenteval.dataset import generate_case

case_dir = generate_case(case_id="my_case", failure_type="tool_hallucination")
```

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
  - `case_version` from the `expected_outcome.md` header (`null` if absent)
  - Convenience `labels` (e.g., `primary:Tool Hallucination`, `severity:Critical`)

- **Markdown template** (`case_XXX.evaluation.md`):
  - Human-friendly summary (IDs, failures, severity, case version, labels)
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

## Rule-Based Failure Tagging

The evaluation runner automatically tags traces with failure patterns detected via heuristic
rules in `src/agenteval/core/tagger.py`. Tags are included in evaluation templates under the
`auto_tags` field.

Current failure detectors:

| Tag | Pattern |
|-----|---------|
| `incomplete_execution` | Tool call without a following observation containing output |
| `hallucination_tool_output` | Final answer contradicts documented tool output |
| `ui_mismatch` | Multiple screenshots with state-changing steps |
| `format_violation` | Narrative text in a JSON-only constrained response |

Tags propagate into both the per-case evaluation templates and the aggregated summary report.

---

## Inter-Reviewer Calibration

The calibration CLI computes pairwise inter-reviewer agreement from reviewer score files:

```bash
agenteval-eval-calibration \
  --scores-dir scores \
  --output-json reports/calibration.json \
  --output-md reports/calibration.md
```

This will:

- Discover all reviewer score files in `scores/` (format: `case_XXX_reviewer.json`)
- Compute per-dimension pairwise percent agreement and Cohen's Kappa
- Write structured JSON and Markdown calibration reports

Reviewer score files are validated against `schemas/reviewer_score_schema.json`.

---

## Streamlit UI

AgentEval Workbench includes an optional Streamlit-based web interface for interactive use.
The UI is a thin presentation layer — all logic flows through `src/agenteval/core/service.py`,
which composes the existing library APIs without modifying any CLI modules.

### Launch

```bash
pip install -e ".[ui]"
streamlit run app/app.py
```

The app opens at `http://localhost:8501` with four pages accessible via sidebar navigation.

### Pages

| Page | What it does |
|------|-------------|
| **Generate** | Create benchmark cases (case ID, failure type, overwrite toggle). Auto-validates the dataset after generation. Includes a standalone "Validate Dataset" button. |
| **Evaluate** | Run the evaluation pipeline on all cases. Displays a per-case summary table with case ID, primary failure, severity, scored dimensions, and auto-detected tags. |
| **Inspect** | Browse cases from a dropdown. View case metadata, trace steps (with color-coded type badges), and evaluation template dimensions with scores. |
| **Report** | Generate aggregated summary reports. Shows dimension statistics, failure frequency counts, severity distribution, and improvement recommendations. |

### Architecture

- **`app/`** lives outside the library package — Streamlit is an optional dependency, not a core requirement.
- **`service.py`** orchestrates calls to `generator.generate_case()`, `validator.validate_dataset()`, `runner.main()`, and `report.main()` without modifying any of those modules.
- UI pages import only from `agenteval.core.service` — never directly from runner, report, validator, or generator.
- All existing CLI commands remain fully backward-compatible.

---

## Running Tests

The project uses pytest with strict markers and fail-fast mode:

```bash
# Run full test suite
pytest tests/ -v

# With coverage
pytest tests/ --cov=agenteval --cov-report=term-missing
```

The test suite covers all modules (175 tests):

- `test_types.py` — frozen dataclass construction, defaults, immutability
- `test_validator.py` — path safety, security scanning, structure checks, schema validation, header validation, severity model, batch reporting, version-bump detection, CLI
- `test_generator.py` — case generation, failure presets, overwrite handling, path safety
- `test_loader.py` — rubric/trace/reviewer-score loading and parsing
- `test_runner.py` — header parsing, trace summarization, template generation, case_version propagation, CLI
- `test_report.py` — scale parsing, dimension stats, overall scores, recommendations, CLI
- `test_tagger.py` — all four failure tag detectors and trace-level tagging
- `test_calibration.py` — percent agreement, Cohen's kappa, calibration report, CLI
- `test_service.py` — service layer delegation, list/load/run orchestration, error handling

---

## Continuous Integration & Pre-Commit Hooks

This repository includes a GitHub Actions workflow that automatically runs the dataset validator on:

- Every push
- Every pull request

A pre-commit hook (`.pre-commit-config.yaml`) also runs validation before every local commit, blocking commits with errors while allowing warnings through.

The CI pipeline prevents:

- Unsafe benchmark cases
- Schema-breaking traces
- Secret leaks
- Malformed dataset structures
- Missing YAML header fields (including `case_version`)

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
- Evaluator consistency must be measurable (via inter-reviewer calibration).
- Security must be enforced at the dataset level.
- All modules must have automated test coverage.

---

## Intended Audience

- AI Model Evaluators
- QA Engineers working with LLM systems
- Agent system developers
- Research teams building autonomous workflows
- Organizations implementing structured AI evaluation

---


