# Data Model: Auto-Scoring Engine

**Feature**: 004-auto-scoring-engine
**Date**: 2026-03-22

## Entities

### DimensionScoreResult

The output of a single evaluator for one rubric dimension.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| dimension_name | string | Yes | Rubric dimension key (e.g., "tool_use") |
| score | integer or null | Yes | Score within rubric scale (e.g., 0-2), null if scoring failed |
| weight | float | Yes | Rubric dimension weight (from rubric definition) |
| scale | string | Yes | Rubric scale string (e.g., "0-2") |
| evidence_step_ids | list[string] | Yes | Trace step IDs supporting the score |
| notes | string | Yes | Evaluator reasoning/explanation |
| confidence | float or null | No | 0.0-1.0 for LLM evaluators, omitted for rule-based |
| evaluator_type | string | Yes | "rule" or "llm" |
| error | string or null | No | Error message if scoring failed (when score is null) |

### AutoEvaluation

Complete auto-scoring result for a single benchmark case.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| case_id | string | Yes | Benchmark case identifier |
| scoring_type | string | Yes | Always "auto" |
| rubric_version | string | Yes | Rubric version used for scoring |
| dimensions | map[string, DimensionScoreResult] | Yes | Keyed by dimension name |
| auto_tags | list[string] | Yes | Failure tags detected by tagger |
| metadata | AutoEvaluationMetadata | Yes | Scoring run metadata |

### AutoEvaluationMetadata

Metadata about the auto-scoring execution.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| timestamp | string (ISO 8601) | Yes | When scoring was executed |
| evaluator_versions | map[string, string] | No | Version info per evaluator |
| model | string or null | No | LLM model identifier (if any LLM evaluator used) |

### Evaluator (Protocol)

Interface that all evaluators must implement.

| Method | Signature | Description |
|--------|-----------|-------------|
| dimension_name | property -> string | Which rubric dimension this evaluator scores |
| score_dimension | (trace, rubric_dimension) -> DimensionScoreResult | Score a single dimension |

### EvaluatorRegistry

Maps dimension names to evaluator instances.

| Method | Signature | Description |
|--------|-----------|-------------|
| register | (evaluator) -> None | Add an evaluator for its dimension |
| get | (dimension_name) -> Evaluator or None | Look up evaluator for a dimension |
| score_all | (trace, rubric) -> dict[str, DimensionScoreResult] | Score all registered dimensions |

## Relationships

```text
AutoEvaluation
├── contains → DimensionScoreResult (one per rubric dimension)
├── contains → AutoEvaluationMetadata
└── references → Rubric (version string)

EvaluatorRegistry
├── contains → Evaluator instances (keyed by dimension_name)
└── used by → scorer.py orchestrator

Evaluator
├── reads → Trace (steps, metadata)
├── reads → RubricDimension (scale, scoring_guide)
└── produces → DimensionScoreResult
```

## State Transitions

AutoEvaluation dimensions have two states:

- **Scored**: `score` is an integer, `error` is null
- **Failed**: `score` is null, `error` contains reason string

There is no intermediate state; each dimension is scored or failed in a single pass.

## Validation Rules

- `score` must be within the rubric dimension's scale range (e.g., 0-2) or null
- `confidence` must be between 0.0 and 1.0 (inclusive) when present
- `evidence_step_ids` must reference valid step_id values from the trace
- `evaluator_type` must be one of: "rule", "llm"
- `scoring_type` must be "auto"
- `rubric_version` must match the version of the rubric used for scoring

## Filesystem Layout

```text
# Auto-evaluation files follow existing output conventions
runs/<run_id>/
├── run.json
├── case_001.evaluation.json       # Manual evaluation (existing)
├── case_001.auto_evaluation.json  # Auto evaluation (new)
├── case_002.evaluation.json
├── case_002.auto_evaluation.json
└── summary.evaluation.json        # Aggregated report (updated to include auto scores)

# Or in reports/ for direct CLI usage
reports/
├── case_001.evaluation.json
├── case_001.auto_evaluation.json
└── summary.evaluation.json
```
