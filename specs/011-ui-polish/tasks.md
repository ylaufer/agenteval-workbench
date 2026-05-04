# Tasks: UI Polish (Feature 011)

**Input**: `specs/011-ui-polish/`
**Branch**: `011-ui-polish`

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Shared Components (Blocking Prerequisites)

- [X] T001 Create `app/components/empty_state.py` with `render_empty_state(icon, title, message, action_label=None, action_page=None)` — centered bordered container, Material icon, title, caption, optional button that sets `st.session_state.nav_to_page` and triggers rerun
- [X] T002 Create `app/components/workflow_nav.py` with `render_next_step_hint(current_page)` — shows a `st.info` banner (with icon) suggesting the logical next page after completing an action; mapping: generate→inspect, inspect→evaluate, evaluate→report, report→compare

**Checkpoint**: Both components importable; no UI changes yet

---

## Phase 2: Sidebar Workflow Indicator

- [X] T003 Update `app/app.py` sidebar: add a "Workflow" section below navigation showing the 4-step pipeline (Generate → Inspect → Evaluate → Report) with the current page highlighted using `:material/arrow_right:` and completed steps using `:material/check_circle:`; use `st.session_state.get("nav_to_page")` to redirect navigation when set by empty state buttons

**Checkpoint**: Sidebar shows workflow steps; current page is highlighted

---

## Phase 3: Empty States Integration

- [X] T004 [P] [US2] Update `app/page_inspect.py`: replace bare `st.info("No cases...")` with `render_empty_state(":material/folder_open:", "No cases yet", "Generate benchmark cases to start inspecting traces.", "Go to Generate", "Generate")`
- [X] T005 [P] [US2] Update `app/page_evaluate.py`: replace bare `st.info("No cases...")` with `render_empty_state(":material/rule:", "No cases to evaluate", "Generate benchmark cases first, then run auto-scoring here.", "Go to Generate", "Generate")`; replace bare `st.info("No evaluation runs yet...")` with `render_empty_state(":material/history:", "No runs yet", "Run auto-scoring above to create the first evaluation run.")`
- [X] T006 [P] [US2] Update `app/page_report.py`: wrap the "no evaluation templates" info path with `render_empty_state(":material/summarize:", "No evaluations found", "Run the evaluation pipeline on the Evaluate page first.", "Go to Evaluate", "Evaluate")`
- [X] T007 [P] [US2] Update `app/page_compare.py`: replace `st.info("Need at least two...")` with `render_empty_state(":material/compare:", "Not enough runs to compare", "Complete at least two evaluation runs on the Evaluate page.", "Go to Evaluate", "Evaluate")`

**Checkpoint**: Empty states show on all pages when no data exists

---

## Phase 4: Next-Step Navigation Hints

- [X] T008 [US1] Update `app/page_generate.py`: after successful case generation, call `render_next_step_hint("Generate")` to suggest inspecting the new case
- [X] T009 [US1] Update `app/page_evaluate.py`: after successful auto-scoring result, call `render_next_step_hint("Evaluate")` to suggest generating a report
- [X] T010 [US1] Update `app/page_report.py`: after successful report generation, call `render_next_step_hint("Report")` to suggest comparing with other runs

**Checkpoint**: Next-step hints appear after completing key actions

---

## Phase 5: Badge-Based Status Indicators

- [X] T011 [US7] Update `app/page_evaluate.py` case list rows: replace plain `c3.write(case["primary_failure"])` and `c4.write(case["severity"])` with `st.badge()` calls — severity colors: Critical=red, High=orange, Medium=yellow, Low=blue; failure type uses default gray badge
- [X] T012 [US7] Update `app/page_inspect.py` step rendering: replace plain `st.markdown` color string badges for step type with `st.badge()` — thought=blue, tool_call=orange, observation=green, final_answer=violet; replace severity text with `st.badge()` — flagged=red, clean=green

**Checkpoint**: Severity and step-type indicators use `st.badge()`

---

## Phase 6: Polish & Validation

- [X] T013 Run `pytest tests/ -v` — confirm 0 failures
- [X] T014 [P] Run `ruff check src/` and `mypy src/` — confirm 0 new errors
- [X] T015 [P] Run `agenteval-validate-dataset --repo-root .` — confirm passes

---

## Dependencies

- T001, T002 must complete before T003–T012
- T003 depends on T001 (uses `nav_to_page` session key)
- T004–T007 depend on T001
- T008–T010 depend on T002
- T011–T012 independent of T001/T002
- T013–T015 depend on all prior tasks
