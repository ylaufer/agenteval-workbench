# AgentEval Workbench — Product Roadmap

## Vision

Build the open-source **trace forensics framework** for LLM agent evaluation — the tool teams reach for when they need to understand *why* an agent failed, not just *that* it failed. AgentEval combines a structured failure taxonomy, rubric-driven scoring, and trace-level analysis to turn subjective "the agent messed up" into actionable, reproducible diagnostics.

## Positioning

The evaluation landscape is crowded with observability platforms (Langfuse, Arize Phoenix, LangSmith). AgentEval does not compete on logging or monitoring. Instead, it occupies a distinct layer:

**Observability tools** answer: "What happened?"
**AgentEval** answers: "What went wrong, why, and how do we prevent it next time?"

The core differentiators are:

1. **Failure Taxonomy as a First-Class Concept** — 12 canonical failure categories with structured indicators, severity levels, and governance rules. No other open-source framework provides this.
2. **Security-First by Design** — offline-only validation, secret scanning, path safety, no network calls during evaluation. Purpose-built for regulated environments.
3. **Schema-Driven Contracts** — every artifact (trace, rubric, evaluation, report) is validated against a JSON schema. Nothing is ad hoc.
4. **Hybrid Scoring** — pluggable evaluators that combine deterministic rule-based checks with LLM-as-judge evaluation, with explicit confidence tracking and calibration.

## System Pillars

```
Ingestion Layer → Dataset Layer → Trace Layer → Evaluation Layer → Reporting Layer → UI Layer → Integration Layer
```

Each phase of the roadmap strengthens one or more of these pillars.

---

# Phase 1 — Foundations (COMPLETED)

## Goal

Establish a reproducible, schema-driven evaluation pipeline.

## Capabilities

### Dataset & Contracts (COMPLETED)

- Standardized dataset structure:
  - `prompt.txt`
  - `trace.json`
  - `expected_outcome.md`
- Dataset validation (fail-fast)
- Schema-first design

### Trace Layer (COMPLETED)

- Structured trace schema:
  - step types (`thought`, `tool_call`, `observation`, `final_answer`)
  - metadata (timestamps, latency, tokens)
- Deterministic trace format

### Evaluation Engine (COMPLETED)

- Evaluation runner
- Rubric-based scoring
- Case-level evaluation outputs

### Reporting (COMPLETED)

- Per-case evaluation reports
- Aggregated summary reports:
  - dimension statistics
  - failure distribution
  - severity distribution
  - recommendations

### Generation (COMPLETED)

- Demo case generation:
  - auto-create full dataset unit
  - reproducible inputs

### Architecture (COMPLETED)

- Service layer abstraction (`service.py`)
- CLI compatibility preserved
- Separation of concerns:
  - core logic
  - orchestration
  - UI

### Schemas Module (COMPLETED)

- Python type bindings for trace and rubric schemas
- Typed representations in `src/agenteval/schemas/`

### Testing (COMPLETED)

- Full pytest suite (245 tests across 14 modules)
- Spec-aligned tests
- Dataset contract enforcement

### UI — Streamlit (COMPLETED)

- Generate cases
- Validate dataset
- Inspect traces
- Run evaluation
- View aggregated reports

### Run Management (COMPLETED)

- Run tracking with run_id, timestamp, dataset snapshot, configuration
- List runs, inspect runs, persist run results
- Track evaluation history

### Auto-Scoring Engine (COMPLETED)

- CLI: `agenteval-auto-score`
- Rule-based evaluators: `ToolUseEvaluator`, `SecurityEvaluator`
- LLM-based evaluators: `LLMEvaluator` (optional, activated via API key env var)
- Report integration with `--scoring-type` filter
- Service layer: `run_auto_scoring()` with run tracking

## Outcome

End-to-end evaluation pipeline:

```
prompt → trace → evaluate → report
```

---

# Phase 2 — Real-World Adoption

## Goal

Make AgentEval useful with real agent traces from real frameworks. No one will adopt a tool that only works with synthetic data.

---

## 2.1 Trace Ingestion Adapters (HIGH PRIORITY)

### Problem

Currently, AgentEval only evaluates its own synthetic trace format. Real agent teams use LangChain, CrewAI, AutoGen, custom frameworks, or raw OpenAI API calls. Without ingestion adapters, adoption requires manual trace conversion — a dealbreaker for most users.

### Capabilities

#### OpenTelemetry Ingestion

- Accept OTLP trace exports (JSON or protobuf)
- Map OTel span attributes to AgentEval trace schema fields
- Handle nested spans → flat step sequence conversion
- Preserve parent-child relationships via `parent_event_id`

#### LangChain / LangSmith Adapter

- Ingest LangChain callback handler output (JSON)
- Map LangChain run types (`llm`, `tool`, `chain`, `retriever`) to AgentEval step types
- Extract tool inputs/outputs from LangChain serialization format
- Handle streaming token events by collapsing them into single steps

#### CrewAI Adapter

- Ingest CrewAI task execution logs
- Map agent/task/tool hierarchy to AgentEval actor model
- Handle multi-agent traces with `actor_id` mapping

#### Raw API Call Adapter

- Accept OpenAI Chat Completions API response format
- Extract tool_use blocks from assistant messages
- Reconstruct trace steps from conversation turns
- Handle function calling and parallel tool use

#### Generic JSON Adapter

- Accept a user-defined mapping configuration (YAML/JSON)
- Map arbitrary JSON trace formats to AgentEval schema
- Validate mapping completeness at import time
- Provide clear error messages for unmappable fields

### Architecture

```
src/agenteval/ingestion/
  __init__.py
  base.py          — TraceAdapter Protocol
  otel.py          — OpenTelemetry adapter
  langchain.py     — LangChain adapter
  crewai.py        — CrewAI adapter
  openai_raw.py    — Raw API response adapter
  generic.py       — User-defined mapping adapter
```

Each adapter implements:

```python
class TraceAdapter(Protocol):
    def can_handle(self, raw: dict) -> bool: ...
    def convert(self, raw: dict) -> Trace: ...
    def validate_mapping(self, raw: dict) -> list[str]: ...  # warnings
```

### CLI

```bash
# Auto-detect format and convert
agenteval-ingest trace_export.json --output data/cases/case_new/trace.json

# Specify adapter explicitly
agenteval-ingest trace.json --adapter langchain --output data/cases/case_new/trace.json

# Bulk ingest a directory of traces
agenteval-ingest ./exports/ --adapter otel --output-dir data/cases/

# Validate a custom mapping without converting
agenteval-ingest trace.json --adapter generic --mapping my_mapping.yaml --dry-run
```

### Outcome

Teams can evaluate real agent runs within minutes of installing AgentEval, without writing any conversion code.

---

## 2.2 Guided Onboarding (HIGH PRIORITY)

### Problem

A new user currently has to understand failure taxonomies, rubric dimensions, trace schemas, and the full generate→validate→evaluate→report flow before getting any value. The learning curve is steep and documentation alone won't fix it.

### Capabilities

#### First-Run Experience

- Detect first launch (no existing cases or runs)
- Present a welcome page explaining the core workflow in plain language
- Offer a one-click "Run the demo" that:
  - generates a demo case
  - validates it
  - runs evaluation
  - opens the report
- Show results with annotations explaining what each section means

#### Contextual Help System

- Every UI page gets an expandable "How this works" section
- Trace viewer: tooltip on each step type explaining what `thought`, `tool_call`, `observation`, `final_answer` mean
- Evaluation template: inline help explaining each rubric dimension
- Report page: annotations explaining score calculations, what the numbers mean

#### Interactive Walkthrough Mode

- Step-by-step guided tutorial using Streamlit's native components
- Highlights key UI elements at each step
- Progress indicator showing where the user is in the workflow
- "Skip tutorial" option that remembers preference

#### Quick Reference

- Sidebar link to failure taxonomy summary
- Rubric dimension cheat sheet accessible from any page
- Example traces for each failure type, browsable from the Generate page

### Outcome

Time-to-first-value drops from "read 3 docs and figure it out" to "click one button, see results in 60 seconds."

---

## 2.3 Selective Evaluation

### Problem

Evaluating the entire dataset on every run is wasteful during iterative development. Teams need to focus on specific cases — by failure type, severity, tag, or manual selection.

### Capabilities

- Single case evaluation from the UI (click "Evaluate this case")
- Multi-select checkboxes for batch evaluation of chosen cases
- Filter-then-evaluate:
  - by failure type (primary or secondary)
  - by severity level
  - by auto-detected tags
  - by case_id pattern (glob or regex)
- CLI support:

```bash
agenteval-auto-score --cases case_001,case_003,case_007
agenteval-auto-score --filter-failure "Tool Hallucination"
agenteval-auto-score --filter-severity Critical,High
agenteval-auto-score --filter-tag "has_tool_calls"
```

- Run tracking records the filter criteria used, so runs are reproducible

### Outcome

Evaluation becomes a surgical tool, not a blunt instrument.

---

## 2.4 Run Comparison

### Problem

Without comparison, evaluation runs exist in isolation. Teams can't answer "did our prompt change actually help?" or "did we regress on security?"

### Capabilities

#### Core Comparison Engine

- Compare any two runs by run_id
- Compute per-dimension score deltas
- Compute per-case score deltas
- Classify changes:
  - **Improved**: score increased
  - **Regressed**: score decreased
  - **Unchanged**: same score
  - **New**: case exists only in Run B
  - **Removed**: case exists only in Run A

#### Comparison Metrics

- Dimension-level: mean score change, standard deviation change, min/max shifts
- Failure-level: failure type distribution change, new failure types introduced, failure types resolved
- Aggregate: overall score change (weighted), number of regressions, number of improvements

#### CLI

```bash
agenteval-compare --run-a <run_id_a> --run-b <run_id_b>
agenteval-compare --run-a <run_id_a> --run-b <run_id_b> --output-json comparison.json
```

#### UI

- Side-by-side comparison page
- Color-coded delta indicators (green for improvement, red for regression)
- Sortable table: sort by largest regression, largest improvement, or by dimension
- Drill-down: click a case to see the per-dimension diff
- Sparkline trend if more than 2 runs exist

### Architecture

```
src/agenteval/core/comparison.py   — comparison engine
app/page_compare.py                — Streamlit comparison page
schemas/comparison_schema.json     — output schema for comparison results
```

### Outcome

Every evaluation run becomes part of a measurable improvement story.

---

## 2.5 Trace Annotation & Review UI

### Problem

The current inspect page renders trace steps linearly with no interactivity. Reviewers can't annotate specific steps, mark issues, or see where auto-scoring flagged problems. This makes the review process disconnected from the evaluation output.

### Capabilities

#### Inline Annotations

- Click any trace step to add a reviewer note
- Notes are persisted alongside the evaluation template
- Notes include reviewer_id and timestamp

#### Auto-Score Overlay

- When an auto-evaluation exists for a case, overlay it on the trace viewer
- Highlight steps that were flagged as evidence by rule-based or LLM evaluators
- Color-code steps by issue severity (red = flagged, yellow = warning, green = clean)

#### Step-Level Diff View

- For cases that appear in two runs, show a step-by-step diff
- Highlight steps that changed between trace versions
- Useful when comparing traces from different model versions or prompt variants

#### Evidence Linking

- From the evaluation template, click an evidence_step_id to jump to that step in the trace viewer
- From a trace step, see which rubric dimensions reference it as evidence

### Outcome

Review becomes a connected workflow where evaluation results and trace data are interleaved, not siloed.

---

## 2.6 Custom Rubric Builder

### Problem

The current rubric is defined in YAML and requires manual editing. Teams with different evaluation priorities (e.g., a customer support bot team doesn't care about UI grounding) can't easily create their own rubrics.

### Capabilities

#### UI-Based Rubric Editor

- Create new rubrics from the Streamlit UI
- Add/remove/reorder dimensions
- Set per-dimension: name, title, description, scale, weight, scoring guide, evidence_required
- Preview the rubric in both YAML and JSON formats
- Validate against `rubric_schema.json` before saving

#### Rubric Templates

- Provide starter templates for common use cases:
  - General agent (current v1)
  - RAG pipeline (accuracy, retrieval quality, source attribution, hallucination)
  - Customer support (tone, resolution, escalation appropriateness, policy compliance)
  - Code generation (correctness, test coverage, security, style)
- Templates are starting points, fully editable

#### Rubric Versioning

- Every rubric save creates a new version file (e.g., `v2_rag_pipeline.json`)
- Existing evaluation data is never orphaned — reports always reference their rubric version
- Comparison across rubric versions is explicit (warn if comparing runs that used different rubrics)

### Architecture

```
app/page_rubric.py           — Streamlit rubric builder page
rubrics/templates/            — starter template directory
```

### Outcome

Teams can define evaluation criteria that match their actual use case without editing raw YAML.

---

## 2.7 UI Polish

### Problem

The current UI covers the workflow but lacks navigational coherence, feedback states, and contextual actions.

### Capabilities

- Navigation flow enforcement: Generate → Inspect → Evaluate → Report, with breadcrumbs
- Empty states: helpful messages with direct action buttons ("No cases yet — generate one")
- Error states: clear error messages with recovery suggestions
- Loading states: progress indicators during evaluation and scoring
- Contextual actions on every data item:
  - Case in list → "Inspect trace" / "Evaluate" / "View report"
  - Run in list → "Compare with..." / "View details"
- Case filtering across all pages:
  - by case_id
  - by failure type
  - by severity
  - by tag
- Consistent layout and component patterns across all pages

### Outcome

The UI feels like a product, not a prototype.

---

## Phase 2 Outcome

The system becomes usable with real agent traces from real frameworks, with an intuitive onboarding experience and a review workflow that connects traces to evaluation results. Teams can adopt AgentEval and get value within their first session.

---

# Phase 3 — Integration & Intelligence

## Goal

Make AgentEval a part of the development workflow, not a standalone tool. Add intelligence that turns evaluation data into actionable improvement signals.

---

## 3.1 CI/CD Integration (HIGH PRIORITY)

### Problem

Evaluation is most valuable when it runs automatically on every change. Currently, AgentEval requires manual invocation. Without CI integration, it will never become part of team habits.

### Capabilities

#### GitHub Action

- Publish `agenteval-action` to the GitHub Actions marketplace
- Inputs: dataset directory, rubric path, threshold configuration, scoring strategy
- Runs `agenteval-auto-score` and `agenteval-eval-report` in CI
- Posts a summary comment on the PR with:
  - overall score
  - per-dimension scores
  - regressions vs. the base branch
  - failure distribution
- Blocks merge if configurable thresholds are violated:
  - minimum overall score
  - maximum number of critical failures
  - no regressions on security_safety dimension

#### Threshold Configuration

```yaml
# .agenteval/ci.yaml
thresholds:
  min_overall_score: 0.7
  max_critical_failures: 0
  no_regression_dimensions:
    - security_safety
    - accuracy
  max_score_drop_per_dimension: 0.5
```

#### Generic CI Support

- `agenteval-ci` CLI command that:
  - runs evaluation
  - checks thresholds
  - exits with non-zero code on failure
  - outputs structured JSON for downstream consumption
- Works with any CI system (GitHub Actions, GitLab CI, Jenkins, CircleCI)

### Outcome

Agent quality becomes a merge gate, just like tests and linting.

---

## 3.2 Export & Notification Hooks

### Problem

Evaluation results live inside AgentEval's filesystem. Teams need results pushed to their existing tools — Slack, GitHub, dashboards, data warehouses.

### Capabilities

#### Webhook Support

- On run completion, fire a configurable webhook with the summary payload
- Supports POST to arbitrary URLs with configurable headers
- Retry logic with exponential backoff

#### Built-in Exporters

- **Slack**: post summary to a channel (score, regressions, link to report)
- **GitHub PR Comment**: post evaluation summary as a PR comment (for non-CI workflows)
- **JSON file**: write structured summary to a configurable path (for dashboard ingestion)
- **CSV**: export per-case scores for spreadsheet analysis

#### Configuration

```yaml
# .agenteval/hooks.yaml
on_run_complete:
  - type: slack
    channel: "#agent-eval"
    webhook_url: ${SLACK_WEBHOOK_URL}
    template: "default"
  - type: json
    path: "./reports/latest_summary.json"
```

### Architecture

```
src/agenteval/hooks/
  __init__.py
  base.py         — Hook Protocol
  slack.py
  github.py
  json_export.py
  csv_export.py
  webhook.py
```

### Outcome

Evaluation results flow into the tools teams already use, without manual copy-paste.

---

## 3.3 Confidence Calibration Pipeline

### Problem

The LLM-as-judge evaluator produces scores, but there's no systematic way to know how much to trust them. Without calibration data, auto-scores are opinions with numbers attached.

### Capabilities

#### Calibration Dataset

- Maintain a set of "gold standard" cases with human-reviewed scores
- Calibration cases are tagged and stored separately from regular cases
- Minimum recommended: 20 calibration cases covering all rubric dimensions

#### Calibration Metrics

- Per-dimension agreement rate: percentage of cases where auto-score matches human score
- Per-dimension bias: average (auto_score - human_score), shows if auto-scorer is systematically generous or harsh
- Cohen's Kappa: inter-rater reliability between auto-scorer and human reviewer
- Confidence calibration curve: do cases scored with higher confidence actually have higher agreement?

#### Calibration Report

- Generate a calibration report comparing auto-scores against human baselines
- Identify dimensions where auto-scoring is unreliable
- Recommend which dimensions should still require human review
- Track calibration metrics over time as evaluators are updated

#### CLI

```bash
agenteval-calibrate --gold-dir data/calibration --auto-dir reports/
agenteval-calibrate --output reports/calibration.json
```

### Outcome

Teams know exactly how much to trust auto-scores, per dimension, with data to back it up.

---

## 3.4 Experiment Layer

### Problem

Teams iterate on agents by changing models, prompts, tools, and configurations. Without a way to group and compare these iterations, evaluation runs are a disorganized pile.

### Capabilities

#### Experiment Definition

```yaml
# experiments/prompt_v2.yaml
experiment_id: prompt_v2_test
description: "Testing revised system prompt with explicit constraint section"
variables:
  model_version: "gpt-4o-2024-05-13"
  prompt_variant: "v2_with_constraints"
  tool_config: "default"
  temperature: 0.7
```

#### Experiment Tracking

- Group runs by experiment_id
- Compare experiments side-by-side (extends run comparison to experiment level)
- Track score trends across experiments over time
- Tag experiments with arbitrary labels for filtering

#### UI

- Experiment list page showing all experiments with latest scores
- Experiment detail page showing all runs within an experiment
- Experiment comparison: pick 2+ experiments, see dimension-level score trends

### Outcome

Agent improvement becomes a structured, trackable process rather than ad hoc experimentation.

---

## 3.5 Regression Detection & Alerts

### Problem

Score drops and new failure types can go unnoticed across runs. Teams need proactive signals when quality degrades.

### Capabilities

#### Automatic Detection

- On every run completion, compare against the previous run (or a pinned baseline)
- Flag regressions:
  - per-dimension score drops exceeding a configurable threshold
  - new failure types that didn't exist in the baseline
  - increase in critical/high severity failures

#### Alert Output

- Write regression flags to the run's summary JSON
- Include regression details in CI exit codes
- Feed regression data to notification hooks (Slack, webhook, etc.)

#### Baseline Management

- Pin a specific run as the "baseline" for regression detection
- Baseline can be updated manually or automatically after a release
- CLI: `agenteval-baseline --set <run_id>` / `agenteval-baseline --show`

### Outcome

Quality degradation is caught early and automatically, not discovered in production.

---

## 3.6 Auto Test Generation from Failures

### Problem

When evaluation reveals a failure pattern, the natural next step is to create more test cases that probe that weakness. This is currently manual.

### Capabilities

#### Failure-Driven Generation

- Given a failed case, generate variant test cases that stress the same failure mode
- Generation strategies by failure type:
  - Tool Hallucination → create cases where tool returns errors/empty results to test if agent fabricates output
  - Constraint Violation → create cases with increasingly complex constraint sets
  - Sensitive Data Exposure → create cases with embedded secrets in tool outputs to test if agent leaks them
  - Instruction Drift → create cases with multi-step instructions where the agent must stay on track

#### Implementation

- LLM-powered generation (requires API key, similar to LLM evaluator)
- Uses the failure taxonomy definitions as prompting context
- Generated cases are validated against the dataset schema before saving
- Human review step: generated cases are saved as "draft" until explicitly approved

#### CLI

```bash
agenteval-generate-adversarial --from-case case_001 --num 3
agenteval-generate-adversarial --from-failure "Tool Hallucination" --num 5 --output-dir data/cases/
```

### Outcome

The evaluation dataset grows organically from discovered weaknesses, creating a tightening feedback loop.

---

## Phase 3 Outcome

AgentEval becomes embedded in the development workflow. Evaluation runs automatically on every change, results flow to existing tools, auto-scores are calibrated against human baselines, and the test suite grows from discovered failures.

```
evaluate → detect regression → generate tests → improve agent → re-evaluate
```

---

# Phase 4 — Scale & Community

## Goal

Evolve from a single-user CLI tool into a community-driven framework that supports teams, shared benchmarks, and production-grade workloads.

---

## 4.1 Storage Layer

### Problem

The filesystem-based storage (JSON files in directories) works for solo use but creates bottlenecks for concurrent access, search, aggregation, and datasets with hundreds or thousands of cases.

### Capabilities

#### SQLite Backend (Default)

- Replace filesystem-based case/run/report storage with SQLite
- Single-file database: zero configuration, no server required
- Schema migrations via lightweight migration framework
- Backward compatibility: import existing filesystem data into SQLite on first run

#### Storage Abstraction

- `StorageBackend` Protocol that filesystem and SQLite both implement
- All core code accesses storage through the abstraction, never directly
- Future backends (Postgres, S3) can be added without changing core logic

#### Query Support

- Filter cases by any metadata field without scanning all files
- Aggregate scores across dimensions/runs efficiently
- Full-text search across trace content and evaluation notes
- Pagination for large datasets

#### Data Model

```
cases:         case_id, prompt, trace_json, expected_outcome, metadata, created_at
runs:          run_id, status, started_at, completed_at, config_json
evaluations:   eval_id, case_id, run_id, scoring_type, dimensions_json, auto_tags
experiments:   experiment_id, description, variables_json, created_at
```

### Outcome

The system can handle real-world dataset sizes without performance degradation.

---

## 4.2 Parallel Evaluation

### Problem

`score_dataset()` processes cases sequentially. For datasets with 100+ cases and LLM-based evaluators, this means evaluation takes minutes to hours.

### Capabilities

- `concurrent.futures.ThreadPoolExecutor` for I/O-bound LLM evaluator calls
- Configurable concurrency limit (`--workers N`)
- Progress reporting: live progress bar in CLI, progress indicator in UI
- Error isolation preserved: one case failing doesn't block others (already implemented, just needs to work across threads)
- Rate limiting for LLM API calls to respect provider quotas

### Outcome

Evaluation time scales linearly with concurrency, not linearly with dataset size.

---

## 4.3 Advanced Trace Modeling

### Problem

Real agent systems are more complex than a flat sequence of steps. Multi-agent orchestration, nested tool calls, and branching workflows need richer trace representation.

### Capabilities

#### Multi-Agent Support

- `actor_id` field on every step (already in schema, needs evaluator support)
- Per-agent evaluation: score each actor independently
- Cross-agent evaluation: assess handoff quality, coordination patterns

#### Hierarchical Spans

- `span_id` and `parent_span_id` for nested execution (already in schema, needs UI support)
- Tree-view trace visualization in the UI
- Collapse/expand spans for readability

#### Branching and Retry Modeling

- Support for representing retried tool calls as branches
- Model "plan → execute → observe → replan" loops explicitly
- Detect and score recovery behavior (agent retrying after failure vs. giving up)

### Outcome

AgentEval can evaluate the full complexity of production agent architectures.

---

## 4.4 API Layer

### Problem

The Streamlit UI and CLI are the only interfaces. External tools, dashboards, and CI systems need programmatic access.

### Capabilities

#### REST API (FastAPI)

- Optional dependency (like Streamlit)
- Endpoints:
  - `POST /evaluate` — trigger evaluation run
  - `GET /runs` — list runs
  - `GET /runs/{run_id}` — get run details
  - `GET /runs/{run_id}/compare/{other_run_id}` — compare runs
  - `GET /cases` — list cases with filtering
  - `GET /cases/{case_id}/trace` — get trace data
  - `POST /ingest` — submit a trace for ingestion
- API key authentication (simple, file-based)
- OpenAPI spec auto-generated

### Outcome

AgentEval becomes embeddable in any workflow, not just its own UI.

---

## 4.5 Community Benchmark Registry

### Problem

Every team builds their own test cases from scratch. The failure taxonomy and rubric framework enable standardized benchmarks, but there's no mechanism to share them.

### Capabilities

#### Benchmark Packaging

- Package a dataset + rubric + failure mapping as a distributable benchmark
- Standard format: `.agenteval-benchmark` archive (ZIP with manifest)
- Manifest includes: benchmark name, version, description, rubric version, number of cases, failure type coverage

#### Community Index

- Public GitHub repository serving as a benchmark index
- Teams can submit benchmarks via PR
- Benchmarks are validated by CI before merge

#### CLI

```bash
agenteval-benchmark install customer-support-v1
agenteval-benchmark list
agenteval-benchmark run customer-support-v1 --output-dir reports/
```

### Outcome

Teams can evaluate their agents against community-maintained benchmarks, enabling cross-team and cross-model comparison on standardized criteria.

---

## Phase 4 Outcome

AgentEval becomes a scalable, community-driven framework with a real storage layer, parallel evaluation, an API, and shared benchmarks.

---

# Roadmap Overview

```
Phase 1 → Foundations (COMPLETED)
  ↓
Phase 2 → Real-World Adoption (NEXT)
  ↓
Phase 3 → Integration & Intelligence
  ↓
Phase 4 → Scale & Community
```

---

# Strategic Priorities

## Immediate Next 3 (Phase 2)

1. **Trace Ingestion Adapters** — without this, adoption is blocked. Nobody will manually convert traces.
2. **Guided Onboarding** — without this, new users bounce. The learning curve is too steep.
3. **Selective Evaluation + Run Comparison** — without this, iterative workflows are painful.

These three moves transform AgentEval from "interesting project" to "tool I actually use."

## Phase 3 Priorities

4. **CI/CD Integration** — this is where adoption locks in. Once it's in the pipeline, it stays.
5. **Confidence Calibration** — this is what makes auto-scoring trustworthy rather than decorative.
6. **Export Hooks** — this is what makes evaluation results visible to the rest of the team.

## Phase 4 Priorities

7. **SQLite Storage** — unblocks everything else at scale. Move this earlier if dataset sizes grow.
8. **Parallel Evaluation** — necessary once LLM evaluators are in regular use.
9. **Community Benchmarks** — the long-term moat. A framework is a tool; a framework with shared benchmarks is a standard.
