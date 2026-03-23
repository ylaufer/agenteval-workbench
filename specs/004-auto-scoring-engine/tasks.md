# Tasks: Auto-Scoring Engine

**Input**: Design documents from `specs/004-auto-scoring-engine/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Add types, schema, and register new CLI entry point

- [X] T001 Add DimensionScoreResult and AutoEvaluation types to src/agenteval/core/types.py
- [X] T002 Create auto_evaluation_schema.json in schemas/auto_evaluation_schema.json — defines required structure for auto-evaluation output files
- [X] T003 Register new CLI entry point (agenteval-auto-score) in pyproject.toml
- [X] T004 [P] Create evaluators package directory src/agenteval/core/evaluators/__init__.py with EvaluatorRegistry class

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Evaluator protocol and registry that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Implement Evaluator protocol in src/agenteval/core/evaluators/base.py — define score_dimension method signature and dimension_name property
- [X] T006 Implement EvaluatorRegistry in src/agenteval/core/evaluators/__init__.py — register(), get(), score_all(), registered_dimensions() methods with per-dimension error isolation
- [X] T007 Implement score_case() in src/agenteval/core/scorer.py — load trace from case directory, score all registered dimensions via registry, return AutoEvaluation dict
- [X] T008 Implement score_dataset() in src/agenteval/core/scorer.py — iterate cases in dataset directory, call score_case() for each, write {case_id}.auto_evaluation.json to output directory, return list of results
- [X] T009 Implement default_registry() in src/agenteval/core/scorer.py — factory function that creates registry with all built-in evaluators
- [X] T010 Write tests for EvaluatorRegistry and scorer in tests/test_scorer.py — cover registry register/get/score_all, score_case with mock evaluator, score_dataset file output, error isolation (one evaluator fails, others still score), empty trace handling

**Checkpoint**: Core scoring framework works — can register evaluators, score cases, and produce output files

---

## Phase 3: User Story 1 — Rule-Based Auto-Scoring (Priority: P1) MVP

**Goal**: Automatically score evaluation cases using deterministic rule-based evaluators for tool_use and security_safety dimensions

**Independent Test**: Run auto-scoring on an existing benchmark case and verify that tool_use and security_safety dimensions receive automatic scores with evidence and notes, persisted in a structured output file

### Implementation for User Story 1

- [X] T011 [P] [US1] Implement ToolUseEvaluator in src/agenteval/core/evaluators/tool_use.py — score tool_use dimension using trace analysis: check for incomplete executions, hallucinated outputs, unnecessary calls; scoring 0/1/2 per rubric guide with evidence step IDs
- [X] T012 [P] [US1] Implement SecurityEvaluator in src/agenteval/core/evaluators/security.py — score security_safety dimension using security scan patterns: check for secret leakage, unsafe content, policy violations; scoring 0/1/2 per rubric guide with evidence step IDs
- [X] T013 [US1] Register both evaluators in default_registry() in src/agenteval/core/scorer.py — update factory to include ToolUseEvaluator and SecurityEvaluator
- [X] T014 [US1] Write tests for ToolUseEvaluator in tests/test_evaluators.py — cover score 0 (hallucinated output), score 1 (unnecessary calls), score 2 (correct usage), empty trace, trace with no tool calls
- [X] T015 [US1] Write tests for SecurityEvaluator in tests/test_evaluators.py — cover score 0 (secret leak detected), score 1 (risky patterns), score 2 (clean trace), trace with no security-relevant content
- [X] T016 [US1] Validate auto_evaluation output against schemas/auto_evaluation_schema.json in tests/test_scorer.py — verify output from score_case() passes JSON schema validation

**Checkpoint**: Rule-based auto-scoring works for 2 dimensions. Output files validate against schema. Existing tests still pass.

---

## Phase 4: User Story 2 — LLM-Based Auto-Scoring (Priority: P2)

**Goal**: Use an LLM as a judge to score rubric dimensions that require subjective reasoning

**Independent Test**: Configure an LLM evaluator for one dimension, run auto-scoring, and verify the LLM returns a valid score mapped to rubric scale with reasoning

### Implementation for User Story 2

- [X] T017 [US2] Implement LLM provider adapter in src/agenteval/core/evaluators/llm_provider.py — abstract interface for sending prompt and receiving response via stdlib urllib.request, support for API key from environment variable, response parsing
- [X] T018 [US2] Implement LLMEvaluator in src/agenteval/core/evaluators/llm_evaluator.py — construct prompt from trace + rubric dimension, send to LLM provider, parse response into DimensionScoreResult with score, reasoning, evidence, confidence, and model identifier
- [X] T019 [US2] Add score validation logic in LLMEvaluator — reject scores outside rubric scale range, handle network errors and invalid responses gracefully, populate error field on failure
- [X] T020 [US2] Write tests for LLMEvaluator in tests/test_evaluators.py — mock LLM provider, cover valid response parsing, out-of-range score rejection, network error handling, confidence extraction, model identifier in metadata
- [X] T021 [US2] Update default_registry() in src/agenteval/core/scorer.py to optionally include LLM evaluators when configured (check for API key env var)

**Checkpoint**: LLM-based scoring works for configurable dimensions. Fails gracefully without API key. Existing rule-based scoring unaffected.

---

## Phase 5: User Story 3 — Auto-Score Aggregation in Reports (Priority: P3)

**Goal**: Include auto-generated scores in summary reports alongside manual scores with source attribution

**Independent Test**: Generate auto-scores, run summary report, and verify auto-scores appear with source attribution and filtering works

### Implementation for User Story 3

- [X] T022 [US3] Update report.py to discover and load *.auto_evaluation.json files in src/agenteval/core/report.py — extend file discovery to include auto-evaluation files alongside existing *.evaluation.json
- [X] T023 [US3] Add scoring source attribution to summary report in src/agenteval/core/report.py — distinguish manual vs auto scores in dimension statistics, add source field to per-case entries
- [X] T024 [US3] Add scoring type filter argument to report CLI in src/agenteval/core/report.py — accept --scoring-type flag (manual, auto, combined) to filter which scores are included in aggregation
- [X] T025 [US3] Write tests for report aggregation with auto-scores in tests/test_report.py — cover combined report, manual-only filter, auto-only filter, source attribution correctness

**Checkpoint**: Summary reports correctly include and distinguish auto vs manual scores.

---

## Phase 6: User Story 4 — Auto-Scoring via CLI (Priority: P3)

**Goal**: Run auto-scoring from the command line for scripting and automation

**Independent Test**: Run the CLI command on benchmark dataset and verify it produces auto-evaluation files with correct exit codes

### Implementation for User Story 4

- [X] T026 [US4] Implement main() CLI entry point in src/agenteval/core/scorer.py — parse --dataset-dir, --output-dir, --rubric, --strategy arguments; call score_dataset(); print summary; handle exit codes (0 all cases scored, 1 one or more cases failed to produce output, 2 invalid args)
- [X] T027 [US4] Add service.run_auto_scoring() to src/agenteval/core/service.py — orchestrate auto-scoring with run tracking (create run, score, complete/fail), delegate to scorer.score_dataset()
- [X] T028 [US4] Write tests for CLI entry point in tests/test_scorer.py — test argument parsing, output format, exit codes for success, partial failure, and invalid arguments
- [X] T029 [US4] Re-install package in editable mode and verify agenteval-auto-score CLI works end-to-end

**Checkpoint**: Auto-scoring accessible via CLI with correct exit codes and run tracking integration.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation

- [X] T030 Run full test suite (pytest tests/ -v) and verify all tests pass
- [X] T031 Run linting and type checking (ruff check src/ && ruff format --check src/ && mypy src/)
- [X] T032 Verify backward compatibility: run agenteval-eval-runner, agenteval-eval-report, agenteval-validate-dataset and confirm identical behavior
- [X] T033 Update README.md — add agenteval-auto-score to Key Commands section, add evaluators/ to project structure, update test count
- [X] T034 Verify auto-scoring produces valid output for all 12 benchmark cases in data/cases/ and confirm rule-based scoring completes in under 10 seconds total (NFR-001: < 5s per case)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (types and schema must exist) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — MVP, delivers rule-based scoring
- **US2 (Phase 4)**: Depends on Phase 2 — can run in parallel with US1
- **US3 (Phase 5)**: Depends on Phase 3 (needs auto-evaluation files to aggregate)
- **US4 (Phase 6)**: Depends on Phase 3 (CLI wraps scoring that must work)
- **Polish (Phase 7)**: Depends on all prior phases

### User Story Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1: Rule-Based Scoring)
                                                 ├─→ Phase 5 (US3: Report Aggregation)
                                                 └─→ Phase 6 (US4: CLI)
                                           → Phase 4 (US2: LLM Scoring) [parallel with US1]
                                                                         └─→ Phase 7 (Polish)
```

### Parallel Opportunities

- **Phase 1**: T003 and T004 can run in parallel
- **Phase 3**: T011 and T012 can run in parallel (different evaluator files)
- **Phase 4 + Phase 3**: US2 (LLM) can run in parallel with US1 (Rule-Based) after Phase 2
- **Phase 5 + Phase 6**: US3 (Reports) and US4 (CLI) can run in parallel after US1

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T010)
3. Complete Phase 3: User Story 1 (T011-T016)
4. **STOP and VALIDATE**: Auto-scoring produces valid output for benchmark cases with 2 dimensions scored
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Scoring framework works
2. US1 (Rule-Based) → Test independently → MVP!
3. US2 (LLM Scoring) → Test independently → Extended coverage
4. US3 (Report Aggregation) + US4 (CLI) → Test independently → Full integration
5. Polish → Production-ready

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- No new runtime dependencies for rule-based scoring — stdlib only
- LLM evaluators use stdlib urllib.request (no new dependencies)
- runner.py and report.py are NOT modified for US1/US2 — auto-scoring is a parallel pipeline
- report.py IS modified for US3 to include auto-scores in aggregation
- Existing CLI commands remain backward compatible throughout all phases
