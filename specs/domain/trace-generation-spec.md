# Feature Spec: Trace Generation from Agent Execution

## 1. Objective

Enable the system to generate valid structured traces from live agent executions,
so that they can be evaluated using the existing evaluation pipeline.

---

## 2. Problem

Currently, the system evaluates pre-existing traces from dataset cases.

There is no mechanism to:
- execute an agent
- capture its behavior
- generate a trace compatible with the trace schema

This prevents end-to-end evaluation.

---

## 3. Scope

This feature will introduce a minimal execution layer that:

- accepts user input
- executes a demo agent
- captures execution steps
- generates a valid trace object

---

## 4. Requirements

### Functional

- Accept a user input string
- Execute a simple agent (demo or mock)
- Capture execution steps:
  - reasoning
  - tool_call
  - tool_result
  - final_output
- Generate a trace object compatible with the existing schema
- Persist trace to `data/cases/<case_id>/trace.json`

---

### Non-functional

- Must be deterministic for testing
- Must not break existing evaluation pipeline
- Must produce schema-valid traces

---

## 5. Output Contract

Generated trace must include:

- run_id
- task_id
- steps[]
- metadata

And must be loadable by:
- `load_trace()`
- `tag_trace()`

---

## 6. Non-goals

- Real-time tracing
- Multi-agent orchestration
- Integration with external frameworks (LangChain, etc.)

---

## 7. Success Criteria

- Generated trace can be evaluated by existing runner
- Evaluation templates are successfully produced
- No schema validation errors