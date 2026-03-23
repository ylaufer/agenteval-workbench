# Research: Auto-Scoring Engine

**Feature**: 004-auto-scoring-engine
**Date**: 2026-03-22

## R1: Evaluator Architecture Pattern

**Decision**: Protocol-based evaluator with registry pattern.

**Rationale**: Each evaluator implements a `score_dimension()` method accepting trace data and a rubric dimension definition, returning a `DimensionScoreResult`. An `EvaluatorRegistry` maps dimension names to evaluator instances. This follows the Strategy pattern and mirrors how `tagger.py` already works (each tag detector is a function checked against trace data), but with a formal protocol for extensibility.

**Alternatives considered**:
- **Inheritance-based**: Abstract base class with subclasses. Rejected because Python protocols are lighter, support duck typing, and don't force inheritance hierarchies.
- **Plugin discovery via entry points**: Using `importlib.metadata` to discover evaluators at runtime. Rejected as over-engineered for V1 — the registry can be populated explicitly in code. Plugin discovery can be added later without breaking the API.
- **Single evaluator function per dimension**: Individual functions without a registry. Rejected because it lacks a uniform interface and makes configuration harder.

## R2: Rule-Based Evaluator Scope (V1)

**Decision**: Implement rule-based evaluators for 2 dimensions: `tool_use` and `security_safety`.

**Rationale**: These two dimensions have the most objective, deterministic scoring criteria:
- **tool_use**: Can check tool call correctness (valid params, no hallucinated outputs, no unnecessary calls) by analyzing step sequences — directly leveraging patterns already implemented in `tagger.py` (`_tag_incomplete_execution`, `_tag_hallucination_tool_output`).
- **security_safety**: Can check for secret leakage, unsafe content patterns using the existing `_scan_text_for_security_violations()` from the validator plus rubric `redact_patterns`.

The remaining 4 dimensions (accuracy, completeness, ui_grounding, reasoning_quality) require subjective judgment and are better suited for LLM-based evaluation in US2.

**Alternatives considered**:
- Implementing all 6 dimensions with rules. Rejected because accuracy, completeness, reasoning_quality, and ui_grounding require semantic understanding that deterministic rules cannot reliably provide.
- Implementing only 1 dimension. Rejected because 2 dimensions better proves the architecture handles multiple evaluators and the registry pattern.

## R3: LLM Evaluator Integration Strategy

**Decision**: Use a simple HTTP client (stdlib `urllib.request`) to call LLM APIs, with an adapter interface that supports multiple providers.

**Rationale**: The constitution mandates minimal dependencies (Principle V). Using stdlib `urllib.request` avoids adding `httpx` or `requests` as a dependency. The adapter interface allows swapping providers (OpenAI, Anthropic, etc.) without changing evaluator logic.

**Alternatives considered**:
- **httpx**: Better ergonomics and async support. Rejected because it adds a runtime dependency that violates Principle V unless placed under optional extras.
- **anthropic SDK / openai SDK**: Provider-specific SDKs. Rejected because they're heavy dependencies and lock to one provider.
- **stdlib urllib only**: Selected. Simple, no dependencies, sufficient for synchronous API calls. Can be wrapped in a thin provider adapter.

**Implementation note**: LLM evaluator is an optional feature. The `[llm]` extras group can be empty for V1 (using stdlib only). If a richer HTTP client is needed later, it can be added as an optional dependency.

## R4: Auto-Evaluation Output Location

**Decision**: Auto-evaluation files are stored alongside manual evaluation files, distinguished by filename convention (`{case_id}.auto_evaluation.json` vs `{case_id}.evaluation.json`).

**Rationale**: Consistent with the existing convention where evaluation files live in the output directory (either `reports/` or `runs/<run_id>/`). The filename suffix clearly distinguishes scoring source. The report aggregator can glob for both patterns.

**Alternatives considered**:
- Separate `auto_reports/` directory. Rejected because it fragments output and complicates report aggregation.
- Embedding auto scores inside the existing `*.evaluation.json`. Rejected because it mixes manual and auto scores, complicating the hybrid model and backward compatibility.

## R5: Confidence Value Semantics

**Decision**: Confidence is optional (float 0.0–1.0), included only for LLM-based evaluators. Rule-based evaluators always have implicit confidence of 1.0 (deterministic).

**Rationale**: LLM responses have inherent uncertainty. A confidence value lets downstream consumers weight or filter results. Rule-based evaluators are deterministic by definition, so confidence is always 1.0 and can be omitted from output to keep it clean.

**Alternatives considered**:
- Mandatory confidence for all evaluators. Rejected because it adds noise for rule-based evaluators where the value is always 1.0.
- No confidence at all. Rejected because it loses valuable signal from LLM evaluators.

## R6: Error Handling Strategy

**Decision**: Per-dimension error isolation with structured error reporting in output.

**Rationale**: Each dimension is scored independently. If one evaluator fails (exception, invalid response, timeout), the failure is recorded in that dimension's output (`score: null`, `error: "reason"`), and all other dimensions continue. This matches the spec requirement for partial results and is consistent with how the existing runner handles case-level errors.

**Alternatives considered**:
- Fail-fast on any error. Rejected because partial results are more valuable than no results.
- Retry with backoff. Rejected for V1 as over-engineering; can be added to LLM evaluators later.
