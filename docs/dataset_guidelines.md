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
- Contain all steps in chronological order
- Explicitly show tool calls, observations, reasoning, and final output
- Avoid including any secrets or external URLs

---

### expected_outcome.md
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

Each case must map to specific evaluation dimensions, such as:

- Task Completion
- Tool Appropriateness
- Tool Grounding
- Instruction Adherence
- Output Formatting
- Safety & Compliance
- Reasoning Consistency
- Efficiency

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
- Instruction drift
- Partial completion
- Tool schema misuse
- UI grounding mismatch
- Unsafe output
- Format violation
- Latency mismanagement
- Reasoning inconsistency

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

If a case is modified:

- Document changes
- Update taxonomy mapping if needed
- Maintain backward traceability
- Avoid silent edits

Evaluation datasets should be treated as controlled artifacts.

---

# 11. What This Dataset Demonstrates

This dataset demonstrates:

- Structured LLM evaluation capability
- Autonomous agent failure analysis
- Rubric-based assessment design
- Security-aware benchmarking
- Evaluation reproducibility
- AI governance alignment

It reflects production-grade AI model evaluation practices.
