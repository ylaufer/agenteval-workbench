# Tasks: Run Tracking

**Input**: Design documents from `specs/003-run-tracking/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: Add types and register new CLI entry points

- [X] T001 Add RunStatus and RunRecord types to src/agenteval/core/types.py
- [X] T002 Register new CLI entry points (agenteval-list-runs, agenteval-inspect-run) in pyproject.toml
- [X] T003 Add "runs" to module exports in src/agenteval/core/__init__.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core run tracking library module that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Implement generate_run_id() in src/agenteval/core/runs.py
- [X] T005 Implement create_run() in src/agenteval/core/runs.py — creates run directory under runs/<run_id>/, writes initial run.json with status running, validates paths via _safe_resolve_within()
- [X] T006 Implement complete_run() and fail_run() in src/agenteval/core/runs.py — read existing run.json, update status/timestamps/error, write back
- [X] T007 Implement get_run() and get_run_dir() in src/agenteval/core/runs.py — lookup a run by ID, return RunRecord or None
- [X] T008 Write tests for run lifecycle (create, complete, fail) in tests/test_runs.py — cover generate_run_id format, create_run directory creation, complete_run/fail_run status transitions, get_run lookup, missing run returns None

**Checkpoint**: Core run lifecycle works — can create, complete, fail, and retrieve individual runs

---

## Phase 3: User Story 1 — Track an Evaluation Run (Priority: P1) MVP

**Goal**: Each evaluation execution automatically produces a tracked run record with results persisted exclusively under the run directory

**Independent Test**: Run the evaluation pipeline once and verify that a new run record is created with unique ID, timestamp, dataset reference, and evaluation results are persisted under `runs/<run_id>/`

### Implementation for User Story 1

- [X] T009 [US1] Modify service.run_evaluation() in src/agenteval/core/service.py — create run via runs.create_run(), pass run dir as output_dir to runner.main(), then call report.main() against the run dir to generate summary under the run record, call complete_run on success or fail_run on error
- [X] T010 [US1] Write tests for run-aware service.run_evaluation() in tests/test_service.py — verify run directory created, run.json written with correct status, evaluation files persisted under run dir, failure case creates failed run record
- [X] T011 [US1] Verify backward compatibility of agenteval-eval-runner CLI — run the existing CLI command directly and confirm it still writes to the specified --output-dir without run tracking

**Checkpoint**: Evaluation pipeline creates tracked runs. Results persisted under runs/<run_id>/ exclusively. Existing CLI unchanged.

---

## Phase 4: User Story 2 — List Past Runs (Priority: P2)

**Goal**: Users can see a chronological list of all past evaluation runs

**Independent Test**: Execute multiple evaluation runs, then verify list_runs() returns all runs in reverse chronological order with correct metadata

### Implementation for User Story 2

- [X] T012 [US2] Implement list_runs() in src/agenteval/core/runs.py — scan runs/ directory, read run.json from each subdirectory, sort by started_at descending, handle missing/invalid run.json gracefully
- [X] T013 [US2] Add service.list_runs() to src/agenteval/core/service.py — delegate to runs.list_runs(), convert RunRecord list to list of dicts
- [X] T014 [US2] Write tests for list_runs() in tests/test_runs.py — multiple runs sorted correctly, empty runs directory returns empty list, corrupted run.json skipped gracefully, runs/ directory missing returns empty list
- [X] T015 [US2] Add run history section to app/page_evaluate.py — display run list table below evaluation action with run ID, status, case count, started timestamp

**Checkpoint**: Users can list all past runs in reverse chronological order via library, service layer, and UI

---

## Phase 5: User Story 3 — Inspect a Run (Priority: P2)

**Goal**: Users can drill into a specific run to see full details — metadata, per-case results, and summary statistics

**Independent Test**: Select a past run and verify inspect shows all per-case evaluation results, summary stats, dataset reference, configuration, and timestamps

### Implementation for User Story 3

- [X] T016 [US3] Implement get_run_results() and get_run_summary() in src/agenteval/core/runs.py — load evaluation JSON files from run directory, load summary.evaluation.json
- [X] T017 [P] [US3] Add service.get_run(), service.get_run_results(), service.get_run_summary() to src/agenteval/core/service.py — delegate to runs module, convert to dicts
- [X] T018 [US3] Write tests for get_run_results() and get_run_summary() in tests/test_runs.py — run with evaluation files returns correct list, run with summary returns dict, missing files return empty/None
- [X] T019 [US3] Add run detail view to app/page_inspect.py — add run selector dropdown, display run metadata, per-case summary table, and aggregated summary when a run is selected

**Checkpoint**: Users can inspect any past run to see full details via library, service layer, and UI

---

## Phase 6: User Story 4 — Access Run Results via CLI (Priority: P3)

**Goal**: List and inspect runs from the command line for scripting and automation

**Independent Test**: Run CLI list-runs and inspect-run commands, verify output matches runs created

### Implementation for User Story 4

- [X] T020 [US4] Implement main_list() CLI entry point in src/agenteval/core/runs.py — format tabular output with run ID, status, case count, started timestamp; handle empty state with suggestion message
- [X] T021 [US4] Implement main_inspect() CLI entry point in src/agenteval/core/runs.py — accept run_id positional argument, display full run metadata and per-case results table; exit code 1 if run not found
- [X] T022 [US4] Write tests for CLI entry points in tests/test_runs.py — test main_list output format, empty state message, main_inspect with valid and invalid run_id, exit codes
- [X] T023 [US4] Re-install package in editable mode and verify both new CLI commands work: agenteval-list-runs and agenteval-inspect-run <run_id>

**Checkpoint**: All run tracking features accessible via CLI

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation and documentation

- [X] T024 Run full test suite (pytest tests/ -v) and verify all tests pass including new test_runs.py
- [X] T025 Run linting and type checking (ruff check src/ && ruff format --check src/ && mypy src/)
- [X] T026 Verify backward compatibility: run agenteval-eval-runner, agenteval-eval-report, agenteval-validate-dataset and confirm identical behavior
- [X] T027 Update README.md — add new CLI commands (agenteval-list-runs, agenteval-inspect-run) to Key Commands section, update project structure to include runs.py
- [X] T028 Verify Streamlit UI works end-to-end: evaluate page creates runs, run history displays, inspect page shows run details

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (types must exist) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — BLOCKS US2, US3 (needs runs to exist for listing/inspecting)
- **US2 (Phase 4)**: Depends on Phase 3 (needs runs to list)
- **US3 (Phase 5)**: Depends on Phase 3 (needs runs to inspect); can run in parallel with US2
- **US4 (Phase 6)**: Depends on Phase 4 + Phase 5 (CLI exposes both list and inspect)
- **Polish (Phase 7)**: Depends on all prior phases

### User Story Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundational) → Phase 3 (US1: Track Run)
                                                  ├─→ Phase 4 (US2: List Runs)  ──┐
                                                  └─→ Phase 5 (US3: Inspect Run) ─┤
                                                                                   └─→ Phase 6 (US4: CLI)
                                                                                         └─→ Phase 7 (Polish)
```

### Parallel Opportunities

- **Phase 4 + Phase 5**: US2 (List) and US3 (Inspect) can run in parallel after US1 is complete
- **Within Phase 2**: T004-T007 are sequential (each builds on prior), but T008 (tests) can start after T004
- **Within Phase 5**: T017 (service layer) can run in parallel with T016 (runs module) since they're different files

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T008)
3. Complete Phase 3: User Story 1 (T009-T011)
4. **STOP and VALIDATE**: Evaluation creates tracked runs, results persisted correctly
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Run lifecycle works
2. US1 (Track Run) → Test independently → MVP!
3. US2 (List Runs) + US3 (Inspect Run) → Test independently → Full run management
4. US4 (CLI) → Test independently → Automation-ready
5. Polish → Production-ready

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- No new runtime dependencies — stdlib only (datetime, secrets, json)
- runner.py and report.py are NOT modified — run tracking is orchestration in runs.py + service.py
- Existing CLI commands remain backward compatible throughout all phases
