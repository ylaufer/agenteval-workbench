# Tasks: Custom Rubric Builder (Feature 010)

**Input**: `specs/010-custom-rubric-builder/`
**Branch**: `010-custom-rubric-builder`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)
- Tests included per spec.md Testing Requirements

---

## Phase 1: Setup

**Purpose**: Create the core data model stub that all subsequent phases depend on.

- [X] T001 Create `src/agenteval/core/rubric_builder.py` with `RubricDimension` and `RubricDraft` dataclasses, `VALID_SCALES` tuple, and `SCALE_KEYS` dict per `specs/010-custom-rubric-builder/data-model.md`

**Checkpoint**: Data model classes importable; no functions implemented yet

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement all core library functions in `rubric_builder.py`. All user stories depend on this phase.

**⚠️ CRITICAL**: No UI or test work can begin until this phase is complete.

- [X] T002 Implement `list_templates(repo_root)` and `load_template(template_id, repo_root)` in `src/agenteval/core/rubric_builder.py` (scan `rubrics/templates/*.json`, raise `FileNotFoundError` if missing)
- [X] T003 Implement `validate_rubric(rubric)` in `src/agenteval/core/rubric_builder.py` — jsonschema validation against `schemas/rubric_schema.json` plus semantic checks: `name` matches `^[a-z0-9_]+$`, scoring_guide has all keys for scale, at least one dimension
- [X] T004 Implement `next_version(name, repo_root)` in `src/agenteval/core/rubric_builder.py` — scan `rubrics/v*_{name}.json`, return `"v1"` if none exist, `"v{n+1}"` otherwise
- [X] T005 Implement `save_rubric(name, rubric, repo_root)` in `src/agenteval/core/rubric_builder.py` — validate name pattern, call `validate_rubric()`, set `rubric["version"]`, write `rubrics/v{N}_{name}.json` via `_safe_resolve_within()`
- [X] T006 Implement `list_rubrics(repo_root)` in `src/agenteval/core/rubric_builder.py` — return sorted stems from `rubrics/*.json` excluding `templates/` subdirectory

**Checkpoint**: All 6 functions importable and callable; no UI yet

---

## Phase 3: User Story 1 — Template-Based Rubric Creation (Priority: P1) 🎯 MVP

**Goal**: 4 starter templates exist on disk; library functions work end-to-end; service layer wrappers present; test coverage for the full create→validate→save pipeline.

**Independent Test**: `python -c "from agenteval.core.rubric_builder import list_templates, load_template, save_rubric; from agenteval.dataset.validator import _get_repo_root; r = _get_repo_root(); assert len(list_templates(r)) == 4; t = load_template('rag_pipeline', r); print(save_rubric('rag_pipeline', t | {'version':'draft'}, r))"`

- [X] T007 [P] [US1] Create `rubrics/templates/general_agent.json` with 6 dimensions matching `rubrics/v1_agent_general.json` (accuracy, tool_use, instruction_following, ui_grounding, efficiency, security_safety) on scale `"0-2"` with complete scoring guides
- [X] T008 [P] [US1] Create `rubrics/templates/rag_pipeline.json` with 4 dimensions: `accuracy`, `retrieval_quality`, `source_attribution`, `hallucination_detection` on scale `"0-2"` with complete scoring guides
- [X] T009 [P] [US1] Create `rubrics/templates/customer_support.json` with 4 dimensions: `tone_empathy`, `resolution_quality`, `escalation_appropriateness`, `policy_compliance` on scale `"0-2"` with complete scoring guides
- [X] T010 [P] [US1] Create `rubrics/templates/code_generation.json` with 4 dimensions: `correctness`, `test_coverage`, `security`, `code_style` on scale `"0-2"` with complete scoring guides
- [X] T011 [US1] Add 5 service layer wrappers to `src/agenteval/core/service.py`: `list_rubric_templates()`, `load_rubric_template(template_id)`, `validate_rubric(rubric)`, `save_rubric(name, rubric) -> str`, `list_rubrics()` — each delegates to `rubric_builder.*` per `specs/010-custom-rubric-builder/contracts/library.md`
- [X] T012 [US1] Write `tests/test_rubric_builder.py` with tests for: `list_templates` returns 4 sorted IDs, `load_template` returns dict with `dimensions` key, `load_template` raises `FileNotFoundError` for unknown ID, `list_rubrics` excludes templates dir, `next_version` returns `"v1"` when none exist and `"v2"` when `v1_{name}.json` exists
- [X] T013 [US1] Add `validate_rubric` and `save_rubric` tests to `tests/test_rubric_builder.py`: valid rubric passes, rubric missing `version` fails, rubric with invalid dimension name fails, rubric with incomplete scoring_guide keys fails, `save_rubric` writes file with correct version stem, second save increments to `v2`

**Checkpoint**: `pytest tests/test_rubric_builder.py -v` passes; all 4 templates loadable via library

---

## Phase 4: User Story 2 — Dimension Management UI (Priority: P1)

**Goal**: Rubric Builder page renders with template selector, editable dimension list (expanders), add/remove/reorder controls.

**Independent Test**: Launch Streamlit, navigate to Rubric Builder, load RAG Pipeline template, add a dimension, remove a dimension, reorder with ↑/↓, verify session state updates correctly.

- [X] T014 [US2] Create `app/page_rubric.py` with `render_rubric_builder()` function: initialize session state with `st.session_state.setdefault("rubric_dims", [])`, `st.session_state.setdefault("rubric_template_source", None)`, `st.session_state.setdefault("rubric_name", "")`, `st.session_state.setdefault("rubric_description", "")`, render template selector dropdown (options from `service.list_rubric_templates()` + "Blank"), rubric name/description text inputs, and dimension list as `st.expander` per dimension showing name/scale/weight summary
- [X] T015 [US2] Add dimension field editor inside each `st.expander` in `app/page_rubric.py`: `name` text_input, `title` text_input, `description` text_area, `scale` selectbox (`"0-2"/"1-5"/"0-4"`), `weight` number_input (min 0.0, step 0.1), `evidence_required` checkbox, scoring_guide text_areas auto-derived from selected scale keys (one per score value)
- [X] T016 [US2] Add ↑/↓ swap buttons and "Remove" button per dimension row in `app/page_rubric.py`: ↑ disabled at index 0, ↓ disabled at last index, Remove blocked when only 1 dimension remains (show `st.warning`)
- [X] T017 [US2] Add "+ Add Dimension" button in `app/page_rubric.py` that appends a blank dimension dict with default scale `"0-2"`, weight `1.0`, evidence_required `True`, and empty scoring_guide keys for the scale
- [X] T018 [US2] Add "Rubric Builder" page entry to `st.navigation` in `app/app.py` pointing to `app/page_rubric.py`

**Checkpoint**: Rubric Builder page loads in Streamlit; template selector populates from `rubrics/templates/`; dimensions are add/remove/reorder functional

---

## Phase 5: User Story 3 — Validation and Preview (Priority: P1)

**Goal**: Users can preview rubric as JSON/YAML and explicitly validate before saving; save is blocked on validation failure.

**Independent Test**: Load a template, click Validate → see green success; remove scoring guide text for a key → click Validate → see red error; click Save → file written to `rubrics/v1_{name}.json`.

- [X] T019 [US3] Add `st.tabs(["JSON Preview", "YAML Preview"])` section in `app/page_rubric.py`: JSON tab renders current session state dims as rubric dict via `st.code(json.dumps(rubric, indent=2), language="json")`
- [X] T020 [US3] Add `_rubric_to_yaml_preview(rubric: dict) -> str` helper in `app/page_rubric.py` using stdlib-only recursive formatter for the known rubric structure (handles str/int/float/bool/list/dict, indents 2 spaces per level); populate YAML Preview tab with `st.code(yaml_text, language="yaml")`
- [X] T021 [US3] Add "Validate" button in `app/page_rubric.py` calling `service.validate_rubric(rubric_dict)`, storing result in `st.session_state["rubric_valid"]`; display `st.success("Rubric is valid")` or `st.error` block listing each error; set `st.session_state["rubric_valid"] = False` whenever any dimension field changes (via widget `on_change` callbacks)
- [X] T022 [US3] Add "Save Rubric" button in `app/page_rubric.py` disabled/gated when `st.session_state.get("rubric_valid") is not True`; on click: call `service.save_rubric(name, rubric_dict)`, display `st.success(f"Saved: {path}")`, clear `rubric_valid` state

**Checkpoint**: Full US3 done; `pytest tests/test_rubric_builder.py -v` still green; quickstart.md Scenario 3 works end-to-end in Streamlit

---

## Phase 6: User Story 4 — Rubric Mismatch Warning (Priority: P2)

**Goal**: Comparing two runs with different rubric versions shows a visible warning.

**Independent Test**: Inspect `src/agenteval/core/comparison.py` — `ComparisonResult` has `rubric_mismatch: bool`; `page_compare.py` renders `st.warning(...)` when flag is True.

- [X] T023 [US4] Add `rubric_mismatch: bool` and `rubric_versions: tuple[str, str]` fields to `ComparisonResult` in `src/agenteval/core/comparison.py`; add rubric version extraction logic to `compare_runs()` that reads `rubric_path` from each run's `run.json`, extracts the filename stem as the version ID, and sets `rubric_mismatch = True` when they differ
- [X] T024 [US4] In `app/page_compare.py`, after comparison result is loaded, check `result.rubric_mismatch` and display `st.warning(f"⚠️ Rubric mismatch: run A used '{result.rubric_versions[0]}', run B used '{result.rubric_versions[1]}'. Scores may not be directly comparable.")` before the comparison table

**Checkpoint**: Two runs with different rubric versions show warning banner in Compare page

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T025 Run `pytest tests/test_rubric_builder.py -v` and `pytest tests/ -v` to confirm all tests pass (0 failures)
- [X] T026 [P] Run `agenteval-validate-dataset --repo-root .` to confirm new files in `rubrics/templates/` pass security scan
- [X] T027 [P] Verify `ruff check src/` and `mypy src/` pass with zero new errors after all changes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user story phases
- **US1 (Phase 3)**: Depends on Phase 2
- **US2 (Phase 4)**: Depends on Phase 2 (library) — can start alongside US1 once Phase 2 is done
- **US3 (Phase 5)**: Depends on Phase 4 (same page file)
- **US4 (Phase 6)**: Depends on Phase 2 only (comparison.py is independent of the UI)
- **Polish (Phase 7)**: Depends on all phases complete

### User Story Dependencies

- **US1 (P1)**: After Foundational — independent of US2/US3/US4
- **US2 (P1)**: After Foundational — independent of US1/US3/US4
- **US3 (P1)**: After US2 (same file, additive changes to page_rubric.py)
- **US4 (P2)**: After Foundational — independent of US1/US2/US3

### Parallel Opportunities

- T007, T008, T009, T010 — all create different template files, fully parallel
- T012, T013 are in the same test file — run sequentially
- T014–T017 are all in `page_rubric.py` — run sequentially (same file)
- T025, T026, T027 — different commands, fully parallel

---

## Parallel Example: US1 Templates

```bash
# All 4 template files are independent — create in parallel:
Task T007: rubrics/templates/general_agent.json
Task T008: rubrics/templates/rag_pipeline.json
Task T009: rubrics/templates/customer_support.json
Task T010: rubrics/templates/code_generation.json
```

---

## Implementation Strategy

### MVP First (US1 + US2 + US3 Only — the core builder)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: US1 — templates + tests + service wrappers
4. Complete Phase 4: US2 — dimension management UI
5. Complete Phase 5: US3 — validation + preview + save
6. **STOP and VALIDATE**: Run quickstart.md Scenario 3 in Streamlit
7. Ship US4 (mismatch warning) as follow-up if pressed for time

### Incremental Delivery

1. Phase 1+2 → Library complete, testable via Python REPL
2. Phase 3 → Templates available, full pipeline tested
3. Phase 4+5 → Full Streamlit UI working (US1+US2+US3)
4. Phase 6 → Comparison safety net (US4)
5. Phase 7 → All checks green, ready to merge

---

## Notes

- [P] tasks = different files, no inter-task dependencies
- [Story] label maps task to its user story for traceability
- `save_rubric` must use `_safe_resolve_within()` for path safety (constitution §I)
- No new runtime dependencies — YAML preview uses stdlib only (constitution §V)
- Template files are JSON (not YAML) — consistent with rest of codebase
- All dimension `name` fields must match `^[a-z0-9_]+$` (schema constraint)
- Scoring guide keys must exactly match the chosen scale's key set
