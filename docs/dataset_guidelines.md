# Dataset Design Guidelines

This document defines the standards for creating benchmark cases within AgentEval Workbench.

The goal is to ensure consistency, reproducibility, security, and evaluation clarity across all benchmark scenarios.

---

# 1. Purpose of the Benchmark Dataset

The benchmark dataset exists to:

- Evaluate LLM and autonomous agent outputs
- Identify structured failure patterns
- Support rubric-based scoring
- Enable evaluator calibration
- Ensure consistent failure classification
- Prevent unsafe or malformed evaluation inputs

The dataset is not a random collection of examples.
It is a controlled evaluation instrument.

---

# 2. Case Structure Requirements

Each case must follow this folder structure:

```
data/cases/
  case_XXX_short_description/
    prompt.txt
    trace.json
    expected_outcome.md
```

## Required Files

### prompt.txt
Contains the original user instruction given to the agent.

Must:
- Be deterministic
- Contain no secrets
- Contain no URLs
- Contain no absolute paths

---

### trace.json
Represents the structured agent execution trace.

Must:
- Validate against `schemas/trace_schema.json`
- Contain all steps/events in chronological order (append-only event log)
- Explicitly show tool calls, observations, reasoning spans, and final output
- Avoid including any secrets or external URLs

---

### expected_outcome.md

Must begin with a YAML front matter header containing all 5 required fields:

```
---
Case ID: XXX
Primary Failure: <Failure Category>
Secondary Failures: <Optional, comma-separated>
Severity: <Low | Moderate | High | Critical>
case_version: 1.0
---
```

Describes:

- Intended behavior
- Expected correct behavior
- Failure classification
- Rubric dimensions impacted

This file must clearly explain:

- Why the agent behavior is correct or incorrect
- Which failure taxonomy tags apply
- Which rubric dimensions should be penalized

---

# 3. Failure Taxonomy Alignment

Each case must explicitly map to one or more failure categories defined in:

```
docs/failure_taxonomy.md
```

Every case must declare:

- Primary failure type
- Secondary failure types (if applicable)
- A short justification for classification

No case should exist without taxonomy mapping.

---

# 4. Rubric Mapping Requirements

Each case must map to the canonical rubric evaluation dimensions. The `### DimensionName` headers in `expected_outcome.md` must use the snake_case IDs from the rubric schema — these are the identifiers the evaluator framework actually consumes:

- `accuracy`
- `completeness`
- `tool_use`
- `ui_grounding`
- `reasoning_quality`
- `security_safety`

Do not use informal labels such as "Task Completion", "Tool Appropriateness", "Safety & Compliance", or "Reasoning Consistency" as section headers — always use the canonical snake_case IDs listed above.

The expected_outcome.md must clearly describe:

- Which dimensions fail
- Which dimensions pass
- Severity level (minor, moderate, critical)

---

# 5. Security Constraints (Mandatory)

All cases must comply with security-first constraints enforced by the validator:

- No API keys
- No Bearer tokens
- No secret-like strings
- No external URLs
- No absolute filesystem paths
- No path traversal attempts

Cases violating these rules will fail CI validation.

Security violations are treated as dataset integrity failures.

---

# 6. Determinism Requirements

Benchmark cases must be deterministic.

This means:

- No time-dependent logic
- No randomness
- No external API dependencies
- No dynamic content

Traces must represent a fixed scenario.

---

# 7. Trace Design Standards

Traces must:

- Clearly separate reasoning from tool calls
- Explicitly show tool inputs and outputs
- Maintain consistent structure
- Avoid ambiguity

To support evaluator-friendly analysis and interoperability with external trace engines:

- Treat each entry in `steps` as an explicit **event** with a stable `step_id` / `event_id`
- Use `parent_event_id` to explicitly model parent-child relationships
  (for example: `tool_call` → `observation`, or reasoning spans that coordinate multiple tools)
- Use `actor_id` to distinguish between user, agent, and tool actors when relevant
- Use `span_id` to group multiple low-level events into higher-level reasoning or tool spans
- Use `context_refs` to point to external artifacts (screenshots, documents, DOM snapshots) via
  stable identifiers only — never raw payloads

Tool hallucination cases must explicitly show:

- Claimed tool invocation
- Missing corresponding execution step

Instruction drift cases must explicitly show:

- Deviation from original user request

Partial completion cases must clearly demonstrate:

- Incomplete fulfillment of required subtasks

---

# 8. Benchmark Coverage Rules

The dataset must include coverage across:

- Tool hallucination
- Unnecessary tool invocation
- Tool schema misuse
- Tool output misinterpretation
- Instruction drift
- Partial completion
- Constraint violation
- Format violation
- Reasoning inconsistency
- Latency mismanagement
- Unsafe output
- Sensitive data exposure
- UI grounding mismatch

Each failure type must have at least one canonical case.

---

# 9. Evaluator Calibration Support

Cases should be designed to:

- Reduce ambiguity
- Provide clear scoring expectations
- Allow multiple evaluators to independently reach similar conclusions

Future extensions may include:

- Agreement metrics
- Inter-rater consistency tracking
- Scoring variance analysis

---

# 10. Versioning Policy

Each case tracks its own version via the `case_version` field in the `expected_outcome.md` header.

### Version Bump Rules

- New cases start at `case_version: 1.0`
- Increment `case_version` when modifying `trace.json` or `expected_outcome.md` content
- Changes to `prompt.txt` only (e.g., typo fixes) do not require a version bump
- The validator warns (but does not block) when content changes are detected without a version bump

### When Modifying a Case

1. Make the necessary changes to `trace.json` and/or `expected_outcome.md`
2. Increment `case_version` in the YAML header (e.g., `1.0` → `1.1`)
3. Update taxonomy mapping if the failure classification changed
4. Run `agenteval-validate-dataset --repo-root .` to verify no errors
5. Commit — the pre-commit hook will validate automatically

Evaluation datasets should be treated as controlled artifacts. Avoid silent edits.

---

# 11. Case Generation

New cases can be auto-generated using the case generator:

```bash
agenteval-generate-case --case-id case_013 --failure-type tool_hallucination
```

The generator:

- Produces all 3 required files (`prompt.txt`, `trace.json`, `expected_outcome.md`)
- Includes all 5 required YAML header fields (including `case_version: 1.0`)
- Supports all 13 canonical failure-type presets (matches `docs/quick_reference_taxonomy.md`)
- Validates output directory is within the repo root
- Generated cases pass validation immediately

Available failure types: `tool_hallucination`, `unnecessary_tool_invocation`, `tool_schema_misuse`, `tool_output_misinterpretation`, `instruction_drift`, `partial_completion`, `constraint_violation`, `format_violation`, `reasoning_inconsistency`, `latency_mismanagement`, `unsafe_output`, `sensitive_data_exposure`, `ui_grounding_mismatch`.

---

# 12. What This Dataset Demonstrates

This dataset demonstrates:

- Structured LLM evaluation capability
- Autonomous agent failure analysis
- Rubric-based assessment design
- Security-aware benchmarking
- Evaluation reproducibility
- AI governance alignment

It reflects production-grade AI model evaluation practices.
