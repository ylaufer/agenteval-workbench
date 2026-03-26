# AgentEval Workbench

Open-source trace forensics framework for LLM agent evaluation.

AgentEval helps you understand *why* an agent failed, not just *that* it failed. It combines a structured failure taxonomy, rubric-driven scoring, and trace-level analysis to turn vague "the agent messed up" into actionable, reproducible diagnostics.

## How It's Different

Observability tools (Langfuse, LangSmith, Arize) answer **"what happened?"**
AgentEval answers **"what went wrong, why, and how do we prevent it next time?"**

The core differentiators:

- **Failure Taxonomy** — 12 canonical failure categories (tool hallucination, instruction drift, constraint violation, etc.) with structured indicators and severity levels. Failures are classified, not just logged.
- **Security-First** — offline-only validation, secret scanning, path traversal protection, no network calls during evaluation. Built for regulated environments.
- **Schema-Driven Contracts** — every artifact (trace, rubric, evaluation, report) is validated against a JSON schema. Nothing is ad hoc.
- **Hybrid Scoring** — pluggable evaluators combining deterministic rule-based checks with LLM-as-judge evaluation, with explicit confidence tracking.

## Quick Start

```bash
# Clone and set up
git clone https://github.com/ylaufer/agenteval-workbench.git
cd agenteval-workbench
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
# .venv\Scripts\activate         # Windows

pip install -e .                 # core (only dependency: jsonschema)
pip install -e ".[dev]"          # adds ruff, mypy, pytest, pre-commit
pip install -e ".[ui]"           # adds Streamlit UI
```

## The Workflow

```
[ingest traces OR generate case] → validate dataset → evaluate traces → review report → improve agent → repeat
```

### 1a. Ingest traces (from external frameworks)

Convert traces from OpenTelemetry, LangChain, CrewAI, OpenAI, or custom formats.

**Via Streamlit UI** (recommended for interactive use):
- Navigate to the **Ingest** page
- Upload a JSON trace file
- Format is auto-detected and conversion preview is shown
- Save to a new case directory with one click

**Via CLI** (for batch/scripted workflows):
```bash
# Auto-detect format and convert
agenteval-ingest otel_trace.json --output trace.json

# Bulk conversion
agenteval-ingest traces/ --output-dir converted/

# Custom formats with mapping config
agenteval-ingest custom.json --output trace.json --adapter generic --mapping config.yaml
```

**Supported adapters:**
- **OpenTelemetry** (OTLP JSON) - Converts spans to steps, preserves hierarchy
- **LangChain/LangSmith** - Flattens run trees, expands tool calls
- **CrewAI** - Multi-agent task logs with action mapping
- **OpenAI** (Chat Completions API) - Handles parallel tool calls, detects final answers
- **Generic** - Custom JSON with user-defined field mappings

See [docs/ingestion_usage.md](docs/ingestion_usage.md) for detailed examples and [docs/generic_mapping.md](docs/generic_mapping.md) for mapping configuration.

### 1b. Generate a benchmark case

```bash
agenteval-generate-case --case-id my_case --failure-type tool_hallucination
```

Each case contains three files: `prompt.txt` (the agent task), `trace.json` (the step-by-step execution log), and `expected_outcome.md` (failure classification and severity metadata).

### 2. Validate the dataset

```bash
agenteval-validate-dataset --repo-root .
```

Checks structure, schema compliance, security constraints (no secrets, no external URLs, no path traversal), and header completeness. Runs automatically in CI on every push/PR.

### 3. Run evaluation

```bash
# Generate evaluation templates (rubric-based)
agenteval-eval-runner --dataset-dir data/cases --output-dir reports

# Auto-score with rule-based evaluators
agenteval-auto-score --dataset-dir data/cases --output-dir reports

# Auto-score with LLM-as-judge (optional — set ANTHROPIC_API_KEY or OPENAI_API_KEY)
ANTHROPIC_API_KEY=sk-... agenteval-auto-score --dataset-dir data/cases --output-dir reports
```

Auto-scoring uses pluggable evaluators: `ToolUseEvaluator` checks for incomplete executions, hallucinated outputs, and duplicate calls. `SecurityEvaluator` detects leaked secrets and risky patterns. LLM evaluators handle subjective dimensions like accuracy and reasoning quality.

### 4. Generate reports

```bash
agenteval-eval-report --input-dir reports
```

Produces per-dimension statistics, failure distributions, severity breakdowns, and normalized overall scores in both JSON and Markdown.

### 5. Track and compare runs

```bash
agenteval-list-runs
agenteval-inspect-run <run_id>
```

Every evaluation creates a tracked run with timestamps, dataset snapshot, and configuration — so results are always reproducible.

## Streamlit UI

```bash
streamlit run app/app.py
```

Five pages covering the full workflow:
- **Generate** — Create benchmark cases, validate dataset
- **Ingest** — Upload trace files from external frameworks (OTel, LangChain, CrewAI, OpenAI), auto-detect format, preview conversion, and save to case directory
- **Evaluate** — Run scoring pipeline (manual templates or auto-scoring)
- **Inspect** — Browse traces with color-coded step types, view evaluation templates
- **Report** — Aggregated summaries with dimension stats and failure distributions

### Guided Onboarding

First-time users get a complete onboarding experience:

- **Welcome Modal** — One-click demo that generates, validates, evaluates, and reports in <60 seconds
- **Interactive Tutorial** — 6-step walkthrough with auto-navigation and progress tracking
- **Contextual Help** — Expandable "How this works" sections on every page
- **Quick Reference** — Always-accessible sidebar with failure taxonomy (12 categories) and rubric dimensions (6 dimensions)

**Settings** (sidebar) — Toggle contextual help and tutorial mode. Preferences persist across sessions in `~/.agenteval/preferences.json`.

## The Rubric

Six scoring dimensions on a 0-2 scale:

| Dimension | What It Measures | Weight |
|-----------|-----------------|--------|
| Accuracy | Claims match trace evidence | 1.0x |
| Completeness | All user requirements fulfilled | 1.0x |
| Tool Use | Correct, efficient tool usage | 1.0x |
| UI Grounding | Claims match screenshot evidence | 1.0x |
| Reasoning Quality | Step-to-step coherence, no drift | 1.0x |
| Security & Safety | No leaked secrets, no unsafe behavior | 1.5x |

Rubrics are versioned and validated against `schemas/rubric_schema.json`.

## Failure Taxonomy

12 canonical categories organized into five groups:

**Tool Failures** — Tool Hallucination, Unnecessary Invocation, Schema Misuse, Output Misinterpretation

**Instruction Failures** — Instruction Drift, Partial Completion, Constraint Violation

**Output Quality** — Format Violation, Reasoning Inconsistency, Latency Mismanagement

**Safety** — Unsafe Output, Sensitive Data Exposure

**UI/Grounding** — UI Grounding Mismatch

Each case maps to a primary failure and optional secondary failures. See `docs/failure_taxonomy.md` for full definitions.

## Architecture

```
src/agenteval/
  dataset/          validator, generator
  core/
    evaluators/     pluggable evaluator framework (Protocol-based)
    runner.py       evaluation template generation
    scorer.py       auto-scoring orchestrator
    report.py       aggregated reporting
    service.py      UI orchestration layer
    runs.py         run tracking
  schemas/          typed Python bindings for trace/rubric schemas

app/                Streamlit UI (thin presentation layer)
schemas/            JSON schemas (trace, rubric, evaluation, reviewer scores)
rubrics/            versioned rubric definitions
data/cases/         benchmark dataset
docs/               failure taxonomy, dataset guidelines, roadmap
```

Key design decisions: the service layer composes existing APIs without modifying them. UI pages only import from `service.py`. All filesystem access is constrained within the repo root via `_safe_resolve_within()`. The evaluator framework uses `@runtime_checkable` Protocol, so adding a new evaluator means implementing two methods.

## Development

```bash
# Linting
ruff check src/
ruff format --check src/

# Type checking
mypy src/

# Tests (245 tests across 14 modules)
pytest tests/ -v

# Pre-commit hooks
pre-commit install
```

CI runs `agenteval-validate-dataset` on every push and PR. Failures block merge.

## Roadmap

See [`docs/roadmap.md`](docs/roadmap.md) for the full roadmap. The short version:

**Phase 1 (done)** — Schema-driven evaluation pipeline, auto-scoring engine, Streamlit UI, run tracking, 245 tests.

**Phase 2 (in progress)** — Trace ingestion adapters (OpenTelemetry, LangChain, CrewAI), guided onboarding, selective evaluation, run comparison, trace annotation UI, custom rubric builder.

**Phase 3** — CI/CD integration (GitHub Action), export hooks (Slack, webhooks), confidence calibration, experiment tracking, regression detection, auto test generation from failures.

**Phase 4** — SQLite storage backend, parallel evaluation, advanced trace modeling (multi-agent, hierarchical spans), REST API, community benchmark registry.

## License

MIT
