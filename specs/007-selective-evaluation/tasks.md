# Tasks: Selective Evaluation

**Input**: Design documents from `/specs/007-selective-evaluation/`
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ ✅ quickstart.md ✅

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared state dependencies)
- **[Story]**: User story this task belongs to (US1–US4)
- Exact file paths included in all descriptions

---

## Phase 1: Setup

**Purpose**: Verify the existing baseline passes and create the new module stub.

- [x] T001 Activate venv and confirm `pytest tests/ -v` passes clean before any changes
- [x] T002 Create `src/agenteval/core/filtering.py` with module docstring, `from __future__ import annotations`, and stub imports (`fnmatch`, `Path`, `Trace`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core filtering library, tagger extension, scorer plumbing, and service functions. All user stories depend on this phase.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T003 Extend `tag_trace()` in `src/agenteval/core/tagger.py` to append structural tags: `has_tool_calls` (any `tool_call` step), `multi_step` (step count > 3), `has_final_answer` (any `final_answer` step) — append after existing failure tags, backward compatible
- [x] T004 [P] Implement `derive_structural_tags(trace: Trace) -> tuple[str, ...]` in `src/agenteval/core/filtering.py` returning `has_tool_calls`, `multi_step`, `has_final_answer` based on steps
- [x] T005 [P] Implement `get_dataset_tags(case_dirs: list[Path]) -> set[str]` in `src/agenteval/core/filtering.py` — loads `trace.json` per case, calls `tag_trace()`, returns union of all tags; skips unreadable cases silently
- [x] T006 Implement `filter_cases(case_dirs, case_ids, failure_type, severity, tags, pattern) -> list[Path]` in `src/agenteval/core/filtering.py` — AND logic across all non-None criteria; `case_ids` overrides all filters; `failure_type`/`severity` read from `expected_outcome.md` front matter via `load_case_metadata()`; `tags` derived live via `tag_trace()`; `pattern` via `fnmatch.fnmatch()`; unreadable/missing files skip silently; returns empty list (not error) on zero match (depends on T003, T004, T005)
- [x] T007 Add optional `case_filter: list[Path] | None = None` parameter to `score_dataset()` in `src/agenteval/core/scorer.py` — when not None, use `case_filter` as the case dirs list instead of iterating `dataset_dir`; existing callers unaffected
- [x] T008 Add `run_selective_evaluation(case_ids, dataset_dir, output_dir) -> dict[str, Any]` to `src/agenteval/core/service.py` — resolves case dirs from case_ids, warns and skips missing IDs, creates tracked run, calls `score_dataset(case_filter=resolved_dirs)`, returns `{"results": [...], "errors": {...}, "run_id": "..."}` (depends on T006, T007)
- [x] T009 [P] Add `get_dataset_tags(dataset_dir) -> set[str]` wrapper to `src/agenteval/core/service.py` delegating to `filtering.get_dataset_tags()` — used by UI for tag dropdown population (depends on T005)
- [x] T010 [P] Write unit tests for `filtering.py` and tagger structural tags in `tests/test_filtering.py` — cover: `filter_cases` with each criterion independently, AND combination, zero-match, missing files, `derive_structural_tags` all three tags, `get_dataset_tags` union behavior; also add structural tag assertions to `tests/test_tagger.py`

**Checkpoint**: `pytest tests/test_filtering.py tests/test_tagger.py -v` passes. Foundation ready.

---

## Phase 3: User Story 1 — CLI Filtering (Priority: P1) 🎯 MVP

**Goal**: `agenteval-auto-score` accepts `--cases`, `--filter-failure`, `--filter-severity`, `--filter-tag`, `--filter-pattern`; filters dataset before scoring; backward compatible.

**Independent Test**:
```bash
agenteval-auto-score --cases case_001
agenteval-auto-score --filter-severity Critical
agenteval-auto-score --filter-pattern "case_0*"
# With no matching cases:
agenteval-auto-score --filter-failure "nonexistent" # exits 0 with message
```

- [x] T011 [US1] Add `--cases`, `--filter-failure`, `--filter-severity`, `--filter-tag`, `--filter-pattern` arguments to `argparse` in `src/agenteval/core/scorer.py:main()` — `--cases` is comma-separated string; `--filter-severity` and `--filter-tag` are comma-separated; all default to `None`
- [x] T012 [US1] Wire filter args in `scorer.main()`: parse comma-separated values, call `filter_cases()` to produce `case_filter`, pass to `score_dataset(case_filter=...)` in `src/agenteval/core/scorer.py`
- [x] T013 [US1] Handle edge cases in `scorer.main()` in `src/agenteval/core/scorer.py`: zero-match filter prints `"No cases matched the specified filter."` and exits 0; nonexistent case IDs from `--cases` print per-ID warning to stderr and continue with valid IDs
- [x] T014 [P] [US1] Write CLI filter tests in `tests/test_scorer.py` — cover: `--cases` with valid IDs, `--cases` with unknown ID (warning + skip), `--filter-failure`, `--filter-severity`, `--filter-pattern`, zero-match filter exit 0, combined filters AND behavior

**Checkpoint**: `agenteval-auto-score --cases case_001` scores only that case. All prior behavior unchanged when no filter args given.

---

## Phase 4: User Story 2 — Single Case Evaluation UI (Priority: P2)

**Goal**: Users can click "Evaluate This Case" from the Inspect page to auto-score a single case and see results inline without leaving the page.

**Independent Test**: Open Inspect page → select any case → click "Evaluate This Case" → see dimension scores inline.

- [x] T015 [US2] Import `run_selective_evaluation` from `agenteval.core.service` in `app/page_inspect.py` and add "Evaluate This Case" button to the per-case detail view (below trace steps), calling `run_selective_evaluation([case_id])`
- [x] T016 [US2] Display auto-scoring results inline after single-case evaluation in `app/page_inspect.py` — show dimension scores table (dimension name, score, notes) and any per-case errors; use `st.success` / `st.error` for feedback
- [x] T017 [US2] Wrap single-case evaluation in `st.spinner("Running auto-scoring...")` in `app/page_inspect.py` and add clear label "Run Auto-Scoring on this case" on the button

**Checkpoint**: Single-case evaluate button visible in Inspect page; clicking it shows scores without navigating away.

---

## Phase 5: User Story 3 — Multi-Select & Filter-Based UI (Priority: P3)

**Goal**: Evaluate page shows a filterable case list with checkboxes; users can evaluate selected cases or all filtered cases via clearly labelled auto-scoring buttons.

**Independent Test**: Open Evaluate page → select severity filter → check 2 cases → click "Run Auto-Scoring on Selected (2)" → see per-case results and errors summary.

- [x] T018 [US3] Load case list with metadata (failure_type, severity, tags) on Evaluate page in `app/page_evaluate.py` — call `list_cases()`, `load_case_metadata()` per case, `get_dataset_tags()` for tag options; cache with `st.session_state` to avoid re-scan on every widget interaction
- [x] T019 [US3] Add filter controls row in `app/page_evaluate.py`: failure type `st.selectbox` (values from dataset), severity `st.multiselect` (Critical/High/Medium/Low), tags `st.multiselect` (from `get_dataset_tags()`), pattern `st.text_input` (glob hint)
- [x] T020 [US3] Apply active filters to case list using `filter_cases()` and render filtered cases as checkboxes in `app/page_evaluate.py` — show case_id, failure_type, severity per row
- [x] T021 [US3] Show empty-state message `"No cases match the current filter."` and disable evaluate buttons when filtered list is empty in `app/page_evaluate.py`
- [x] T022 [US3] Add "Run Auto-Scoring on Selected (N)" button in `app/page_evaluate.py` — calls `run_selective_evaluation(selected_case_ids)`; N reflects checked count; disabled when nothing checked
- [x] T023 [US3] Add "Evaluate All Filtered (N)" button in `app/page_evaluate.py` — calls `run_selective_evaluation(filtered_case_ids)`; N reflects filtered count
- [x] T024 [US3] Display batch results after evaluation in `app/page_evaluate.py` — results table (case_id, dimensions scored, auto_tags) plus errors summary "N evaluated, M failed" with per-case error details using `st.warning` / `st.error`

**Checkpoint**: Filter controls visible; selecting severity=Critical and clicking "Evaluate All Filtered" scores only Critical cases.

---

## Phase 6: User Story 4 — Run Metadata Recording (Priority: P4)

**Goal**: Filter criteria used in a selective evaluation run are recorded in run.json and visible in run history.

**Independent Test**: Run `agenteval-auto-score --filter-severity Critical`; inspect `runs/<run_id>/run.json` — `filter_criteria` key present with `{"severity": ["Critical"]}`.

- [x] T025 [US4] Serialize `filter_criteria` dict into run metadata in `src/agenteval/core/service.py:run_selective_evaluation()` — store as `{"case_ids": ..., "failure_type": ..., "severity": ..., "tags": ..., "pattern": ...}` in `RunRecord` config or as extra field in `run.json`
- [x] T026 [US4] Display filter criteria in run history section of `app/page_evaluate.py` — show filter summary line (e.g., "severity: Critical, High") next to run ID; show "all cases" when no filter was applied

**Checkpoint**: `runs/<run_id>/run.json` contains `filter_criteria`. Run history shows filter used.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [x] T027 [P] Write integration tests for selective evaluation end-to-end in `tests/test_service.py` — cover: `run_selective_evaluation()` with valid IDs, missing IDs (warn + skip), empty list; verify `run.json` written with filter_criteria
- [x] T028 [P] Write run metadata persistence tests in `tests/test_runs.py` — verify filter_criteria round-trips through create/read run JSON
- [x] T029 Run full validation suite: `agenteval-validate-dataset --repo-root .`, `ruff check src/`, `ruff format --check src/`, `mypy src/`, `pytest tests/ -v` — fix any issues
- [x] T030 [P] Add CLI reference for `--cases` / `--filter-*` args to `docs/` (update or create `docs/selective_evaluation.md`) with examples from `quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **blocks all user stories**
- **Phase 3 (US1 CLI)**: Depends on Phase 2
- **Phase 4 (US2 Single UI)**: Depends on Phase 2
- **Phase 5 (US3 Multi-Select UI)**: Depends on Phase 2
- **Phase 6 (US4 Run Metadata)**: Depends on Phase 2; T026 depends on T025
- **Phase 7 (Polish)**: Depends on all desired stories complete

### User Story Dependencies

- **US1 (CLI)**: Only needs Phase 2 — independently testable via CLI
- **US2 (Single Case UI)**: Only needs Phase 2 + T008 — independently testable in Inspect page
- **US3 (Multi-Select UI)**: Needs Phase 2 + T008 + T009 — independently testable in Evaluate page
- **US4 (Run Metadata)**: Needs T008 (run_selective_evaluation) — T025 extends it, T026 is UI-only

### Within Each Phase

- T003 before T006 (filter_cases calls tag_trace)
- T006 before T008 (service calls filter_cases)
- T007 before T008 (service calls score_dataset with case_filter)
- T005 before T009 (service wraps get_dataset_tags)
- T008 before T015, T022, T023 (UI calls service)
- T009 before T019 (UI uses get_dataset_tags for tag dropdown)
- T018 before T020 before T021 before T022/T023 (UI build order within page)

### Parallel Opportunities

Within Phase 2 (after T003): T004, T005, T007, T009, T010 can run in parallel
Within Phase 3: T011 → T012 → T013 sequential; T014 parallel with T011–T013
Within Phase 5: T018 → T019 → T020 → T021 → T022/T023 → T024 sequential within page
Phases 3, 4, 5, 6 can start in parallel once Phase 2 is complete

---

## Parallel Example: Phase 2 (Foundational)

```
# After T003 completes:
Task: "Implement derive_structural_tags() in src/agenteval/core/filtering.py"        [T004]
Task: "Implement get_dataset_tags() in src/agenteval/core/filtering.py"             [T005]
Task: "Add case_filter param to score_dataset() in src/agenteval/core/scorer.py"    [T007]
Task: "Add get_dataset_tags() wrapper to src/agenteval/core/service.py"             [T009]
Task: "Write unit tests in tests/test_filtering.py + tests/test_tagger.py"          [T010]

# Then T006 (filter_cases) after T004+T005 complete
# Then T008 (run_selective_evaluation) after T006+T007 complete
```

---

## Implementation Strategy

### MVP (US1 — CLI Filtering Only): T001–T014

1. Complete Phase 1 (Setup)
2. Complete Phase 2 (Foundational)
3. Complete Phase 3 (US1 CLI)
4. **STOP and VALIDATE**: `agenteval-auto-score --cases case_001` works; full test suite passes
5. All prior CLI behavior unchanged

### Incremental Delivery

1. Phase 1 + 2 → filtering library ready
2. Phase 3 (US1) → CLI filtering live → **MVP**
3. Phase 4 (US2) → single-case UI evaluate button
4. Phase 5 (US3) → full filter UI on evaluate page
5. Phase 6 (US4) → run metadata recorded
6. Phase 7 → polish, docs, full test suite

---

## Summary

| Phase | User Story | Tasks | Key Deliverable |
|---|---|---|---|
| 1 — Setup | — | T001–T002 | Clean baseline, filtering.py stub |
| 2 — Foundational | — | T003–T010 | filtering.py, tagger tags, scorer/service plumbing |
| 3 — CLI Filtering | US1 (P1) | T011–T014 | `--cases` / `--filter-*` args on agenteval-auto-score |
| 4 — Single Case UI | US2 (P2) | T015–T017 | "Evaluate This Case" in Inspect page |
| 5 — Multi-Select UI | US3 (P3) | T018–T024 | Filter controls + checkboxes in Evaluate page |
| 6 — Run Metadata | US4 (P4) | T025–T026 | filter_criteria in run.json + run history |
| 7 — Polish | — | T027–T030 | Integration tests, validation suite, docs |

**Total**: 30 tasks
**MVP scope**: T001–T014 (Phases 1–3, 14 tasks)
