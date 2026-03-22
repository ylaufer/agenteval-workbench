# 🧭 AgentEval Workbench — Product Roadmap

## 🎯 Vision

Build a **schema-first AI evaluation platform** that enables reproducible, trace-based evaluation of LLM agents, with actionable insights and continuous improvement loops.

---

# 🧱 System Pillars

The system is structured around the following layers:

Dataset Layer → Trace Layer → Evaluation Layer → Reporting Layer → UI Layer → Experimentation Layer


Each phase of the roadmap strengthens one or more of these pillars.

---

# 🟢 Phase 1 — Foundations (COMPLETED ✅)

## 🎯 Goal
Establish a reproducible, schema-driven evaluation pipeline.

## 🔧 Capabilities

### Dataset & Contracts
- Standardized dataset structure:
  - `prompt.txt`
  - `trace.json`
  - `expected_outcome.md`
- Dataset validation (fail-fast)
- Schema-first design

### Trace Layer
- Structured trace schema:
  - step types (`thought`, `tool_call`, `observation`, `final_answer`)
  - metadata (timestamps, latency, tokens)
- Deterministic trace format

### Evaluation Engine
- Evaluation runner
- Rubric-based scoring
- Case-level evaluation outputs

### Reporting
- Per-case evaluation reports
- Aggregated summary reports:
  - dimension statistics
  - failure distribution
  - severity distribution
  - recommendations

### Generation
- Demo case generation:
  - auto-create full dataset unit
  - reproducible inputs

### Architecture
- Service layer abstraction (`service.py`)
- CLI compatibility preserved
- Separation of concerns:
  - core logic
  - orchestration
  - UI

### UI (Streamlit)
- Generate cases
- Validate dataset
- Inspect traces
- Run evaluation
- View aggregated reports

### Testing
- Full pytest suite
- Spec-aligned tests
- Dataset contract enforcement

## 🧠 Outcome

End-to-end evaluation pipeline:

prompt → trace → evaluate → report


---

# 🟡 Phase 2 — Usability & Experimentation (NEXT 🚀)

## 🎯 Goal
Make the system usable for iterative evaluation and experimentation workflows.

---

## 2.1 Selective Evaluation

Enable running evaluation on subsets:

- Single case
- Multiple selected cases
- Filtered dataset:
  - by failure type
  - by tags
  - by severity

---

## 2.2 Run Management

Introduce explicit run tracking:


---

# 🟡 Phase 2 — Usability & Experimentation (NEXT 🚀)

## 🎯 Goal
Make the system usable for iterative evaluation and experimentation workflows.

---

## 2.1 Selective Evaluation

Enable running evaluation on subsets:

- Single case
- Multiple selected cases
- Filtered dataset:
  - by failure type
  - by tags
  - by severity

---

## 2.2 Run Management

Introduce explicit run tracking:

run_id
timestamp
dataset snapshot
configuration


### Capabilities
- List runs
- Inspect runs
- Persist run results
- Track evaluation history

---

## 2.3 Run Comparison (🔥 Key Feature)

Compare two evaluation runs:


### Capabilities
- List runs
- Inspect runs
- Persist run results
- Track evaluation history

---

## 2.3 Run Comparison (🔥 Key Feature)

Compare two evaluation runs:

Run A vs Run B


### Metrics
- Score differences per dimension
- Failure distribution changes
- Regression detection

### UI
- Side-by-side comparison
- Highlight:
  - improvements
  - regressions
  - unchanged metrics

---

## 2.4 UI Improvements

- Navigation flow:
  - Generate → Inspect → Evaluate → Report
- Case filtering:
  - by case_id
  - by failure type
- Better UX:
  - empty states
  - error states
  - inline feedback
- Contextual actions:
  - “View case”
  - “Inspect trace”
  - “Open report”

---

## 2.5 Real Model Integration

Replace demo agent with real execution:

- OpenAI APIs
- Local models
- External agent systems

### Result
- Real traces
- Real evaluation scenarios

---

## 🧠 Outcome

System evolves from a tool into a **usable evaluation workflow platform**.

---

# 🔵 Phase 3 — Evaluation Intelligence

## 🎯 Goal
Turn evaluation into a continuous improvement system.

---

## 3.1 Experiment Layer

Define experiments:


### Metrics
- Score differences per dimension
- Failure distribution changes
- Regression detection

### UI
- Side-by-side comparison
- Highlight:
  - improvements
  - regressions
  - unchanged metrics

---

## 2.4 UI Improvements

- Navigation flow:
  - Generate → Inspect → Evaluate → Report
- Case filtering:
  - by case_id
  - by failure type
- Better UX:
  - empty states
  - error states
  - inline feedback
- Contextual actions:
  - “View case”
  - “Inspect trace”
  - “Open report”

---

## 2.5 Real Model Integration

Replace demo agent with real execution:

- OpenAI APIs
- Local models
- External agent systems

### Result
- Real traces
- Real evaluation scenarios

---

## 🧠 Outcome

System evolves from a tool into a **usable evaluation workflow platform**.

---

# 🔵 Phase 3 — Evaluation Intelligence

## 🎯 Goal
Turn evaluation into a continuous improvement system.

---

## 3.1 Experiment Layer

Define experiments:

experiment_id
model_version
prompt_variant
tool_config


### Capabilities
- Group runs by experiment
- Compare experiments
- Track improvements over time

---

## 3.2 Auto Test Generation

Generate new test cases from failures:

failure → generate new test cases


### Examples
- Hallucination → adversarial prompts
- Constraint violations → edge cases
- Tool misuse → schema stress tests

---

## 3.3 Regression Detection

Automatically detect:

- Score drops
- Increased failure rates
- New failure types

### Output
- Alerts
- Regression flags

---

## 3.4 CI/CD Integration

Integrate evaluation into development workflow:

- Run evaluations on PR
- Block merges if:
  - regression detected
  - thresholds not met

---

## 🧠 Outcome

Continuous evaluation loop:

evaluate → detect → generate tests → improve → re-evaluate


---

# 🟣 Phase 4 — Platform & Scale

## 🎯 Goal
Evolve into a scalable, multi-user evaluation platform.

---

## 4.1 Storage Layer

Replace filesystem with structured storage:

- Database for:
  - cases
  - traces
  - runs
- Versioned datasets

---

## 4.2 API Layer

Expose platform capabilities via API:

- Run evaluation
- Fetch reports
- Manage datasets
- Manage experiments

---

## 4.3 Multi-user Support

- Authentication
- Team workspaces
- Shared experiments
- Role-based access

---

## 4.4 Advanced Trace Modeling

Support complex agent systems:

- Parent-child spans
- Multi-agent traces
- Tool orchestration flows
- Context propagation tracking

---

## 🧠 Outcome

Full **AI evaluation platform**.

---

# 📊 Roadmap Overview

Phase 1 → Foundations (COMPLETED)
↓
Phase 2 → Usability & Experimentation
↓
Phase 3 → Evaluation Intelligence
↓
Phase 4 → Platform & Scale


---

# 🎯 Strategic Priorities (Recommended)

## 🔥 Next 3 Moves

1. Run Comparison
2. Selective Evaluation
3. Run Tracking (run_id + history)

These deliver the highest value with minimal architectural changes.

---


