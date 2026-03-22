# Tasks: Streamlit UI for AgentEval Workbench

**Input**: Design documents from `specs/002-streamlit-ui/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Included for service layer (Constitution IV mandates tests for new modules). Streamlit pages are tested manually via quickstart.md scenarios.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Library code**: `src/agenteval/`, `tests/` at repository root
- **Streamlit app**: `app/` at repository root

---

## Phase 1: Setup

**Purpose**: Add Streamlit dependency, create directories

- [X] T001 Add `streamlit>=1.30.0` to `[project.optional-dependencies.ui]` in pyproject.toml
- [X] T002 [P] Create `app/` directory at repository root
- [X] T003 Re-install project with UI extras: `pip install -e ".[ui]"`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Create service layer that all UI pages depend on. Runner.py and report.py remain untouched.

**CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational

- [X] T004 [P] Add test for `service.generate_case()` delegating to generator and returning Path in tests/test_service.py
- [X] T005 [P] Add test for `service.validate_dataset()` delegating to validator and returning ValidationResult in tests/test_service.py
- [X] T006 [P] Add test for `service.list_cases()` returning sorted list of case IDs in tests/test_service.py
- [X] T007 [P] Add test for `service.load_case_metadata()` returning parsed YAML header dict in tests/test_service.py
- [X] T008 [P] Add test for `service.load_trace()` returning trace dict in tests/test_service.py
- [X] T009 [P] Add test for `service.load_evaluation_template()` returning None when no template exists in tests/test_service.py
- [X] T010 [P] Add test for `service.run_evaluation()` calling runner.main and returning list of evaluation dicts in tests/test_service.py
- [X] T011 [P] Add test for `service.generate_summary_report()` calling report.main and returning summary dict in tests/test_service.py

### Implementation for Foundational

- [X] T012 Create src/agenteval/core/service.py with `generate_case()` delegating to `dataset.generator.generate_case()` and `validate_dataset()` delegating to `dataset.validator.validate_dataset()`
- [X] T013 Add `list_cases(dataset_dir)` to src/agenteval/core/service.py — list and sort case subdirectories in dataset_dir, default to `data/cases/` via `_get_repo_root()`
- [X] T014 Add `load_case_metadata(case_dir)` to src/agenteval/core/service.py — read expected_outcome.md, parse YAML front matter, return dict of header fields
- [X] T015 Add `load_trace(case_dir)` to src/agenteval/core/service.py — delegate to `core.loader.load_trace()` with `case_dir / "trace.json"`
- [X] T016 Add `load_evaluation_template(case_id, reports_dir)` to src/agenteval/core/service.py — read `{case_id}.evaluation.json` from reports_dir, return parsed dict or None if file does not exist
- [X] T017 Add `run_evaluation(dataset_dir, output_dir)` to src/agenteval/core/service.py — construct argv list, call `runner.main(argv)`, read all generated `*.evaluation.json` files from output_dir, return as `list[dict]`; raise RuntimeError if runner returns non-zero
- [X] T018 Add `generate_summary_report(input_dir, output_dir)` to src/agenteval/core/service.py — construct argv list, call `report.main(argv)`, read `summary.evaluation.json` from output_dir, return as dict; raise RuntimeError if report returns non-zero
- [X] T019 Run `pytest tests/test_service.py -v` to verify all service layer tests pass
- [X] T020 Run backward compatibility check: `agenteval-eval-runner --dataset-dir data/cases --output-dir reports` and `agenteval-eval-report --input-dir reports` — verify identical behavior (runner.py and report.py are untouched)

**Checkpoint**: Service layer ready — all orchestration functions work, CLI behavior unchanged

---

## Phase 3: User Story 1 - Generate and Validate a Demo Case (Priority: P1) MVP

**Goal**: User can generate a benchmark case and validate the dataset from a Streamlit page with sidebar navigation

**Independent Test**: Open the UI, generate a case with a failure type, verify 3 files are created, confirm validation results display with severity grouping and case-ID partitioning.

### Implementation for User Story 1

- [X] T021 [US1] Create `app/app.py` with Streamlit entry point — sidebar navigation with 4 pages (Generate, Evaluate, Inspect, Report), page title, and page routing that imports and calls each page module's `render()` function
- [X] T022 [US1] Create `app/page_generate.py` with `render()` function — case ID text input (optional), failure type dropdown (12 canonical types from `VALID_FAILURE_TYPES` + None), overwrite checkbox, "Generate Case" button that calls `service.generate_case()`
- [X] T023 [US1] Add validation display to `app/page_generate.py` — after generation, auto-call `service.validate_dataset()`, partition issues by `case_id` matching the generated case, show new-case issues prominently with severity badges (errors first), show other-case issues in a collapsed `st.expander`
- [X] T024 [US1] Add standalone "Validate Dataset" button to `app/page_generate.py` — calls `service.validate_dataset()` independently of generation, displays all issues grouped by severity with case_id, file_path, and message
- [X] T025 [US1] Add error handling to `app/page_generate.py` — catch `ValueError` from `service.generate_case()` for existing case (suggest overwrite), invalid failure type, and path-escapes-repo-root; display with `st.error()` and actionable remediation text
- [ ] T026 [US1] Run `streamlit run app/app.py` and manually verify quickstart.md Scenarios 1 and 2 (generate case, validate dataset)

**Checkpoint**: Generate page works — cases can be created and validated from the UI with proper error handling

---

## Phase 4: User Story 2 - Run Evaluation Pipeline (Priority: P2)

**Goal**: User can run the evaluation pipeline on all cases and see a per-case summary table

**Independent Test**: With valid cases in the dataset, click "Run Evaluation" and verify evaluation templates are created in reports/ and the summary table displays case metadata.

### Implementation for User Story 2

- [X] T027 [US2] Create `app/page_evaluate.py` with `render()` function — "Run Evaluation" button that calls `service.run_evaluation()`
- [X] T028 [US2] Add results display to `app/page_evaluate.py` — show summary count ("Processed N cases"), then a `st.dataframe` table with columns: Case ID, Primary Failure, Severity, Scored Dimensions, Auto Tags (one row per evaluation template dict)
- [X] T029 [US2] Add error handling to `app/page_evaluate.py` — catch `RuntimeError` for missing rubric/dataset, display `st.info` when no cases exist suggesting the Generate page, show per-case warnings for invalid traces
- [ ] T030 [US2] Run `streamlit run app/app.py` and manually verify quickstart.md Scenario 3 (run evaluation pipeline)

**Checkpoint**: Evaluate page works — evaluation templates generated and summary displayed

---

## Phase 5: User Story 3 - Inspect Trace and Evaluation Details (Priority: P2)

**Goal**: User can browse cases, view trace steps, case metadata, and evaluation template details

**Independent Test**: Select a case from the dropdown, verify trace steps render with all fields, confirm evaluation template dimensions display with scores.

### Implementation for User Story 3

- [X] T031 [US3] Create `app/page_inspect.py` with `render()` function — case selector dropdown populated via `service.list_cases()`, display `st.info` when no cases exist
- [X] T032 [US3] Add case metadata display to `app/page_inspect.py` — call `service.load_case_metadata()`, display Case ID, Primary Failure, Secondary Failures, Severity, case_version in a key-value layout
- [X] T033 [US3] Add trace viewer to `app/page_inspect.py` — call `service.load_trace()`, display each step sequentially showing step_id, type (with color-coded badge via `st.markdown`), actor_id, content; for tool_call steps show tool_name and tool_input as formatted JSON; for observation steps show tool_output
- [X] T034 [US3] Add evaluation template viewer to `app/page_inspect.py` — call `service.load_evaluation_template()`, display each rubric dimension with title, scale, weight, current score (or "Not yet scored"), and scoring guide text; show `st.info("Run evaluation first")` if template does not exist
- [X] T035 [US3] Add error handling to `app/page_inspect.py` — catch JSON parse errors for invalid trace, display `st.error` with parse message
- [ ] T036 [US3] Run `streamlit run app/app.py` and manually verify quickstart.md Scenario 4 (inspect a case)

**Checkpoint**: Inspect page works — trace steps, metadata, and evaluation details render correctly

---

## Phase 6: User Story 4 - View Aggregated Evaluation Report (Priority: P3)

**Goal**: User can generate and view aggregated summary reports with dimension statistics and failure distributions

**Independent Test**: With evaluation templates in reports/, click "Generate Report" and verify dimension statistics and failure counts are displayed.

### Implementation for User Story 4

- [X] T037 [US4] Create `app/page_report.py` with `render()` function — "Generate Report" button that calls `service.generate_summary_report()`
- [X] T038 [US4] Add report display to `app/page_report.py` — show overview (total cases, scored cases, rubric version), dimension statistics table (Dimension, Weight, Mean Score, Scored Count, Distribution), failure summary (primary failure counts, severity distribution), and recommendations as bulleted list
- [X] T039 [US4] Add output file confirmation to `app/page_report.py` — show `st.success` confirming summary.evaluation.json and summary.evaluation.md were written to reports/
- [X] T040 [US4] Add error handling to `app/page_report.py` — catch `RuntimeError` for missing evaluation templates, display `st.info` suggesting Evaluate page first; catch missing rubric error
- [ ] T041 [US4] Run `streamlit run app/app.py` and manually verify quickstart.md Scenario 5 (generate summary report)

**Checkpoint**: Report page works — summary statistics and failure distributions display correctly

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Full validation, linting, backward compatibility, cleanup

- [X] T042 Run full test suite: `pytest tests/ -v` to verify no regressions across all modules
- [X] T043 Run linting: `ruff check src/` and `ruff format --check src/`
- [X] T044 Run type checking: `mypy src/agenteval/core/service.py` to verify service layer types
- [X] T045 Run dataset validation: `agenteval-validate-dataset --repo-root .`
- [X] T046 Run backward compatibility check: verify `agenteval-eval-runner` and `agenteval-eval-report` CLI output is identical to pre-change behavior
- [ ] T047 Run quickstart.md Scenario 6 end-to-end (error handling across all pages)
- [X] T048 [P] Update src/agenteval/core/__init__.py to include `service` in the `__all__` list

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — creates app.py entry point + Generate page
- **US2 (Phase 4)**: Depends on Phase 2 + T021 from US1 (needs app.py with sidebar routing)
- **US3 (Phase 5)**: Depends on Phase 2 + T021 from US1 (needs app.py with sidebar routing)
- **US4 (Phase 6)**: Depends on Phase 2 + T021 from US1 (needs app.py with sidebar routing)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — creates the app entry point that other stories use
- **US2 (P2)**: Depends on T021 (app.py) from US1 — can run in parallel with US3 after T021 exists
- **US3 (P2)**: Depends on T021 (app.py) from US1 — can run in parallel with US2 after T021 exists
- **US4 (P3)**: Depends on T021 (app.py) from US1 — can run in parallel with US2/US3 after T021 exists

### Within Each User Story

- Service layer functions before UI pages
- Core page rendering before error handling
- Full page pass before checkpoint

### Parallel Opportunities

- T002 can run in parallel with T001 (different targets: directory vs pyproject.toml)
- T004-T011 can all run in parallel (independent test cases in same file)
- T012-T018 are sequential within service.py (same file, building incrementally)
- After T021 (app.py) exists, US2/US3/US4 page implementations can run in parallel (different files)
- T042-T048 in Phase 7: T043, T044, T045, T048 can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational — service layer (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (Generate + Validate page)
4. **STOP and VALIDATE**: Run `streamlit run app/app.py` — generate a case, validate, confirm files created
5. Verify backward compatibility: `agenteval-eval-runner` and `agenteval-validate-dataset` still work

### Incremental Delivery

1. Setup + Foundational → service layer ready, CLI unchanged, runner.py/report.py untouched
2. US1 → Generate & Validate page (MVP!)
3. US2 → Evaluate page (can run in parallel with US3 after T021)
4. US3 → Inspect page (can run in parallel with US2 after T021)
5. US4 → Report page
6. Polish → full suite validation, backward compatibility confirmed

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Service layer (Phase 2) is the critical path — it enables all UI stories
- runner.py and report.py are NEVER modified — all new logic goes in service.py
- UI pages import ONLY from `agenteval.core.service` — never from runner, report, validator, or generator directly
