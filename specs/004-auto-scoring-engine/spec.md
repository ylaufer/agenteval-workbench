# Feature Specification: Auto-Scoring Engine

**Feature Branch**: `004-auto-scoring-engine`
**Created**: 2026-03-22
**Status**: Draft
**Input**: User description: "Enable automatic scoring of evaluation cases based on trace data and rubric definitions, supporting both rule-based and LLM-based evaluation strategies."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Rule-Based Auto-Scoring (Priority: P1)

As an evaluator, I want the system to automatically score evaluation cases using deterministic rule-based logic so that I can eliminate manual scoring for dimensions where objective criteria exist.

Rule-based evaluators analyze trace data against rubric dimensions using deterministic heuristics (e.g., checking whether required tool calls were made, verifying step sequencing, detecting schema compliance). Each evaluator produces a score on the rubric scale, evidence step IDs from the trace, and explanatory notes.

**Why this priority**: Rule-based scoring requires no external dependencies, produces deterministic results, and delivers immediate value by automating the most objective rubric dimensions. This is the minimum viable product — a single rule-based evaluator scoring one dimension proves the architecture end-to-end.

**Independent Test**: Run auto-scoring on an existing benchmark case and verify that at least one rubric dimension receives an automatic score with evidence and notes, persisted in a structured output file.

**Acceptance Scenarios**:

1. **Given** a benchmark case with a valid trace and rubric, **When** auto-scoring is executed, **Then** the system produces an auto-evaluation output file containing scores for all rule-evaluable dimensions, with evidence step IDs and explanatory notes.
2. **Given** a benchmark case where a rule-based evaluator cannot determine a score for a dimension, **When** auto-scoring completes, **Then** that dimension is marked as unevaluated with a reason, and other dimensions are still scored.
3. **Given** a case that already has manual reviewer scores, **When** auto-scoring is executed, **Then** the auto-generated scores are stored separately and do not overwrite or conflict with existing manual scores.

---

### User Story 2 - LLM-Based Auto-Scoring (Priority: P2)

As an evaluator, I want the system to use an LLM as a judge to score rubric dimensions that require subjective reasoning, so that I can scale evaluation to dimensions that rule-based logic cannot handle.

LLM-based evaluators send the trace data and rubric dimension definitions to an LLM, which returns a score on the rubric scale, reasoning for the score, evidence step IDs, and optionally a confidence value. The LLM prompt is constructed from the rubric definition to ensure consistent evaluation criteria.

**Why this priority**: LLM-based evaluation extends coverage to subjective dimensions (e.g., reasoning quality, instruction adherence) that rule-based logic cannot address. However, it introduces an external dependency and non-determinism, making it a natural second-priority after the deterministic foundation is proven.

**Independent Test**: Configure an LLM evaluator for one rubric dimension, run auto-scoring on a benchmark case, and verify the LLM returns a valid score with reasoning that maps to the rubric scale.

**Acceptance Scenarios**:

1. **Given** a benchmark case and an LLM evaluator configured for a rubric dimension, **When** auto-scoring runs, **Then** the LLM produces a score within the rubric scale, reasoning text, and evidence step IDs.
2. **Given** an LLM evaluator that fails (network error, invalid response), **When** auto-scoring runs, **Then** the failed dimension is marked with the error reason, and all other dimensions are still scored.
3. **Given** an LLM evaluator response, **When** the score is recorded, **Then** the output includes the model identifier and an optional confidence value alongside the score.

---

### User Story 3 - Auto-Score Aggregation in Reports (Priority: P3)

As a stakeholder, I want auto-generated scores to be included in summary reports alongside manual scores, so that I can see a complete evaluation picture and compare scoring sources.

Summary reports should distinguish between manual and auto-generated scores, allowing filtering by scoring type. When both manual and auto scores exist for the same case, both are preserved and reported separately.

**Why this priority**: Aggregation is valuable only after scoring produces results. It builds on the reporting infrastructure already in place and extends it to handle the new scoring source.

**Independent Test**: Generate auto-scores for multiple cases, run the summary report, and verify auto-scores appear in the aggregated output with clear source attribution.

**Acceptance Scenarios**:

1. **Given** multiple cases with auto-generated scores, **When** the summary report is generated, **Then** auto-scores are included in dimension statistics with source attribution.
2. **Given** cases with both manual and auto-generated scores, **When** viewing the report, **Then** scores from each source are distinguishable and reported separately.
3. **Given** a report request with a scoring-type filter, **When** the report is generated, **Then** only scores from the specified source are included in the aggregation.

---

### User Story 4 - Auto-Scoring via CLI (Priority: P3)

As a developer or CI pipeline operator, I want to run auto-scoring from the command line so that I can integrate automatic evaluation into scripts and automation workflows.

The CLI command accepts a dataset directory, an output directory, and optionally a scoring strategy filter (rule-based only, LLM only, or both). It produces auto-evaluation output files for each case.

**Why this priority**: CLI access enables automation and CI integration but is not required for the core scoring functionality to work.

**Independent Test**: Run the CLI command on the benchmark dataset and verify it produces auto-evaluation files for each case with correct exit codes.

**Acceptance Scenarios**:

1. **Given** a valid dataset directory and rubric, **When** the CLI auto-score command is executed, **Then** auto-evaluation files are produced for each case, and the command exits with code 0.
2. **Given** scoring failures on some cases, **When** the CLI completes, **Then** partial results are still written, errors are reported to standard error, and the exit code is non-zero.

---

### Edge Cases

- What happens when a trace has zero steps? The system scores all dimensions as unevaluable with reason "empty trace" and produces a valid output file.
- What happens when the rubric defines a dimension that no evaluator can score? The dimension is included in the output with score null and a note indicating no evaluator is registered for it.
- What happens when an LLM evaluator returns a score outside the rubric scale? The system rejects the score, marks the dimension as failed with reason "score out of range", and continues scoring other dimensions.
- What happens when both rule-based and LLM evaluators are configured for the same dimension? The system uses the rule-based evaluator by default (deterministic preference) unless explicitly overridden by configuration.
- What happens when auto-scoring is run on a case that has no expected_outcome.md? The system still scores based on trace data alone, since auto-scoring uses the trace and rubric as primary inputs.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST compute scores for each rubric dimension using registered evaluators, producing a score within the dimension's defined scale, evidence step IDs, and explanatory notes.
- **FR-002**: System MUST support rule-based evaluators that use deterministic logic to score dimensions based on trace data without external dependencies.
- **FR-003**: System MUST support LLM-based evaluators that send trace data and rubric definitions to a language model and parse the response into a structured score.
- **FR-004**: System MUST store auto-generated scores separately from manual reviewer scores, using a distinct output file per case (e.g., `{case_id}.auto_evaluation.json`).
- **FR-005**: System MUST produce partial results when individual dimension scoring fails, recording the error reason per failed dimension without blocking other dimensions.
- **FR-006**: System MUST validate that LLM-returned scores fall within the rubric dimension's defined scale, rejecting out-of-range values.
- **FR-007**: System MUST include metadata in auto-evaluation output identifying the scoring type, evaluator used, and timestamp for each dimension.
- **FR-008**: System MUST reuse existing rubric definitions without modification — evaluators read the same rubric structure used by manual reviewers.
- **FR-009**: System MUST support a pluggable evaluator architecture where new evaluators can be registered without modifying existing evaluator code.
- **FR-010**: System MUST allow summary reports to include auto-generated scores, with the ability to filter by scoring source (manual, auto, or combined).
- **FR-011**: System MUST provide a CLI command to run auto-scoring on a dataset, accepting dataset directory, output directory, and optional strategy filter as arguments.
- **FR-012**: System MUST preserve full backward compatibility — existing runner, report, and validation commands remain unchanged in behavior.
- **FR-013**: LLM-based evaluators MUST include the model identifier in the output metadata for traceability.
- **FR-014**: LLM-based evaluators MUST optionally include a confidence value (0.0 to 1.0) alongside each dimension score.

### Key Entities

- **AutoEvaluation**: The complete auto-scoring result for a single case — contains case ID, scoring type, per-dimension scores, and metadata (model, timestamp).
- **Evaluator**: A scoring strategy that accepts trace data and a rubric dimension definition and returns a score result. May be rule-based (deterministic) or LLM-based (external call).
- **DimensionScoreResult**: The output of a single evaluator for one dimension — score value, evidence step IDs, notes, optional confidence, and error information if scoring failed.
- **EvaluatorRegistry**: A collection of evaluators mapped to rubric dimension names, determining which evaluator handles each dimension.

## Non-Functional Requirements

- **NFR-001**: Rule-based auto-scoring MUST complete within 5 seconds per case for the standard benchmark dataset (12 cases).
- **NFR-002**: Auto-scoring failures MUST NOT corrupt or modify existing evaluation files (manual scores, traces, or rubric definitions).
- **NFR-003**: LLM-based evaluators MUST handle network failures gracefully without crashing the scoring process.
- **NFR-004**: The evaluator architecture MUST allow adding a new evaluator without modifying existing evaluator implementations (open-closed principle).

## Assumptions

- Rule-based evaluators use only trace data and rubric definitions as inputs — no external data sources are required.
- LLM-based evaluators require an API key or endpoint configuration, which is provided via environment variables (not stored in the repository).
- The existing tagger module (`tagger.py`) provides heuristic failure detection that can inform but does not replace dimension-level scoring.
- Auto-evaluation output files are stored alongside manual evaluation files in the same output directory, distinguished by filename convention (`*.auto_evaluation.json` vs `*.evaluation.json`).
- The rubric scale is always numeric (e.g., "0-2") and evaluators return integer scores within that range.
- V1 supports one evaluator per dimension; multi-evaluator ensemble scoring is out of scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Auto-scoring produces a valid output file for 100% of benchmark cases in the dataset, even when individual dimensions fail to score.
- **SC-002**: At least 2 rubric dimensions are automatically scored by rule-based evaluators without any external dependencies.
- **SC-003**: Auto-scoring of all cases in the standard 12-case benchmark completes in under 10 seconds (rule-based only, excluding LLM latency).
- **SC-004**: When a dimension scoring fails, the failure reason is recorded in the output and all other dimensions still receive scores (zero data loss on partial failure).
- **SC-005**: Existing test suite continues to pass with zero regressions after auto-scoring is integrated.
- **SC-006**: Summary reports correctly attribute scores to their source (manual vs auto) when both types exist for the same case.
